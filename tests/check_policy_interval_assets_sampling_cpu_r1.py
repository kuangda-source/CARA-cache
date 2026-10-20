"""Complete14 x two flows on pinned WC/RF/UniPC with explicit small Toy weights."""
import copy
import inspect
from pathlib import Path
from textwrap import dedent
import torch

from wcomr.policy_interval_assets_r1 import matrix, SCENES, cells, COUNTS
from wcomr.policy_interval_assets_sampling_r1 import execute
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
    net=inference.pipe.model.net;model=inference.pipe.model;scheduler=model.sample_scheduler
    # Only the declared Toy latent channel count changes to keep the full406
    # cell grid practical on CPU. Production dimensions are checked separately.
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
    samples={name:type(selected[0])(name) for name in SCENES};rows=[];all_results={}
    def native(self,*a,**kw):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=threshold
    root=Path(artifact_root)/('flow_'+str(flow))
    try:
        for planned in matrix():
            initial.restore();assert initial.fingerprint()==origin
            result=execute(inference,samples[planned['scene']],planned['mode'],
                table_parameters=tables,previous_parameters=prior,runtime=runtime,wc=wc,rf=rf,
                settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                expected_shape=[1,8,2,8,8],output=root/planned['id'],audit=True,CPU_native=native)
            assert result['status']=='COMPLETE'
            assert result['guided_pairs']==result['solver_steps']==36
            assert result['request_memory_lifecycle']['owners_alive_after']==0
            if planned['mode']=='COLLECT':
                assert len(result['interval_cells'])==406
                assert sum(len(c['price_trials']) for c in result['interval_cells'])==2604
                from wcomr.policy_interval_assets_audit_r1 import audit_cells
                verdict=audit_cells(result['interval_cells'],artifact_root,[1,8,2,8,8],tensor_loader)
                assert len(verdict['cells'])==406
            rows.append(dict(**planned,status=result['status']))
            all_results[planned['id']]=result
        for i,scene in enumerate(SCENES):
            group=[all_results['formal_'+str(i)+'_'+m] for m in ('NATIVE','CONTROL','COLLECT')]
            for result in group[1:]:
                assert all(torch.equal(a,b) for a,b in zip(group[0]['guided'],result['guided']))
                assert torch.equal(group[0]['final_latent'],result['final_latent'])
                assert Path(group[0]['video_path']).read_bytes()==Path(result['video_path']).read_bytes()
        warm=[all_results['warm_1_CONTROL'],all_results['warm_2_COLLECT']]
        assert all(torch.equal(a,b) for a,b in zip(warm[0]['guided'],warm[1]['guided']))
        assert torch.equal(warm[0]['final_latent'],warm[1]['final_latent'])
        # An ordinary rejection retains the complete request, creates no cell,
        # and releases the request owner without a replacement sample.
        from wcomr.clean_speed20_r1 import patched
        for mode in ('NATIVE','CONTROL','COLLECT'):
            initial.restore()
            with patched(inference,'generate',lambda *a,**kw:[]):
                result=execute(inference,samples[SCENES[0]],mode,table_parameters=tables,previous_parameters=prior,
                    runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                    inference_module=inference_module,expected_shape=[1,8,2,8,8],output=root/('rejected_'+mode),audit=True,CPU_native=native)
            assert result['status']=='TEXT_REJECTED' and not result.get('interval_cells')
            assert result['request_memory_lifecycle']['owners_alive_after']==0
        return [dict(flow=flow,status='PASS',complete_CPU_paths=14,guard_refusal_controls=3,
            complete_source_time_cells=2030,full_readout_trials=13020,formal_source_time_cells=1624,
            all36_observer_OFF_ON_and_Native_equal=True,full_final_and_CPU_RGB_equal=True,
            nonlinear_head_used=True,owners_released=True,ordinary_initial_state_restored=True,
            declared_Toy_channels=8,real_GPU_or_video_claim=False)]
    finally:
        initial.restore();assert initial.fingerprint()==origin


def run(runtime,tensor_loader,artifact_root):
    old=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(old.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    source=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader)\n'+source[end:]
    ns={**vars(old),'_body':body};exec(compile(source,__file__+'#unchanged-pinned-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='POLICY_INTERVAL_ASSETS_FULL_SCOPE_NUMERICAL_CPU_PASS_NOT_GPU',
        actual_CPU_paths=28,source_time_cells_reloaded=4060,readout_trials=26040,
        formal_cells_across_two_flows=3248,CUDA_initialized=False,GPU_submissions=0)
    return value
