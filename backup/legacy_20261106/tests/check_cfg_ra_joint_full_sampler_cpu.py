"""New RA adapter through actual pinned full36 sampler; Toy CPU only."""
import copy
from dataclasses import asdict
import inspect
from pathlib import Path
import types

import torch

from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor, NATIVE_POLICY_COMPILER_PROOF, MODES
from wcomr.cfg_ra_joint_control import Calibration, JointCDController
from wcomr.cfg_ra_joint_execution import JointPolicyPairExecutor
from wcomr.cfg_paired_probe_forward import forced_reference
from wcomr.cfg_paired_probe_production import compile_production
from wcomr.cfg_paired_probe_velocity import compile_velocity
from wcomr.full_sampling import CompleteStateRoundtrip, STATE_STEPS
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import RNGState, input_signatures
from wcomr.rv0_fork import object_state, restore_object_state


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    value = module_from_spec(spec); spec.loader.exec_module(value)
    return value


def choice(sequence, step):
    if len(sequence) != 36 or any(a not in MODES for a in sequence) or not 1 <= step <= 36:
        raise ValueError('Complete registered four-action sequence required')
    return sequence[step-1]


def exercise(*, inference, flow, runtime, **unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    fixture = inference.pipe.model
    base = copy.deepcopy(fixture.net)
    base.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    condition_class, condition_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    data = torch.linspace(-.3,.4,2048*2*8*8).reshape(1,2048,2,8,8)
    batch = {'video':data, 'fps':torch.tensor([16.]), rf.NUM_CONDITIONAL_FRAMES_KEY:1}
    original_data = tree_digest(batch)
    entry = RNGState()
    records = []

    def run_path(schedule, observers, paired, failure=None):
        entry.restore()
        threshold={'NATIVE_THRESHOLD':.08,'HIGH_THRESHOLD':1e6}[schedule]
        net = copy.deepcopy(base)
        wc.apply_worldcache(net, num_steps=70, ret_ratio=.2, rel_l1_thresh=threshold,
            probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
        net.worldcache_saliency_enabled=True; net.worldcache_saliency_weight=5.0
        net.worldcache_dynamic_decay=True; net.eval()
        config = copy.deepcopy(fixture.config)
        for name, value in dict(min_num_conditional_frames=0,max_num_conditional_frames=0,
                conditional_frames_probs=None,conditional_frame_timestep=.15,
                denoise_replace_gt_frames=True).items():
            setattr(config,name,value)
        m = types.SimpleNamespace(net=net,sample_scheduler=copy.deepcopy(fixture.sample_scheduler),
            config=config,generation=0,tensor_kwargs={'device':'cpu','dtype':torch.float32},
            input_data_key='video',input_image_key='images',tokenizer=fixture.tokenizer)
        m._normalize_video_databatch_inplace=lambda b:setattr(m,'generation',m.generation+1)
        m._augment_image_dim_inplace=lambda b:None
        m.is_image_batch=lambda b:False
        m.get_data_and_condition=lambda b:(None,b['video'],None)
        m.broadcast_split_for_model_parallelsim=lambda x,c,e,s:(x,c,e,s)
        def construct(b):
            if failure == 'condition_construction':
                raise ValueError('Injected video condition construction failure')
            return tuple(condition_class(crossattn_emb=torch.ones(1,3,4)*(1+slot),
                fps=b['fps'].clone(),padding_mask=torch.zeros(1,1,8,8),
                use_video_condition=torch.tensor([slot==0])) for slot in (0,1))
        m.conditioner=types.SimpleNamespace(get_condition_with_negative_prompt=construct,
            get_condition_uncondition=construct)
        m.denoise=types.MethodType(rf.Video2WorldModelRectifiedFlow.denoise,m)
        net.forward=types.MethodType(wc.worldcache_mini_train_dit_forward,net)
        trace={'net_events':[],'velocity':[],'solver_returns':[],'checkpoints':[],'block_visits':[],
            'actions':[],'counters':[],'condition_before':None,'condition_after':None,
            'prefix_decisions':[],'_velocity_tensors':[],'native_branch_actions':[]}
        def before(n,slot,args,kwargs):
            trace['net_events'].append({'kind':'before','call':2*len(trace['velocity'])+slot,
                'slot':slot,'signature':input_signatures(args,kwargs)})
        def after(n,slot,value):
            trace['net_events'].append({'kind':'after','call':2*len(trace['velocity'])+slot,
                'slot':slot,'output_sha256':tree_digest(value)})
        def select(packets):
            assert [(p.slot,p.counter) for p in packets]==[(0,net.cnt),(1,net.cnt+1)]
            assert all(not hasattr(p,'hidden_state') for p in packets)
            delta=[float(b.visits)-v for b,v in zip(net.blocks,trace['_pair_entry_visits'])]
            assert delta==[2.,2.,0.,0.], delta
            if failure=='selector_tail35' and m.sample_scheduler._step_index==34:
                raise ValueError('Injected tail35 selector failure')
            if failure=='invalid_action_tail35' and m.sample_scheduler._step_index==34:
                return 'INVALID'
            if failure=='selector_rng_step23' and m.sample_scheduler._step_index==22:
                torch.rand(1)
            action=''.join('C' if p.native_cache else 'D' for p in packets)
            trace['prefix_decisions'].append({'step':len(trace['velocity'])+1,'counter':net.cnt,
                'chosen_action':action,'actual_prefix_visits_before_any_deep':delta,
                'paid_slots':[p.slot for p in packets],'paid_counters':[p.counter for p in packets]})
            return action
        if paired:
            _,denoise,core=compile_production(runtime,wc,rf,
                before=before if observers else None,after=after if observers else None)
            base_executor=NativePolicyPairedExecutor(m,denoise,torch,
                wc_forward=wc.worldcache_mini_train_dit_forward,
                rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
            table={} if schedule=='NATIVE_THRESHOLD' else {
                (a,t):1. for a in range(1,36) for t in range(a+1,37)}
            cal=Calibration('ACTUAL_SAMPLER_TOY_ONLY_NOT_COSMOS_CAL',table,{t:1. for t in range(1,37)})
            policy=JointCDController(cal,1e6)
            class ObservedJointExecutor(JointPolicyPairExecutor):
                def _select(self,packets):
                    delta=[float(b.visits)-v for b,v in zip(net.blocks,trace['_pair_entry_visits'])]
                    assert delta==[2.,2.,0.,0.],delta
                    action=super()._select(packets)
                    trace['prefix_decisions'].append({'step':len(trace['velocity'])+1,'counter':net.cnt,
                        'chosen_action':action,'actual_prefix_visits_before_any_deep':delta,
                        'paid_slots':[p.slot for p in packets],'paid_counters':[p.counter for p in packets]})
                    return action
            executor=ObservedJointExecutor(base_executor,policy)
            velocity_factory,proof=compile_velocity(runtime,rf,executor,executor.choose)
            if failure=='net_binding':
                old_forward=net.forward
                net.forward=lambda *args,**kwargs:old_forward(*args,**kwargs)
        else:
            executor=None;core=None;proof=None
            def reference_forward(*args,**kwargs):
                counter=int(net.cnt);slot=counter%2
                if observers:before(net,slot,args,kwargs)
                deep_visits=[float(b.visits) for b in net.blocks[net.probe_depth:]]
                value=forced_reference(runtime,vars(wc),'DD')(net,*args,**kwargs)
                changes=[float(b.visits)-v for b,v in zip(net.blocks[net.probe_depth:],deep_visits)]
                assert changes in ([0.,0.],[1.,1.])
                trace['native_branch_actions'].append('C' if changes==[0.,0.] else 'D')
                if observers:after(net,slot,value)
                return value
            net.forward=reference_forward
            velocity_factory=rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch
        conditions=[]
        def get_velocity(b,*args,**kwargs):
            velocity=velocity_factory(m,b,*args,**kwargs)
            cells=inspect.getclosurevars(velocity).nonlocals
            assert set(cells)=={'self','condition','uncondition','guidance'}
            assert cells['self'] is m and cells['guidance']==7
            conditions.extend([cells['condition'],cells['uncondition']])
            trace['condition_before']=tree_digest([object_state(c) for c in conditions])
            def observed_velocity(*args,**kwargs):
                counter=int(net.cnt)
                visits=[float(block.visits) for block in net.blocks]
                trace['_pair_entry_visits']=visits.copy()
                value=velocity(*args,**kwargs)
                trace.pop('_pair_entry_visits')
                trace['counters'].append(counter)
                assert value.dtype==torch.float32
                trace['velocity'].append(tree_digest(value))
                trace['_velocity_tensors'].append(value.detach().cpu().clone())
                action=executor.last['action'] if paired else ''.join(trace['native_branch_actions'][-2:])
                delta=[float(block.visits)-before for block,before in zip(net.blocks,visits)]
                expected_deep=float(action.count('D'))
                assert delta==[2.,2.,expected_deep,expected_deep], (action,delta)
                trace['block_visits'].append(delta)
                trace['actions'].append(action)
                return value
            return observed_velocity
        m.get_velocity_fn_from_batch=get_velocity
        m.generate_samples_from_batch=types.MethodType(fixture.generate_samples_from_batch.__func__,m)
        scheduler=m.sample_scheduler;original_step=scheduler.step
        generator=[None]
        def step(*args,**kwargs):
            if failure=='solver_tail' and scheduler._step_index==35:
                raise ValueError('Injected final solver failure')
            value=original_step(*args,**kwargs)
            generator[0]=kwargs['generator']
            if scheduler._step_index==22:
                saved_conditions=copy.deepcopy([object_state(c) for c in conditions])
                snapshot=CompleteStateRoundtrip(net,scheduler,value[0],[generator[0]])
                fingerprint=snapshot.fingerprint()
                value[0].add_(.123);net.cnt=-10
                for buffer in net.buffers():buffer.add_(10)
                for c in conditions:
                    c.gt_frames.add_(.3)
                    object.__setattr__(c,'discarded_child_field','CPU')
                restored=snapshot.restore()
                for c,saved in zip(conditions,saved_conditions):restore_object_state(c,saved)
                assert snapshot.fingerprint()==fingerprint
                assert tree_digest([object_state(c) for c in conditions])==tree_digest(saved_conditions)
                value=(restored,)+value[1:]
                trace['roundtrip_step22_complete']=True
            trace['solver_returns'].append(tree_digest(value))
            if scheduler._step_index in STATE_STEPS:
                snapshot=CompleteStateRoundtrip(net,scheduler,value[0],[generator[0]])
                trace['checkpoints'].append({'step':scheduler._step_index,'components':snapshot.components(),
                    'fingerprint':snapshot.fingerprint()})
            return value
        scheduler.step=step
        parameter_versions=[(id(p),p._version) for p in net.parameters()]
        try:
            with torch.no_grad():
                latent=m.generate_samples_from_batch(copy.deepcopy(batch),guidance=7,seed=3,
                    state_shape=(2048,2,8,8),n_sample=1,is_negative_prompt=observers,num_steps=35,shift=5)
        except ValueError as error:
            if failure is None:raise
            expected={'selector_tail35':('Injected tail35 selector failure',34),
                'solver_tail':('Injected final solver failure',35),
                'net_binding':('Wrapped or changed net.forward would be bypassed',0),
                'condition_construction':('Injected video condition construction failure',0),
                'invalid_action_tail35':('Explicit CC/DC/CD/DD action required',34),
                'selector_rng_step23':('Selector changed counter or CPU RNG',22)}
            assert expected[failure][0] in str(error)
            assert len(trace['solver_returns'])==expected[failure][1]
            if executor is not None and failure in ('selector_tail35','invalid_action_tail35'):
                assert executor.poisoned
                failed_counter=int(net.cnt)
                failed_rng=torch.get_rng_state().clone()
                try:
                    executor.pair(None,None,None,(),select)
                except ValueError as poisoned_error:
                    assert 'Poisoned executor cannot continue' in str(poisoned_error)
                else:
                    raise AssertionError('Poisoned tail executor continued')
                assert net.cnt==failed_counter and torch.equal(failed_rng,torch.get_rng_state())
            assert tree_digest(batch)==original_data and not torch.cuda.is_initialized()
            return {'kind':'native_policy_tail_failure','flow':flow,'failure':failure,
                'status':'EXPECTED_REJECTION','error':str(error),
                'completed_solver_steps':len(trace['solver_returns']),
                'planned_solver_steps':36,'whole_fixture_copy_discarded':True,
                'poisoned_continuation_rejected':True,
                'arbitrary_fault_full_rollback_claim':False}
        if failure is not None:
            raise AssertionError('Full sampler failure returned output: '+failure)
        assert parameter_versions==[(id(p),p._version) for p in net.parameters()]
        assert not any(module.training for module in net.modules())
        trace['condition_after']=tree_digest([object_state(c) for c in conditions])
        assert trace['condition_before']==trace['condition_after']
        assert tree_digest(batch)==original_data
        assert len(trace['velocity'])==len(trace['solver_returns'])==36
        assert trace['counters'][-2:]==[68,0] and net.cnt==2
        assert len(trace['checkpoints'])==5
        trace.update(final_latent_sha256=tree_digest(latent),
            final_components=CompleteStateRoundtrip(net,scheduler,latent,[generator[0]]).components(),
            final_solver_sha256=tree_digest({k:v for k,v in object_state(scheduler).items() if k!='step'}),
            generator_state_sha256=tree_digest(generator[0].get_state()),
            global_rng_sha256=tree_digest(RNGState().signatures()),parameter_versions_unchanged=True,
            all_modules_eval=True,condition_class_AST_SHA=condition_sha)
        trace['_final_latent_tensor']=latent
        if paired:trace.update(core_compiler=dict(core),velocity_compiler=dict(proof),native_policy_compiler=dict(NATIVE_POLICY_COMPILER_PROOF),policy_history=[asdict(d) for d in policy.history])
        return trace

    try:
        reference=run_path('NATIVE_THRESHOLD',False,False)
        dense=run_path('NATIVE_THRESHOLD',False,True)
        assert reference['actions']==dense['actions']==['DD']*36
        assert torch.equal(reference.pop('_final_latent_tensor'),dense.pop('_final_latent_tensor'))
        ref_v=reference.pop('_velocity_tensors');dense_v=dense.pop('_velocity_tensors')
        assert all(torch.equal(a,b) for a,b in zip(ref_v,dense_v))
        assert len(dense['policy_history'])==36 and dense['roundtrip_step22_complete']
        assert len(dense['prefix_decisions'])==28
        records.append({'kind':'RA_actual_sampler_all_dense_control','flow':flow,
            'status':'TOY_FULL36_PAIRED_DD_EQUALS_ORIGINAL_FORCED_DD',
            'actual_all36_guided_and_final_latent_equal':True,'reference':reference,'joint':dense})
        reuse=run_path('HIGH_THRESHOLD',False,True)
        assert reuse['actions']==['DD']*7+['CC']*28+['DD']
        assert len(reuse['policy_history'])==36 and len(reuse['prefix_decisions'])==28
        assert reuse['prefix_decisions'][-1]['paid_counters']==[68,69]
        assert reuse['policy_history'][34]['anchor_before']==7
        assert reuse['policy_history'][35]['reason']=='actual_protected_dense'
        assert reuse['policy_history'][35]['step']==36
        assert torch.isfinite(reuse.pop('_final_latent_tensor')).all()
        assert all(torch.isfinite(v).all() for v in reuse.pop('_velocity_tensors'))
        records.append({'kind':'RA_actual_sampler_joint_reuse_execution','flow':flow,
            'status':'TOY_FULL36_ACTUAL_REUSE_DEEP_VISITS_AND_CFG_CHECKED','joint':reuse})
        return records
    finally:
        entry.restore()


def run(runtime):
    runtime=Path(runtime)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=runtime,**kw))
    assert len(result['checks'])==4
    result.update(status='RA_JOINT_EXECUTION_ACTUAL_PINNED_SAMPLER_TOY_CPU_NOT_CALIBRATED_COSMOS',
        complete_paths=6,solver_updates=216,net_calls=432,
        actual_source_forced_DD_control_comparisons=2,
        actual_source_joint_reuse_complete_paths=2,
        actual_Cosmos_calibration_generated=False,production_policy_installed=False,
        limits='Actual pinned WC/RF/UniPC full36; Toy weights/attention/preparation, no CUDA, real2B, videos, calibration or quality/speed result.')
    return result
