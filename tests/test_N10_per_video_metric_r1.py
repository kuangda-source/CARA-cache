"""Pinned function bodies with synthetic native-size decoders/model doubles.

No checkpoint, codec, real generated video or GPU is used. Original frame
selection/scoring bodies run; image transforms and neural nets are doubles.
"""
import ast
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import random
from types import ModuleType, SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
import torch.nn.functional as F

from wcomr import imaging_quality, rv0_video_reader
from wcomr.automatic_quality_r1 import sampling_spec, text_sha
from wcomr.automatic_quality_metric_r1 import PinnedVideoMetric, sha

ROOT=Path(__file__).resolve().parents[1]
PACK=json.loads((ROOT/'reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json').read_text())


def bodies(relative, names, namespace):
    record=next(r for r in PACK['records'] if r['path']==relative)
    path=ROOT/PACK['source_root']/relative;raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    nodes=[n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    module=ModuleType('SYNTHETIC_PINNED_BODY_NOT_MODEL_RUNTIME')
    module.__dict__.update(namespace,__file__=str(path))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),module.__dict__)
    return module


class SyntheticCV2:
    CAP_PROP_FPS=5;COLOR_BGR2RGB=4
    def __init__(self,bad_geometry=False):self.captures=[];self.bad_geometry=bad_geometry
    def VideoCapture(self,path):
        outer=self
        class Capture:
            def __init__(self):self.index=0;self.closed=False
            def get(self,key):return 16.
            def isOpened(self):return not self.closed
            def release(self):self.closed=True
            def read(self):
                if self.index==93:return False,None
                shape=(400,768,3) if outer.bad_geometry else (432,768,3)
                result=np.full(shape,self.index,dtype=np.uint8);self.index+=1
                return True,result
        answer=Capture();self.captures.append(answer);return answer
    @staticmethod
    def cvtColor(frame,code):return frame[...,::-1].copy()
    @staticmethod
    def absdiff(left,right):
        if left.dtype==np.uint8:return np.abs(left.astype(np.int16)-right.astype(np.int16)).astype(np.uint8)
        return np.abs(left-right)


def helpers():
    bridge=SimpleNamespace(mode='native')
    def set_bridge(mode):bridge.mode=mode
    decord=ModuleType('decord');decord.bridge=SimpleNamespace(set_bridge=set_bridge)
    class Reader:
        def __init__(self,*args,**kwargs):pass
        def __len__(self):return 93
        def get_avg_fps(self):return 16.
        def get_batch(self,indices):
            data=np.stack([np.full((432,768,3),i,dtype=np.uint8) for i in indices])
            if bridge.mode=='torch':return torch.from_numpy(data)
            return SimpleNamespace(shape=data.shape,asnumpy=lambda:data)
    namespace=dict(np=np,torch=torch,random=random,VideoReader=Reader,
        dino_transform=lambda size:lambda images:images,
        clip_transform=lambda size:lambda images:images)
    utils=bodies('vbench/utils.py',('get_frame_indices','load_video','read_frames_decord_by_fps'),namespace)
    return utils,decord


def make(dimension,root,bad_geometry=False,poison_average=False):
    path=root/'SYNTHETIC_NOT_REAL_VIDEO.mp4';path.write_bytes(b'IDENTITY_FIXTURE_NOT_A_VIDEO')
    cv=SyntheticCV2(bad_geometry);utils,decord=helpers()
    namespace=dict(np=np,torch=torch,F=F,os=__import__('os'),cv2=cv,
        tqdm=lambda values,**kwargs:values,get_rank=lambda:0,
        load_video=utils.load_video,dino_transform=utils.dino_transform,
        clip_transform=utils.clip_transform,read_frames_decord_by_fps=utils.read_frames_decord_by_fps)
    if dimension=='subject_consistency':
        module=bodies('vbench/subject_consistency.py',('subject_consistency',),namespace)
        def model(image):
            return torch.stack([image.mean(dim=(1,2,3)),torch.ones(image.shape[0]),torch.full((image.shape[0],),2.)],dim=1)
    elif dimension=='overall_consistency':
        if poison_average:namespace['np']=SimpleNamespace(mean=lambda values:999.)
        module=bodies('vbench/overall_consistency.py',('get_text_features','get_vid_features','overall_consistency'),namespace)
        class Model:
            def encode_text(self,text):return torch.tensor([[1.,2.,3.]])
            def encode_vision(self,images,test):return torch.tensor([[1.,2.,3.]])
        model=Model()
    elif dimension=='motion_smoothness':
        utility=bodies('vbench/third_party/amt/utils/utils.py',
                       ('InputPadder','img2tensor','tensor2img','check_dim_and_resize'),dict(F=F,torch=torch,np=np))
        namespace.update({k:getattr(utility,k) for k in ('InputPadder','img2tensor','tensor2img','check_dim_and_resize')})
        module=bodies('vbench/motion_smoothness.py',('FrameProcess','MotionSmoothness','motion_smoothness'),namespace)
        model=module.MotionSmoothness.__new__(module.MotionSmoothness);model.device='cpu';model.niters=1
        model.initialization();model.model=lambda left,right,embt,**kwargs:dict(imgt_pred=(left+right)/2)
    elif dimension=='dynamic_degree':
        utility=bodies('vbench/third_party/RAFT/core/utils_core/utils.py',('InputPadder',),dict(F=F,torch=torch,np=np))
        namespace['InputPadder']=utility.InputPadder
        module=bodies('vbench/dynamic_degree.py',('DynamicDegree','dynamic_degree'),namespace)
        model=module.DynamicDegree.__new__(module.DynamicDegree);model.device='cpu'
        def flow(left,right,**kwargs):
            assert kwargs==dict(iters=20,test_mode=True)
            return None,torch.zeros(1,2,*left.shape[-2:])
        model.model=flow
    elif dimension=='temporal_flickering':
        module=bodies('vbench/temporal_flickering.py',('get_frames','mae_seq','calculate_mae','cal_score','temporal_flickering'),namespace)
        model=None
    else:raise ValueError('Separate original MUSIQ helper fixture')
    bound={str(Path(module.__file__).resolve()):sha(module.__file__),str(Path(utils.__file__).resolve()):sha(utils.__file__)}
    scorer=PinnedVideoMetric(dimension,module,model,source_sha256=bound,scorer_fingerprint='SYNTHETIC_SCORER',
        device='cpu',utils=utils if dimension in ('subject_consistency','overall_consistency') else None)
    prompt='Exact synthetic original text; never a filename.'
    planned=dict(input_status='READY_TO_SCORE',dimension=dimension,scorer_fingerprint='SYNTHETIC_SCORER',
        prompt=prompt,prompt_sha256=text_sha(prompt),video_path=str(path),video_sha256=sha(path),
        expected_sampling=sampling_spec(dimension),case_id='SYNTHETIC_CASE',method='SYNTHETIC_METHOD')
    return scorer,planned,module,model,utils,decord,cv


class PerVideoMetricControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads=torch.get_num_threads();torch.set_num_threads(2)
    @classmethod
    def tearDownClass(cls):torch.set_num_threads(cls.threads)

    def test_original_per_video_calls_and_actual_selection_for_all_five_VBench_dimensions(self):
        for dimension in ('subject_consistency','overall_consistency','motion_smoothness','dynamic_degree','temporal_flickering'):
            with self.subTest(dimension=dimension),tempfile.TemporaryDirectory() as folder:
                scorer,p,module,model,utils,decord,cv=make(dimension,Path(folder))
                original_reader=utils.VideoReader;original_cv=module.cv2
                with patch.dict(sys.modules,{'decord':decord}):value=scorer.score(p)
                self.assertEqual(value['observed_sampling'],sampling_spec(dimension))
                self.assertEqual(value['status'],'SCORED');self.assertTrue(value['unweighted_original_per_video_result'])
                self.assertIs(utils.VideoReader,original_reader);self.assertIs(module.cv2,original_cv)
                self.assertTrue(all(cap.closed for cap in cv.captures))
                if dimension=='dynamic_degree':self.assertIs(value['value'],False)
                if dimension=='temporal_flickering':self.assertAlmostEqual(value['value'],254/255.)

    def test_upstream_average_cannot_replace_per_video_value(self):
        with tempfile.TemporaryDirectory() as folder:
            scorer,p,_,_,_,decord,_=make('overall_consistency',Path(folder),poison_average=True)
            with patch.dict(sys.modules,{'decord':decord}):value=scorer.score(p)
            self.assertAlmostEqual(value['value'],1.,places=6);self.assertNotEqual(value['value'],999.)

    def test_wrong_actual_frame_selection_is_refused_and_hooks_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            scorer,p,_,_,utils,decord,_=make('overall_consistency',Path(folder))
            original=utils.VideoReader
            # Alter only this synthetic namespace's original selector dependency.
            utils.read_frames_decord_by_fps.__globals__['get_frame_indices']=lambda *args,**kwargs:list(range(8))
            with patch.dict(sys.modules,{'decord':decord}),self.assertRaisesRegex(ValueError,'source selection'):
                scorer.score(p)
            self.assertIs(utils.VideoReader,original)

    def test_bad_geometry_releases_original_decoder_and_restores_module(self):
        with tempfile.TemporaryDirectory() as folder:
            scorer,p,module,model,_,_,cv=make('motion_smoothness',Path(folder),bad_geometry=True)
            before=dict(vars(model.fp));original=module.cv2
            with self.assertRaisesRegex(ValueError,'geometry'):scorer.score(p)
            self.assertIs(module.cv2,original);self.assertEqual(vars(model.fp),before)
            self.assertTrue(cv.captures and all(cap.closed for cap in cv.captures))

    def test_video_prompt_and_ineligible_inputs_refuse_before_decoder(self):
        for kind in ('file','prompt','ineligible'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                scorer,p,_,_,_,_,cv=make('temporal_flickering',Path(folder))
                if kind=='file':Path(p['video_path']).write_bytes(b'CHANGED')
                elif kind=='prompt':p['prompt']='Changed prompt'
                else:p['input_status']='NOT_APPLICABLE_STATIC_SCOPE'
                with self.assertRaises(ValueError):scorer.score(p)
                self.assertFalse(cv.captures)

    def test_source_identity_required_before_any_original_metric_call(self):
        with tempfile.TemporaryDirectory() as folder:
            _,_,module,model,_,_,_=make('temporal_flickering',Path(folder))
            with self.assertRaisesRegex(ValueError,'source bytes'):
                PinnedVideoMetric('temporal_flickering',module,model,source_sha256={},scorer_fingerprint='SYNTHETIC')

    def test_copied_module_cannot_bypass_actual_decoder_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            _,_,module,model,_,_,_=make('temporal_flickering',Path(folder))
            copied=SimpleNamespace(**vars(module))
            bound={str(Path(module.__file__).resolve()):sha(module.__file__)}
            with self.assertRaisesRegex(ValueError,'module globals'):
                PinnedVideoMetric('temporal_flickering',copied,model,source_sha256=bound,
                    scorer_fingerprint='SYNTHETIC')

    def test_original_MUSIQ_complete93_raw_mean_and_actual_preprocessing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'SYNTHETIC.mp4';path.write_bytes(b'NOT_A_REAL_VIDEO')
            @contextmanager
            def decoded_video(path):
                yield ((np.full((432,768,3),i,dtype=np.uint8),i,'1/16') for i in range(93))
            reader=SimpleNamespace(__file__=rv0_video_reader.__file__,decoded_video=decoded_video)
            model=lambda image:image.mean().reshape(1)*100
            sources={str(Path(m.__file__).resolve()):sha(m.__file__) for m in (imaging_quality,rv0_video_reader)}
            scorer=PinnedVideoMetric('MUSIQ_LONGER512',imaging_quality,model,video_reader=reader,
                source_sha256=sources,scorer_fingerprint='SYNTHETIC')
            p=dict(input_status='READY_TO_SCORE',dimension='MUSIQ_LONGER512',scorer_fingerprint='SYNTHETIC',
                prompt='Synthetic.',prompt_sha256=text_sha('Synthetic.'),video_path=str(path),video_sha256=sha(path),
                expected_sampling=sampling_spec('MUSIQ_LONGER512'),case_id='SYNTHETIC',method='SYNTHETIC')
            value=scorer.score(p)
            self.assertEqual(len(value['frame_scores']),93);self.assertGreater(value['value'],10.)
            self.assertAlmostEqual(value['value'],46/255.*100,places=4)
            self.assertEqual(len(value['decoder_evidence']['model_input_shapes']),93)


if __name__=='__main__':unittest.main()
