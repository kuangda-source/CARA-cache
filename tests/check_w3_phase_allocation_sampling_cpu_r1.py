"""Full72 Toy paths using bound WC/RF/UniPC and frozen phase/T1 parameters."""
import ast, copy, hashlib, inspect, json, types
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.w3_phase_allocation_runtime_r1 import execute, METHODS
from wcomr.source_phase_absolute_h1_batch_r1 import execute as old_execute
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));module=module_from_spec(spec);spec.loader.exec_module(module);return module

def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    p=json.loads((ROOT/'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    frozen=json.loads((ROOT/'manifests/wc_w3_T1_primary6_ridge1_window4_frozen_candidate_20261016.json').read_text())
    old=json.loads((ROOT/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    cal=Calibration('DECLARED_TOY_PHASE_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('DECLARED_TOY_BOUND_H1_QUOTES',p['source_A_cost_seconds']['D'],p['cost_seconds']['D'],p['cost_seconds']['P']),
        partial_prior=CreationPhasePrior('DECLARED_TOY_POSITIVE_ROOT',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,
        specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec},inference_module=inference_module,
        expected_shape=config['expected_shape'],table_parameters={'SOURCE_PHASE':p},previous_parameters=old)
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint();checks=[];off_controls=[]
    try:
        for i,sample in enumerate(selected):
            originals=None
            for method in METHODS:
                outcomes=[]
                for audit in (True,False):
                    initial.restore();assert initial.fingerprint()==origin
                    value=execute(inference,sample,method,frozen_T1=frozen,output=Path(artifact_root)/str(flow)/str(i)/(method+str(audit)),audit=audit,**common)
                    assert value['status']=='COMPLETE' and value['solver_steps']==value['guided_pairs']==36
                    assert len(value['source_history'])==36 and not value['online_teacher_calls']
                    assert value['request_memory_lifecycle']['owners_alive_after']==0
                    if method in ('H1_CAD','T1_CAD'):assert 'PP' not in value['actions']
                    for h in value['source_history']:
                        if h['action']!='DD' and not h.get('native_cycle_reset'):assert h['true_D_before']==h['true_D_after']
                        assert h['teacher_calls']==h['A_readout']['teacher_calls']==h['A_readout']['extra_deep_blocks']==0
                    if not audit:assert value['in_timing_guided_copies']==value['in_timing_hashes']==value['research_checkpoints']==0
                    outcomes.append(value)
                a,b=outcomes
                assert torch.equal(a['final_latent'],b['final_latent']) and a['actions']==b['actions'] and a['A_history']==b['A_history']
                assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
                checks.append(dict(scene=sample.name,method=method,semantic_actions=a['semantic_plan'],audit_lean_final_actions_Ahistory_mock_output_equal=True,
                    boundary_owner_release=True,ordinary_pairs=72))
                if method=='H1_ORIGINAL':originals=a
            initial.restore()
            previous,_=old_execute(inference,sample,'TABLE_PHASE_H1',output=Path(artifact_root)/str(flow)/str(i)/'ORIGINAL_H1_CONTROL',audit=True,**common)
            assert previous['status']=='COMPLETE' and len(previous['guided'])==36
            assert originals['actions']==previous['actions'] and originals['A_history']==previous['A_history']
            assert all(torch.equal(x,y) for x,y in zip(originals['guided'],previous['guided']))
            assert torch.equal(originals['final_latent'],previous['final_latent'])
            assert Path(originals['video_path']).read_bytes()==Path(previous['video_path']).read_bytes()
            off_controls.append(dict(scene=sample.name,all36_guided_final_actions_Ahistory_mock_output_equal=True))
        assert len(checks)==16 and len(off_controls)==4
        return [dict(flow=flow,status='PASS',method_pair_checks=checks,original_H1_controls=off_controls,
            complete_CPU_paths=36,ordinary_pairs=1296,all36_audit_lean_controls=True,all_owners_released=True)]
    finally:initial.restore();assert initial.fingerprint()==origin

def run(runtime,tensor_loader,artifact_root):
    setup=load('check_partial_mlp_guided_sampling_cpu_r1');full=load('check_full_sampling')
    source=dedent(inspect.getsource(setup.exercise));start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    # The local CPU harness supplies exact AST-loaded WC/RF bodies, avoiding
    # optional CUDA package imports. Production imports remain a later gate.
    before1='    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc'
    before2='    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf'
    assert changed.count(before1)==changed.count(before2)==1
    changed=changed.replace(before1,'    wc = _WC').replace(before2,'    rf = _RF')
    namespace={**vars(setup),'_body':body}
    exec(compile(changed,__file__+'#declared-Toy-setup','exec'),namespace)
    def exercise(**kw):
        namespace['_WC']=kw['wc']
        path=Path(runtime)/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
        nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow'];assert len(nodes)==1
        rf=types.ModuleType('declared_local_CPU_pinned_RF')
        vars(rf).update(torch=torch,Text2WorldModelRectifiedFlow=object,DataType=kw['wc'].DataType,
            parallel_state=types.SimpleNamespace(is_initialized=lambda:False),NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames')
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*nodes],type_ignores=[])),str(path),'exec'),vars(rf))
        namespace['_RF']=rf
        return namespace['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw)
    value=full.run(runtime,exercise=exercise)
    assert {c['flow'] for c in value['checks']}=={False,True}
    assert sum(c['complete_CPU_paths'] for c in value['checks'])==72
    value.update(status='W3_PHASE_T1_FULL72_LOCAL_TOY_SAMPLING_CPU_PASS_NOT_PRODUCTION_CPU',
        actual_CPU_paths=72,ordinary_pairs=2592,CFG_calls=5184,model_weights_loaded=0,
        real_videos_generated=0,new_policy_quality_or_speed_claim=False,
        full_RF_class_AST_unchanged=True,local_optional_package_imports_bypassed=True)
    return value
