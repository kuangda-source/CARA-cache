"""One offline shared shrink of the existing post-RF phase A proposal.

The measured proposal already uses alpha 1/.5. Its moments are not divided by
that alpha or claimed to recover a different FP32 output. No online teacher,
branch parameter, router, model install or video objective is introduced here.
"""
import hashlib
import json
import math

from .action_cost_ranking import ORIGINS

MODES = ('A_W1_ONE_PHASE', 'A_BETA1_ONE_PHASE')
RELATIVE_RIDGE = .1
MIN_RELATIVE_UPDATE_ENERGY = 1e-12


def fit_shared_shrink(records, *, mode, source_sha256):
    if (mode not in MODES or type(records) is not list or len(records) != 8
            or type(source_sha256) is not str or len(source_sha256) != 64
            or any(c not in '0123456789abcdef' for c in source_sha256)):
        raise ValueError('Complete eight-origin registered phase A proposal required')
    parsed = {}
    for record in records:
        if type(record) is not dict:
            raise ValueError('Structured same-state moments required')
        key = (record.get('scene'), record.get('state'))
        origins = [(s, 'step'+str(t)) for s, t in ORIGINS]
        if key not in origins or key in parsed:
            raise ValueError('Missing, duplicate or foreign CAL origin')
        if record.get('diagnostics', {}).get('actual_CFG_coefficients') != [8, -7]:
            raise ValueError('Actual combined CFG moment coordinates required')
        e, b, q = [record[k] for k in ('base_guided_MSE',
            'guided_error_update_mean_dot', 'guided_update_mean_square')]
        if (any(type(x) not in (int, float) or not math.isfinite(x) for x in (e,b,q))
                or e < 0 or q < 0
                or b*b > e*q + 1e-12*max(1., e*q)):
            raise ValueError('Finite squared-norm and Cauchy moments required')
        parsed[key] = (e,b,q)
    order = [(s, 'step'+str(t)) for s,t in ORIGINS]
    e,b,q = [math.fsum(parsed[o][i] for o in order)/8 for i in range(3)]
    small = q <= MIN_RELATIVE_UPDATE_ENERGY*max(e, 1e-30)
    shrink = 0. if small else min(1., max(0., -b/((1+RELATIVE_RIDGE)*q)))
    rows = []
    for origin in order:
        e0,b0,q0 = parsed[origin]
        def loss(k):
            value = math.fsum((e0, 2*k*b0, k*k*q0))
            if value < -1e-12*max(1.,e0,q0):
                raise ValueError('Meaningfully negative squared guided loss')
            return max(0., value)
        rows.append({'scene':origin[0], 'state':origin[1],
            'original_C_guided_MSE':e0, 'registered_phase_A_guided_MSE':loss(1.),
            'fitted_shrink_guided_MSE':loss(shrink),
            'C_minus_fitted_guided_MSE':e0-loss(shrink),
            'phase_A_minus_fitted_guided_MSE':loss(1.)-loss(shrink)})
    fingerprint = hashlib.sha256(json.dumps({'mode':mode, 'source':source_sha256,
        'records':records, 'relative_ridge':RELATIVE_RIDGE,
        'minimum_relative_update_energy':MIN_RELATIVE_UPDATE_ENERGY},
        sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()
    return {'status':'OFFLINE_PHASE_A_SHARED_SHRINK_NOT_DEPLOYED_OR_VIDEO_RESULT',
        'mode':mode, 'source_sha256':source_sha256, 'fingerprint':fingerprint,
        'shared_shrink':shrink, 'effective_shared_alpha_early':shrink,
        'effective_shared_alpha_late':.5*shrink,
        'registered_phase_boundary_step':25, 'relative_ridge':RELATIVE_RIDGE,
        'minimum_relative_update_energy':MIN_RELATIVE_UPDATE_ENERGY,
        'fallback_original_due_to_small_update':small,
        'scene_and_step_equal_base_MSE':e, 'mean_error_update_dot':b,
        'mean_update_square':q, 'all_eight_origin_losses':rows,
        'scene_and_step_equal_fitted_guided_MSE':math.fsum(
            r['fitted_shrink_guided_MSE'] for r in rows)/8,
        'same_shrink_for_both_CFG_branches':True,
        'per_branch_regularizer_or_coefficient_not_fitted':True,
        'measured_phase_proposal_not_rescaled_to_full_strength':True,
        'supplied_moments_same_state_teacher_proven_by_this_function':False,
        'GPU_submissions':0, 'model_parameters_changed':False,
        'endpoint_or_generalization_or_clean_latency_claim':False}
