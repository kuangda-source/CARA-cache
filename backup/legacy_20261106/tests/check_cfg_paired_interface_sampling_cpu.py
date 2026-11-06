"""Actual new guarded interface batch with declared Toy CPU boundaries."""
import copy
from contextlib import nullcontext
import hashlib
from pathlib import Path
import tempfile
import types

import torch

from wcomr.cfg_paired_interface_sampling import run_interface_batch,verify_batch
from wcomr.cfg_teacher_sampling import vector_artifact
from wcomr.h0_mode import establish_shared_eval
from wcomr.mid_coverage import tree_digest


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


def exercise(*,inference,samples,settings,inference_module,flow,runtime,tensor_loader,artifact_root=None,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    samples=samples[-1:];model=inference.pipe.model;net=model.net
    saved=(net.prepare_embedded_sequence,model.conditioner.get_condition_with_negative_prompt,
        model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition)
    config_before=copy.deepcopy(vars(model.config))
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    cls,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    def conditions(b):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+slot),fps=b['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,2048,2,8,8),0,0,
                num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,2048,2,8,8),None)
    for name in ('denoise','get_velocity_fn_from_batch'):
        setattr(model,name,types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep=-1;model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0
    model.config.conditional_frames_probs=None
    mode=establish_shared_eval(net)
    settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    config={'sample_names':['human'],'run_id':'H_T58_CPU_BATCH','logical_copy_cap_bytes':6*(1<<30),
        'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'expected_components':50,'expected_shape':[1,2048,2,8,8]}
    contexts=[(config['run_id']+':human','Toy_actual_modules','actual_frozen_condition')]
    checks=[]
    try:
        for scenario in ('complete','writer_failure'):
            if artifact_root is None:storage=tempfile.TemporaryDirectory(prefix='paired-interface-sampling-')
            else:
                target=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario;target.mkdir(parents=True,exist_ok=False)
                storage=nullcontext(str(target))
            state={};error=None
            with storage as tmp:
                def writer(path,tensors):
                    if scenario=='writer_failure' and path.name=='DD_OBS_ON_second_PAIRED.pt':
                        raise ValueError('Injected final local vector writer failure')
                    return vector_artifact(path,tensors)
                try:
                    run_interface_batch(inference,samples,wc,settings,state=state,save=lambda:None,output=Path(tmp),
                        inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,
                        config=config,rf_module=rf,writer=writer)
                except BaseException as exc:error=str(exc)
                assert (state['planned_parents'],state['planned_videos'],state['planned_local_pairs'])==(2,2,16)
                if scenario=='complete':
                    assert error is None,error
                    verdict=verify_batch(state);assert verdict['complete_comparisons']==8
                    rows=state['parents'][1]['origin']['pairs'];raw={}
                    for row in rows:
                        art=row['artifact'];p=Path(art['path']).resolve()
                        assert p.is_relative_to(Path(tmp).resolve()) and hashlib.sha256(p.read_bytes()).hexdigest()==art['sha256']
                        value=tensor_loader(p,weights_only=True,map_location='cpu')
                        assert set(value)=={'conditional','unconditional','guided'}
                        assert all(v.dtype==torch.float32 and list(v.shape)==config['expected_shape'] for v in value.values())
                        assert all(tree_digest(value[k])==art['tensor_sha256'][k] for k in value)
                        assert torch.equal(value['conditional']+7*(value['conditional']-value['unconditional']),value['guided'])
                        if row['action'] in raw:assert all(torch.equal(raw[row['action']][k],value[k]) for k in value)
                        else:raw[row['action']]=value
                    assert len(list(Path(tmp).rglob('*.pt')))==16
                    refused=[]
                    for fault in ('missing_pair','wrong_observer','wrong_order','wrong_repeat','wrong_output',
                                  'wrong_state','wrong_artifact','wrong_parent','missing_net','wrong_origin'):
                        bad=copy.deepcopy(state);origin=bad['parents'][1]['origin'];pair=origin['pairs'][1]
                        if fault=='missing_pair':origin['pairs'].pop()
                        elif fault=='wrong_observer':pair['observers']=True
                        elif fault=='wrong_order':pair['order']='ORIGINAL'
                        elif fault=='wrong_repeat':pair['repetition']='first_invalid'
                        elif fault=='wrong_output':pair['guided_sha256']='0'*64
                        elif fault=='wrong_state':pair['pair_end_components']['output']='0'*64
                        elif fault=='wrong_artifact':pair['artifact']['tensor_sha256']['guided']='0'*64
                        elif fault=='wrong_parent':bad['parents'][1]['final_latent_sha256']='0'*64
                        elif fault=='missing_net':bad['parents'][1]['inputs'].pop()
                        elif fault=='wrong_origin':origin['status']='PENDING'
                        try:verify_batch(bad)
                        except ValueError:refused.append(fault)
                        else:raise AssertionError('Incomplete/mutated interface accepted: '+fault)
                    checks.append({'kind':'actual_interface_batch','flow':flow,'scenario':scenario,'status':'PASS',
                        'receipt':state,'raw_tensors_reloaded':48,'guided_and_cross_order_observer_repeats_direct_equal':True,
                        'semantic_evidence_mutations_refused':refused,'condition_class_AST_SHA':class_sha})
                else:
                    assert error and 'Injected final local vector writer failure' in error,error
                    assert state['parents'][-1]['status']=='INTERFACE_PARENT_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
                    assert state['parents'][-1]['origin']['status']=='INTERFACE_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
                    rows=state['parents'][-1]['origin']['pairs']
                    assert len(rows)==16 and all(r['parent_restored'] and r['bindings_restored'] for r in rows)
                    assert 'artifact' not in rows[-1] and len(list(Path(tmp).rglob('*.pt')))==15
                    checks.append({'kind':'actual_interface_batch','flow':flow,'scenario':scenario,'status':'EXPECTED_FAILURE',
                        'error':error,'receipt':state,'complete_scope_retained':True,'initial_full_state_restored':True})
                assert all(float(v)==0 for v in net.buffers()) and not any(m.training for m in net.modules())
        return checks
    finally:
        net.prepare_embedded_sequence=saved[0];model.conditioner.get_condition_with_negative_prompt=saved[1]
        model.get_velocity_fn_from_batch=saved[2];model.denoise=saved[3];model.get_data_and_condition=saved[4]
        vars(model.config).clear();vars(model.config).update(config_before)


def run(runtime,tensor_loader,artifact_root):
    runtime=Path(runtime)
    old=load('check_cfg_paired_local_interface_cpu').run(runtime)
    new=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(
        runtime=runtime,tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(old['checks'])==64 and len(new['checks'])==4
    new['checks']=old['checks']+new['checks']
    new['limits']='Actual new two guarded parent interface batch and source-pinned WC/RF/UniPC; Toy CPU weights, attention, preparation, decode/writer. Generated Toy raw tensor reloads only, no model weights, GPU, real videos or endpoint labels.'
    return new
