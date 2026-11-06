"""New BASE/D46 composition on pinned sampler and Video2World CPU Toy.

Call46 proposals are deliberately C or D only in this fixture; weights,
network, decoder and writer are Toy. Not a new-seed scientific result.
"""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch
from wcomr.h0_mode import establish_shared_eval
from wcomr.rv0_actions import OneActionRouter
from wcomr.rv0_d46_seed_causal import run_d46_seed_batch
from wcomr.rv0_d46_seed_evaluation import verify_seed_row


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def mutations(row):
    refused=[]
    for kind in ['pre46_state','pre46_history','pre46_input','empty_final','final_digest','target_proposal','outside_action','missing_repeat','byte_bridge']:
        bad=copy.deepcopy(row);children={c['label']:c for c in bad['children']}
        if kind=='missing_repeat':bad['children'].pop()
        elif kind=='byte_bridge':bad['decoded_children'][1]['artifact']['sha256']='0'*64
        else:
            for label in ('REFRESH_first','REFRESH_second'):
                c=children[label];report=c['record']['action_report']
                if kind=='pre46_state':c['pre46']['components']['cpu_rng']='0'*64
                elif kind=='pre46_history':c['pre46']['own_history'][1]=[]
                elif kind=='pre46_input':c['inputs'][1]={'corruption':True}
                elif kind=='empty_final':c['record']['final_state_components']={}
                elif kind=='final_digest':c['record']['final_state_sha256']='0'*64
                elif kind=='target_proposal':report['suffix_events'][1]['native_skip']=not report['suffix_events'][1]['native_skip']
                elif kind=='outside_action':report['suffix_events'][3]['requested']='D'
        try:verify_seed_row(bad,2)
        except ValueError:refused.append(kind)
        else:raise AssertionError('Corrupted evidence accepted: '+kind)
    return refused


def exercise(*,inference,samples,wc,settings,inference_module,flow,runtime,**unused):
    samples=samples[-1:];model=inference.pipe.model;net=model.net
    old=(net.prepare_embedded_sequence,model.conditioner.get_condition_with_negative_prompt,net.forward,
         inference_module.save_img_or_video,inference_module.guardrail_presets.run_video_guardrail,OneActionRouter.decide)
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    frozen,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1,3,4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1,2048,2,8,8),0,0,num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    mode=establish_shared_eval(net);settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    config={'sample_names':['human'],'run_id':'CPU_D46_SEED:test','target_calls':[46],
            'maximum_age_solver_steps':32,'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
    contexts=[(config['run_id']+':human','toy_model','condition:human')];attempts=[]
    try:
        cases=['native_C','native_D_noop']+(['child_writer','child_guardrail'] if flow else [])
        for case in cases:
            def decide(router,*args):
                if router.pending['call']==46:
                    adjusted=list(args);adjusted[2]=case!='native_D_noop';args=tuple(adjusted)
                return old[5](router,*args)
            OneActionRouter.decide=decide
            def writer(value,path,fps):
                if case=='child_writer' and 'child_OFF1' in str(path):return
                return old[3](value,path,fps)
            guard_calls=[0]
            def guard(frames,runner):
                guard_calls[0]+=1
                if case=='child_guardrail' and guard_calls[0]==1:return None
                return old[4](frames,runner)
            inference_module.save_img_or_video=writer;inference_module.guardrail_presets.run_video_guardrail=guard
            state={};error=None
            with tempfile.TemporaryDirectory(prefix='d46-seed-core-') as tmp:
                try:
                    run_d46_seed_batch(inference,samples,wc,settings,state=state,save=lambda:None,output=Path(tmp),
                        inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,config=config)
                except Exception as exc:error=str(exc)
                assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs'])==(1,6,4)
                if case.startswith('native_'):
                    assert error is None,error
                    assert state['status']=='D46_SEED_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
                    row=state['requests'][0];verdict=verify_seed_row(row,2)
                    assert verdict['original_D46_noop']==(case=='native_D_noop')
                    refused=mutations(row)
                else:
                    assert error and state['requests'][0]['status']=='TECH_BLOCKED'
                    assert state['requests'][0]['children'][0]['record']['parent_restored']
                    refused=[];verdict=None
                attempts.append({'flow':flow,'case':case,'error':error,'receipt':state,'verdict':verdict,
                    'mutation_refusals':refused,'pinned_video_class_AST_sha256':class_sha,'CPU_MOCK_outputs_not_video':True})
            assert net.forward==old[2] and not hasattr(net,'_wc_rv0_router')
            assert all(float(b)==0 for b in net.buffers())
        return attempts
    finally:
        net.prepare_embedded_sequence=old[0];model.conditioner.get_condition_with_negative_prompt=old[1]
        net.forward=old[2];inference_module.save_img_or_video=old[3]
        inference_module.guardrail_presets.run_video_guardrail=old[4];OneActionRouter.decide=old[5]


def run(runtime):
    result=load('check_full_sampling').run(Path(runtime),exercise=lambda **k:exercise(runtime=Path(runtime),**k))
    assert len(result['checks'])==6 and not torch.cuda.is_initialized()
    result.update(status='D46_FRESH_SEED_AFFECTED_CORE_CPU_PASS_NOT_GPU',GPU_submissions=0,RV_labels=0,
        complete_successful_parents=4,complete_successful_suffixes=24,successful_mock_outputs=16,
        failed_attempts_retained=2,mutation_refusals=36,native_C_and_original_D_noop_covered=True,
        CUDA_initialized=False,fresh_seed_GPU_feasibility='UNTESTED_BY_CPU_TOY')
    return result
