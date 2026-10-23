"""Compare old fixed-mask and PG executors through unchanged pinned WC/RF/UniPC.
Toy weights, conditioning, decoder/writer are explicit; actual import/codec is a
separate production CPU gate. All four declared inputs and both flow modes.
"""
import ast, hashlib, inspect, json, types
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_fixed_mask_r1 import execute_fixed
from wcomr.policy_generator_r1.historical_bridge import historical_policies
from wcomr.policy_generator_r1.production_sampling import execute as pg_execute
from wcomr import clean_speed20_r1 as clean
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    # Same nonlinear head and nonzero branch conditions as accepted PG controls.
    model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*a,**kw):return x+.01*x.square()
    net.final_layer=Head().eval();net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    params=json.loads((ROOT/'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    old=json.loads((ROOT/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    cal=Calibration('DECLARED_CPU_HISTORY_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('DECLARED_CPU_ONLY',params['source_A_cost_seconds']['D'],params['cost_seconds']['D'],params['cost_seconds']['P']),partial_prior=CreationPhasePrior('DECLARED_CPU_ONLY',.005,.3,early_creation_floor=.005,late_creation_floor=.02),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec},inference_module=inference_module,expected_shape=[1,8,2,8,8])
    pg=load('check_cara_pg_production_sampling_cpu_r1');profile=pg.test_profile();policies=historical_policies(profile)
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint();checks=[];paths=0
    def compare(a,b,full):
        assert torch.equal(a['final_latent'],b['final_latent'])
        if a['method']=='NATIVE' or b['method']=='NATIVE':
            assert all(r['actions'] is None if r['method']=='NATIVE' else r['actions']==['DD']*36 for r in (a,b))
        else:assert a['actions']==b['actions']
        assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
        if full:assert len(a['guided'])==len(b['guided'])==36 and all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
    try:
        for i,sample in enumerate(selected):
            for role,policy in policies.items():
                outcomes=[]
                for entry in ('OLD','PG'):
                    for audit in ((True,False) if i==0 else (True,)):
                        initial.restore();assert initial.fingerprint()==origin
                        args=dict(common,output=Path(artifact_root)/str(flow)/str(i)/(role+entry+str(audit)),audit=audit)
                        if entry=='OLD':
                            r=execute_fixed(inference,sample,replay_plan=policy['actions'],table_parameters=params,previous_parameters=old,**args)
                            history=[h['A_readout'] for h in r['source_history']]
                            assert all(h['true_D_before']==h['true_D_after'] for h in r['source_history'] if h['action']!='DD')
                        else:
                            r=pg_execute(inference,sample,profile=profile,policy=policy,**args)
                            assert all(h['fallback_reason'] is None for h in r['semantic_history'])
                            history=[h['source_history'] for h in r['semantic_history']]
                        assert r['status']=='COMPLETE' and r['guided_pairs']==r['solver_steps']==36
                        for t,h in enumerate(history,1):
                            if policy['actions'][t-1]!='D':
                                anchors=[j for j,a in enumerate(policy['actions'][:t-1],1) if a=='D'][-2:]
                                actual_anchors=r['source_history'][t-1]['true_D_before'] if entry=='OLD' else h['past_D_steps']
                                assert actual_anchors==[anchors,anchors], (role,entry,t,actual_anchors,anchors)
                                if entry=='OLD' and policy['actions'][t-1]=='A':assert h['past_D_steps']==actual_anchors
                                assert h['shared_alpha']==(policy['shared_alpha'][t-1] or 0.)
                            assert h['teacher_calls']==0
                        if outcomes:compare(outcomes[0],r,audit)
                        outcomes.append(r);paths+=1
                checks.append(dict(input=sample.name,role=role,all36_guided_equal=True,final_latent_and_mock_video_equal=True,alpha_and_true_anchor_history_equal=True,audit_lean_checked=i==0))
        # Explicit same-entry all-D reference and direct Native equality.
        profile,ps=pg.plans()
        def native(self,*a,**kw):
            threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
            try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
            finally:self.worldcache_rel_l1_thresh=threshold
        controls=[]
        for audit in (True,False):
            for entry in ('NATIVE','PG'):
                initial.restore();args=dict(common,output=Path(artifact_root)/str(flow)/(entry+str(audit)),audit=audit)
                r=clean.execute(inference,selected[0],'NATIVE',CPU_native=native,**args) if entry=='NATIVE' else pg_execute(inference,selected[0],profile=profile,policy=ps['ALL_D'],**args)
                if controls:compare(controls[0],r,audit)
                controls.append(r);paths+=1
        assert paths==74
        return [dict(flow=flow,status='PASS',complete_CPU_paths=paths,checks=checks,Native_allD_equal=True,all36_audit_lean_controls=True)]
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
        namespace['_RF']=rf
        return namespace['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw)
    value=full.run(runtime,exercise=exercise)
    assert {c['flow'] for c in value['checks']}=={False,True}
    assert sum(c['complete_CPU_paths'] for c in value['checks'])==148
    value.update(status='HISTORICAL_BRIDGE_FULL148_LOCAL_NUMERICAL_CPU_PASS_NOT_PRODUCTION_CPU',
        actual_CPU_paths=148,ordinary_pairs=5328,CFG_calls=10656,model_weights_loaded=0,
        real_videos_generated=0,new_policy_quality_or_speed_claim=False,
        full_RF_class_AST_unchanged=True,local_optional_package_imports_bypassed=True)
    return value
