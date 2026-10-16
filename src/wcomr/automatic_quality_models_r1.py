"""Shared original constructors for CPU validation and later admitted scoring.

Importing this module constructs no model and imports no neural framework.
``construct`` is called only after the caller's source/resource checks. The
scoring factory additionally requires the complete independent CPU proof;
the production driver still owns whole-card authorization and GPU admission.
"""
from contextlib import contextmanager
import gc
import hashlib
import importlib
import importlib.metadata
import inspect
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROLES = ('DINO', 'AMT_S', 'RAFT_THINGS', 'ViCLIP', 'MUSIQ_SPAQ')
WEIGHTS = {
    'DINO': (343242485, 'bf34ad0f424b9029b593e8dc3ed553bf26e88bcba0d32bf3e62a6209cb64c85e'),
    'AMT_S': (12038359, '07e7e03405c213fe4405678db9b42d05671e48c56faf6a441b99bb0047d3cf77'),
    'RAFT_THINGS': (21108000, 'fcfa4125d6418f4de95d84aec20a3c5f4e205101715a79f193243c186ac9a7e1'),
    'ViCLIP': (1710545812, '7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56'),
    'MUSIQ_SPAQ': (108610983, '358bb6af275e28ea56821d44fb55c6cb83645db11f394d3ad65b2d149965ab50'),
}
BPE_SHA = '924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a'
MUSIQ_SOURCE_SHA = 'ddab924a5ff529e1668404fa058777a9d00890390166c2b12ef7fffdc0baebb3'
ROLE_FOR_DIMENSION = dict(subject_consistency='DINO', motion_smoothness='AMT_S',
    overall_consistency='ViCLIP', dynamic_degree='RAFT_THINGS', MUSIQ_LONGER512='MUSIQ_SPAQ',
    temporal_flickering=None)
MODEL_CLASSES = dict(DINO='vision_transformer.VisionTransformer', AMT_S='networks.AMT-S.Model',
    RAFT_THINGS='vbench.third_party.RAFT.core.raft.RAFT', ViCLIP='vbench.third_party.ViCLIP.viclip.ViCLIP',
    MUSIQ_SPAQ='pyiqa.archs.musiq_arch.MUSIQ')
SELF_REF = 'src/wcomr/automatic_quality_models_r1.py'


def sha(path):
    path = Path(path); before = path.stat(); digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''): digest.update(block)
    after = path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError('Original model source/resource changed while reading')
    return digest.hexdigest()


def construct(role, stage, resource, torch, device):
    """Original constructors only; no alternative checkpoint or download fallback."""
    if role not in ROLES or device not in ('cpu', 'cuda'):
        raise ValueError('Explicit original model role and execution device required')
    stage, resource = Path(stage), Path(resource)
    wrapper = tokenizer = None
    if role == 'DINO':
        model = torch.hub.load(repo_or_dir=str(stage/'external/dino'), model='dino_vitb16',
                               source='local', pretrained=False)
        model.load_state_dict(torch.load(str(resource),map_location='cpu'),strict=True)
    elif role == 'AMT_S':
        from vbench.motion_smoothness import MotionSmoothness
        wrapper = MotionSmoothness(str(stage/'upstream/vbench/third_party/amt/cfgs/AMT-S.yaml'),
                                  str(resource), device)
        model = wrapper.model
    elif role == 'RAFT_THINGS':
        from easydict import EasyDict
        from vbench.dynamic_degree import DynamicDegree
        args = EasyDict(model=str(resource), small=False, mixed_precision=False, alternate_corr=False)
        wrapper = DynamicDegree(args, device); model = wrapper.model
    elif role == 'ViCLIP':
        from vbench.third_party.ViCLIP.simple_tokenizer import SimpleTokenizer
        from vbench.third_party.ViCLIP.viclip import ViCLIP
        tokenizer = SimpleTokenizer(str(stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz'))
        model = ViCLIP(tokenizer=tokenizer, pretrain=str(resource))
    else:
        if importlib.metadata.version('pyiqa') != '0.1.10':
            raise ValueError('Frozen PyIQA version changed')
        import pyiqa.archs.musiq_arch as architecture
        if sha(inspect.getfile(architecture)) != MUSIQ_SOURCE_SHA:
            raise ValueError('Frozen original MUSIQ implementation changed')
        model = architecture.MUSIQ(pretrained_model_path=str(resource))
    model = model.float().to(device).eval().requires_grad_(False)
    return SimpleNamespace(role=role, model=model, wrapper=wrapper, tokenizer=tokenizer)


class OriginalMetricFactory:
    """Sequential, independently CPU-accepted original models for a scoring run."""
    def __init__(self, *, stage, resources, CPU_acceptance, CPU_registration,
                 scorer_fingerprint, torch, device):
        if (CPU_acceptance.get('status') != 'N10_ALL_FIVE_MODEL_CPU_INDEPENDENTLY_ACCEPTED_NOT_QUALITY'
                or CPU_acceptance.get('CPU_accepted') is not True
                or CPU_acceptance.get('registered_model_denominator') != 5
                or CPU_acceptance.get('accepted_models') != 5
                or CPU_acceptance.get('source_revision') != CPU_registration['source_revision']
                or [r['role'] for r in CPU_acceptance['rows']] != list(ROLES)
                or any(r['status'] != 'CPU_ROLE_ACCEPTED' for r in CPU_acceptance['rows'])
                or any(r['proof'].get('constructor_source_sha256') != sha(__file__)
                    for r in CPU_acceptance['rows'])
                or CPU_registration['roles'] != list(ROLES)
                or CPU_registration['purpose'] != 'N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
                or CPU_registration['official_VBench_commit'] != 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
                or CPU_registration['payload_sha256'].get(SELF_REF) != sha(__file__)
                or set(resources) != set(ROLES) or device not in ('cpu','cuda')):
            raise ValueError('Complete independent CPU proof of the same original constructor is required')
        self.stage = Path(stage).resolve(); self.resources = resources
        self.CPU_registration = CPU_registration; self.CPU_acceptance = CPU_acceptance
        self.scorer_fingerprint, self.torch, self.device = scorer_fingerprint, torch, device
        self.active = False
        for role, (size,digest) in WEIGHTS.items():
            record = resources[role]; path = Path(record['path'])
            if (record['bytes'] != size or record['sha256'] != digest or not path.is_absolute()
                    or not path.is_file() or path.name.endswith('.part') or path.stat().st_size != size):
                raise ValueError('Keep every complete original checkpoint, including later model roles')
        self.verify_sources()
        self.verify_all_imported()
        os.environ['VBENCH_CACHE_DIR'] = str(self.stage/'cache')
        sys.path.insert(0,str(self.stage/'upstream'))

    def verify_sources(self):
        for name, digest in self.CPU_registration['payload_sha256'].items():
            relative = Path(name); path = self.stage/relative
            if (relative.is_absolute() or '..' in relative.parts or path.is_symlink()
                    or not path.resolve().is_relative_to(self.stage) or sha(path) != digest):
                raise ValueError('The original CPU-accepted metric source changed')
        if sha(self.stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz') != BPE_SHA:
            raise ValueError('Verify the real original tokenizer before metric imports')

    def verify_import(self, module):
        path = Path(module.__file__).resolve()
        if path.is_relative_to(self.stage):
            relative = str(path.relative_to(self.stage))
            if self.CPU_registration['payload_sha256'].get(relative) != sha(path):
                raise ValueError('An undeclared model/metric source was imported')
        elif module.__name__ != 'pyiqa.archs.musiq_arch' or sha(path) != MUSIQ_SOURCE_SHA:
            raise ValueError('Installed code silently replaced the original staged metric')
        return path

    def verify_all_imported(self):
        for name, module in list(sys.modules.items()):
            if (name=='vbench' or name.startswith('vbench.')) and getattr(module,'__file__',None):
                self.verify_import(module)

    @contextmanager
    def __call__(self, dimension):
        if self.active: raise ValueError('Release the previous original scoring model first')
        if dimension not in ROLE_FOR_DIMENSION: raise ValueError('One registered dimension required')
        self.verify_sources(); role = ROLE_FOR_DIMENSION[dimension]
        resource = Path(self.resources[role]['path']) if role else None
        if role and sha(resource) != WEIGHTS[role][1]:
            raise ValueError('Original model checkpoint changed before construction')
        loaded = scorer = None; released = False; self.active = True
        try:
            from .automatic_quality_metric_r1 import PinnedVideoMetric
            module = importlib.import_module('wcomr.imaging_quality' if dimension=='MUSIQ_LONGER512' else 'vbench.'+dimension)
            self.verify_import(module)
            if role:
                loaded = construct(role,self.stage,resource,self.torch,self.device)
                self.verify_all_imported()
                model = loaded.model
                if (type(model).__module__+'.'+type(model).__qualname__ != MODEL_CLASSES[role]
                        or model.training or any(p.device.type!=self.device or p.dtype!=self.torch.float32
                            or p.requires_grad for p in model.parameters())
                        or sum(p.numel() for p in model.parameters()) != next(r['proof']['parameter_count']
                            for r in self.CPU_acceptance['rows'] if r['role']==role)):
                    raise ValueError('Loaded model class, precision, mode or parameter count differs from CPU proof')
                self.verify_import(sys.modules[type(model).__module__])
            utils = importlib.import_module('vbench.utils') if dimension in ('subject_consistency','overall_consistency') else None
            reader = importlib.import_module('wcomr.rv0_video_reader') if dimension=='MUSIQ_LONGER512' else None
            for helper in [x for x in (utils,reader) if x is not None]: self.verify_import(helper)
            sources = {str(path.resolve()): digest for name,digest in self.CPU_registration['payload_sha256'].items()
                       for path in [self.stage/name]}
            scorer = PinnedVideoMetric(dimension,module,
                loaded.wrapper if role in ('AMT_S','RAFT_THINGS') else loaded.model if loaded else None,
                source_sha256=sources,scorer_fingerprint=self.scorer_fingerprint,device=self.device,
                utils=utils,tokenizer=loaded.tokenizer if loaded else None,video_reader=reader)
            with self.torch.inference_mode(): yield scorer
        finally:
            try:
                if scorer is not None: scorer.close()
                if loaded is not None:
                    if loaded.wrapper is not None: loaded.wrapper.model = None
                    loaded.model = loaded.wrapper = loaded.tokenizer = None
                scorer = loaded = None
                if 'model' in locals(): del model
                gc.collect()
                if self.device == 'cuda':
                    self.torch.cuda.synchronize(); self.torch.cuda.empty_cache()
                released = True
            finally:
                self.active = not released
