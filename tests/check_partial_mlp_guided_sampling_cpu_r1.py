"""Actual full UniPC/guarded pipeline with a four-scene collection batch.

Toy CPU weights/attention/prepare/decode/writer remain explicit stand-ins. The
new batch, pinned WC/RF/condition class, full sampler and complete vector reload
are executed. Neither its fitting values nor mock files are real CAL/video.
"""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.partial_mlp_guided_sampling import run_batch, verify_batch, audit_vectors, METHODS, A_METHODS, COMPILER_PROOF
from wcomr.partial_mlp_deployment_sampling import P_STEPS, LAYERS
from wcomr.cfg_mf00_interface_sampling import vector_file
from wcomr.h0_mode import establish_shared_eval


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


def pinned_blocks(runtime):
    import ast,hashlib,math
    from typing import Optional
    from dataclasses import dataclass
    from einops import rearrange
    path=Path(runtime)/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'
    classes=[v for v in ast.parse(raw).body if isinstance(v,ast.ClassDef) and v.name in ('Block','GPT2FeedForward')]
    assert len(classes)==2
    class TinyAttention(torch.nn.Module):
        def __init__(self,*args,**kwargs):super().__init__()
        def forward(self,x,context=None,**kwargs):return .07*x+(0 if context is None else .002*context.mean())
        def init_weights(self):pass
    @dataclass
    class VideoSize:
        T:int
        H:int
        W:int
    namespace={'torch':torch,'nn':torch.nn,'math':math,'Optional':Optional,'amp':torch.amp,
               'rearrange':rearrange,'Attention':TinyAttention,'I2VCrossAttention':TinyAttention,'VideoSize':VideoSize}
    exec(compile(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])),str(path)+'#P0_full_CPU_Block','exec'),namespace)
    return torch.nn.ModuleList([namespace['Block'](8,8,2,mlp_ratio=4,use_adaln_lora=False,
                     backend='declared_CPU_attention') for _ in range(28)]).eval()


def exercise(*,inference,samples,settings,inference_module,flow,runtime,tensor_loader,artifact_root,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    model=inference.pipe.model;net=model.net
    saved=(net.prepare_embedded_sequence,model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition)
    old_net=(net.blocks,net.t_embedder,net.unpatchify)
    old_head=net.final_layer
    old_topology=(len(list(net.named_modules())),len(list(net.named_buffers())))
    net.blocks=pinned_blocks(runtime)
    class DeclaredIdentityHead(torch.nn.Module):
        def forward(self,x,*args,**kw):return x
    net.final_layer=DeclaredIdentityHead().eval()
    net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),None)
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous().repeat(1,256,1,1,1)
    new_topology=(len(list(net.named_modules())),len(list(net.named_buffers())))
    expected_components=50+sum(new_topology)-sum(old_topology)
    conditioner=model.conditioner.get_condition_with_negative_prompt;cfg=copy.deepcopy(vars(model.config))
    cls,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    # Declared Toy prepare/unpatchify:512 hidden tokens permit real .5/.75
    # gathered paths with the production128-token block size; output stays at
    # the existing full-sampler CPU fixture's2048x2x8x8 geometry.
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:8].movedim(1,-1).contiguous()
        .repeat_interleave(2,2).repeat_interleave(2,3),None,None)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
            .set_video_condition(torch.zeros(1,2048,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,2048,2,8,8),None)
    # The historical pipe fixture omits this batch key. The actual RF factory
    # then defaults to one conditional frame, even when the sample says T2V.
    # Explicitly bind the zero-frame request used by this collection control.
    original_prepare=inference.pipe._get_data_batch_input
    def prepare_zero_frame_request(*args,**kwargs):
        batch=original_prepare(*args,**kwargs)
        assert 'num_conditional_frames' not in batch
        return {**batch,'num_conditional_frames':0}
    inference.pipe._get_data_batch_input=prepare_zero_frame_request
    for name in ('denoise','get_velocity_fn_from_batch'):
        setattr(model,name,types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep=-1;model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0;model.config.conditional_frames_probs=None
    mode=establish_shared_eval(net); settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    names=['AV28_CPU','Human_CPU','misc_CPU','AV51_CPU']; selected=[type(samples[0])(n) for n in names]
    config={'sample_names':names,'run_id':'A_P0_FULL_SAMPLER_CPU','logical_copy_cap_bytes':6*(1<<30),
        'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'expected_components':expected_components,'expected_shape':[1,2048,2,8,8],
        'CPU_mutate_owned_state_before_restore':True}
    contexts=[(config['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
    original_forward_attributes=[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
    results=[]
    try:
        for scenario in ('complete','last_parent_writer_failure'):
            output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario;output.mkdir(parents=True,exist_ok=False)
            state={};error=None
            def save():
                p=output/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(p)
            def writer(path,values):
                if scenario=='last_parent_writer_failure' and path.name=='AV51_CPU_A_P0_BETA1_ONE_PHASE.pt':
                    raise ValueError('Injected final full-parent vector writer failure')
                return vector_file(path,values)
            try:
                run_batch(inference,selected,wc,settings,state=state,save=save,output=output,inference_module=inference_module,
                    contexts=contexts,mode_setup=mode,runtime=runtime,config=config,rf_module=rf,writer=writer)
            except BaseException as exc:error=str(exc)
            assert state['planned_parent_paths']==72 and state['planned_origins']==0 and len(state['requests'])==4,(error,state.get('requests'))
            assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
            assert not any(m.training for m in net.modules())
            assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
            if scenario=='complete':
                assert error is None,error
                verdict=verify_batch(state);raw=audit_vectors(state,output,tensor_loader,config['expected_shape'])
                assert raw['actual_guided_reloaded']==2592 and raw['actual_latents_reloaded']==72
                assert raw['independent_partial_full_trajectory_comparisons']==16 and len(raw['files'])==72
                P_reuses=consecutive_P=projection_rows=0
                for r in state['requests']:
                    for row in r['paths']:
                        assert row['condition_fields_before']==row['condition_fields_after']
                        assert all(m['finite'] and m['nonzero_elements']==0 for m in row['actual_condition_masks'])
                        assert row['actual_raw_solver_configuration']['raw_values']
                        assert all(c['checkpoint_perturbation_executed'] for c in row['P0_roundtrips'])
                        method=row['collect'];d=row['collection_complete']['deployment']
                        linear=row['collection_complete']['Linear_inputs']
                        assert all(v['layer'] in LAYERS and v['slot'] in (0,1) for v in linear)
                        for step in range(1,37):
                            entries=[v for v in linear if v['step']==step]
                            action=row['actions'][step-1]
                            if action=='CC':assert not entries
                            else:
                                active=512 if action=='DD' or method=='FULL_P_DECLARED_P' else 256 if method.endswith('050') or method in A_METHODS else 384
                                assert len(entries)==16 and all(v['rows']==active for v in entries)
                                projection_rows+=len(entries)
                        if not d:continue
                        for h in d['history']:
                            if h['action']=='CC' and all(v['kind']=='P' for v in h['working_sources']):
                                P_reuses+=1;assert h['true_D_before']==h['true_D_after']
                                assert h['working_source_ages']==[h['step']-v['created_step'] for v in h['working_sources']]
                            if h['action']=='PP' and h['step']-1 in P_STEPS:consecutive_P+=1
                            if h['action']=='PP':
                                assert all(v['last_actual_D']<h['step'] and not v['is_WorldCache_D_anchor_or_RA_zero_risk_source'] for v in h['actual_projection_records'])
                        assert d['history'][34]['native_cycle_reset'] and d['history'][35]['true_D_after']==[[36],[36]]
                assert P_reuses==360 and consecutive_P==200,(P_reuses,consecutive_P)
                refused=[]
                for fault in ('missing_scene','missing_method','wrong_complete_route','modified_condition_field','P_as_true_D','P_as_zero_risk','missing_roundtrip','A_history_missing','A_P_as_D','A_head_cost_missing','A_wrong_strength'):
                    bad=copy.deepcopy(state);row=bad['requests'][-1]['paths'][4 if not fault.startswith('A_') else 14]
                    if fault=='missing_scene':bad['requests'].pop()
                    elif fault=='missing_method':bad['requests'][-1]['paths'].pop()
                    elif fault=='wrong_complete_route':row['actions'][8]='DD'
                    elif fault=='modified_condition_field':row['condition_fields_before'][0]['fps']='0'*64
                    elif fault=='missing_roundtrip':row['P0_roundtrips'].pop()
                    elif fault=='A_history_missing':row['collection_complete']['deployment']['A_readout']['history'].pop()
                    elif fault=='A_P_as_D':row['collection_complete']['deployment']['A_readout']['history'][8]['branch_status']=['ACTUAL_D']*2
                    elif fault=='A_head_cost_missing':row['collection_complete']['actual_original_plus_candidate_heads'].pop()
                    elif fault=='A_wrong_strength':row['collection_complete']['deployment']['A_readout']['history'][8]['shared_alpha']=0
                    else:
                        h=row['collection_complete']['deployment']['history'][8]
                        if fault=='P_as_true_D':h['true_D_after']=[[9],[9]]
                        else:h['working_sources'][0]['RA_zero_risk_reset_allowed']=True
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Incomplete/contaminated batch accepted: '+fault)
                p=Path(raw['files'][-1]['path']);saved_bytes=p.read_bytes()
                try:
                    p.write_bytes(saved_bytes[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'changed or truncated' in str(exc)
                    else:raise AssertionError('Truncated actual vector accepted')
                finally:p.write_bytes(saved_bytes)
                results.append({'flow':flow,'scenario':scenario,'status':'PASS','verdict':verdict,
                    'actual_tensor_audit':raw,'receipt':state,'mutation_refusals':refused,
                    'actual_artifact_truncation_refused':True,'condition_class_AST_SHA':class_sha,
                    'P_source_reuse_C_checks':P_reuses,'consecutive_P_checks':consecutive_P,
                    'actual_Linear_inputs_checked':projection_rows,'compiler_proof':COMPILER_PROOF})
            else:
                assert error=='Injected final full-parent vector writer failure',error
                row=state['requests'][-1]['paths'][-1]
                assert row['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED' and len(row['guided_sha256'])==36
                assert row['collection_complete']['complete_pairs']==36 and 'vector_artifact' not in row
                assert len(list(output.rglob('*.pt')))==71 and len(list(output.rglob('*.mp4')))==72
                results.append({'flow':flow,'scenario':scenario,'status':'EXPECTED_FAILURE','error':error,
                    'complete_scope_retained':True,'receipt':state,'initial_full_state_restored':True,
                    'installed_MLP_methods_restored':True})
        return results
    finally:
        inference.pipe._get_data_batch_input=original_prepare
        net.blocks,net.t_embedder,net.unpatchify=old_net
        del net.final_layer
        net.final_layer=old_head
        net.prepare_embedded_sequence=saved[0]
        model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition=saved[1:]
        model.conditioner.get_condition_with_negative_prompt=conditioner
        vars(model.config).clear();vars(model.config).update(cfg)


def run(runtime,tensor_loader,artifact_root):
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(result['checks'])==4
    result['limits']='Full ordinary pinned UniPC/guarded pipeline plus deployed A and P0, D-only anchors/provenance and own-state perturbation/restoration. Four Toy requests,13 P0 controls and5 A modes, both flows and complete final-writer-failure repetitions. Declared Toy CPU weights/attention/prepare/decode/writer; no Cosmos/video quality or clean latency.'
    return result
