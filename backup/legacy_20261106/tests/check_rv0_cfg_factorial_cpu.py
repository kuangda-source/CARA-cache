"""Exercise all four current-action combinations on pinned sampler/CPU Toy.

Model and video writer are mocks. Tests cover double-action restoration,
changing pre46 state, legal/native suffix and evidence rejection, not quality.
"""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch
from wcomr.h0_mode import establish_shared_eval
from wcomr.rv0_actions import OneActionRouter
from wcomr.rv0_cfg_factorial_actions import FactorialCFGRouter,FactorialCFGPlan
from wcomr.rv0_cfg_factorial_causal import run_cfg_factorial_batch
from wcomr.rv0_cfg_factorial_evaluation import verify_factorial_row


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def mutations(row):
    kinds=['empty_pre45','pre45_digest','pre45_history','current45_input','current46_input',
        'empty_pre46','empty_final','final_digest','missing_current46','future_request',
        'future_not_native','wrong_CFG','illegal_age','missing_probe','wrong_deep_count','reset_missing',
        'missing_repeat','byte_bridge','raw_config_values','numerical_config','metadata_values','missing_cfg0','cfg0_pre46_mismatch']
    refused=[]
    for kind in kinds:
        bad=copy.deepcopy(row);cs={c['label']:c for c in bad['children']}
        if kind=='missing_repeat':bad['children'].pop()
        elif kind=='byte_bridge':bad['decoded_children'][1]['artifact']['sha256']='0'*64
        else:
            for label in ('PAIRED_first','PAIRED_second'):
                c=cs[label];es=c['record']['action_report']['suffix_events']
                if kind=='empty_pre45':c['pre45']['components']={}
                elif kind=='pre45_digest':c['pre45']['fingerprint']='0'*64
                elif kind=='pre45_history':c['pre45']['own_history'][0]=[]
                elif kind=='current45_input':c['inputs'][0]={'corrupted':True}
                elif kind=='current46_input':c['inputs'][1]={'corrupted':True}
                elif kind=='empty_pre46':c['pre46']['components']={}
                elif kind=='empty_final':c['record']['final_state_components']={}
                elif kind=='final_digest':c['record']['final_state_sha256']='0'*64
                elif kind=='missing_current46':es[1]['requested']=None
                elif kind=='future_request':es[3]['requested']='D'
                elif kind=='future_not_native':es[3]['selected_skip']=not es[3]['native_skip']
                elif kind=='wrong_CFG':es[0]['cfg_slot']=1
                elif kind=='illegal_age':es[0]['age_solver_steps']=0
                elif kind=='missing_probe':es[0]['paid_probe']=False
                elif kind=='wrong_deep_count':c['deep'][0]=0
                elif kind=='reset_missing':es[-3]['native_cycle_reset']=False
                elif kind=='raw_config_values':c['pre45']['solver_configuration']['raw_values']['solver_order']=999
                elif kind=='numerical_config':c['pre45']['solver_configuration']['numerical_values']['solver_order']=999
                elif kind=='metadata_values':c['pre45']['solver_configuration']['default_name_metadata']=['invented']
                elif kind=='missing_cfg0':cs['CFG0_first']['record']['action_report']['requested_full_calls']=[]
                elif kind=='cfg0_pre46_mismatch':cs['CFG0_first']['pre46']['fingerprint']='0'*64
        try:verify_factorial_row(bad,2)
        except (ValueError,KeyError):refused.append(kind)
        else:raise AssertionError('Corrupted paired evidence accepted: '+kind)
    return refused


def exercise(*,inference,samples,wc,settings,inference_module,flow,runtime,**unused):
    samples=samples[-1:];model=inference.pipe.model;net=model.net
    old=(net.prepare_embedded_sequence,model.conditioner.get_condition_with_negative_prompt,net.forward,
        inference_module.save_img_or_video,inference_module.guardrail_presets.run_video_guardrail,
        OneActionRouter.decide,FactorialCFGRouter.decide)
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    frozen,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1,3,4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1,2048,2,8,8),0,0,num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    mode=establish_shared_eval(net);settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    config={'sample_names':['human'],'run_id':'CPU_CFG_FACTORIAL:test','target_calls':[46],
        'paired_full_calls':[45,46],'maximum_age_solver_steps':32,'logical_copy_cap_bytes':6*(1<<30),
        'workspace_reserve_bytes':4*(1<<30)}
    contexts=[(config['run_id']+':human','toy_model','condition:human')];attempts=[]
    try:
        cases=['native_CC','native_DD_noop']+(['failure_second_action','failure_cfg0_action','failure_paired_writer','failure_paired_guardrail'] if flow else [])
        for case in cases:
            def parent_decide(router,*args):
                if router.pending['call'] in (45,46):
                    adjusted=list(args);adjusted[2]=case!='native_DD_noop';args=tuple(adjusted)
                return old[5](router,*args)
            def paired_decide(router,*args):
                if (case=='failure_second_action' and type(router.plan) is FactorialCFGPlan
                        and router.plan.mode=='PAIRED' and router.pending['call']==46):
                    router.history[1]=[]
                if (case=='failure_cfg0_action' and type(router.plan) is FactorialCFGPlan
                        and router.plan.mode=='CFG0' and router.pending['call']==45):
                    router.history[0]=[]
                return old[6](router,*args)
            OneActionRouter.decide=parent_decide;FactorialCFGRouter.decide=paired_decide
            def writer(value,path,fps):
                if case=='failure_paired_writer' and 'child_PAIRED_first' in str(path):return
                return old[3](value,path,fps)
            guard_calls=[0]
            def guard(frames,runner):
                guard_calls[0]+=1
                if case=='failure_paired_guardrail' and guard_calls[0]==4:return None
                return old[4](frames,runner)
            inference_module.save_img_or_video=writer;inference_module.guardrail_presets.run_video_guardrail=guard
            state={};error=None
            with tempfile.TemporaryDirectory(prefix='paired-cfg-core-') as tmp:
                try:
                    run_cfg_factorial_batch(inference,samples,wc,settings,state=state,save=lambda:None,output=Path(tmp),
                        inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,config=config)
                except Exception as exc:error=str(exc)
                assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs'])==(1,10,6)
                if case.startswith('native_'):
                    assert error is None,error
                    assert state['status']=='CFG_FACTORIAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
                    row=state['requests'][0];verdict=verify_factorial_row(row,2);cs={c['label']:c for c in row['children']}
                    assert cs['PAIRED_first']['record']['action_report']['decision_interventions']==2
                    assert cs['CFG1_first']['record']['action_report']['decision_interventions']==1
                    assert cs['CFG0_first']['record']['action_report']['decision_interventions']==1
                    if case=='native_CC':
                        assert cs['PAIRED_first']['deep'][:2]==[2,2] and cs['CFG1_first']['deep'][:2]==[0,2]
                        assert cs['PAIRED_first']['pre46']!=cs['CFG1_first']['pre46']
                        assert cs['CFG0_first']['deep'][:2]==[2,0]
                        assert cs['CFG0_first']['pre46']==cs['PAIRED_first']['pre46']
                    else:
                        assert all(cs['PAIRED_first'][k]==cs['BASE_first'][k] for k in ('inputs','outputs','deep','banks','solver_outputs','final_latent_sha256'))
                    refused=mutations(row)
                    bridge=None
                else:
                    assert error and state['requests'][0]['status']=='TECH_BLOCKED'
                    label='CFG0_first' if case=='failure_cfg0_action' else 'PAIRED_second' if case=='failure_second_action' else 'PAIRED_first'
                    paired=next(c for c in state['requests'][0]['children'] if c['label']==label)
                    assert paired['record']['parent_restored']
                    refused=[];verdict=None;bridge=None
                attempts.append({'flow':flow,'case':case,'error':error,'receipt':state,'verdict':verdict,
                    'historical_bridge_CPU_mock':bridge,'mutation_refusals':refused,
                    'pinned_video_class_AST_sha256':class_sha,'CPU_MOCK_outputs_not_video':True})
            assert net.forward==old[2] and not hasattr(net,'_wc_rv0_router')
            assert all(float(b)==0 for b in net.buffers())
        return attempts
    finally:
        net.prepare_embedded_sequence=old[0];model.conditioner.get_condition_with_negative_prompt=old[1]
        net.forward=old[2];inference_module.save_img_or_video=old[3]
        inference_module.guardrail_presets.run_video_guardrail=old[4]
        OneActionRouter.decide=old[5];FactorialCFGRouter.decide=old[6]


def run(runtime):
    result=load('check_full_sampling').run(Path(runtime),exercise=lambda **k:exercise(runtime=Path(runtime),**k))
    assert len(result['checks'])==8 and not torch.cuda.is_initialized()
    result.update(status='CFG_FACTORIAL_AFFECTED_CORE_CPU_PASS_NOT_GPU',GPU_submissions=0,RV_labels=0,
        complete_successful_parents=4,complete_successful_suffixes=40,successful_mock_outputs=24,
        failed_attempts_retained=4,mutation_refusals=92,paired_two_actions_and_original_DD_noop_covered=True,
        changed_pre46_after_first_action_is_valid=True,CUDA_initialized=False,
        CFG_factorial_real_GPU_feasibility='UNTESTED_BY_CPU_TOY')
    return result
