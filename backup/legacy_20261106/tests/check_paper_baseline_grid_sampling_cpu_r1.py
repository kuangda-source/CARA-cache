"""Complete two-flow/four-request finite grid with explicit Toy boundaries."""
import ast
import copy
import hashlib
import inspect
import json
import types
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.paper_baseline_grid_r1 import METHODS, RA_THRESHOLD, execute, point
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_absolute_h1_batch_r1 import execute as previous_execute

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root):
    model = inference.pipe.model
    net = model.net
    p = json.loads((ROOT/'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    old = json.loads((ROOT/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    calibration = Calibration('DECLARED_TOY_GRID_AGE6',
        {(a,n): .99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
        {n: 1. for n in range(1,37)})
    prior = CreationPhasePrior('DECLARED_TOY_ROOT', .005, .3,
                              early_creation_floor=.005, late_creation_floor=.02)
    spec = dict(threshold=RA_THRESHOLD,
        costs=Costs('DECLARED_TOY_FROZEN_QUOTES',p['source_A_cost_seconds']['D'],p['cost_seconds']['D'],p['cost_seconds']['P']),
        partial_prior=prior,working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs = {'SOURCE_RA':spec, 'A_CPD_BETA1_ONE_PHASE':spec}

    def native(self, *a, **kw):
        # Declared CPU-only dense stand-in, identical to old clean-speed tests.
        # Actual production must use the verified official class forward.
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try: return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally: self.worldcache_rel_l1_thresh = threshold

    common = dict(runtime=runtime,wc=wc,rf=rf,settings=settings,
        calibration=calibration,specs=specs,inference_module=inference_module,
        expected_shape=config['expected_shape'],CPU_native=native,
        table_parameters={'SOURCE_PHASE':p},previous_parameters=old)
    initial = CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    origin = initial.fingerprint()
    checks, bridges, total_pairs = [], [], 0
    default_bridge = {'NATIVE35':'NATIVE','WC_DEFAULT':'WC','RA_DEFAULT':'RA',
                      'A_NO_P':'A_NO_P','TABLE_PHASE_H1':'TABLE_PHASE_H1'}
    try:
        for i, sample in enumerate(selected):
            defaults = {}
            for method in METHODS:
                pnt = point(method)
                request = copy.copy(sample)
                request.num_steps = pnt['requested_steps']
                results = []
                for audit in (True,False):
                    initial.restore(); assert initial.fingerprint()==origin
                    value = execute(inference,request,method,
                        output=Path(artifact_root)/str(flow)/str(i)/(method+str(audit)),
                        audit=audit,**common)
                    assert value['status']=='COMPLETE'
                    assert value['solver_steps']==value['guided_pairs']==pnt['actual_updates']
                    assert len(value['scheduler_timesteps'])==pnt['actual_updates']
                    assert value['request_memory_lifecycle']['components_alive_after']==0
                    if not audit:
                        assert value['in_timing_guided_copies']==value['in_timing_hashes']==value['research_checkpoints']==0
                    else:
                        assert len(value['guided'])==pnt['actual_updates']
                    if pnt['family']=='NATIVE':
                        assert set(value['native_block_CFG_counts'].values())=={2*pnt['actual_updates']}
                        assert value['actions'] is None
                    results.append(value)
                    total_pairs += pnt['actual_updates']
                a,b = results
                assert torch.equal(a['final_latent'],b['final_latent'])
                assert a['actions']==b['actions'] and a['A_history']==b['A_history']
                assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
                checks.append(dict(scene=sample.name,method=method,
                    requested_steps=pnt['requested_steps'],actual_updates=pnt['actual_updates'],
                    audit_lean_final_actions_Ahistory_mock_equal=True,
                    components_released=True,native_block_CFG_counts=a.get('native_block_CFG_counts'),
                    actual_threshold=pnt['threshold'],installed_thresholds=a['installed_thresholds']))
                if method in default_bridge: defaults[method]=a
            for method, previous in default_bridge.items():
                initial.restore(); assert initial.fingerprint()==origin
                kw = dict(common,output=Path(artifact_root)/str(flow)/str(i)/('old_'+method),audit=True)
                if method=='WC_DEFAULT':
                    kw.pop('table_parameters');kw.pop('previous_parameters')
                    value = clean.execute(inference,sample,'WC',**kw)
                else:
                    value,_ = previous_execute(inference,sample,previous,**kw)
                saved = defaults[method]
                assert value['status']=='COMPLETE' and len(value['guided'])==36
                assert all(torch.equal(a,b) for a,b in zip(saved['guided'],value['guided']))
                assert torch.equal(saved['final_latent'],value['final_latent'])
                assert saved['actions']==value['actions'] and saved['A_history']==value['A_history']
                assert Path(saved['video_path']).read_bytes()==Path(value['video_path']).read_bytes()
                bridges.append(dict(scene=sample.name,method=method,
                    all36_guided_final_actions_Ahistory_mock_equal=True))
                total_pairs += 36
        assert len(checks)==44 and len(bridges)==20 and total_pairs==3680
        return [dict(flow=flow,status='PASS',method_pair_checks=checks,default_method_bridges=bridges,
            complete_CPU_paths=108,ordinary_pairs=total_pairs,CFG_calls=2*total_pairs,
            all_audit_lean_and_default_controls_equal=True,all_components_released=True,
            Native_boundary='DECLARED_CPU_DENSE_WC_BODY_STANDIN_NOT_REAL_MODEL_CLASS')]
    finally:
        initial.restore(); assert initial.fingerprint()==origin


def run(runtime, tensor_loader, artifact_root):
    setup = load('check_partial_mlp_guided_sampling_cpu_r1')
    full = load('check_full_sampling')
    source = dedent(inspect.getsource(setup.exercise))
    start = source.index('    results=[]\n    try:')
    end = source.index('\n    finally:\n',start)+1
    changed = source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    for old,new in (
        ('    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc','    wc = _WC'),
        ('    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf','    rf = _RF')):
        assert changed.count(old)==1
        changed=changed.replace(old,new)
    ns={**vars(setup),'_body':body}
    exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)

    def exercise(**kw):
        wc=kw['wc']; ns['_WC']=wc
        wc_path=Path(runtime)/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
        assert Path(wc.worldcache_mini_train_dit_forward.__code__.co_filename).resolve()==wc_path.resolve()
        wc.__file__=str(wc_path)
        full.load_functions(wc_path,['compute_saliency_map'],vars(wc))
        rf_path=Path(runtime)/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
        raw=rf_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
        cls=[n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow']
        assert len(cls)==1
        rf=types.ModuleType('declared_grid_CPU_pinned_RF');rf.__file__=str(rf_path)
        vars(rf).update(torch=torch,Text2WorldModelRectifiedFlow=object,DataType=wc.DataType,
            parallel_state=types.SimpleNamespace(is_initialized=lambda:False),NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames')
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*cls],type_ignores=[])),str(rf_path),'exec'),vars(rf))
        ns['_RF']=rf
        return ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw)

    value=full.run(runtime,exercise=exercise)
    assert {r['flow'] for r in value['checks']}=={False,True}
    assert sum(r['complete_CPU_paths'] for r in value['checks'])==216
    value.update(status='N05_CORE_GRID_FULL216_LOCAL_TOY_CPU_PASS_NOT_PRODUCTION',
        actual_CPU_paths=216,ordinary_pairs=7360,CFG_calls=14720,
        audit_lean_pairs=88,default_method_bridges=40,
        production_CPU_accepted=False,real_video_quality_or_speed_claim=False,
        real_videos_generated=0,weights_loaded=0)
    return value
