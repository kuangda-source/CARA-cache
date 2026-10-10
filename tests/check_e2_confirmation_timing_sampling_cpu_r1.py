"""Full frozen E2 matrix with actual pinned sampler and explicit Toy boundaries."""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_ra_baseline import threshold_from_collection
from wcomr.cfg_guided_w1_deployment_sampling import run_comparison as run_batch, verify_comparison as verify_batch, audit_comparison_vectors as audit_vectors, vector_file
from wcomr.cfg_ra_calibration_table import load_table
from wcomr.h0_mode import establish_shared_eval


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercise(*,inference,samples,settings,inference_module,flow,runtime,tensor_loader,
             artifact_root,calibration_cpu_result,inputs,old_A_CPU_result,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    prior=[r for r in calibration_cpu_result['checks'] if r['status']=='PASS' and r['flow']==flow]
    assert len(prior)==1
    prior=prior[0]
    calibration=load_table(prior['actual_tensor_audit']['table'],permit_toy=True)
    initialized=threshold_from_collection(prior['receipt'],calibration)
    assert len(initialized['observed_intervals'])==8 and initialized['threshold']>0
    assert not initialized['endpoint_quality_used_to_choose_threshold']
    model,net=inference.pipe.model,inference.pipe.model.net
    original_head=net.final_layer
    # The shared historical fixture uses an identity function. A preserves
    # actual head buffers, so expose the same numerical function through the
    # nn.Module interface used by the real head; this adds one mode component.
    class ToyIdentityHead(torch.nn.Module):
        def forward(self,*args,**kwargs):
            return original_head(*args,**kwargs)
    net.final_layer=ToyIdentityHead()
    saved=(net.prepare_embedded_sequence,model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition)
    original_conditioner=model.conditioner.get_condition_with_negative_prompt
    config_before=copy.deepcopy(vars(model.config))
    sample_class=type(samples[0])
    previous_dump=vars(sample_class).get('model_dump')
    sample_class.model_dump=lambda self,**kwargs:json.loads(self.model_dump_json())
    previous_decoder=model.tokenizer.decode
    # The Native request contract checks the real output dimensions. This is
    # still an explicit Toy decoder, now producing actual full-size tensors.
    model.tokenizer.decode=lambda latent:previous_decoder(latent).mean(dim=(-2,-1),keepdim=True).expand(1,3,93,432,768)
    cls,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+slot),fps=batch['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,2048,2,8,8),0,0,
                num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,2048,2,8,8),None)
    for name in ('denoise','get_velocity_fn_from_batch'):
        setattr(model,name,types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep=-1
    model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0
    model.config.conditional_frames_probs=None
    # Explicit stand-in Native class body for the CPU composition test only.
    # It always executes all pinned WC deep blocks; the real Native class origin
    # and unchanged forward source must be checked separately before GPU use.
    original_class_forward=type(net).forward
    def dense_toy_native(self,*args,**kwargs):
        threshold=self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*args,**kwargs)
        finally:self.worldcache_rel_l1_thresh=threshold
    dense_toy_native.__module__='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit'
    dense_toy_native.__qualname__='MinimalV1LVGDiT.forward'
    type(net).forward=dense_toy_native
    private_scheduler=copy.deepcopy(model.sample_scheduler)
    private_scheduler.set_timesteps(35,use_kerras_sigma=model.config.use_kerras_sigma_at_inference,device='cpu')
    policy={'scheduler_class':type(private_scheduler).__name__,'requested_steps':35,
        'actual_steps':36,'cfg_calls':72,'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,
        'timesteps':private_scheduler.timesteps.tolist()}
    modes=establish_shared_eval(net)
    settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    import hashlib
    import wcomr.e2_confirmation_timing_sampling_r1 as e2
    names=[r['name'] for r in inputs['requests']]+[inputs['timing_slots'][0]['CAL_name'],inputs['timing_slots'][-1]['CAL_name']]
    selected={name:sample_class(name) for name in names}
    for name,sample in selected.items():
        sample.seed=next((r['seed'] for r in inputs['requests'] if r['name']==name),0)
    config={'run_id':'E2_CPU','model_context':'Toy_actual_modules',
            'expected_shape':[1,2048,2,8,8]}
    checks=[]
    base=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')
    def record(check):
        checks.append(check)
        temporary=base/'partial_checks.tmp'
        temporary.write_text(json.dumps(checks,indent=2,allow_nan=False)+'\n')
        temporary.replace(base/'partial_checks.json')
    original_generate=inference.generate
    original_digest=e2.tree_digest
    active={};hash_calls={}
    def measured_generate(*a,**k):
        inside=True
        rows=active.get('state',{}).get('slots',[])
        row=next((r for r in reversed(rows) if r['status']=='STARTED'),active.get('row'))
        active['inside']=row
        try:return original_generate(*a,**k)
        finally:active.pop('inside',None)
    def counted_digest(value):
        row=active.get('inside')
        if row is not None:
            key=row['id'];hash_calls[key]=hash_calls.get(key,0)+1
            if row['mode']=='TIMING':raise AssertionError('Pure E2 outer content hash executed inside TIMING')
        return original_digest(value)
    inference.generate=measured_generate;e2.tree_digest=counted_digest
    try:
        for scenario in ('complete','parity_last_writer_failure'):
            output=base/scenario;output.mkdir(parents=True,exist_ok=False)
            state={};active['state']=state;error=None
            def save():
                temp=output/'receipt.tmp';temp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');temp.replace(output/'receipt.json')
            def writer(path,tensors):
                if scenario=='parity_last_writer_failure' and path.name=='parity_BETA1_ONE_PHASE.pt':
                    raise ValueError('Injected E2 last parity vector writer failure')
                return vector_file(path,tensors)
            try:
                e2.run_matrix(inference,selected,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,mode_setup=modes,runtime=runtime,config=config,
                    rf_module=rf,calibration=calibration,threshold=initialized['threshold'],
                    sampling_policy=policy,inputs=inputs,writer=writer)
            except BaseException as exc:error=str(exc)
            assert len(state['slots'])==76 and state['planned_scientific_paths']==72
            assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
            if scenario!='complete':
                assert error and 'Injected E2 last parity vector writer failure' in error,error
                assert [r['status'] for r in state['slots'][:4]]==['COMPLETE_PATH']*3+['TECH_BLOCKED']
                assert all(r['status']=='NOT_STARTED' for r in state['slots'][4:])
                try:e2.verify_matrix(state,inputs)
                except ValueError:pass
                else:raise AssertionError('Incomplete E2 accepted')
                record({'flow':flow,'scenario':scenario,'status':'EXPECTED_FAILURE',
                    'receipt':state,'all76_slots_retained':True,'initial_full_state_restored':True})
                continue
            assert error is None,error
            verdict=e2.verify_matrix(state,inputs)
            raw=e2.audit_vectors(state,inputs,output,tensor_loader,config['expected_shape'])
            assert verdict['accepted']==76 and verdict['rejected']==0
            assert raw['actual_guided_reloaded']==1584 and raw['actual_final_latents_reloaded']==76
            assert all(hash_calls.get(r['id'],0)==0 for r in state['slots'] if r['mode']=='TIMING')
            assert all(hash_calls.get(r['id'],0)>0 for r in state['slots'] if r['mode']=='AUDIT')
            old_good=next(c for c in old_A_CPU_result['checks'] if c['flow']==flow and c['status']=='PASS')
            old_rows=old_good['receipt']['batch']['requests'][0]['paths']
            matches=[]
            for row in state['slots'][:4]:
                previous=next(r for r in old_rows if r['method']==row['method'])
                old_art=previous['vector_artifact'];p=Path(old_art['path'])
                assert p.stat().st_size==old_art['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==old_art['sha256']
                before=tensor_loader(p,weights_only=True,map_location='cpu')
                after=tensor_loader(Path(row['vector_artifact']['path']),weights_only=True,map_location='cpu')
                assert row['actions']==previous['actions']
                assert all(torch.equal(a,b) for a,b in zip(before['guided'],after['guided']))
                assert torch.equal(before['final_latent'],after['final_latent'])
                matches.append({'method':row['method'],'actual_all36_guided_and_final_equal':True,
                    'old_vector_sha256':old_art['sha256'],'old_source_readonly':True})
            refused=[]
            for fault in ('drop_scientific_slot','alter_order','alter_actions','wrong_A_alpha','future_D_anchor',
                          'unpaid_head','wrong_full_calls','claimed_clean_acceptance','wrong_parity','missing_prepared'):
                bad=copy.deepcopy(state)
                row=next(r for r in bad['slots'] if r['method']=='BETA1_ONE_PHASE')
                if fault=='drop_scientific_slot':bad['slots'].pop()
                elif fault=='alter_order':bad['slots'][10],bad['slots'][11]=bad['slots'][11],bad['slots'][10]
                elif fault=='alter_actions':row['actions'][10]='DD' if row['actions'][10]=='CC' else 'CC'
                elif fault=='wrong_A_alpha':row['A_readout']['history'][24]['shared_alpha']=1
                elif fault=='future_D_anchor':row['A_readout']['history'][10]['past_D_steps'][0]=[11]
                elif fault=='unpaid_head':next(h for h in row['A_readout']['history'] if h['action']=='CC')['extra_heads']=0
                elif fault=='wrong_full_calls':row['block_counts']['full_calls']+=1
                elif fault=='claimed_clean_acceptance':bad['clean_latency_accepted']=True
                elif fault=='wrong_parity':next(r for r in bad['slots'] if r['section']=='TIMING')['actual_audit_timing_endpoint_and_action_parity']=False
                elif fault=='missing_prepared':row['prepared_input_calls']=[]
                try:e2.verify_matrix(bad,inputs)
                except ValueError:refused.append(fault)
                else:raise AssertionError('Malformed E2 accepted: '+fault)
            trunc=Path(state['slots'][-1]['vector_artifact']['path']);original=trunc.read_bytes()
            try:
                trunc.write_bytes(original[:-1])
                try:e2.audit_vectors(state,inputs,output,tensor_loader,config['expected_shape'])
                except ValueError as exc:assert 'Actual E2 vector bytes changed' in str(exc)
                else:raise AssertionError('Truncated E2 final timing artifact accepted')
            finally:trunc.write_bytes(original)
            record({'flow':flow,'scenario':scenario,'status':'PASS','receipt':state,
                'verdict':verdict,'actual_tensor_audit':raw,'unchanged_old_A_sampler_parity':matches,
                'semantic_mutation_refusals':refused,'final_timing_truncation_refused':True,
                'outer_hash_calls_inside_generate':dict(hash_calls),'condition_class_AST_SHA':class_sha})
        # Expected guardrail refusals keep their original path and do not need
        # an artificial substitution. Standalone controls exercise fresh hooks.
        from wcomr.full_sampling import CompleteStateRoundtrip
        reset=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
        standalone_forward=net.forward
        original_text=inference_module.guardrail_presets.run_text_guardrail
        original_video=inference_module.guardrail_presets.run_video_guardrail
        try:
            active.pop('state',None)
            for kind,method in (('TEXT_REJECTED','W1_ONE_PHASE'),('VIDEO_REJECTED','BETA1_ONE_PHASE'),
                                ('TEXT_REJECTED','NATIVE'),('VIDEO_REJECTED','NATIVE')):
                reset.restore();out=base/(kind+'_'+method)
                row={'id':kind+'_'+method,'method':method,'status':'NOT_STARTED'};active['row']=row
                if kind=='TEXT_REJECTED':inference_module.guardrail_presets.run_text_guardrail=lambda *a:False
                else:inference_module.guardrail_presets.run_video_guardrail=lambda *a:None
                e2.execute_path(inference,selected[names[-2]],wc,settings,row=row,save=lambda:None,output=out,
                    inference_module=inference_module,context=('E2_CPU:'+names[-2],'Toy_actual_modules','Toy_condition'),
                    mode_setup=modes,runtime=runtime,config=config,rf_module=rf,calibration=calibration,
                    threshold=initialized['threshold'],sampling_policy=policy,mode='AUDIT' if method=='NATIVE' else 'TIMING')
                assert row['status']==kind and row['video_artifact'] is None
                assert row['solver_steps']==(0 if kind=='TEXT_REJECTED' else 36)
                assert inference.setup_args.keep_going is False
                if method!='NATIVE':assert hash_calls.get(row['id'],0)==0
                record({'flow':flow,'scenario':kind,'status':'EXPECTED_REJECTION','receipt':row})
                inference_module.guardrail_presets.run_text_guardrail=original_text
                inference_module.guardrail_presets.run_video_guardrail=original_video
        finally:
            reset.restore()
            net.forward=standalone_forward
            inference_module.guardrail_presets.run_text_guardrail=original_text
            inference_module.guardrail_presets.run_video_guardrail=original_video
        return checks
    finally:
        inference.generate=original_generate;e2.tree_digest=original_digest
        del net.final_layer
        net.final_layer=original_head
        type(net).forward=original_class_forward
        model.tokenizer.decode=previous_decoder
        if previous_dump is None:
            delattr(sample_class,'model_dump')
        else:
            sample_class.model_dump=previous_dump
        net.prepare_embedded_sequence=saved[0]
        model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition=saved[1:]
        model.conditioner.get_condition_with_negative_prompt=original_conditioner
        vars(model.config).clear()
        vars(model.config).update(config_before)


def run(runtime,tensor_loader,artifact_root,calibration_cpu_result,inputs,old_A_CPU_result):
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,
        calibration_cpu_result=calibration_cpu_result,inputs=inputs,old_A_CPU_result=old_A_CPU_result,**kw))
    assert len(result['checks'])==12
    result['limits']='Actual pinned WC/RF/UniPC full76 matrix, unchanged old-A saved Toy outputs, flow OFF/ON and failure/refusal controls. Explicit Toy weights/attention/native class/16x16 prepare/93x432x768 decode/JSON writer/calibration; no real-model equivalence, real videos, quality or latency claim.'
    return result
