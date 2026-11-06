"""Pinned UniPC/WC full-suffix placement controls with frozen Video2World AST.

Network/weights/conditioning inputs/decoder/writer are declared Toy fixtures.
The fixed-mask control leaves the official sampler and WC side effects intact.
"""
import copy
from dataclasses import replace
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.prepared_input import PreparedInputReplay, RNGState, input_signatures
from wcomr.rv0_fork import WC_CONFIGURATION, official_suffix, object_state
from wcomr.rv0_fixed_plan import FixedMaskPlan
from wcomr.rv0_fixed_mask import FixedMaskRouter, FixedMaskSuffixControl


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercise(*, inference, samples, wc, settings, flow, runtime, **kwargs):
    model, net, scheduler = inference.pipe.model, inference.pipe.model.net, inference.pipe.model.sample_scheduler
    caller = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    caller_sha = caller.fingerprint()
    original_forward, original_prepare = net.forward, net.prepare_embedded_sequence
    original_conditioner = model.conditioner.get_condition_with_negative_prompt
    config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    keys = {k for k in WC_FIELDS if hasattr(net, k)}
    net.prepare_embedded_sequence = lambda x, **kwargs: (x.movedim(1, -1).contiguous(), None, None)
    video = load('check_rv0_video_actions_cpu')
    frozen, class_sha = video.pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])

    def conditions(batch):
        gt = torch.arange(32, dtype=torch.float32).reshape(1, 2, 2, 2, 4)/31
        result = []
        for slot in (0, 1):
            c = frozen(crossattn_emb=torch.ones(1, 3, 4)*(1+slot+.1*(batch['prompt']=='human')),
                       fps=batch['fps'], padding_mask=torch.zeros(1, 1, 2, 4),
                       use_video_condition=torch.tensor([slot == 0]))
            result.append(c.set_video_condition(gt.clone(), 0, 0, num_conditional_frames=1)
                          .edit_for_inference(is_cfg_conditional=slot == 0, num_conditional_frames=1))
        return tuple(result)

    model.conditioner.get_condition_with_negative_prompt = conditions
    source = runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    checks = []
    try:
        for sample in samples:
            entry = RNGState()
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            observations, branches, failures = [], [], []
            parent_mask = None
            pairs = []
            for instrumented in (False, True):
                entry.restore()
                with torch.no_grad():
                    for name, value in net.named_buffers():
                        value.copy_(caller.buffers[name][1])
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
                router = FixedMaskRouter(('CPU_FIXED:'+sample.name, 'toy_model', 'condition:'+sample.name)) if instrumented else None
                if router:
                    router.install(net, wc, source)
                hooks = Hooks()
                current = {'inputs': [], 'outputs': [], 'deep': [], 'banks': [], 'solver': []}
                observations.append(current)
                stage = {'inside': False}
                count = [0]
                prior_prepare = inference.pipe._get_data_batch_input
                inference.pipe._get_data_batch_input = prepared
                hooks.wrap(model, 'get_velocity_fn_from_batch', after=lambda v: stage.update(velocity=v))
                hooks.wrap(model, 'denoise', before=lambda a, k: stage.update(noise=a[0]))
                handles = [b.register_forward_hook(lambda *a: count.__setitem__(0, count[0]+1))
                           for b in list(net.blocks)[1:]]
                def before_forward(a, k):
                    current['inputs'].append(input_signatures(a, k)); count[0] = 0
                def after_forward(v):
                    current['outputs'].append(tree_digest(v)); current['deep'].append(count[0])
                    current['banks'].append(tree_digest([net.residual_cache, net.probe_residual_cache,
                        net.residual_window, net.probe_residual_window, net.accumulated_rel_l1_distance,
                        net.resume_flag, net.worldcache_step_skipped_count]))
                hooks.wrap(net, 'forward', before=before_forward, after=after_forward)
                def after_step(value):
                    if stage['inside']:
                        return
                    current['solver'].append(tree_digest(value))
                    if scheduler._step_index != 22 or router is None:
                        return
                    fork = FixedMaskSuffixControl(model, value[0].squeeze(0), stage['noise'],
                        stage['generator'], stage['velocity'], suffix, router=router, context=router.context)
                    ids = tuple(id(c) for c in fork.conditions)
                    csha = [tree_digest(object_state(c)) for c in fork.conditions]
                    before = copy.deepcopy(current)
                    stage['inside'] = True
                    def attempt(label, plan):
                        start = len(current['inputs'])
                        latent = fork.run_mask(label, plan)
                        assert ids == tuple(id(c) for c in fork.conditions)
                        assert csha == [tree_digest(object_state(c)) for c in fork.conditions]
                        branches.append({'label': label, 'swap_calls': list(plan.swap_calls),
                            'inputs': copy.deepcopy(current['inputs'][start:]),
                            'outputs': current['outputs'][start:].copy(), 'deep': current['deep'][start:].copy(),
                            'banks': current['banks'][start:].copy(), 'latent': tree_digest(latent),
                            'record': copy.deepcopy(fork.records[-1])})
                    def refuse(label, plan, mutate, at_call=None):
                        arm = router.arm
                        decide = router.decide
                        def broken(candidate):
                            arm(candidate)
                            if at_call is None:
                                mutate(candidate)
                        def broken_decide(*args):
                            if router.pending['call'] == at_call:
                                mutate(plan)
                            return decide(*args)
                        router.arm = broken
                        if at_call is not None:
                            router.decide = broken_decide
                        try:
                            try:
                                fork.run_mask(label, plan)
                            except ValueError:
                                pass
                            else:
                                raise AssertionError('Invalid live branch accepted: '+label)
                            record = copy.deepcopy(fork.records[-1])
                            assert record['status'] == 'TECH_BLOCKED' and record['parent_restored']
                            assert router.snapshot() == fork.router_parent
                            assert ids == tuple(id(c) for c in fork.conditions)
                            assert csha == [tree_digest(object_state(c)) for c in fork.conditions]
                            failures.append(record)
                        finally:
                            router.arm = arm
                            router.decide = decide
                    try:
                        base = FixedMaskPlan(parent_mask)
                        attempt('base_first', base)
                        for slot, pair in enumerate(pairs):
                            attempt('swap_'+str(slot)+'_first', replace(base, swap_calls=pair))
                        for slot, pair in reversed(list(enumerate(pairs))):
                            attempt('swap_'+str(slot)+'_second', replace(base, swap_calls=pair))
                        attempt('base_second', base)
                        # All mutations happen inside _execute_suffix, so failures
                        # must restore both own-state caches and the router ledger.
                        slot = (pairs[0][0]-1) % 2
                        target = replace(base, swap_calls=pairs[0])
                        refuse('missing_own_CFG_history', target,
                               lambda p: router.history[slot].clear(), at_call=pairs[0][0])
                        refuse('changed_eval', target, lambda p: setattr(net.blocks[0], 'training', True))
                        def corrupt_prefix(p):
                            router.events[0]['actual_action'] = 'C'
                        refuse('changed_prefix_ledger', target, corrupt_prefix)
                        def nonfinite(p):
                            net.residual_cache[slot].flatten()[0] = float('nan')
                        refuse('nonfinite_own_cache', target, nonfinite, at_call=pairs[0][0])
                        def stale(p):
                            step = router.pending['solver_step']
                            router.history[slot] = [step-3, step-2]
                            router.plan = replace(p, maximum_age_solver_steps=1)
                        refuse('infeasible_source_age', target, stale, at_call=pairs[0][0])
                        # A protected call must use its natural action, never an
                        # override to preserve the requested quota. Flip only
                        # call69's expected action after arming, then reject.
                        def protected(p):
                            desired = list(p.parent_mask)
                            desired[68] = 'D' if desired[68] == 'C' else 'C'
                            router.plan = replace(p, parent_mask=tuple(desired))
                        refuse('protected_native_mismatch', base, protected)
                    finally:
                        stage['inside'] = False
                        current.clear(); current.update(before)
                hooks.wrap(scheduler, 'step', before=lambda a, k: stage.update(generator=k['generator']), after=after_step)
                hooks.wrap(model, 'generate_samples_from_batch', after=lambda v: current.update(latent=tree_digest(v)))
                try:
                    with tempfile.TemporaryDirectory(prefix='rv0-fixed-cpu-') as directory:
                        paths = inference.generate([sample], output_dir=Path(directory))
                        current['artifact'] = Path(paths[0]).read_bytes().hex()
                    current['rng'] = RNGState().signatures()
                    current['state'] = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)).fingerprint()
                    if not instrumented:
                        parent_mask = tuple('C' if d == 0 else 'D' for d in current['deep'])
                        FixedMaskPlan(parent_mask).validate()
                        for slot in (0, 1):
                            candidates = [(n, m) for n in range(45+slot, 69, 2) if parent_mask[n-1] == 'C'
                                for m in range(n+2, 69, 2) if parent_mask[m-1] == 'D']
                            assert candidates, 'CPU fixture has no mixed same-CFG swap: '+repr(parent_mask)
                            pairs.append(candidates[0])
                finally:
                    hooks.close(); inference.pipe._get_data_batch_input = prior_prepare
                    for handle in handles:
                        handle.remove()
                    if router:
                        router.close()
            assert observations[0] == observations[1]
            by = {b['label']: b for b in branches}
            assert len(branches) == 6 and len(failures) == 6
            base = by['base_first']
            for field in ('inputs', 'outputs', 'banks', 'deep'):
                assert base[field] == observations[0][field][44:]
            assert base['latent'] == observations[0]['latent']
            for name in ('base', 'swap_0', 'swap_1'):
                a, b = by[name+'_first'], by[name+'_second']
                for field in ('inputs', 'outputs', 'banks', 'deep', 'latent'):
                    assert a[field] == b[field]
                assert a['record']['final_state_components'] == b['record']['final_state_components']
            for slot, (n, m) in enumerate(pairs):
                swap = by['swap_'+str(slot)+'_first']
                assert base['inputs'][:n-44] == swap['inputs'][:n-44]
                assert base['deep'][n-45] == 0 and swap['deep'][n-45] == 3
                assert base['deep'][m-45] == 3 and swap['deep'][m-45] == 0
                differences = [j+45 for j, (a, b) in enumerate(zip(base['deep'], swap['deep'])) if a != b]
                assert differences == [n, m]
            for branch in branches:
                record, report = branch['record'], branch['record']['action_report']
                assert record['parent_restored'] and len(report['suffix_events']) == 28
                assert report['quota_matched_per_CFG'] and not report['equal_runtime']
                assert report['protected_calls_preserved_without_override'] and not report['online_policy']
                assert not report['current_truth_used_for_decision'] and not report['single_step_RV_label']
                assert [e['actual_action'] for e in report['suffix_events']] == report['actual_actions'][44:]
                assert all(not e.get('actual_native_override') for e in report['suffix_events'][-4:])
            checks.append({'sample': sample.name, 'flow': flow, 'CPU_fixture_pairs': [list(p) for p in pairs],
                'pinned_Video2World_class_AST_sha256': class_sha,
                'original_OFF_and_fixed_base_all72_full_pipeline_state_RNG_equal': True,
                'swap_only_two_actions_own_branch_state_and_per_CFG_counts_preserved': True,
                'same_input_through_first_swap_cache_vs_full': True,
                'base_and_both_swaps_repeat_order_independent': True,
                'protected_actions_not_overridden_and_infeasible_attempt_retained': True,
                'condition_identity_values_frozen_class_preserved': True,
                'complete_suffixes': len(branches), 'TECH_BLOCKED_restored': len(failures),
                'branches': branches, 'failures': failures})
        return checks
    finally:
        net.forward = original_forward; net.prepare_embedded_sequence = original_prepare
        model.conditioner.get_condition_with_negative_prompt = original_conditioner
        for key in set(WC_FIELDS)-keys:
            if hasattr(net, key):
                delattr(net, key)
        for key, value in config.items():
            setattr(net, key, value)
        caller.restore()
        assert caller.fingerprint() == caller_sha


def run(runtime):
    controls = load('check_full_sampling').run(Path(runtime),
        exercise=lambda **k: exercise(runtime=Path(runtime), **k))
    assert not torch.cuda.is_initialized()
    assert len(controls['checks']) == 4
    return {'status': 'FIXED_MASK_FULL_SUFFIX_CPU_PASS_NOT_REAL_GPU', 'controls': controls,
            'CPU_groups': 4, 'complete_suffixes': 24, 'TECH_BLOCKED_restored': 24,
            'GPU_submissions': 0, 'RV_labels': 0, 'CUDA_initialized': False,
            'limits': 'Pinned original sampler/WC/Video2World class bodies; Toy network, inputs, weights, decoder and writer.'}
