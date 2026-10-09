"""Fit a explicitly coarse prior from complete raw same-state calibration.

No synthetic correlation or propagation constants fill unmeasured labels.
The deployed grid is an estimated prior, not an observed anchor/step table.
"""
import hashlib
import json
import math
from statistics import median

import torch

from .cfg_ra_calibration import TARGET_STEPS, ORIGIN_ANCHORS
from .cfg_ra_joint_control import Calibration


def statistics(cc, dd):
    keys = {'conditional', 'unconditional', 'guided', 'final_latent'}
    if set(cc) != keys or set(dd) != keys:
        raise ValueError('Complete two raw four-tensor calibration artifacts required')
    for values in (cc, dd):
        shape = values['guided'].shape
        if (any(v.dtype != torch.float32 or v.shape != shape
                or not bool(torch.isfinite(v).all()) for v in values.values())
                or not torch.equal(values['guided'], values['conditional']+7*(values['conditional']-values['unconditional']))):
            raise ValueError('Actual full FP32 geometry/CFG arithmetic differs')
    ec = (cc['conditional'].double()-dd['conditional'].double()).flatten()
    eu = (cc['unconditional'].double()-dd['unconditional'].double()).flatten()
    eg = (cc['guided'].double()-dd['guided'].double()).flatten()
    endpoint = (cc['final_latent'].double()-dd['final_latent'].double()).flatten()
    nc, nu, ng, ne = [float(torch.linalg.vector_norm(v)) for v in (ec, eu, eg, endpoint)]
    rho = max(-1., min(1., float(torch.dot(ec, eu))/(nc*nu))) if nc > 0 and nu > 0 else None
    gain = ne/ng if ng > 0 else None
    return {'conditional_error_norm': nc, 'unconditional_error_norm': nu,
        'actual_guided_error_norm': ng, 'final_latent_difference_norm': ne,
        'rho': rho, 'gain': gain, 'undefined_rho': rho is None, 'undefined_gain': gain is None,
        'error_space': 'ACTUAL_POST_RF_DENOISE_VELOCITY',
        'gain_definition': 'L2(final_CC-final_DD)/L2(actual_guided_CC-actual_guided_DD)',
        'gain_includes_actual_timestep_and_complete_UniPC_suffix': True,
        'video_quality_or_future_time_label': False}


def fit_table(rows, *, sample_names, fingerprint_context, toy=False):
    if (type(sample_names) not in (list, tuple) or len(sample_names) != 2
            or len(set(sample_names)) != 2 or not all(type(n) is str and n for n in sample_names)
            or not fingerprint_context or type(toy) is not bool):
        raise ValueError('Two explicit calibration scenes and source context required')
    expected = {(n, t) for n in sample_names for t in TARGET_STEPS}
    if (len(rows) != 6 or {(r['sample_name'], r['target_step']) for r in rows} != expected
            or any(r['shared_anchor'] != ORIGIN_ANCHORS[r['target_step']]
                   or r['reuse_age'] != r['target_step']-r['shared_anchor']
                   or not r['raw_artifacts_independently_reloaded'] for r in rows)):
        raise ValueError('Complete six-origin scope and raw measurements required')
    correlations = []
    by_time = {t: [] for t in TARGET_STEPS}
    for r in rows:
        rho, gain = r['statistics']['rho'], r['statistics']['gain']
        if rho is not None:
            if not isinstance(rho, (int, float)) or not math.isfinite(rho) or not -1 <= rho <= 1:
                raise ValueError('Invalid actual correlation')
            correlations.append(float(rho))
        if gain is not None:
            if not isinstance(gain, (int, float)) or not math.isfinite(gain) or gain < 0:
                raise ValueError('Invalid actual propagation gain')
            by_time[r['target_step']].append(float(gain))
    if not correlations or any(not values for values in by_time.values()):
        raise ValueError('Coarse prior requires observed correlation and gain at every registered stage')
    rho_prior = median(correlations)
    stage_gain = {t: median(v) for t, v in by_time.items()}
    def interpolate(t):
        if t <= TARGET_STEPS[0]: return stage_gain[TARGET_STEPS[0]]
        if t >= TARGET_STEPS[-1]: return stage_gain[TARGET_STEPS[-1]]
        for a, b in zip(TARGET_STEPS, TARGET_STEPS[1:]):
            if a <= t <= b:
                return stage_gain[a]+(stage_gain[b]-stage_gain[a])*(t-a)/(b-a)
        raise AssertionError('Interpolation stage missing')
    gains = {t: interpolate(t) for t in range(1, 37)}
    cells = {(a, t): rho_prior for a in range(1, 36) for t in range(a+1, min(a+6, 36)+1)}
    payload = {'protocol': 'COSMOS_SHARED_D6_COARSE_CAL_R1', 'source_context': fingerprint_context,
        'toy_only_not_Cosmos_calibration': toy, 'observed_rows': rows,
        'rho_aggregation': 'equal-origin median over defined six-origin measurements',
        'rho_prior': rho_prior, 'defined_rho_count': len(correlations),
        'gain_aggregation': 'per-stage median over defined two-scene measurements',
        'stage_gain': {str(t): v for t, v in stage_gain.items()},
        'defined_gain_count_by_stage': {str(t): len(v) for t, v in by_time.items()},
        'gain_interpolation': 'linear in logical step; nearest measured stage outside [13,33]',
        'gains': {str(t): g for t, g in gains.items()},
        'rho_at': [{'anchor': a, 'step': t, 'rho': rho, 'estimated_prior_not_observed_cell': True}
                   for (a, t), rho in cells.items()],
        'maximum_estimated_reuse_age': 6, 'missing_or_older_cells_action': 'DD',
        'observed_age_and_stage_confounded': True,
        'endpoint_latent_calibration_not_quality_or_time_result': True,
        'paid_proxy_definition': 'WC_PAID_DELTA_Y', 'guided_weights': [8, -7]}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return Calibration(fingerprint, cells, gains), {**payload, 'fingerprint': fingerprint}


def load_table(payload, *, permit_toy=False):
    raw = dict(payload)
    fingerprint = raw.pop('fingerprint')
    actual = hashlib.sha256(json.dumps(raw, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if (actual != fingerprint or raw['protocol'] != 'COSMOS_SHARED_D6_COARSE_CAL_R1'
            or raw['toy_only_not_Cosmos_calibration'] and not permit_toy):
        raise ValueError('Source-bound real calibration table required')
    cal, rebuilt = fit_table(raw['observed_rows'],
        sample_names=sorted({r['sample_name'] for r in raw['observed_rows']}),
        fingerprint_context=raw['source_context'], toy=raw['toy_only_not_Cosmos_calibration'])
    if rebuilt != payload:
        raise ValueError('Calibration estimates disagree with the actual observation rows')
    return cal
