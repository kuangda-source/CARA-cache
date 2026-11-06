"""All four actions through the actual complete sampler; declared Toy CPU limits."""
import copy
import inspect
from pathlib import Path
import types

import torch

from wcomr.cfg_paired_probe_mixed import mixed_forced_reference, MixedProductionPairedExecutor, MIXED_COMPILER_PROOF, MODES
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


def exercise(*, inference, flow, runtime, action_schedules, **unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    fixture = inference.pipe.model
    base = copy.deepcopy(fixture.net)
    base.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    condition_class, condition_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    refs = {a: mixed_forced_reference(runtime, dict(vars(wc)), a) for a in MODES}
    data = torch.linspace(-.3,.4,2048*2*8*8).reshape(1,2048,2,8,8)
    batch = {'video':data, 'fps':torch.tensor([16.]), rf.NUM_CONDITIONAL_FRAMES_KEY:1}
    original_data = tree_digest(batch)
    entry = RNGState()
    records = []

    def run_path(schedule, observers, paired, failure=None):
        entry.restore()
        sequence = action_schedules[schedule]
        assert len(sequence)==36 and all(mode in MODES for mode in sequence)
        net = copy.deepcopy(base)
        wc.apply_worldcache(net, num_steps=70, ret_ratio=.2, rel_l1_thresh=.08,
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
            'prefix_decisions':[],'_velocity_tensors':[]}
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
            if failure=='selector_step23' and m.sample_scheduler._step_index==22:
                raise ValueError('Injected step23 selector failure')
            if failure=='invalid_action_step23' and m.sample_scheduler._step_index==22:
                return 'INVALID'
            if failure=='selector_rng_step23' and m.sample_scheduler._step_index==22:
                torch.rand(1)
            action=choice(sequence,len(trace['velocity'])+1)
            trace['prefix_decisions'].append({'step':len(trace['velocity'])+1,'counter':net.cnt,
                'chosen_action':action,'actual_prefix_visits_before_any_deep':delta,
                'paid_slots':[p.slot for p in packets],'paid_counters':[p.counter for p in packets]})
            return action
        if paired:
            _,denoise,core=compile_production(runtime,wc,rf,
                before=before if observers else None,after=after if observers else None)
            executor=MixedProductionPairedExecutor(m,denoise,torch,
                wc_forward=wc.worldcache_mini_train_dit_forward,
                rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
            velocity_factory,proof=compile_velocity(runtime,rf,executor,select)
            if failure=='net_binding':
                old_forward=net.forward
                net.forward=lambda *args,**kwargs:old_forward(*args,**kwargs)
        else:
            executor=None;core=None;proof=None
            def reference_forward(*args,**kwargs):
                counter=int(net.cnt);slot=counter%2
                if observers:before(net,slot,args,kwargs)
                # Same joint tail protection as the paired executor, rather
                # than silently comparing the last original CC with paired DD.
                warmup=int(net.worldcache_num_steps*net.worldcache_ret_ratio)
                action='DD' if counter<warmup or counter>=net.worldcache_num_steps-2 else choice(sequence,len(trace['velocity'])+1)
                value=refs[action](net,*args,**kwargs)
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
                warmup=int(net.worldcache_num_steps*net.worldcache_ret_ratio)
                protected=counter<warmup or counter+1>=net.worldcache_num_steps-1
                action='DD' if protected else choice(sequence,len(trace['velocity']))
                if paired:
                    assert executor.last['action']==action and executor.last['protected']==protected
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
            expected={'selector_step23':('Injected step23 selector failure',22),
                'solver_tail':('Injected final solver failure',35),
                'net_binding':('Wrapped or changed net.forward would be bypassed',0),
                'condition_construction':('Injected video condition construction failure',0),
                'invalid_action_step23':('Explicit CC/DC/CD/DD action required',22),
                'selector_rng_step23':('Selector changed counter or CPU RNG',22)}
            assert expected[failure][0] in str(error)
            assert len(trace['solver_returns'])==expected[failure][1]
            if executor is not None and failure in ('selector_step23','net_binding','invalid_action_step23','selector_rng_step23'):
                assert executor.poisoned
            assert tree_digest(batch)==original_data and not torch.cuda.is_initialized()
            return {'kind':'four_action_full_sampler_failure','flow':flow,'failure':failure,
                'status':'EXPECTED_REJECTION','error':str(error),
                'completed_solver_steps':len(trace['solver_returns']),
                'planned_solver_steps':36,'whole_fixture_copy_discarded':True,
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
        if paired:trace.update(core_compiler=dict(core),velocity_compiler=dict(proof),mixed_compiler=dict(MIXED_COMPILER_PROOF))
        return trace

    try:
        for schedule in action_schedules:
            groups=[]
            for observers in (False,True):
                for repetition in (0,1):
                    ref=run_path(schedule,observers,False)
                    new=run_path(schedule,observers,True)
                    assert torch.equal(ref.pop('_final_latent_tensor'),new.pop('_final_latent_tensor'))
                    original_values=ref.pop('_velocity_tensors');paired_values=new.pop('_velocity_tensors')
                    assert len(original_values)==len(paired_values)==36
                    assert all(torch.equal(a,b) for a,b in zip(original_values,paired_values))
                    keys=('velocity','solver_returns','checkpoints','actions','counters','block_visits','condition_before',
                        'condition_after','roundtrip_step22_complete','final_latent_sha256','final_components',
                        'final_solver_sha256','generator_state_sha256','global_rng_sha256')
                    assert all(ref[k]==new[k] for k in keys)
                    if observers:
                        events=lambda rows:{(r['kind'],r['call']):r for r in rows}
                        assert len(ref['net_events'])==len(new['net_events'])==144
                        assert events(ref['net_events'])==events(new['net_events'])
                    else:
                        assert not ref['net_events'] and not new['net_events']
                    record={'kind':'four_action_full_sampler_comparison','flow':flow,'schedule':schedule,
                        'observers':observers,'repetition':repetition,'status':'PASS',
                        'solver_updates_per_path':36,'net_calls_per_path':72,
                        'original':ref,'paired':new,'all_complete_path_fields_equal':True,
                        'all_branch_observations_equal':True,'all_36_guided_tensors_direct_equal':True,
                        'full_action_sequence':action_schedules[schedule].copy(),'mixed_action_steps':[i+1 for i,a in enumerate(new['actions']) if a in ('DC','CD')]}
                    records.append(record);groups.append(record)
            invariant=('velocity','solver_returns','checkpoints','actions','block_visits','final_latent_sha256',
                'final_components','final_solver_sha256','generator_state_sha256','global_rng_sha256')
            assert all(all(row['paired'][k]==groups[0]['paired'][k] for k in invariant) for row in groups)
        for failure in ('selector_step23','solver_tail','net_binding','condition_construction','invalid_action_step23','selector_rng_step23'):
            records.append(run_path('FOUR_ACTION_CYCLE',True,True,failure))
        return records
    finally:
        entry.restore()


def run(runtime,tensor_loader,artifact_root,schedules):
    runtime=Path(runtime)
    assert len(schedules)==4 and 'FOUR_ACTION_CYCLE' in schedules
    old=load('check_cfg_paired_interface_sampling_cpu').run(runtime,tensor_loader,artifact_root)
    full=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(
        runtime=runtime,action_schedules=schedules,**kw))
    assert len(old['checks'])==68 and len(full['checks'])==44
    full['checks']=old['checks']+full['checks']
    full['limits']=('Complete four-action controller and source-pinned actual WC/RF/UniPC full36 to latent; '
        'Toy four-block CPU weights, attention, preparation, condition construction, normalize and broadcast. '
        'Prior H-T58 complete 68 rows and 96 generated Toy tensor reloads retained. New comparisons do not '
        'decode/write videos, load model weights, run CUDA or produce real2B, latency, policy or endpoint claims.')
    return full
