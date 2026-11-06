"""Production placement composition on pinned sampler/WC/Video2World CPU Toy.

Pairs selected from an uninstrumented Toy trajectory are explicit fixtures;
they do not stand in for the four frozen real CAL pairs or GPU feasibility.
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
from wcomr.mid_coverage import WC_FIELDS
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import WC_CONFIGURATION
from wcomr.rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from wcomr.rv0_native_tail_causal import run_native_tail_causal_batch
from wcomr.rv0_native_tail_evaluation import audit_trajectories, verify_native_tail_row
from wcomr.rv0_native_tail import NativeTailRouter as FixedMaskRouter
from wcomr.rv0_native_tail_scope import LABELS, ENCODED

CPU_ATTEMPTS=[]
TAIL_DIFFERENCE_PROOFS=[]


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def exercise(*, inference, samples, wc, settings, inference_module, flow, runtime, **unused):
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
            pairs = []
            for slot in (0,1):
                candidates = [(n,m) for n in range(45+slot,69,2) if mask[n-1]=='C'
                    for m in range(n+2,69,2) if mask[m-1]=='D']
                assert candidates, 'Toy fixture must contain a same-CFG C/D pair'
                pairs.append({'CFG_slot':slot,'calls':list(candidates[0])})
            scenes.append({'scene':sample.name,'parent_action_mask':list(mask),
                'parent_full_counts_per_CFG':list(cfg_full_counts(mask)),
                'parent_mask_sha256':mask_sha256(mask),'cases':[
                    {'name':'46','CFG_slot':1,'swap_calls':pairs[1]['calls']},
                    {'name':'61','CFG_slot':0,'swap_calls':pairs[0]['calls']}]})
        saved.restore()
        for key in set(WC_FIELDS)-saved_keys:
            if hasattr(net,key): delattr(net,key)
        for key,value in saved_config.items(): setattr(net,key,value)
        config = {'scope':{'run_id':'CPU_NATIVE_TAIL:composition', 'scenes':scenes,
                          'CPU_TOY_fixture':True,'maximum_age_solver_steps':33,
                          'scope_counts':[1,10,6,2], 'order':LABELS, 'encoded':['PARENT']+ENCODED,
                          'responsive_calls_only':[69,70]},
            'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
        contexts = [(config['scope']['run_id']+':'+s.name,'toy_model','condition:'+s.name) for s in samples]
        failures = [None] if not flow else [None, 'tail_proposal_difference', 'own_tail_history', 'mode_seal', 'child_writer']
        for failure in failures:
            state = {}
            def writer(value, path, fps):
                if failure == 'child_writer' and 'child_TAIL46_first' in str(path):
                    return
                return original_writer(value, path, fps)
            def arm(router, plan, native_tail):
                original_arm(router, plan, native_tail)
                if failure == 'mode_seal' and native_tail:
                    router.native_tail = False
            def decide(router, *args):
                if router.native_tail and router.pending['call'] in (69, 70):
                    if failure == 'tail_proposal_difference':
                        adjusted = list(args)
                        adjusted[2] = router.plan.action_mask()[router.pending['call']-1] != 'C'
                        args = tuple(adjusted)
                    if failure == 'own_tail_history':
                        router.history[router.pending['cfg_slot']].clear()
                return original_decide(router, *args)
            inference_module.save_img_or_video = writer
            FixedMaskRouter.arm_mode = arm; FixedMaskRouter.decide = decide
            try:
                with tempfile.TemporaryDirectory(prefix='native-tail-core-') as directory:
                    error = None
                    try:
                        run_native_tail_causal_batch(inference, samples, wc, settings, state=state, save=lambda:None,
                            output=Path(directory), inference_module=inference_module, contexts=contexts,
                            mode_setup=mode, runtime=runtime, config=config, require_historical_bridge=False)
                    except Exception as exception:
                        error = str(exception)
                    item = {'flow':flow, 'failure':failure, 'error':error,
                            'receipt':copy.deepcopy(state), 'fixture_config':copy.deepcopy(config)}
                    CPU_ATTEMPTS.append(item)
                    if os.environ.get('WC_NATIVE_TAIL_CPU_ATTEMPTS'):
                        Path(os.environ['WC_NATIVE_TAIL_CPU_ATTEMPTS']).write_text(json.dumps(CPU_ATTEMPTS, indent=2)+'\n')
                    assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs']) == (1,10,6)
                    if failure in ('own_tail_history', 'mode_seal', 'child_writer'):
                        assert error and state['requests'][0]['status']=='TECH_BLOCKED', item
                        child = state['requests'][0]['children'][-1]
                        assert child['label']=='TAIL46_first' and child['record']['parent_restored']
                        assert child['status']=='TECH_BLOCKED'
                    else:
                        assert error is None, error
                        audit_trajectories(state, config, 3)
                        row = state['requests'][0]
                        if failure == 'tail_proposal_difference':
                            responsive = [c for c in row['children'] if c['native_tail']]
                            for child in responsive:
                                events = child['record']['action_report']['suffix_events'][-4:-2]
                                assert all(e['tail_response_changes_fixed_action'] for e in events)
                                TAIL_DIFFERENCE_PROOFS.append({'label':child['label'],
                                    'tail_events':events, 'actual_counts':child['record']['action_report']['per_CFG_full_counts']})
                        for mutation in ['missing_repeat','count','action','pre69_input','pre69_solver','pre69_history',
                                         'native_proposal','outside_tail','final_state','pipeline','encoding','own_age','restore']:
                            damaged = copy.deepcopy(row); child = damaged['children'][3]
                            report = child['record']['action_report']
                            if mutation=='missing_repeat': damaged['children'].pop()
                            elif mutation=='count': report['per_CFG_full_counts'][0]+=1
                            elif mutation=='action': child['deep'][0]=99
                            elif mutation=='pre69_input': child['inputs'][24]={'corrupted':True}
                            elif mutation=='pre69_solver': child['pre69_state_components']={}
                            elif mutation=='pre69_history': child['pre69_router_history']=[[],[]]
                            elif mutation=='native_proposal': report['suffix_events'][-4]['native_skip']=not report['suffix_events'][-4]['native_skip']
                            elif mutation=='outside_tail': report['actual_actions'][67]='D' if report['actual_actions'][67]=='C' else 'C'
                            elif mutation=='final_state': child['record']['final_state_components']={}
                            elif mutation=='pipeline': damaged['decoded_children'][0]['pipeline'].pop()
                            elif mutation=='encoding': damaged['decoded_children'][0]['artifact']['sha256']='0'*64
                            elif mutation=='own_age': next(e for e in report['suffix_events'] if e['actual_action']=='C')['age_solver_steps']=34
                            elif mutation=='restore': child['record']['parent_restored']=False
                            try: verify_native_tail_row(damaged, scenes[0], 3)
                            except ValueError: pass
                            else: raise AssertionError('Corrupted native-tail evidence accepted: '+mutation)
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
    assert len(result['checks'])==6
    assert not torch.cuda.is_initialized()
    result.update(status='NATIVE_TAIL_COMPLETE_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU',
        CUDA_initialized=False, complete_CPU_parents=3, complete_CPU_suffixes=30,
        mock_outputs_not_videos=18, failures_retained=3, raw_mutation_refusals=39,
        deliberate_native_tail_action_changes=len(TAIL_DIFFERENCE_PROOFS)*2,
        GPU_submissions=0, RV_labels=0, real_pair_feasibility='NOT_TESTED_BY_CPU_TOY')
    assert len(TAIL_DIFFERENCE_PROOFS)==4
    return result
