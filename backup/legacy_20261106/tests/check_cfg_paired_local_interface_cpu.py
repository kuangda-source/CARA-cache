"""S22 restored local interface inside complete original Toy CPU parents."""
import copy
import inspect
from pathlib import Path
import types

import torch

from wcomr.cfg_paired_local_interface import PairedLocalInterface, verify_comparisons
from wcomr.full_sampling import CompleteStateRoundtrip, STATE_STEPS
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import object_state, official_suffix


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


def exercise(*,inference,flow,runtime,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    fixture=inference.pipe.model
    base=copy.deepcopy(fixture.net)
    base.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    condition_class,condition_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    data=torch.linspace(-.3,.4,2048*2*8*8).reshape(1,2048,2,8,8)
    batch={'video':data,'fps':torch.tensor([16.]),rf.NUM_CONDITIONAL_FRAMES_KEY:1}
    original_data=tree_digest(batch)
    entry=RNGState()
    suffix=official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    parents=[]
    records=[]
    try:
        for phase in ('OFF','ON'):
            entry.restore()
            net=copy.deepcopy(base)
            wc.apply_worldcache(net,num_steps=70,ret_ratio=.06,rel_l1_thresh=.08,
                probe_depth=2,osi_enabled=True,flow_enabled=flow,flow_scale=1)
            net.worldcache_saliency_enabled=True;net.worldcache_saliency_weight=5.0
            net.worldcache_dynamic_decay=True;net.eval()
            config=copy.deepcopy(fixture.config)
            for name,value in dict(min_num_conditional_frames=0,max_num_conditional_frames=0,
                    conditional_frames_probs=None,conditional_frame_timestep=.15,
                    denoise_replace_gt_frames=True).items():setattr(config,name,value)
            m=types.SimpleNamespace(net=net,sample_scheduler=copy.deepcopy(fixture.sample_scheduler),config=config,
                generation=0,tensor_kwargs={'device':'cpu','dtype':torch.float32},input_data_key='video',
                input_image_key='images',tokenizer=fixture.tokenizer)
            m._normalize_video_databatch_inplace=lambda b:setattr(m,'generation',m.generation+1)
            m._augment_image_dim_inplace=lambda b:None
            m.is_image_batch=lambda b:False
            m.get_data_and_condition=lambda b:(None,b['video'],None)
            m.broadcast_split_for_model_parallelsim=lambda x,c,e,s:(x,c,e,s)
            def construct(b):
                return tuple(condition_class(crossattn_emb=torch.ones(1,3,4)*(1+slot),fps=b['fps'].clone(),
                    padding_mask=torch.zeros(1,1,8,8),use_video_condition=torch.tensor([slot==0])) for slot in (0,1))
            m.conditioner=types.SimpleNamespace(get_condition_with_negative_prompt=construct,get_condition_uncondition=construct)
            m.denoise=types.MethodType(rf.Video2WorldModelRectifiedFlow.denoise,m)
            net.forward=types.MethodType(wc.worldcache_mini_train_dit_forward,net)
            trace={'velocity':[],'solver_returns':[],'checkpoints':[],'condition_before':None,'condition_after':None}
            capture={}
            def get_velocity(b,*args,**kwargs):
                raw=rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch(m,b,*args,**kwargs)
                cells=inspect.getclosurevars(raw).nonlocals
                assert set(cells)=={'self','condition','uncondition','guidance'} and cells['guidance']==7
                capture.update(velocity=raw,conditions=(cells['condition'],cells['uncondition']))
                trace['condition_before']=tree_digest([object_state(c) for c in capture['conditions']])
                def observed(noise,x,t):
                    capture['noise']=noise
                    value=raw(noise,x,t)
                    trace['velocity'].append(tree_digest(value))
                    return value
                return observed
            m.get_velocity_fn_from_batch=get_velocity
            # Deliberate parent wrappers: the local executor must temporarily
            # replace them, then restore the exact objects before continuation.
            raw_denoise=m.denoise;raw_forward=net.forward
            parent_net=[];parent_branch=[]
            def forward(*args,**kwargs):
                from wcomr.prepared_input import input_signatures
                signature=input_signatures(args,kwargs)
                value=raw_forward(*args,**kwargs)
                parent_net.append({'input':signature,'output':tree_digest(value)})
                return value
            def denoise(*args,**kwargs):
                value=raw_denoise(*args,**kwargs);parent_branch.append(tree_digest(value));return value
            net.forward=forward;m.denoise=denoise
            m.generate_samples_from_batch=types.MethodType(fixture.generate_samples_from_batch.__func__,m)
            scheduler=m.sample_scheduler;raw_step=scheduler.step
            def step(*args,**kwargs):
                value=raw_step(*args,**kwargs);capture['generator']=kwargs['generator']
                trace['solver_returns'].append(tree_digest(value))
                if scheduler._step_index==22 and phase=='ON':
                    latent=value[0].squeeze(0)
                    fork=PairedLocalInterface(m,latent,capture['noise'],capture['generator'],capture['velocity'],suffix,
                        context=('H_T57_CPU_'+str(flow),'TOY_ACTUAL_SOURCE','FROZEN_CONDITION'),
                        runtime=runtime,wc_module=wc,rf_module=rf)
                    baseline=(len(parent_net),len(parent_branch),tree_digest(RNGState().signatures()))
                    tensors={}
                    for action in ('CC','DD'):
                        for observers in (False,True):
                            for repetition in ('first','second'):
                                previous=None
                                for order in ('ORIGINAL','PAIRED'):
                                    label='_'.join((action,str(observers),repetition,order))
                                    row=fork.measure(label,action,order,observers);row['repetition']=repetition
                                    actual=fork.last_tensors
                                    if previous is not None:
                                        assert all(torch.equal(previous[k],actual[k]) for k in actual)
                                        row['direct_torch_equal_against_original']=True
                                    previous=actual
                                    if action in tensors:
                                        assert all(torch.equal(tensors[action][k],actual[k]) for k in actual)
                                    else:tensors[action]=actual
                    assert baseline==(len(parent_net),len(parent_branch),tree_digest(RNGState().signatures()))
                    assert m.denoise is denoise and net.forward is forward and scheduler.step is step
                    verdict=verify_comparisons(fork.records)
                    good=copy.deepcopy(fork.records)
                    failures=[]
                    for fault in ('selector','after_first'):
                        try:fork.measure('FAIL_'+fault,'CC','PAIRED',True,fail=fault)
                        except ValueError as error:
                            assert 'Injected local' in str(error)
                        else:raise AssertionError('Expected declared local failure')
                        bad=fork.records[-1]
                        assert bad['executor_poisoned'] and bad['parent_restored'] and bad['bindings_restored']
                        assert bad['parent_after_components']==bad['origin_components']
                        assert baseline==(len(parent_net),len(parent_branch),tree_digest(RNGState().signatures()))
                        failures.append(copy.deepcopy(bad))
                    records.append({'kind':'local_interface_origin','flow':flow,'status':'PASS',
                        'comparisons':good,'verdict':verdict,'declared_failures':failures,
                        'direct_tensor_equality_all_orders_observers_and_repeats':True,
                        'parent_wrappers_not_bypassed_as_observations':True,'binding_objects_restored':True})
                if scheduler._step_index in STATE_STEPS:
                    snapshot=CompleteStateRoundtrip(net,scheduler,value[0],[capture['generator']])
                    trace['checkpoints'].append({'step':scheduler._step_index,'components':snapshot.components()})
                return value
            scheduler.step=step
            versions=[(id(p),p._version) for p in net.parameters()]
            with torch.no_grad():
                latent=m.generate_samples_from_batch(copy.deepcopy(batch),guidance=7,seed=3,
                    state_shape=(2048,2,8,8),n_sample=1,is_negative_prompt=True,num_steps=35,shift=5)
            assert versions==[(id(p),p._version) for p in net.parameters()]
            assert not any(mod.training for mod in net.modules())
            assert len(trace['velocity'])==len(trace['solver_returns'])==36 and len(parent_net)==len(parent_branch)==72
            assert net.cnt==2 and scheduler._step_index==36
            trace['condition_after']=tree_digest([object_state(c) for c in capture['conditions']])
            assert trace['condition_before']==trace['condition_after']
            trace.update(net=parent_net,branches=parent_branch,final_latent_sha256=tree_digest(latent),
                final_components=CompleteStateRoundtrip(net,scheduler,latent,[capture['generator']]).components(),
                RNG=tree_digest(RNGState().signatures()),condition_class_AST_SHA=condition_sha)
            parents.append((trace,latent))
        old,new=parents
        assert torch.equal(old[1],new[1]) and old[0]==new[0]
        records.append({'kind':'local_interface_full_parent_parity','flow':flow,'status':'PASS',
            'both_full36_72_parents_equal':True,'final_latent_direct_torch_equal':True,'trace':new[0],
            'real_model_or_decode_video_claim':False})
        assert tree_digest(batch)==original_data and not torch.cuda.is_initialized()
        return records
    finally:entry.restore()


def run(runtime):
    runtime=Path(runtime)
    old=load('check_cfg_paired_probe_full_sampler_cpu').run(runtime)
    new=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=runtime,**kw))
    assert len(old['checks'])==60 and len(new['checks'])==4
    new['checks']=old['checks']+new['checks']
    new['limits']='Source-pinned real WC/RF/UniPC code, Toy weights/attention/condition construction/noise, CPU to latent only; no real 2B model, decode, writer, video, GPU timing or endpoint/future-cost labels.'
    return new
