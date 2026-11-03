"""Saved-evidence F19 exploration. No inference, transport, or GPU dispatch."""
import math

import torch

from .cara_fast_spec_r1 import audit_actions, profile_from
from .policy_generator_r1.interval_grammar import Edge, compile_policy


def timing_audit(analysis, manifest, historical_profile):
    rows = {r['role']: r for r in analysis['prompt_equal_summaries']['ALL']}
    seconds = {k: v['time_mean']['T_DD'] for k, v in rows.items()}
    native, f19, shared = (seconds[k] for k in ('NATIVE35', 'F19_C', 'SHARED25_C'))
    a1 = seconds['F19_A1']
    marginal = (shared-f19)/6
    # B + 36*C is identifiable; B (including decode) and C separately are not.
    intercept = f19-19*marginal
    native_marginal = (native-f19)/17
    controls = []
    for row in historical_profile['component_observations']:
        if row['mode'] != 'PROFILE_LEAN':
            continue
        components = row['components']
        shallow = components['shallow_block']
        controls.append(dict(scene=row['scene'], method=row['method'],
            shallow_pair_seconds=shallow['inclusive_CUDA_ms']/1000/(shallow['calls']/4),
            head_per_call_seconds=components['output_head']['inclusive_CUDA_ms']/1000/
                components['output_head']['calls'],
            solver_per_update_seconds=components['solver_update']['inclusive_CUDA_ms']/1000/36,
            VAE_seconds=components['VAE_decode']['inclusive_CUDA_ms']/1000))
    shallow = math.fsum(r['shallow_pair_seconds'] for r in controls)/len(controls)
    actions = manifest['roles']['F19_A1']['policy']['actions']
    counts = {a: actions.count(a) for a in ('D', 'A', 'C')}
    target = native/1.9
    return dict(T_DD_seconds=seconds, target_speedup=1.9,
        target_T_DD_seconds=target, seconds_to_save=a1-target,
        F19_A1_counts=counts,
        marginal_D_to_C_seconds=marginal,
        native_to_F19_marginal_seconds=native_marginal,
        mixed_model_native_residual_seconds=native-(intercept+36*marginal),
        effective_intercept_B_plus_36C_seconds=intercept,
        C_seconds_identified=False, C_seconds=None, decode_seconds_B36=None,
        zero_intercept_C_seconds_hypothesis=intercept/36,
        A1_total_increment_seconds=a1-f19,
        A1_increment_per_A_seconds=(a1-f19)/counts['A'],
        historical_profile_controls=controls,
        historical_shallow_pair_seconds_mean=shallow,
        plain_C_probe_removal_seconds_hypothesis=counts['C']*shallow,
        remaining_gap_after_probe_removal_hypothesis=a1-target-counts['C']*shallow,
        plain_C_to_0p3_seconds_hypothesis_savings=counts['C']*(1-.3),
        historical_profile_is_F19_measurement=False,
        historical_component_intervals_additive=False,
        missing_F19_components=['embedding_and_condition_preparation', 'drift_and_saliency',
            'OSI_and_residual_algebra', 'flow_and_two_warps', 'readout_bookkeeping'],
        measured_candidate_speedup=None, measured_candidate_LPIPS=None)


def _policy(profile, dense, correction_steps):
    edges = []
    for start, end in zip(dense, dense[1:]+[profile.horizon+1]):
        active = [t for t in correction_steps if start < t < end]
        if active and active != list(range(active[0], active[-1]+1)):
            raise ValueError('Corrections must be one contiguous window per interval')
        # Preserve the existing post-RF phase strengths; a window never crosses25.
        if active and active[0] < 25 <= active[-1]:
            raise ValueError('An A window cannot cross the frozen alpha phase boundary')
        edges.append(Edge(start, end, (active[0], active[-1]) if active else (),
            (.5 if active[0] >= 25 else 1.) if active else 0.))
    return compile_policy(profile, edges)


def candidate_layouts(manifest, timing):
    profile = profile_from(manifest['profile'])
    base = manifest['roles']['F19_A1']['policy']
    dense = [t for t, a in enumerate(base['actions'], 1) if a == 'D']
    original_a = [t for t, a in enumerate(base['actions'], 1) if a == 'A']
    choices = [('F17_TAIL', (27, 30)), ('F17_MIDDLE_TAIL', (18, 30)),
               ('F16_TAIL', (24, 27, 30))]
    rows = []
    for name, removed in choices:
        mask = [t for t in dense if t not in removed]
        age_one, age_two = [], []
        for t in range(8, 36):
            if t in mask:
                continue
            age = t-max(s for s in mask if s < t)
            if age == 1:
                age_one.append(t)
            elif age == 2:
                age_two.append(t)
        retained_a = [t for t in original_a if t-1 in mask]
        variants = dict(A1_RETAIN_LEGAL_ORIGINAL=retained_a,
            A1_EACH_INTERVAL=age_one, A2_EACH_INTERVAL=sorted(age_one+age_two),
            C_ONLY=[])
        compiled = {}
        for variant, corrections in variants.items():
            plan = _policy(profile, mask, corrections)
            trace = audit_actions(plan)
            compiled[variant] = dict(policy=plan, trace=trace,
                max_source_age=max(r['source_age'] or 0 for r in trace if r['action'] != 'D'),
                affine_T_DD_hypothesis=timing['T_DD_seconds']['F19_C']-
                    len(removed)*timing['marginal_D_to_C_seconds']+
                    len(corrections)*timing['A1_increment_per_A_seconds'],
                measured_T_DD=None, measured_LPIPS=None)
        marginal = timing['marginal_D_to_C_seconds']
        estimate = timing['T_DD_seconds']['F19_A1']-len(removed)*marginal
        rows.append(dict(candidate=name, removed_D=list(removed), dense_steps=mask,
            count_D=len(mask), preserves_D_8_through_16=True,
            variants=compiled,
            same_A_count_affine_T_DD_hypothesis=estimate,
            same_A_count_affine_speedup_hypothesis=timing['T_DD_seconds']['NATIVE35']/estimate,
            additional_light_C_saving_needed_hypothesis=max(0., estimate-timing['target_T_DD_seconds']),
            evidence='Structural hypothesis; P0 used Uniform19 at8/20, not this F19 deletion',
            GPU_dispatch_ready=False))
    return dict(schema='CARA_F19_16_17D_CPU_CANDIDATES_R1', candidates=rows,
        original_D_steps=dense, original_A_steps=original_a,
        updates=36, protected_D=list(profile.protected_dense),
        selected_candidate=None, real_endpoint_scores=0, GPU_submissions=0)


def lag_pairs(records):
    """Pair only the same request/parent and actual update lag1/2; never fill gaps."""
    index = {(r['prompt'], r['step']): r for r in records}
    if len(index) != len(records):
        raise ValueError('Duplicate saved request/update')
    return [(index[(prompt, step-lag)], target, lag)
        for (prompt, step), target in sorted(index.items()) for lag in (1, 2)
        if (prompt, step-lag) in index]


@torch.no_grad()
def delta_hold_error(source, target, target_C, guidance=7.):
    """Post-RF v_cond + g*(v_cond-v_uncond), matching the real CFG factory.

    Conditional refresh holds delta and has error g*(delta_s-delta_t).
    Unconditional refresh would have coefficient1+g instead.
    """
    tensors = tuple(source)+tuple(target)+tuple(target_C)
    first = tensors[0]
    if any(v.device.type != 'cpu' or v.shape != first.shape or
           not v.is_floating_point() or not bool(torch.isfinite(v).all()) for v in tensors):
        raise ValueError('Finite aligned CPU post-RF branch tensors required')
    if not math.isfinite(guidance) or guidance < 0:
        raise ValueError('Finite nonnegative CFG coefficient required')
    c0, u0, c, u, cc, cu = (v.double() for v in tensors)
    old_delta, delta = c0-u0, c-u
    truth = c+guidance*delta
    hold = c+guidance*old_delta
    error = hold-truth
    expected = guidance*(old_delta-delta)
    if not torch.allclose(error, expected, rtol=1e-10, atol=1e-10):
        raise ValueError('CFG difference-hold identity failed')
    mse = float(error.square().mean())
    base_mse = float((cc+guidance*(cc-cu)-truth).square().mean())
    energy = float(truth.square().mean())
    delta_energy = float(delta.square().mean())
    return dict(guidance=guidance, branch_order=['conditional', 'unconditional'],
        delta_drift_MSE=float((old_delta-delta).square().mean()),
        held_guided_MSE=mse, WC_C_guided_MSE=base_mse,
        held_to_WC_C_MSE_ratio=mse/base_mse if base_mse else None,
        delta_relative_RMSE=math.sqrt(float((old_delta-delta).square().mean())/delta_energy)
            if delta_energy else None,
        guided_relative_RMSE=math.sqrt(mse/energy) if energy else None,
        guided_error_max_abs=float(error.abs().max()),
        beats_or_equals_saved_WC_C=mse <= base_mse,
        error_identity_verified=True, local_error_only=True)


def analyze_saved_B1(assets, expected_manifest_sha256):
    """Read original B1 files once per state on CPU, hash them, retain small outputs."""
    import hashlib
    import json
    from pathlib import Path
    from .innovation_gain_assets_r1 import load_state

    assets = Path(assets)
    raw = (assets/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_manifest_sha256:
        raise ValueError('Original B1 manifest SHA differs')
    manifest = json.loads(raw)
    records = manifest['states']
    expected_steps = (22, 23, 25, 33, 34, 35)
    prompts = sorted({r['prompt'] for r in records})
    if len(records) != 12 or len(prompts) != 2 or {(r['prompt'], r['step']) for r in records} != {
            (p, s) for p in prompts for s in expected_steps}:
        raise ValueError('Original complete12 B1 denominator required')
    saved = {}
    contexts = {}
    for record in records:
        value = load_state(assets, record['artifact'])
        if not all(value[k] for k in ('P0_actual_dense', 'P1_dense_head_RF_equal', 'P2_C_actual_parent_equal')):
            raise ValueError('Original same-state/head/RF identity proof missing')
        prompt = record['prompt']
        context = tuple(value['context'])
        if context[0] != prompt or value['step'] != record['step']:
            raise ValueError('Saved payload identity differs from manifest')
        if prompt in contexts and contexts[prompt] != context:
            raise ValueError('Cannot mix parents/model contexts')
        contexts[prompt] = context
        for pair in (value['teacher'], value['readouts']['WC_C']['outputs']):
            if len(pair) != 2 or any(v.ndim != 5 or v.dtype != torch.float32 for v in pair):
                raise ValueError('Original post-RF FP32 BCTHW branch pair required')
        saved[(prompt, record['step'])] = dict(
            teacher=tuple(v.detach().clone() for v in value['teacher']),
            C=tuple(v.detach().clone() for v in value['readouts']['WC_C']['outputs']))
        del value
    result = []
    for source, target, lag in lag_pairs(records):
        a = saved[(source['prompt'], source['step'])]
        b = saved[(target['prompt'], target['step'])]
        result.append(dict(prompt=target['prompt'], source_step=source['step'],
            target_step=target['step'], actual_update_lag=lag,
            **delta_hold_error(a['teacher'], b['teacher'], b['C'])))
    return dict(schema='CARA_F19_B1_DELTA_HOLD_CPU_R1',
        status='COMPLETE_SAVED_SHARED25_TEACHER_TRACE_LOCAL_DIAGNOSTIC',
        manifest_sha256=expected_manifest_sha256, states=12, inputs=2,
        rows=result, comparisons=len(result),
        lag_counts={str(lag): sum(r['actual_update_lag'] == lag for r in result) for lag in (1, 2)},
        beats_C_counts={str(lag): sum(r['actual_update_lag'] == lag and
            r['beats_or_equals_saved_WC_C'] for r in result) for lag in (1, 2)},
        source_is_saved_shadow_D_not_deployed_refresh=True,
        parent_is_Shared25_C_not_F19=True, single_branch_cache_trajectory_validated=False,
        full36_D_target_coverage=False, GPU_screen_ready=False,
        measured_LPIPS=None, measured_speedup=None, GPU_submissions=0)
