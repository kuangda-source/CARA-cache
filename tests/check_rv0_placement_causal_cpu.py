"""Production placement composition on pinned sampler/WC/Video2World CPU Toy.

Pairs selected from an uninstrumented Toy trajectory are explicit fixtures;
they do not stand in for the four frozen real CAL pairs or GPU feasibility.
"""
import copy
from dataclasses import replace
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.h0_mode import establish_shared_eval
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import WC_FIELDS
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import WC_CONFIGURATION
from wcomr.rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from wcomr.rv0_placement_causal import run_placement_causal_batch
from wcomr.rv0_placement_evaluation import audit_trajectories, verify_placement_row
from wcomr.rv0_fixed_mask import FixedMaskRouter


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def exercise(*, inference, samples, wc, settings, inference_module, flow, runtime, **unused):
    model, net = inference.pipe.model, inference.pipe.model.net
    original_prepare = net.prepare_embedded_sequence
    original_batch = inference.pipe._get_data_batch_input
    original_conditioner = model.conditioner.get_condition_with_negative_prompt
    original_forward = net.forward
    original_writer = inference_module.save_img_or_video
    original_guard = inference_module.guardrail_presets.run_video_guardrail
    original_arm = FixedMaskRouter.arm
    original_decide = FixedMaskRouter.decide
    saved = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    saved_config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    saved_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    net.prepare_embedded_sequence = lambda x, **kw: (x.movedim(1, -1).contiguous(), None, None)
    frozen, class_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        gt=torch.arange(32,dtype=torch.float32).reshape(1,2,2,2,4)/31
        return tuple(frozen(crossattn_emb=torch.ones(1, 3, 4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'],padding_mask=torch.zeros(1,1,2,4),use_video_condition=torch.tensor([slot==0]))
            .set_video_condition(gt.clone(),0,0,num_conditional_frames=1)
            .edit_for_inference(is_cfg_conditional=slot==0,num_conditional_frames=1) for slot in (0, 1))
    model.conditioner.get_condition_with_negative_prompt = conditions
    # Deterministic preparation is a Toy fixture only, including both scene inputs.
    def deterministic_batch(*args, **kwargs):
        entry = RNGState()
        torch.manual_seed(284)
        try:
            return original_batch(*args, **kwargs)
        finally:
            entry.restore()
    inference.pipe._get_data_batch_input = deterministic_batch
    mode = establish_shared_eval(net)
    # Same Toy conditions/settings as the previously passed fixed-mask interface.
    # The real production settings/pairs in the frozen scope remain untouched.
    scenes, states = [], []
    try:
        for sample in samples:
            saved.restore()
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            deep, count = [], [0]
            handles = [b.register_forward_hook(lambda *a: count.__setitem__(0, count[0]+1)) for b in list(net.blocks)[settings['probe_depth']:]]
            hooks = Hooks()
            hooks.wrap(net, 'forward', before=lambda a,k: count.__setitem__(0,0), after=lambda v: deep.append(count[0]))
            try:
                with tempfile.TemporaryDirectory() as directory:
                    inference.generate([sample], output_dir=Path(directory))
            finally:
                hooks.close()
                for handle in handles: handle.remove()
                net.forward = original_forward
            mask = tuple('C' if d == 0 else 'D' for d in deep)
            FixedMaskPlan(mask).validate()
            pairs = []
            for slot in (0,1):
                candidates = [(n,m) for n in range(45+slot,69,2) if mask[n-1]=='C'
                    for m in range(n+2,69,2) if mask[m-1]=='D']
                assert candidates, 'Toy fixture must contain a same-CFG C/D pair'
                pairs.append({'CFG_slot':slot,'calls':list(candidates[0])})
            scenes.append({'scene':sample.name,'parent_action_mask':list(mask),
                'parent_full_counts_per_CFG':list(cfg_full_counts(mask)),
                'parent_mask_sha256':mask_sha256(mask),'swaps':pairs})
        saved.restore()
        for key in set(WC_FIELDS)-saved_keys:
            if hasattr(net,key): delattr(net,key)
        for key,value in saved_config.items(): setattr(net,key,value)
        config = {'scope':{'run_id':'CPU_PLACEMENT:composition', 'scenes':scenes,
                          'CPU_TOY_fixture':True,'maximum_age_solver_steps':33},
            'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
        contexts = [(config['scope']['run_id']+':'+s.name,'toy_model','condition:'+s.name) for s in samples]
        failures = [None] if not flow else [None,'child_writer','child_guardrail','prefix_mask',
                                            'own_CFG_history','protected_native_action']
        for failure in failures:
            state = {}; guard_calls=[0]
            def writer(value,path,fps):
                if failure=='child_writer' and 'child_BASE1' in str(path): return
                return original_writer(value,path,fps)
            def guard(frames,runner):
                guard_calls[0]+=1
                if failure=='child_guardrail' and guard_calls[0]==2: return None
                return original_guard(frames,runner)
            def arm(router,plan):
                if failure=='prefix_mask':
                    router.events[0]['actual_action']='C'
                original_arm(router,plan)
                if failure=='protected_native_action':
                    mask=list(plan.parent_mask); mask[68]='C' if mask[68]=='D' else 'D'
                    router.plan=replace(plan,parent_mask=tuple(mask))
            def decide(router,*args):
                if failure=='own_CFG_history' and router.plan is not None and router.pending['call'] in router.plan.swap_calls:
                    router.history[router.pending['cfg_slot']].clear()
                return original_decide(router,*args)
            inference_module.save_img_or_video=writer
            inference_module.guardrail_presets.run_video_guardrail=guard
            FixedMaskRouter.arm=arm; FixedMaskRouter.decide=decide
            try:
                with tempfile.TemporaryDirectory(prefix='rv0-placement-composition-') as directory:
                    error=None
                    try:
                        run_placement_causal_batch(inference,samples,wc,settings,state=state,save=lambda:None,
                            output=Path(directory),inference_module=inference_module,contexts=contexts,
                            mode_setup=mode,runtime=runtime,config=config,require_historical_bridge=False)
                    except Exception as exception:
                        error=str(exception)
                    assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs'])==(2,16,10)
                    if failure:
                        assert error and state['requests'][0]['status']=='TECH_BLOCKED'
                        child=state['requests'][0]['children'][-1]
                        assert child['status']=='TECH_BLOCKED' and child['record']['parent_restored']
                        expected={'child_writer':'guardrail rejection','child_guardrail':'guardrail rejection',
                            'prefix_mask':'parent prefix','own_CFG_history':'own-CFG true-full',
                            'protected_native_action':'Protected native action'}[failure]
                        assert expected in error,error
                    else:
                        assert error is None,error
                        audit_trajectories(state,config,3)
                        for row,scene in zip(state['requests'],scenes):
                            assert row['historical_WC_encoded_bridge_pass']=='CPU_TOY_NOT_REAL_REFERENCE'
                            assert all(c=='cpu_rv0_pinned_video_condition.Video2WorldCondition' for c in row['condition_classes'])
                            mutations=['missing_repeat','quota','action','swap_input','protected_override',
                                       'final_state','pipeline','encoding','own_age','restore']
                            for mutation in mutations:
                                damaged=copy.deepcopy(row)
                                child=damaged['children'][3]
                                if mutation=='missing_repeat': damaged['children'].pop()
                                elif mutation=='quota': child['record']['action_report']['per_CFG_full_counts'][0]+=1
                                elif mutation=='action': child['deep'][0]=99
                                elif mutation=='swap_input': child['inputs'][0]={'corrupted':True}
                                elif mutation=='protected_override': child['record']['action_report']['suffix_events'][-3]['actual_native_override']=True
                                elif mutation=='final_state': child['record']['final_state_components']={}
                                elif mutation=='pipeline': damaged['decoded_children'][0]['pipeline'].pop()
                                elif mutation=='encoding': damaged['decoded_children'][1]['artifact']['sha256']='0'*64
                                elif mutation=='own_age': next(e for e in child['record']['action_report']['suffix_events'] if e['actual_action']=='C')['age_solver_steps']=34
                                elif mutation=='restore': child['record']['parent_restored']=False
                                try: verify_placement_row(damaged,scene,3)
                                except ValueError: pass
                                else: raise AssertionError('Corrupted placement evidence accepted: '+mutation)
                    states.append({'flow':flow,'failure':failure,'error':error,'receipt':state,
                        'fixture_config':copy.deepcopy(config),'frozen_condition_class_AST_sha256':class_sha,
                        'CPU_MOCK_outputs_not_video':True,'real_frozen_pair_feasibility':'NOT_TESTED_BY_TOY'})
                assert net.forward==original_forward and not hasattr(net,'_wc_rv0_router')
                assert all(float(b)==0 for b in net.buffers())
                assert all(not m.training for m in net.modules())
            finally:
                inference_module.save_img_or_video=original_writer
                inference_module.guardrail_presets.run_video_guardrail=original_guard
                FixedMaskRouter.arm=original_arm; FixedMaskRouter.decide=original_decide
        return states
    finally:
        net.forward=original_forward; net.prepare_embedded_sequence=original_prepare
        inference.pipe._get_data_batch_input=original_batch
        model.conditioner.get_condition_with_negative_prompt=original_conditioner
        saved.restore()
        for key in set(WC_FIELDS)-saved_keys:
            if hasattr(net,key): delattr(net,key)
        for key,value in saved_config.items(): setattr(net,key,value)


def run(runtime):
    result=load('check_full_sampling').run(Path(runtime),exercise=lambda **k:exercise(runtime=Path(runtime),**k))
    assert len(result['checks'])==7
    assert not torch.cuda.is_initialized()
    result.update(status='PLACEMENT_FULL_COMPOSITION_CPU_PASS_NOT_GPU',CUDA_initialized=False,
        complete_successful_parents=4,complete_successful_suffixes=32,successful_mock_outputs=20,
        failed_attempts_retained=5,raw_mutation_refusals=40,GPU_submissions=0,RV_labels=0,
        real_frozen_pair_GPU_legality='NOT_TESTED_BY_CPU_TOY')
    return result
