"""Original-constructor/factory interfaces using tiny synthetic model doubles.

No original checkpoint, codec, video, model forward, CUDA or network is used.
Tiny torch parameters exercise inference mode and reference cleanup only.
"""
from contextlib import ExitStack
import copy
import gc
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import weakref

import torch

from wcomr import automatic_quality_models_r1 as M
from wcomr import automatic_quality_metric_r1 as metric

ROOT=Path(__file__).resolve().parents[1]
BPE=ROOT/'.sync/wc-N10-official-tokenizer-pinned-r1-20261016/bpe_simple_vocab_16e6.txt.gz'


class TinySyntheticModel(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.weight=torch.nn.Parameter(torch.zeros(2,3))


class DummyScorer:
    def __init__(self,dimension,module,model,**kwargs):
        self.dimension,self.model=dimension,model
        self.scorer_fingerprint=kwargs['scorer_fingerprint']
        self.tokenizer=kwargs['tokenizer']
    def close(self): self.model=self.tokenizer=None


def fixture(root):
    root=root.resolve();stage=root/'stage';stage.mkdir(); sources={};modules={};calls=[];refs=[]
    def module(name,relative):
        path=stage/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('# EXPLICIT SYNTHETIC SOURCE, NOT THE OFFICIAL MODEL\n')
        sources[str(path.relative_to(stage))]=M.sha(path)
        value=ModuleType(name);value.__file__=str(path);value.__path__=[]
        modules[name]=value;return value
    for name in ['vbench','vbench.third_party','vbench.third_party.ViCLIP','pyiqa','pyiqa.archs']:
        module(name,'upstream/'+name.replace('.','/')+'/__init__.py')
    model_module=module('SYNTHETIC_N10_MODEL','upstream/SYNTHETIC_N10_MODEL.py')
    Toy=type('SyntheticMetricModel',(TinySyntheticModel,),{'__module__':model_module.__name__})
    model_module.SyntheticMetricModel=Toy
    def toy():
        answer=Toy();refs.append(weakref.ref(answer));return answer
    for dimension in M.ROLE_FOR_DIMENSION:
        name='wcomr.imaging_quality' if dimension=='MUSIQ_LONGER512' else 'vbench.'+dimension
        module(name,('src/' if name.startswith('wcomr.') else 'upstream/')+name.replace('.','/')+'.py')
    module('vbench.utils','upstream/vbench/utils.py')
    module('wcomr.rv0_video_reader','src/wcomr/rv0_video_reader.py')
    def amt(config,checkpoint,device):
        calls.append(('AMT',config,checkpoint,device));return SimpleNamespace(model=toy())
    modules['vbench.motion_smoothness'].MotionSmoothness=amt
    def raft(args,device):
        calls.append(('RAFT',dict(vars(args)),device));return SimpleNamespace(model=toy())
    modules['vbench.dynamic_degree'].DynamicDegree=raft
    module('easydict','upstream/easydict.py').EasyDict=lambda **kwargs:SimpleNamespace(**kwargs)
    def tokenizer(path):calls.append(('TOKENIZER',path));return 'SYNTHETIC_TOKENIZER'
    module('vbench.third_party.ViCLIP.simple_tokenizer','upstream/vbench/third_party/ViCLIP/simple_tokenizer.py').SimpleTokenizer=tokenizer
    def clip(**kwargs):calls.append(('ViCLIP',kwargs));return toy()
    module('vbench.third_party.ViCLIP.viclip','upstream/vbench/third_party/ViCLIP/viclip.py').ViCLIP=clip
    arch=module('pyiqa.archs.musiq_arch','upstream/pyiqa/archs/musiq_arch.py')
    def musiq(**kwargs):calls.append(('MUSIQ',kwargs));return toy()
    arch.MUSIQ=musiq
    for name,value in list(modules.items()):
        if '.' in name and name.rsplit('.',1)[0] in modules:
            setattr(modules[name.rsplit('.',1)[0]],name.rsplit('.',1)[1],value)
    constructor=stage/M.SELF_REF;constructor.parent.mkdir(exist_ok=True,parents=True)
    shutil.copyfile(M.__file__,constructor);sources[M.SELF_REF]=M.sha(constructor)
    bpe=stage/'cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz';bpe.parent.mkdir(parents=True);shutil.copyfile(BPE,bpe)
    sources[str(bpe.relative_to(stage))]=M.sha(bpe)
    resources={};weights={}
    for role in M.ROLES:
        path=root/(role+'.pth');torch.save({'weight':torch.ones(2,3)},path)
        weights[role]=(path.stat().st_size,M.sha(path))
        resources[role]=dict(path=str(path),bytes=weights[role][0],sha256=weights[role][1])
    registration=dict(source_revision='SYNTHETIC_NO_REAL_CPU_JOB',roles=list(M.ROLES),
        official_VBench_commit='fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490',
        purpose='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING',payload_sha256=sources)
    accepted=dict(status='N10_ALL_FIVE_MODEL_CPU_INDEPENDENTLY_ACCEPTED_NOT_QUALITY',
        CPU_accepted=True,registered_model_denominator=5,accepted_models=5,
        source_revision=registration['source_revision'],rows=[dict(role=role,status='CPU_ROLE_ACCEPTED',
            proof=dict(parameter_count=6,constructor_source_sha256=M.sha(M.__file__))) for role in M.ROLES])
    def hub(**kwargs):calls.append(('DINO',kwargs));return toy()
    def build(scorer_fingerprint='a'*64):
        return M.OriginalMetricFactory(stage=stage,resources=resources,CPU_acceptance=accepted,
            CPU_registration=registration,scorer_fingerprint=scorer_fingerprint,torch=torch,device='cpu')
    stack=ExitStack();stack.enter_context(patch.dict(sys.modules,modules))
    stack.enter_context(patch.dict(os.environ,dict(os.environ)))
    stack.enter_context(patch.object(sys,'path',list(sys.path)))
    stack.enter_context(patch.object(M,'WEIGHTS',weights))
    stack.enter_context(patch.object(M,'MODEL_CLASSES',{r:model_module.__name__+'.SyntheticMetricModel' for r in M.ROLES}))
    stack.enter_context(patch.object(M,'MUSIQ_SOURCE_SHA',M.sha(arch.__file__)))
    stack.enter_context(patch.object(M.importlib.metadata,'version',return_value='0.1.10'))
    stack.enter_context(patch.object(torch.hub,'load',side_effect=hub))
    stack.enter_context(patch.object(metric,'PinnedVideoMetric',DummyScorer))
    return SimpleNamespace(stage=stage,resources=resources,weights=weights,registration=registration,
        accepted=accepted,calls=calls,refs=refs,build=build,stack=stack,modules=modules)


class OriginalMetricFactoryControls(unittest.TestCase):
    def test_all_five_shared_constructors_and_sequential_reference_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                factory=f.build()
                for dimension in M.ROLE_FOR_DIMENSION:
                    with factory(dimension) as scorer:
                        self.assertEqual(scorer.dimension,dimension);self.assertFalse(torch.is_grad_enabled())
                        self.assertTrue(factory.active)
                        with self.assertRaisesRegex(ValueError,'Release'):
                            with factory(dimension): pass
                    self.assertFalse(factory.active);gc.collect()
                    self.assertTrue(all(ref() is None for ref in f.refs))
                self.assertEqual(len(f.refs),5)
                dino=next(c for c in f.calls if c[0]=='DINO')[1]
                self.assertEqual(dino,dict(repo_or_dir=str(f.stage/'external/dino'),model='dino_vitb16',source='local',pretrained=False))
                amt=next(c for c in f.calls if c[0]=='AMT')
                self.assertEqual(amt[1],str(f.stage/'upstream/vbench/third_party/amt/cfgs/AMT-S.yaml'))
                self.assertEqual(amt[2:],(f.resources['AMT_S']['path'],'cpu'))
                raft=next(c for c in f.calls if c[0]=='RAFT')
                self.assertEqual(raft[1],dict(model=f.resources['RAFT_THINGS']['path'],small=False,mixed_precision=False,alternate_corr=False))
                self.assertEqual(next(c for c in f.calls if c[0]=='ViCLIP')[1],dict(tokenizer='SYNTHETIC_TOKENIZER',pretrain=f.resources['ViCLIP']['path']))
            finally:f.stack.close()

    def test_DINO_explicit_checkpoint_is_loaded_strictly_before_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                factory=f.build()
                with factory('subject_consistency') as scorer:
                    self.assertTrue(torch.equal(scorer.model.weight,torch.ones(2,3)))
                    self.assertFalse(scorer.model.weight.requires_grad);self.assertFalse(scorer.model.training)
                    self.assertEqual(scorer.model.weight.dtype,torch.float32)
            finally:f.stack.close()

    def test_incomplete_or_other_constructor_CPU_proof_refuses_before_loading(self):
        for kind in ('count','missing','constructor','stage_source'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                f=fixture(Path(folder))
                try:
                    if kind=='count':f.accepted['accepted_models']=4
                    elif kind=='missing':f.accepted['rows'].pop()
                    elif kind=='constructor':f.accepted['rows'][0]['proof']['constructor_source_sha256']='0'*64
                    else:f.registration['payload_sha256'][M.SELF_REF]='0'*64
                    with self.assertRaises(ValueError):f.build()
                    self.assertFalse(f.calls)
                finally:f.stack.close()

    def test_missing_later_resource_refuses_whole_factory_before_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                Path(f.resources['ViCLIP']['path']).unlink()
                with self.assertRaises(ValueError):f.build()
                self.assertFalse(f.calls)
            finally:f.stack.close()

    def test_source_or_checkpoint_change_between_contexts_refuses_before_model_load(self):
        for kind in ('source','checkpoint'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as folder:
                f=fixture(Path(folder))
                try:
                    factory=f.build()
                    path=(f.stage/'upstream/vbench/utils.py') if kind=='source' else Path(f.resources['DINO']['path'])
                    path.write_bytes(b'CHANGED'+path.read_bytes()[7:])
                    with self.assertRaises(ValueError):
                        with factory('subject_consistency'): pass
                    self.assertFalse(f.calls);self.assertFalse(factory.active)
                finally:f.stack.close()

    def test_wrong_actual_parameter_count_is_released_without_yielding_scorer(self):
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                f.accepted['rows'][0]['proof']['parameter_count']=7;factory=f.build()
                with self.assertRaisesRegex(ValueError,'parameter count'):
                    with factory('subject_consistency'):self.fail('Wrong model must not score')
                self.assertFalse(factory.active);self.assertTrue(all(ref() is None for ref in f.refs))
            finally:f.stack.close()

    def test_already_imported_installed_VBench_is_refused_before_any_model(self):
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                outside=Path(folder)/'WRONG_INSTALLED.py';outside.write_text('# WRONG INSTANCE\n')
                f.modules['vbench.utils'].__file__=str(outside)
                with self.assertRaisesRegex(ValueError,'Installed code'):f.build()
                self.assertFalse(f.calls)
            finally:f.stack.close()

    def test_shared_factory_drives_all960_positions_and_releases_all_five_models(self):
        from test_N10_complete_batch_r1 import inputs
        from wcomr.automatic_quality_batch_r1 import execute,key,reconstruct
        bundle,raw,contrasts=inputs()
        class BatchScorer(DummyScorer):
            def score(self,planned):
                assert not torch.is_grad_enabled()
                return copy.deepcopy(raw[key(planned)])
        with tempfile.TemporaryDirectory() as folder:
            f=fixture(Path(folder))
            try:
                factory=f.build(bundle['scorer_fingerprint']);events=[]
                with patch.object(metric,'PinnedVideoMetric',BatchScorer):
                    result=execute(bundle,contrasts,factory,events.append,bootstrap_repetitions=2)
                self.assertEqual(result['metric_status_counts'],dict(SCORED=800,NOT_APPLICABLE_STATIC_SCOPE=160))
                self.assertEqual(reconstruct(bundle,events)['final'],result)
                self.assertEqual(len(f.refs),5);self.assertFalse(factory.active)
                self.assertTrue(all(ref() is None for ref in f.refs))
            finally:f.stack.close()

    def test_CPU_worker_and_factory_keep_original_resource_identities_and_shared_entry(self):
        spec=importlib.util.spec_from_file_location('N10_CONSTRUCTOR_SOURCE_INTERFACE_ONLY',ROOT/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py')
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        self.assertEqual(M.ROLES,original.ROLES);self.assertEqual(M.WEIGHTS,original.WEIGHTS)
        self.assertEqual(M.BPE_SHA,original.BPE_SHA);self.assertEqual(M.MUSIQ_SOURCE_SHA,original.MUSIQ_SOURCE_SHA)
        import ast
        tree=ast.parse((ROOT/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py').read_text())
        probe=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='probe')
        imports=[n for n in ast.walk(probe) if isinstance(n,ast.ImportFrom) and n.module=='wcomr.automatic_quality_models_r1']
        calls=[n for n in ast.walk(probe) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='construct']
        self.assertEqual(len(imports),1);self.assertEqual(len(calls),1)

    def test_cold_constructor_module_import_loads_no_neural_framework(self):
        import subprocess,os
        code='from wcomr import automatic_quality_models_r1 as m; import sys,json; assert "torch" not in sys.modules; print(json.dumps(dict(roles=list(m.ROLES),torch_imported=False)))'
        result=subprocess.run([sys.executable,'-S','-c',code],capture_output=True,text=True,
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
        self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(result.stdout);self.assertFalse(value['torch_imported']);self.assertEqual(value['roles'],list(M.ROLES))


if __name__=='__main__':unittest.main()
