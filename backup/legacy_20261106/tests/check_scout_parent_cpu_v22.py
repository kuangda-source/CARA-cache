import ast
import hashlib
import types
"""Full sparse-parent ON/OFF controls with explicit small CPU stand-ins."""
import json
import copy
import inspect
from pathlib import Path
from textwrap import dedent
import torch

from wcomr.policy_interval_assets_r1 import cells
from wcomr.scout_parent_v22 import execute, noise_coordinates
from wcomr.scout_readout_v22 import PARENT_FINGERPRINT, STATE_STEPS, LABELS
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_absolute_h1_control_r1 import VERSION, fingerprint


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader):
    metadata=json.loads((Path(__file__).resolve().parents[1]/'plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json').read_text())
    expected_rows={v['step']:v for v in metadata['rows_per_prompt']}
    net=inference.pipe.model.net;model=inference.pipe.model;scheduler=model.sample_scheduler
    # Small declared latent geometry; production geometry is a separate gate.
    model.config.state_ch=8
    class NonlinearHead(torch.nn.Module):
        def forward(self,x,*a,**kw):return x+.01*x.square()
    net.final_layer=NonlinearHead().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
            .set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    cal=Calibration('EXPLICIT_TOY_FULL_LEGAL_SOURCE_GRID',{(s,t):.99 for s,t in cells()},
        {t:1. for t in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('SYNTHETIC',1.,4.,3.5),partial_prior=CreationPhasePrior(
        'SYNTHETIC',.005,.3,early_creation_floor=.005,late_creation_floor=.02),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec};prior={'fingerprint':'UNCHANGED_TOY_PRIOR','gamma':.5}
    p=dict(version=VERSION,gamma=.5,table_model=dict(grouping='SOURCE_PHASE',target='absolute_guided_MSE',
        current_teacher_energy_is_online_feature=False,cells={s+'_'+phase:dict(status='FIT',C_scale=100.,
        A_ratios={'FUSION_A':.02},actual_NEW_P_birth_mean=.0001) for s in ('D','P') for phase in ('EARLY','LATE')}),
        cost_seconds={'C':1.,'A':1.3,'P':3.5,'D':4.},source_A_cost_seconds={'D':1.1,'P':1.3},lambda_seconds_per_weighted_absolute_MSE=100.)
    p['fingerprint']=fingerprint(p);tables={'SOURCE_PHASE':p}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    root=Path(artifact_root)/('flow_'+str(flow));records=[]
    try:
        for name in ('OLD_CAL_CPU_0','OLD_CAL_CPU_1'):
            sample=type(selected[0])(name); group=[]
            for enabled in (False,True):
                initial.restore();payloads=[]
                def sink(value):
                    # Serialize then reload all branch tensors and conditions,
                    # not just scalar error rows. Bulk fixture stays untracked.
                    path=root/name/('state_'+str(value['step'])+'.pt');path.parent.mkdir(parents=True,exist_ok=True)
                    with path.open('xb') as f:torch.save(value,f)
                    v=tensor_loader(path)
                    assert v['step']==value['step'] and set(v['summary'])==set(LABELS)
                    e=expected_rows[v['step']]
                    assert v['xi']==e['xi'] and v['sigma']==e['sigma']
                    assert v['source_anchor_steps']==[e['anchor_older'],e['anchor_b']]
                    assert set(v['pre_pair_checkpoint']) >= {'WC_cache','solver','torch_cpu_rng','numpy_rng'}
                    assert v['P0_actual_dense'] and v['P1_dense_head_RF_equal'] and v['P2_C_actual_parent_equal']
                    payloads.append(v['step'])
                result=execute(inference,sample,enabled=enabled,context=(name,'DECLARED_TOY_WEIGHTS',PARENT_FINGERPRINT),
                    sink=sink,copy_cap=1<<30,table_parameters=tables,previous_parameters=prior,
                    runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                    inference_module=inference_module,expected_shape=[1,8,2,8,8],
                    output=root/name/('ON' if enabled else 'OFF'),audit=True)
                assert result['status']=='COMPLETE'
                assert result['scout_lifecycle']['owners_alive_after']==0
                assert payloads==(list(STATE_STEPS) if enabled else [])
                group.append(result)
            assert all(torch.equal(a,b) for a,b in zip(group[0]['guided'],group[1]['guided']))
            assert torch.equal(group[0]['final_latent'],group[1]['final_latent'])
            assert Path(group[0]['video_path']).read_bytes()==Path(group[1]['video_path']).read_bytes()
            records.append(dict(request=name,full36_OFF_ON_equal=True,final_latent_and_declared_CPU_RGB_equal=True,
                selected_states=6,readout_positions=36,actual_dense_teacher_pairs=6,owner_released=True))
        faults=[]
        sample=type(selected[0])('OLD_CAL_CPU_FAILURE')
        for fault_name in ('teacher_failure','last_state_writer_failure','copy_cap'):
            initial.restore();owner_refs=[];saved_steps=[]
            original_forwards=[b.mlp.forward for b in net.blocks]
            def fault(site,step,owner):
                if fault_name=='teacher_failure' and step==22:
                    import weakref
                    owner_refs.append(weakref.ref(owner))
                    owner.controller.accumulated=999.
                    owner.head_calls.append({'injected':True})
                    torch.rand(3)
                    raise ValueError('INJECTED_TEACHER_FAILURE')
            def sink(value):
                saved_steps.append(value['step'])
                if fault_name=='last_state_writer_failure' and value['step']==35:
                    raise OSError('INJECTED_LAST_STATE_DISK_FAILURE')
            expected={'teacher_failure':'INJECTED_TEACHER_FAILURE',
                'last_state_writer_failure':'INJECTED_LAST_STATE_DISK_FAILURE',
                'copy_cap':'copy budget exceeded'}[fault_name]
            try:
                execute(inference,sample,enabled=True,context=(sample.name,'DECLARED_TOY_WEIGHTS',PARENT_FINGERPRINT),
                    sink=sink,copy_cap=1 if fault_name=='copy_cap' else 1<<30,fault=fault,
                    table_parameters=tables,previous_parameters=prior,runtime=runtime,wc=wc,rf=rf,
                    settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                    expected_shape=[1,8,2,8,8],output=root/fault_name,audit=True)
            except Exception as exc:
                assert expected in str(exc),repr(exc)
            else:raise AssertionError('Injected boundary accepted')
            assert [b.mlp.forward for b in net.blocks]==original_forwards
            assert not any(b.mlp.layer1._forward_pre_hooks or b.mlp.layer2._forward_pre_hooks for b in net.blocks)
            import gc
            gc.collect();assert all(r() is None for r in owner_refs)
            assert saved_steps==(list(STATE_STEPS) if fault_name=='last_state_writer_failure' else [])
            faults.append(dict(fault=fault_name,original_error_preserved=True,adapter_uninstalled=True,
                attempted_sink_positions=len(saved_steps),
                completed_sink_positions=max(0,len(saved_steps)-(fault_name=='last_state_writer_failure')),no_replay=True))
        # Mapping must reject another call's timestep and malformed sigma grid.
        from types import SimpleNamespace
        grid=json.loads((Path(__file__).resolve().parents[1]/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json').read_text())['schedules'][2]
        scheduler_case=SimpleNamespace(sigmas=torch.tensor(grid['sigmas']),timesteps=torch.tensor(grid['timesteps']))
        t=grid['timesteps'][21]
        noise_coordinates(scheduler_case,22,torch.tensor([t]))
        for bad in ('timestep','grid','different_valid_grid'):
            obj=copy.deepcopy(scheduler_case)
            if bad=='grid':obj.sigmas[-1]=.01
            if bad=='different_valid_grid':obj.sigmas[1]-=.00001
            try:noise_coordinates(obj,22,torch.tensor([t-1 if bad=='timestep' else t]))
            except ValueError:pass
            else:raise AssertionError('Invalid actual time identity accepted')
        return [dict(flow=flow,status='PASS',requests=records,actual_CPU_paths=4,failed_boundary_attempts=faults,time_mapping_rejections=3,
            pinned_WC_RF_UniPC=True,weights_attention_prepare_decode_writer='DECLARED_SMALL_CPU_STANDINS',
            full_Cosmos_weights=False,scientific_readout_gate_evaluated=False)]
    finally:
        initial.restore();assert initial.fingerprint()==origin


def run(runtime,tensor_loader,artifact_root):
    old=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(old.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    source=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader)\n'+source[end:]
    full=load('check_full_sampling')
    # The local CPU harness supplies exact AST-loaded WC/RF bodies, avoiding
    # optional CUDA package imports. Production imports remain a later gate.
    before1='    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc'
    before2='    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf'
    assert source.count(before1)==source.count(before2)==1
    source=source.replace(before1,'    wc = _WC').replace(before2,'    rf = _RF')
    ns={**vars(old),'_body':body}
    exec(compile(source,__file__+'#declared-Toy-old','exec'),ns)
    def exercise(**kw):
        ns['_WC']=kw['wc']
        wc_path=Path(runtime)/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
        assert Path(kw['wc'].worldcache_mini_train_dit_forward.__code__.co_filename).resolve()==wc_path.resolve()
        kw['wc'].__file__=str(wc_path)
        full.load_functions(wc_path,['compute_saliency_map'],vars(kw['wc']))
        path=Path(runtime)/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
        nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow'];assert len(nodes)==1
        rf=types.ModuleType('declared_local_CPU_pinned_RF')
        rf.__file__=str(path)
        vars(rf).update(torch=torch,Text2WorldModelRectifiedFlow=object,DataType=kw['wc'].DataType,
            parallel_state=types.SimpleNamespace(is_initialized=lambda:False),NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames')
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*nodes],type_ignores=[])),str(path),'exec'),vars(rf))
        ns['_RF']=rf
        return ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw)
    value=full.run(runtime,exercise=exercise)
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='SCOUT_SPARSE_PARENT_SOURCE_PATH_CPU_PASS_NOT_REAL_WEIGHT_ACCEPTANCE',
        actual_CPU_paths=8,failed_boundary_attempts=6,selected_states=24,readout_positions=144,
        CUDA_initialized=False,GPU_submissions=0,server_actions=0)
    return value
