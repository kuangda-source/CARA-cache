"""CPU-only CFG diagnostics from the complete original twelve B1 states.

No head/model replay or fitted parameters. All comparisons retain the original
Shared25-C parent and are local teacher-trace diagnostics, not F19 endpoints.
"""
import hashlib
import json
import math
from pathlib import Path

import torch

from .cara_f19_zero_gpu_r1 import delta_hold_error, lag_pairs
from .innovation_gain_assets_r1 import load_state


def guided(pair):
    return pair[0]+7*(pair[0]-pair[1])


def mse(left, right):
    return float((left.double()-right.double()).square().mean())


def summarize(rows, metric):
    per_input = []
    for prompt in sorted({r['prompt'] for r in rows}):
        selected = [r for r in rows if r['prompt'] == prompt]
        numerator = math.fsum(r[metric] for r in selected)/len(selected)
        c = math.fsum(r['WC_C_guided_MSE_FP32'] for r in selected)/len(selected)
        a = math.fsum(r['A_PHASE_guided_MSE_FP32'] for r in selected)/len(selected)
        per_input.append(dict(prompt=prompt, pairs=len(selected), MSE=numerator,
            WC_C_MSE=c, A_PHASE_MSE=a,
            ratio_to_C=numerator/c if c else None, ratio_to_A=numerator/a if a else None,
            beats_C=sum(r[metric] <= r['WC_C_guided_MSE_FP32'] for r in selected),
            beats_A=sum(r[metric] <= r['A_PHASE_guided_MSE_FP32'] for r in selected)))
    if not rows:
        return dict(pairs=0, independent_inputs=0, MSE=None)
    mean = lambda key: math.fsum(r[key] for r in per_input)/len(per_input)
    value, c, a = mean('MSE'), mean('WC_C_MSE'), mean('A_PHASE_MSE')
    return dict(pairs=len(rows), independent_inputs=len(per_input), per_input=per_input,
        MSE=value, WC_C_MSE=c, A_PHASE_MSE=a,
        ratio_of_input_equal_means_to_C=value/c if c else None,
        ratio_of_input_equal_means_to_A=value/a if a else None,
        beats_C=sum(r['beats_C'] for r in per_input), beats_A=sum(r['beats_A'] for r in per_input),
        worst_pair_MSE=max(r[metric] for r in rows),
        uncertainty='Two exposed inputs; correlated saved states; descriptive only')


@torch.no_grad()
def analyze(assets, manifest_sha256, *, progress=None):
    assets = Path(assets)
    raw = (assets/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest_sha256:
        raise ValueError('Original B1 manifest SHA differs')
    manifest = json.loads(raw)
    records = manifest['states']
    prompts = sorted({r['prompt'] for r in records})
    if len(records) != 12 or len(prompts) != 2 or {(r['prompt'], r['step']) for r in records} != {
            (p, s) for p in prompts for s in (22,23,25,33,34,35)}:
        raise ValueError('Complete original B1 twelve-state denominator required')
    pairs = lag_pairs(records)
    compact, state_rows, contexts = {}, [], {}
    for index, record in enumerate(records):
        if progress:
            progress(dict(phase='LOADING_AND_HASHING_STATE', index=index, total=12,
                prompt=record['prompt'], step=record['step']))
        value = load_state(assets, record['artifact'])
        if not all(value[k] for k in ('P0_actual_dense','P1_dense_head_RF_equal','P2_C_actual_parent_equal')):
            raise ValueError('Original same-state/head/RF identity proof missing')
        context, prompt, step = tuple(value['context']), record['prompt'], record['step']
        if context[0] != prompt or value['step'] != step or (
                prompt in contexts and contexts[prompt] != context):
            raise ValueError('Cannot mix requests/model/parent/updates')
        contexts[prompt] = context
        selected = dict(D=tuple(value['teacher']), C=tuple(value['readouts']['WC_C']['outputs']),
                        A=tuple(value['readouts']['A_PHASE']['outputs']))
        tensors = [v for pair in selected.values() for v in pair]
        if any(v.device.type != 'cpu' or v.ndim != 5 or v.dtype != torch.float32 or
                v.shape != tensors[0].shape or not bool(torch.isfinite(v).all()) for v in tensors):
            raise ValueError('Finite aligned CPU FP32 BCTHW post-RF pairs required')
        truth, C, A = (guided(selected[k]) for k in ('D','C','A'))
        c_mse, a_mse = mse(C,truth), mse(A,truth)
        original_c = value['summary']['WC_C']['MSE']
        original_a = value['summary']['A_PHASE']['MSE']
        if not math.isclose(c_mse,original_c,rel_tol=1e-7,abs_tol=1e-10) or not math.isclose(
                a_mse,original_a,rel_tol=1e-7,abs_tol=1e-10):
            raise ValueError('Saved post-RF errors differ from original accepted scalar summary')
        dc = guided((selected['D'][0],selected['C'][1]))
        cd = guided((selected['C'][0],selected['D'][1]))
        ec, eu = (selected['C'][b].double()-selected['D'][b].double() for b in (0,1))
        ec2, eu2, cross = float(ec.square().mean()), float(eu.square().mean()), float((ec*eu).mean())
        independent = 64*ec2+49*eu2
        signed = -112*cross
        state_rows.append(dict(prompt=prompt,step=step,xi=float(value['xi']),
            tensor_shape=list(tensors[0].shape), true_past_D_steps=[a['step'] for a in value['anchors'][0]],
            WC_C_guided_MSE_FP32=c_mse,A_PHASE_guided_MSE_FP32=a_mse,
            conditional_D_unconditional_C_MSE_FP32=mse(dc,truth),
            conditional_C_unconditional_D_MSE_FP32=mse(cd,truth),
            cond_branch_error_MSE=ec2,uncond_branch_error_MSE=eu2,
            branch_error_cosine=cross/math.sqrt(ec2*eu2) if ec2*eu2 else None,
            independently_weighted_error_energy=independent,signed_cross_energy=signed,
            cancellation_fraction=-signed/independent if independent else None,
            original_C_and_A_scalar_summary_reproduced=True))
        compact[(prompt,step)] = dict(D=tuple(v.clone() for v in selected['D']),
            C=tuple(v.clone() for v in selected['C']),xi=float(value['xi']),
            WC_C_guided_MSE_FP32=c_mse,A_PHASE_guided_MSE_FP32=a_mse)
        del value, selected, tensors, truth, C, A, dc, cd, ec, eu
    rows, extrapolated = [], []
    for source, target, lag in pairs:
        prompt, t, s = target['prompt'], target['step'], source['step']
        past, current = compact[(prompt,s)], compact[(prompt,t)]
        c, u = current['D']
        old_delta = past['D'][0]-past['D'][1]
        truth = guided(current['D'])
        held = c+7*old_delta
        unconditional = u+8*old_delta
        row = dict(prompt=prompt,source_step=s,target_step=t,actual_update_lag=lag,
            **delta_hold_error(past['D'],current['D'],current['C']),
            held_guided_MSE_FP32=mse(held,truth),
            unconditional_refresh_held_delta_MSE_FP32=mse(unconditional,truth),
            full_guided_output_hold_MSE_FP32=mse(guided(past['D']),truth),
            WC_C_guided_MSE_FP32=current['WC_C_guided_MSE_FP32'],
            A_PHASE_guided_MSE_FP32=current['A_PHASE_guided_MSE_FP32'],
            cond_temporal_drift_MSE=mse(c,past['D'][0]),
            uncond_temporal_drift_MSE=mse(u,past['D'][1]))
        rows.append(row)
        older_steps = [v for p,v in compact if p == prompt and 0 < s-v <= 2]
        if older_steps:
            older = compact[(prompt,max(older_steps))]
            denominator = past['xi']-older['xi']
            if denominator <= 0 or current['xi'] <= past['xi']:
                raise ValueError('Strict causal noise-coordinate order required')
            ratio = (current['xi']-past['xi'])/denominator
            older_delta = older['D'][0]-older['D'][1]
            predicted = old_delta+ratio*(old_delta-older_delta)
            extrapolated.append(dict(prompt=prompt,older_step=max(older_steps),source_step=s,
                target_step=t,actual_update_lag=lag,noise_coordinate_ratio=ratio,
                linear_delta_guided_MSE_FP32=mse(c+7*predicted,truth),
                held_guided_MSE_FP32=row['held_guided_MSE_FP32'],
                WC_C_guided_MSE_FP32=current['WC_C_guided_MSE_FP32'],
                A_PHASE_guided_MSE_FP32=current['A_PHASE_guided_MSE_FP32']))
    summaries = {str(lag): summarize([r for r in rows if r['actual_update_lag'] == lag],
                    'held_guided_MSE_FP32') for lag in (1,2)}
    return dict(schema='CARA_F19_REAL_B1_SAVED_CPU_DIAGNOSTICS_R2',
        status='COMPLETE_REAL_SAVED_SHARED25_TEACHER_TRACE_DIAGNOSTIC',
        manifest_sha256=manifest_sha256,states=12,independent_inputs=2,
        state_rows=state_rows,delta_hold_rows=rows,lag_summaries=summaries,
        same_state_summary={key:summarize(state_rows,key) for key in (
            'conditional_D_unconditional_C_MSE_FP32','conditional_C_unconditional_D_MSE_FP32')},
        linear_delta_extrapolation_rows=extrapolated,
        linear_delta_extrapolation_summary=summarize(extrapolated,'linear_delta_guided_MSE_FP32'),
        manifest_file_records=len(records)+len(manifest.get('unique_anchors',[])),
        original_scalar_checks_reproduced=24,CFG_coefficient=7,
        source_is_saved_shadow_D_not_deployed_refresh=True,parent_is_Shared25_C_not_F19=True,
        single_branch_cache_trajectory_validated=False,full36_D_target_coverage=False,
        actual_LPIPS=None,actual_GPU_speedup=None,GPU_submissions=0,
        GPU_screen_ready=False,endpoint_inference_or_rescoring=0)
