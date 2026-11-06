"""New coarse-calibration core through pinned RF/WC/UniPC full36 Toy CPU."""
import copy
import inspect
from pathlib import Path
import tempfile
import types

import torch

from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from wcomr.cfg_paired_probe_production import compile_production
from wcomr.cfg_paired_probe_velocity import compile_velocity
from wcomr.cfg_ra_calibration import (SharedSchedulePairExecutor, CoarseCalibrationFork,
    TARGET_STEPS, DENSE_STEPS, ORIGIN_ANCHORS)
from wcomr.cfg_ra_calibration_table import statistics, fit_table, load_table
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import object_state, official_suffix


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercise(*, inference, flow, runtime, **unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    fixture = inference.pipe.model
    condition_class, _ = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    original = copy.deepcopy(fixture.net)
    original.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    entry = RNGState()
    all_rows, paths = [], []
    total_net_calls = 0
    total_solver_updates = 0
    def reject(call, message):
        try: call()
        except (ValueError, KeyError) as error:
            return {'control': message, 'error': str(error), 'rejected': True}
        raise AssertionError('Mutation unexpectedly accepted: '+message)

    with tempfile.TemporaryDirectory(prefix='ra-cal-full36-') as directory:
        root = Path(directory)
        def run_path(scene, collect):
            nonlocal total_net_calls, total_solver_updates
            entry.restore()
            net = copy.deepcopy(original)
            wc.apply_worldcache(net, num_steps=70, ret_ratio=.2, rel_l1_thresh=.08,
                probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
            net.worldcache_saliency_enabled = True
            net.worldcache_saliency_weight = 5.
            net.worldcache_dynamic_decay = True
            net.eval()
            config = copy.deepcopy(fixture.config)
            for name, value in dict(min_num_conditional_frames=0,max_num_conditional_frames=0,
                    conditional_frames_probs=None,conditional_frame_timestep=.15,
                    denoise_replace_gt_frames=True).items():
                setattr(config,name,value)
            m = types.SimpleNamespace(net=net, sample_scheduler=copy.deepcopy(fixture.sample_scheduler),
                config=config, generation=0, tensor_kwargs={'device':'cpu','dtype':torch.float32},
                input_data_key='video',input_image_key='images',tokenizer=fixture.tokenizer)
            m._normalize_video_databatch_inplace = lambda b: setattr(m,'generation',m.generation+1)
            m._augment_image_dim_inplace = lambda b: None
            m.is_image_batch = lambda b: False
            m.get_data_and_condition = lambda b: (None,b['video'],None)
            m.broadcast_split_for_model_parallelsim = lambda x,c,e,s: (x,c,e,s)
            def construct(b):
                return tuple(condition_class(crossattn_emb=torch.ones(1,3,4)*(1+slot+.1*(scene=='Human')),
                    fps=b['fps'].clone(),padding_mask=torch.zeros(1,1,8,8),
                    use_video_condition=torch.tensor([slot==0])) for slot in (0,1))
            m.conditioner = types.SimpleNamespace(get_condition_with_negative_prompt=construct,
                get_condition_uncondition=construct)
            m.denoise = types.MethodType(rf.Video2WorldModelRectifiedFlow.denoise,m)
            net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward,net)
            _, denoise, _ = compile_production(runtime,wc,rf)
            base = NativePolicyPairedExecutor(m,denoise,torch,
                wc_forward=wc.worldcache_mini_train_dit_forward,
                rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
            executor = SharedSchedulePairExecutor(base)
            factory, _ = compile_velocity(runtime,rf,executor,executor.choose)
            capture = {'in_fork': False}
            trace = {'scene':scene,'collect':collect,'guided':[],'solver':[],
                'actions':[],'checkpoints':[],'origins':[]}
            conditions = []
            def count(*unused):
                nonlocal total_net_calls
                total_net_calls += 1
            handle = net.blocks[0].register_forward_hook(count)
            def get_velocity(b,*args,**kwargs):
                velocity = factory(m,b,*args,**kwargs)
                cells = inspect.getclosurevars(velocity).nonlocals
                assert set(cells)=={'self','condition','uncondition','guidance'} and cells['guidance']==7
                conditions.extend((cells['condition'],cells['uncondition']))
                trace['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                capture['velocity'] = velocity
                def measured(noise,latent,timestep):
                    capture['noise'] = noise
                    before = [float(b.visits) for b in net.blocks]
                    value = velocity(noise,latent,timestep)
                    delta = [float(b.visits)-v for b,v in zip(net.blocks,before)]
                    action = executor.history[-1]['action']
                    assert delta==[2.,2.,float(action.count('D')),float(action.count('D'))]
                    trace['guided'].append(value.detach().cpu().clone())
                    trace['actions'].append(action)
                    return value
                return measured
            m.get_velocity_fn_from_batch = get_velocity
            m.generate_samples_from_batch = types.MethodType(fixture.generate_samples_from_batch.__func__,m)
            scheduler = m.sample_scheduler
            original_step = scheduler.step
            def writer(label,values):
                path = root/(scene+'-'+label+'.pt')
                assert not path.exists()
                torch.save(values,path)
                loaded = torch.load(path,weights_only=True,map_location='cpu')
                assert set(loaded)==set(values)
                assert all(torch.equal(values[k],loaded[k]) for k in values)
                return {'path':str(path),'tensor_sha256':{k:tree_digest(v) for k,v in loaded.items()}}
            def step(*args,**kwargs):
                nonlocal total_solver_updates
                value = original_step(*args,**kwargs)
                total_solver_updates += 1
                if capture['in_fork']:
                    return value
                trace['solver'].append(tree_digest(value))
                completed = len(trace['solver'])
                assert scheduler._step_index==completed and len(executor.history)==completed
                latent = value[0].squeeze(0)
                if completed in (12,22,32,36):
                    snapshot = CompleteStateRoundtrip(net,scheduler,latent,[kwargs['generator']])
                    trace['checkpoints'].append({'step':completed,'components':snapshot.components(),
                        'own_history':copy.deepcopy(executor.history),'own_fingerprint':executor.fingerprint()})
                if collect and completed+1 in TARGET_STEPS:
                    capture['in_fork'] = True
                    try:
                        fork = CoarseCalibrationFork(m,latent,capture['noise'],kwargs['generator'],
                            capture['velocity'],suffix,context=(scene,'ToyActualRF','actual-condition'),executor=executor)
                        origin = {'step':completed+1,'arms':fork.records}
                        trace['origins'].append(origin)
                        for mode in ('CC','DD'):
                            fork.measure(mode,writer=writer,label='step'+str(completed+1)+'-'+mode,save=lambda:None)
                        a,b = origin['arms']
                        assert a['origin_components']==b['origin_components']
                        assert a['origin_own_fingerprint']==b['origin_own_fingerprint']
                        assert a['current_input_sha256']==b['current_input_sha256']
                        assert all(r['parent_restored'] and r['own_shared_history_restored'] for r in (a,b))
                        assert fork.snapshot.fingerprint()==fork.parent_fingerprint
                        assert executor.fingerprint()==fork.own_fingerprint
                        raw = [torch.load(r['artifact']['path'],weights_only=True,map_location='cpu') for r in (a,b)]
                        all_rows.append({'sample_name':scene,'target_step':completed+1,
                            'shared_anchor':ORIGIN_ANCHORS[completed+1],
                            'reuse_age':completed+1-ORIGIN_ANCHORS[completed+1],
                            'raw_artifacts_independently_reloaded':True,'statistics':statistics(*raw)})
                    finally:
                        capture['in_fork'] = False
                return value
            scheduler.step = step
            batch = {'video':torch.linspace(-.3,.4,2048*2*8*8).reshape(1,2048,2,8,8),
                     'fps':torch.tensor([16.]),rf.NUM_CONDITIONAL_FRAMES_KEY:1}
            batch_sha = tree_digest(batch)
            params = [(p,p._version) for p in net.parameters()]
            try:
                with torch.no_grad():
                    final = m.generate_samples_from_batch(copy.deepcopy(batch),guidance=7,seed=3,
                        state_shape=(2048,2,8,8),n_sample=1,is_negative_prompt=True,num_steps=35,shift=5)
                assert len(trace['solver'])==len(trace['guided'])==36
                assert trace['actions']==['DD' if t in DENSE_STEPS else 'CC' for t in range(1,37)]
                assert len(trace['origins'])==(3 if collect else 0)
                assert all(p._version==v for p,v in params) and not any(m.training for m in net.modules())
                assert tree_digest(batch)==batch_sha
                trace.update(conditions_after=tree_digest([object_state(c) for c in conditions]),
                    final_latent=final.detach().cpu().clone(),rng_after=RNGState().signatures(),
                    own_history=copy.deepcopy(executor.history), own_fingerprint=executor.fingerprint())
                assert trace['conditions_before']==trace['conditions_after']
                return trace
            finally:
                handle.remove()
        try:
            for scene in ('Common','Human'):
                off,on = run_path(scene,False),run_path(scene,True)
                assert all(torch.equal(a,b) for a,b in zip(off['guided'],on['guided']))
                assert torch.equal(off['final_latent'],on['final_latent'])
                for key in ('solver','actions','checkpoints','conditions_before','conditions_after',
                            'rng_after','own_history','own_fingerprint'):
                    assert off[key]==on[key],key
                paths.append({'scene':scene,'full36_parent_OFF_ON_actual_equal':True,
                    'complete_origins':on['origins'],'parent_actions':on['actions'],
                    'conditions_and_global_RNG_equal':True})
            cal,payload = fit_table(all_rows,sample_names=['Common','Human'],
                fingerprint_context='ACTUAL_PINNED_TOY_FULL36_NOT_COSMOS',toy=True)
            assert load_table(payload,permit_toy=True).fingerprint==cal.fingerprint
            controls = [reject(lambda:load_table(payload),'Toy table cannot enter real deployment'),
                reject(lambda:fit_table(all_rows[:-1],sample_names=['Common','Human'],
                    fingerprint_context='TOY',toy=True),'Incomplete origin scope')]
            changed = copy.deepcopy(payload)
            changed['rho_prior'] += .001
            controls.append(reject(lambda:load_table(changed,permit_toy=True),'Changed estimated prior'))
            assert all((a,t) not in cal.rho_at for a in range(1,30) for t in (a+7,))
            assert set(cal.gains)==set(range(1,37))
            assert total_solver_updates==312 and total_net_calls==624,(total_solver_updates,total_net_calls)
            return [{'kind':'RA_calibration_actual_full_sampler_Toy_CPU','flow':flow,
                'status':'COMPLETE_SIX_ORIGIN_CAL_CORE_CPU_NOT_COSMOS',
                'parent_paths':4,'same_state_origins':6,'complete_child_arms':12,
                'actual_solver_updates':total_solver_updates,'actual_net_calls':total_net_calls,
                'full36_OFF_ON_comparisons':2,'paths':paths,'table':payload,'refusal_controls':controls,
                'saved_first_velocity_reused':True,'observed_rows':all_rows}]
        finally:
            entry.restore()


def run(runtime):
    result = load('check_full_sampling').run(Path(runtime),exercise=lambda **kw:exercise(runtime=Path(runtime),**kw))
    assert len(result['checks'])==2
    result.update(status='RA_COARSE_CAL_CORE_PINNED_FULL36_TOY_CPU_NOT_COSMOS',
        complete_parent_paths=8,same_state_origins=12,complete_child_arms=24,
        solver_updates=624,net_calls=1248,full36_parent_OFF_ON_comparisons=4,
        GPU_submissions=0,actual_Cosmos_calibration_generated=False,
        limits='Actual pinned RF/WC/UniPC; Toy weights and attention, no real2B, CUDA, video, policy or quality result.')
    return result
