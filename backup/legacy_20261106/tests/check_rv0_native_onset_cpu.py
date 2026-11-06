"""Response-onset composition on pinned sampler/WC/Video2World CPU Toy.

Pairs selected from an uninstrumented Toy trajectory are explicit fixtures;
they do not stand in for the registered real Human61 pair or GPU feasibility.
"""
import copy
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.h0_mode import establish_shared_eval
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import WC_CONFIGURATION
from wcomr.rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from wcomr.rv0_native_onset_causal import run_native_response_causal_batch
from wcomr.rv0_native_onset_evaluation import audit_trajectories, verify_native_response_row
from wcomr.rv0_native_onset import NativeResponseRouter as FixedMaskRouter
from wcomr.rv0_native_onset_scope import LABELS, ENCODED, CALLS

CPU_ATTEMPTS=[]
RESPONSE_DIFFERENCE_PROOFS=[]
RESUME_NONFLOW = None


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def verify_mutation_refusals(row, scene):
    refused = []
    for mutation in ['missing_repeat','window','count','action','pre65_input',
        'pre65_state','pre67_state','pre69_history','native_proposal',
        'outside_window','final_state','final_state_missing_component',
            'final_state_digest','final_state_output','pre_state_inventory','pipeline','encoding','own_age','restore','prefix_bank']:
        damaged = copy.deepcopy(row)
        mode = {'pre67_state':'RESP67','pre69_history':'LATE69'}.get(mutation,'RESP65')
        by = {c['label']:c for c in damaged['children']}
        targets = [by[mode+'_'+repeat] for repeat in ('first','second')]
        if mutation=='missing_repeat': damaged['children'].pop()
        elif mutation=='pipeline': damaged['decoded_children'][0]['pipeline'].pop()
        elif mutation=='encoding': damaged['decoded_children'][0]['artifact']['sha256']='0'*64
        else:
            # Change both repeats, so prefix/state/window checks must reject
            # even when the two deliberately corrupted records still agree.
            for child in targets:
                report = child['record']['action_report']
                if mutation=='window': child['responsive_calls']=[67,68,69,70]
                elif mutation=='count': report['per_CFG_full_counts'][0]+=1
                elif mutation=='action': child['deep'][0]=99
                elif mutation=='pre65_input': child['inputs'][20]={'corrupted':True}
                elif mutation=='pre65_state': child['response_boundaries']['65']['components']={'corrupted':'0'*64}
                elif mutation=='pre67_state': child['response_boundaries']['67']['components']={'corrupted':'0'*64}
                elif mutation=='pre69_history': child['response_boundaries']['69']['own_CFG_history']=[[],[]]
                elif mutation=='native_proposal':
                    e=next(e for e in report['suffix_events'] if e['call'] in child['responsive_calls'])
                    e['native_skip']=not e['native_skip']
                elif mutation=='outside_window': report['actual_actions'][63]='D' if report['actual_actions'][63]=='C' else 'C'
                elif mutation=='final_state': child['record']['final_state_components']={}
                elif mutation=='final_state_missing_component': child['record']['final_state_components'].pop('cpu_rng')
                elif mutation=='final_state_digest': child['record']['final_state_sha256']='0'*64
                elif mutation=='final_state_output':
                    child['record']['final_state_components']['output']='0'*64
                    child['record']['final_state_sha256']=tree_digest(child['record']['final_state_components'])
                elif mutation=='pre_state_inventory': child['response_boundaries']['65']['components'].pop('cpu_rng')
                elif mutation=='own_age': next(e for e in report['suffix_events'] if e['actual_action']=='C')['age_solver_steps']=34
                elif mutation=='restore': child['record']['parent_restored']=False
                elif mutation=='prefix_bank': child['banks'][19]='0'*64
        try: verify_native_response_row(damaged, scene, 3)
        except ValueError: refused.append(mutation)
        else: raise AssertionError('Corrupted response-onset evidence accepted: '+mutation)
    assert len(refused) == 20
    return refused


def persist_attempt(item):
    CPU_ATTEMPTS.append(item)
    if os.environ.get('WC_NATIVE_ONSET_CPU_ATTEMPTS'):
        Path(os.environ['WC_NATIVE_ONSET_CPU_ATTEMPTS']).write_text(json.dumps(CPU_ATTEMPTS, indent=2)+'\n')


def exercise(*, inference, samples, wc, settings, inference_module, flow, runtime, **unused):
    if flow is False and RESUME_NONFLOW is not None:
        item = copy.deepcopy(RESUME_NONFLOW)
        assert item['flow'] is False and item['failure'] is None and item['error'] is None
        audit_trajectories(item['receipt'], item['fixture_config'], 3)
        row = item['receipt']['requests'][0]
        item['audit_mutation_refusals'] = verify_mutation_refusals(row, item['fixture_config']['scope']['scenes'][0])
        item['reused_prior_complete_sampling'] = True
        item['new_sampling_executions'] = 0
        persist_attempt(item)
        return [item]
    samples = samples[-1:]
    model, net = inference.pipe.model, inference.pipe.model.net
    original_prepare = net.prepare_embedded_sequence
    original_batch = inference.pipe._get_data_batch_input
    original_conditioner = model.conditioner.get_condition_with_negative_prompt
    original_forward = net.forward
    original_writer = inference_module.save_img_or_video
    original_guard = inference_module.guardrail_presets.run_video_guardrail
    original_arm = FixedMaskRouter.arm_mode
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
            candidates = [(n,m) for n in range(45,63,2) if mask[n-1]=='C'
                for m in range(n+2,65,2) if mask[m-1]=='D']
            assert candidates, 'Toy fixture requires one own-CFG C/D pair before65'
            scenes.append({'scene':sample.name,'parent_action_mask':list(mask),
                'parent_full_counts_per_CFG':list(cfg_full_counts(mask)),
                'parent_mask_sha256':mask_sha256(mask),
                'case':{'name':'61','CFG_slot':0,'swap_calls':list(candidates[0])}})
        saved.restore()
        for key in set(WC_FIELDS)-saved_keys:
            if hasattr(net,key): delattr(net,key)
        for key,value in saved_config.items(): setattr(net,key,value)
        config = {'scope':{'run_id':'CPU_NATIVE_ONSET:composition', 'scenes':scenes,
                          'CPU_TOY_fixture':True,'maximum_age_solver_steps':33,
                          'scope_counts':[1,10,6,2], 'order':LABELS, 'encoded':['PARENT']+ENCODED,
                          'responsive_calls':CALLS},
            'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
        contexts = [(config['scope']['run_id']+':'+s.name,'toy_model','condition:'+s.name) for s in samples]
        failures = [None] if not flow else [None, 'response_proposal_difference',
            'own_response_history', 'window_seal', 'illegal_start', 'child_writer']
        fault_cases = ('own_response_history', 'window_seal', 'illegal_start', 'child_writer')
        for failure in failures:
            state = {}
            def writer(value, path, fps):
                if failure == 'child_writer' and 'child_RESP65_first' in str(path):
                    return
                return original_writer(value, path, fps)
            def arm(router, plan, calls):
                if failure == 'illegal_start' and calls == tuple(range(65,71)):
                    original_arm(router, plan, tuple(range(66,71)))
                    return
                original_arm(router, plan, calls)
                if failure == 'window_seal' and calls == tuple(range(65,71)):
                    router.responsive_calls = tuple(range(67,71))
            def decide(router, *args):
                if router.pending['call'] in router.responsive_calls:
                    if failure == 'response_proposal_difference':
                        adjusted = list(args)
                        adjusted[2] = router.plan.action_mask()[router.pending['call']-1] != 'C'
                        args = tuple(adjusted)
                    if failure == 'own_response_history' and router.responsive_calls == tuple(range(65,71)):
                        router.history[router.pending['cfg_slot']].clear()
                return original_decide(router, *args)
            inference_module.save_img_or_video = writer
            FixedMaskRouter.arm_mode = arm; FixedMaskRouter.decide = decide
            try:
                with tempfile.TemporaryDirectory(prefix='native-onset-core-') as directory:
                    error = None
                    try:
                        run_native_response_causal_batch(inference, samples, wc, settings, state=state, save=lambda:None,
                            output=Path(directory), inference_module=inference_module, contexts=contexts,
                            mode_setup=mode, runtime=runtime, config=config, require_historical_bridge=False)
                    except Exception as exception:
                        error = str(exception)
                    item = {'flow':flow, 'failure':failure, 'error':error,
                            'receipt':copy.deepcopy(state), 'fixture_config':copy.deepcopy(config)}
                    persist_attempt(item)
                    assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs']) == (1,10,6)
                    if failure in fault_cases:
                        assert error and state['requests'][0]['status']=='TECH_BLOCKED', item
                        child = state['requests'][0]['children'][-1]
                        assert child['label']=='RESP65_first' and child['record']['parent_restored']
                        assert child['status']=='TECH_BLOCKED'
                    else:
                        assert error is None, error
                        audit_trajectories(state, config, 3)
                        row = state['requests'][0]
                        if failure == 'response_proposal_difference':
                            responsive = [c for c in row['children'] if c['responsive_calls']]
                            for child in responsive:
                                events = [e for e in child['record']['action_report']['suffix_events']
                                          if e['call'] in child['responsive_calls']]
                                assert all(e['response_changes_fixed_action'] for e in events)
                                RESPONSE_DIFFERENCE_PROOFS.append({'label':child['label'],
                                    'response_events':events,
                                    'actual_counts':child['record']['action_report']['per_CFG_full_counts']})
                        item['audit_mutation_refusals'] = verify_mutation_refusals(row, scenes[0])
                        persist_attempt_update = os.environ.get('WC_NATIVE_ONSET_CPU_ATTEMPTS')
                        if persist_attempt_update:
                            Path(persist_attempt_update).write_text(json.dumps(CPU_ATTEMPTS, indent=2)+'\n')
                    states.append(item)
                assert net.forward==original_forward and not hasattr(net,'_wc_rv0_router')
                assert all(float(b)==0 for b in net.buffers())
                assert all(not m.training for m in net.modules())
            finally:
                inference_module.save_img_or_video = original_writer
                FixedMaskRouter.arm_mode = original_arm; FixedMaskRouter.decide = original_decide
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
    result=load('check_full_sampling').run(Path(runtime), exercise=lambda **k:exercise(runtime=Path(runtime), **k))
    assert len(result['checks'])==7
    assert not torch.cuda.is_initialized()
    result.update(status='NATIVE_RESPONSE_ONSET_COMPLETE_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU',
        CUDA_initialized=False, complete_CPU_parents=3, complete_CPU_suffixes=30,
        mock_outputs_not_videos=18, failures_retained=4, raw_mutation_refusals=sum(len(a.get('audit_mutation_refusals', [])) for a in CPU_ATTEMPTS),
        new_complete_CPU_parents=2 if RESUME_NONFLOW is not None else 3,
        reused_complete_CPU_parents=1 if RESUME_NONFLOW is not None else 0,
        new_complete_CPU_suffixes=20 if RESUME_NONFLOW is not None else 30,
        reused_complete_CPU_suffixes=10 if RESUME_NONFLOW is not None else 0,
        new_mock_outputs_not_videos=12 if RESUME_NONFLOW is not None else 18,
        reused_mock_outputs_not_videos=6 if RESUME_NONFLOW is not None else 0,
        deliberate_native_response_action_changes=sum(len(p['response_events']) for p in RESPONSE_DIFFERENCE_PROOFS),
        GPU_submissions=0, RV_labels=0, real_pair_feasibility='NOT_TESTED_BY_CPU_TOY')
    assert len(RESPONSE_DIFFERENCE_PROOFS)==6
    assert result['raw_mutation_refusals'] == 60
    assert len(CPU_ATTEMPTS) == 7
    return result
