"""Pinned per-video metric calls with actual decoder/selection observations.

Model construction, checkpoint validation, CPU acceptance and GPU admission
belong to the scoring driver. This module imports no model and downloads
nothing. Its caller supplies the already validated original model objects.
"""
from contextlib import contextmanager, ExitStack
from fractions import Fraction
import hashlib
import inspect
import math
from pathlib import Path
from statistics import mean

from .automatic_quality_r1 import DIMENSIONS, sampling_spec, text_sha

ENTRIES = dict(subject_consistency='subject_consistency', motion_smoothness='motion_smoothness',
               overall_consistency='overall_consistency', dynamic_degree='dynamic_degree',
               temporal_flickering='temporal_flickering', MUSIQ_LONGER512='score_complete_frames')


def sha(path):
    path = Path(path); before = path.stat(); digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''):
            digest.update(block)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Metric input/source changed while reading')
    return digest.hexdigest()


@contextmanager
def patched(owner, name, value):
    original = getattr(owner, name)
    own = name in vars(owner)
    setattr(owner, name, value)
    try:
        yield
    finally:
        foreign_change = getattr(owner, name) is not value
        if own:
            setattr(owner, name, original)
        else:
            delattr(owner, name)
        if foreign_change:
            raise ValueError('A metric decoder hook changed during its original call')


def selected_indices(source, selected):
    positions = {id(item): index for index, item in enumerate(source)}
    if len(positions) != len(source) or any(id(item) not in positions for item in selected):
        raise ValueError('Observe actual source-frame selection without copying or guessing indices')
    return [positions[id(item)] for item in selected]


class DecoderTrace:
    def __init__(self, path):
        self.path = path
        self.readers, self.batches, self.selections = [], [], []
        self._closers = []

    def decord_factory(self, original):
        trace = self
        def factory(path, *args, **kwargs):
            if str(path) != trace.path:
                raise ValueError('Official decoder opened a different video')
            actual = original(path, *args, **kwargs)
            record = dict(backend='DECORD', source_frames=len(actual), source_fps=float(actual.get_avg_fps()))
            trace.readers.append(record)
            class Reader:
                def __len__(self): return len(actual)
                def __getattr__(self, name): return getattr(actual, name)
                def get_batch(self, indices):
                    indices = [int(i) for i in indices]
                    answer = actual.get_batch(indices)
                    if list(answer.shape) != [len(indices), 432, 768, 3]:
                        raise ValueError('Official decoder frame geometry differs')
                    trace.batches.append(indices)
                    return answer
            return Reader()
        return factory

    def cv2_proxy(self, original):
        trace = self
        class Proxy:
            def __getattr__(self, name): return getattr(original, name)
            def VideoCapture(self, path, *args, **kwargs):
                if str(path) != trace.path:
                    raise ValueError('Official decoder opened a different video')
                actual = original.VideoCapture(path, *args, **kwargs)
                record = dict(backend='OPENCV', source_frames=0,
                    source_fps=float(actual.get(original.CAP_PROP_FPS)), released=False)
                trace.readers.append(record)
                def cleanup():
                    if not record['released']:
                        actual.release(); record['released'] = True
                trace._closers.append(cleanup)
                class Capture:
                    def __getattr__(self, name): return getattr(actual, name)
                    def read(self):
                        success, frame = actual.read()
                        if success:
                            if tuple(frame.shape) != (432,768,3):
                                raise ValueError('Official decoder frame geometry differs')
                            record['source_frames'] += 1
                        return success, frame
                    def release(self):
                        actual.release(); record['released'] = True
                return Capture()
        return Proxy()

    @contextmanager
    def observe(self, dimension, module, model, utils):
        with ExitStack() as stack:
            if dimension in ('subject_consistency','overall_consistency'):
                stack.enter_context(patched(utils, 'VideoReader', self.decord_factory(utils.VideoReader)))
            else:
                stack.enter_context(patched(module, 'cv2', self.cv2_proxy(module.cv2)))
            if dimension == 'motion_smoothness':
                processor = model.fp; original_get, original_extract = processor.get_frames, processor.extract_frame
                actual_source = [None]
                def get_frames(*args, **kwargs):
                    result = original_get(*args, **kwargs); actual_source[0] = result
                    return result
                def extract(frames, *args, **kwargs):
                    result = original_extract(frames, *args, **kwargs)
                    if frames is actual_source[0]:
                        self.selections.append(selected_indices(frames, result))
                    return result
                stack.enter_context(patched(processor, 'get_frames', get_frames))
                stack.enter_context(patched(processor, 'extract_frame', extract))
            elif dimension == 'dynamic_degree':
                original_extract = model.extract_frame
                def extract(frames, *args, **kwargs):
                    result = original_extract(frames, *args, **kwargs)
                    self.selections.append(selected_indices(frames, result))
                    return result
                stack.enter_context(patched(model, 'extract_frame', extract))
            try:
                yield
            finally:
                for close in reversed(self._closers): close()
                self._closers.clear()

    def sampling(self, dimension):
        if (len(self.readers) != 1 or self.readers[0]['source_frames'] != 93
                or not math.isclose(self.readers[0]['source_fps'],16.,rel_tol=0,abs_tol=1e-6)
                or (self.readers[0]['backend']=='OPENCV' and not self.readers[0]['released'])):
            raise ValueError('Observe the complete original93/16fps source and reader release')
        if dimension in ('subject_consistency','overall_consistency'):
            if len(self.batches) != 1:
                raise ValueError('Exactly one original source-index batch required')
            indices, targets = self.batches[0], []
        elif dimension == 'motion_smoothness':
            if len(self.selections) != 2:
                raise ValueError('Observe both actual even inputs and odd source targets')
            indices, targets = self.selections
        elif dimension == 'dynamic_degree':
            if len(self.selections) != 1:
                raise ValueError('Observe the actual optical-flow source selection')
            indices, targets = self.selections[0], []
        else:
            indices, targets = list(range(self.readers[0]['source_frames'])), []
        expected = sampling_spec(dimension)
        result = dict(source_frames=self.readers[0]['source_frames'], source_fps=self.readers[0]['source_fps'],
                      frame_indices=indices, target_indices=targets, policy=expected['policy'])
        if result != expected:
            raise ValueError('Actual original evaluator source selection differs from preregistration')
        return result


class PinnedVideoMetric:
    def __init__(self, dimension, module, model, *, source_sha256, scorer_fingerprint,
                 device='cpu', utils=None, tokenizer=None, video_reader=None):
        if dimension not in DIMENSIONS:
            raise ValueError('One explicitly preregistered dimension required')
        self.dimension, self.module, self.model = dimension, module, model
        self.device, self.utils, self.tokenizer, self.video_reader = device, utils, tokenizer, video_reader
        self.scorer_fingerprint = scorer_fingerprint
        self.sources = {}
        for item in [module] + ([utils] if utils is not None else []) + ([video_reader] if video_reader is not None else []):
            path = Path(item.__file__).resolve(); digest = sha(path)
            if source_sha256.get(str(path)) != digest:
                raise ValueError('Verify the original metric/helper source bytes before invoking it')
            self.sources[str(path)] = digest
        self.entry = getattr(module, ENTRIES[dimension])
        if Path(inspect.getfile(self.entry)).resolve() != Path(module.__file__).resolve():
            raise ValueError('Metric entry belongs to another source module')
        if self.entry.__globals__ is not vars(module):
            raise ValueError('Metric entry must use the original module globals for decoder observations')
        if dimension in ('subject_consistency','overall_consistency') and utils is None:
            raise ValueError('Observe the original decoder globals without replacing preprocessing')
        if dimension == 'MUSIQ_LONGER512' and video_reader is None:
            raise ValueError('The original full-frame RGB reader is required')

    def close(self):
        self.model = self.tokenizer = None

    def score(self, planned):
        if (planned['input_status'] != 'READY_TO_SCORE' or planned['dimension'] != self.dimension
                or planned['scorer_fingerprint'] != self.scorer_fingerprint
                or text_sha(planned['prompt']) != planned['prompt_sha256']):
            raise ValueError('Use the exact eligible video, prompt and evaluator identity')
        path = Path(planned['video_path'])
        if path.is_symlink() or sha(path) != planned['video_sha256']:
            raise ValueError('Original video bytes changed before metric execution')
        if getattr(self.module, ENTRIES[self.dimension]) is not self.entry:
            raise ValueError('The original metric entry was replaced')
        extra = {}
        if self.dimension == 'MUSIQ_LONGER512':
            if self.model is None: raise ValueError('The validated original MUSIQ model is required')
            shapes = []
            def actual_model(tensor):
                if list(tensor.shape) != [1,3,288,512] or str(tensor.dtype) != 'torch.float32':
                    raise ValueError('Observe original longer512 preprocessing on every frame')
                shapes.append(list(tensor.shape)); return self.model(tensor)
            with self.video_reader.decoded_video(path) as frames:
                actual = self.entry(frames, actual_model, self.device)
            if len(shapes) != 93 or actual['frames'] != 93 or len(actual['frame_scores']) != 93:
                raise ValueError('The raw mean must cover all93 actual frame scores')
            times = [Fraction(tick)*Fraction(base) for tick,base in actual['pts']]
            if len(times) != 93 or any(b-a != Fraction(1,16) for a,b in zip(times,times[1:])):
                raise ValueError('Observe all actual16fps source timestamps for the imaging metric')
            value = actual['mean_raw_score']
            observed = dict(source_frames=actual['frames'],source_fps=16,
                frame_indices=list(range(len(actual['frame_scores']))),target_indices=[],
                policy='ALL93_LONGER512_BILINEAR_NO_ANTIALIAS')
            extra.update(frame_scores=actual['frame_scores'],pts=actual['pts'],
                         decoder_evidence=dict(backend='ORIGINAL_FFMPEG_READER',model_input_shapes=shapes))
        else:
            if self.dimension != 'temporal_flickering' and self.model is None:
                raise ValueError('The original validated metric model is required')
            trace = DecoderTrace(str(path))
            with trace.observe(self.dimension,self.module,self.model,self.utils):
                if self.dimension == 'subject_consistency':
                    _average, rows = self.entry(self.model,[str(path)],self.device,False)
                elif self.dimension == 'overall_consistency':
                    _average, rows = self.entry(self.model,[dict(prompt=planned['prompt'],video_list=[str(path)])],
                                               self.tokenizer,self.device,sample='middle')
                elif self.dimension in ('motion_smoothness','dynamic_degree'):
                    _average, rows = self.entry(self.model,[str(path)])
                else:
                    _average, rows = self.entry([str(path)])
            if len(rows) != 1 or rows[0]['video_path'] != str(path):
                raise ValueError('Use the original per-video scalar, never an upstream aggregate or another path')
            value = rows[0]['video_results']
            observed = trace.sampling(self.dimension)
            extra['decoder_evidence'] = dict(readers=trace.readers,batches=trace.batches,selections=trace.selections,
                decoder_pixels_or_preprocessing_not_replaced=True,
                metric_decoder_not_assumed_byte_equal_to_N07_RGB_backend=True)
        if observed != planned['expected_sampling'] or sha(path) != planned['video_sha256']:
            raise ValueError('Actual frame selection or original file identity changed')
        if self.dimension == 'dynamic_degree':
            if value not in (False,True,0,1): raise ValueError('Original per-video activity must remain binary')
            value = bool(value)
        elif isinstance(value,bool) or not math.isfinite(float(value)):
            raise ValueError('Finite raw per-video scalar required')
        else:
            value = float(value)
        if self.dimension == 'MUSIQ_LONGER512' and not math.isclose(mean(extra['frame_scores']),value,rel_tol=1e-11,abs_tol=1e-12):
            raise ValueError('MUSIQ mean cannot replace or omit its original frame scores')
        return dict(case_id=planned['case_id'],method=planned['method'],dimension=self.dimension,
            status='SCORED',value=value,video_sha256=planned['video_sha256'],
            prompt_sha256=planned['prompt_sha256'],scorer_fingerprint=self.scorer_fingerprint,
            observed_sampling=observed,metric_source_sha256=dict(self.sources),
            unweighted_original_per_video_result=True,**extra)
