"""Source-bound real action costs and P creation floors for the fixed sampler.

This factory does not install models, fit future P drift, replay a real adaptive
trajectory or create a GPU card. Dense-control routing has a declared ordering
override; its artificial C cost must never be reported as a measured latency.
"""
from dataclasses import asdict, replace
import hashlib
import json
import math

from .action_cost_ranking import ActionCostRanking, BOUNDARY
from .cfg_ra_joint_control import Calibration
from .source_aware_phase_control import CreationPhasePrior
from .source_aware_working_epoch_control_r2 import STRATEGIES

METHODS = ('SOURCE_RA', 'DYNAMIC_NO_P', 'CPD', 'REF_CPD', 'A_CPD_OFF',
           'A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE', 'DENSE_CONTROL')
FINGERPRINT = '9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a'
THRESHOLD = 0.070744235098772


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def build_parameters(calibration, ranking, floors, *, strategy, floor_source_sha256):
    if (not isinstance(calibration, Calibration) or calibration.fingerprint != FINGERPRINT
            or not isinstance(ranking, ActionCostRanking)
            or ranking.source_kind != 'INDEPENDENTLY_CAPTURED_REAL_FULL_ACTION_COST_CARD'
            or ranking.boundary != BOUNDARY or strategy not in STRATEGIES
            or type(floor_source_sha256) is not str or len(floor_source_sha256) != 64
            or any(c not in '0123456789abcdef' for c in floor_source_sha256)):
        raise ValueError('Current actual calibration, complete costs and bound working strategy required')
    if (floors.get('status') != 'REAL_COMPLETE_CREATION_PHASE_PRIOR_BOUND_NOT_INSTALLED_OR_FUTURE_DRIFT'
            or floors.get('RA_calibration_fingerprint') != FINGERPRINT
            or floors.get('complete_registered_origins') != 8
            or floors.get('complete_registered_mode_rows') != 48
            or floors.get('original_timed_values') != 144
            or floors.get('fixed_P_mode') != 'ROTATION_050'
            or floors.get('creation_phase_boundary') != 25
            or floors.get('borrowed_D_drift_ratio_assumption') != 1
            or floors.get('maximum_consecutive_P') != 2
            or floors.get('P_future_drift_empirically_calibrated') is not False
            or floors.get('model_or_controller_installed') is not False
            or floors.get('positive_complete_phase_prior_available') is not True):
        raise ValueError('Complete positive phase creation floor with explicit transfer role required')
    phase = floors['phase_priors']
    if set(phase) != {'12', '30'}:
        raise ValueError('Both fixed sampled creation phases required')
    for step in ('12', '30'):
        rows = phase[step]['all_four_origins']
        if (phase[step]['complete_defined_denominator'] is not True or len(rows) != 4
                or len({r['scene'] for r in rows}) != 4
                or any(r['step'] != int(step) or r['mode'] != 'ROTATION_050'
                       or r['defined'] is not True for r in rows)):
            raise ValueError('Complete four-scene creation-phase denominator required')
    global_floor = floors['all_eight_origin_global_floor_control']
    early, late = [phase[t]['median_creation_floor_proxy'] for t in ('12', '30')]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
           for v in (global_floor, early, late)):
        raise ValueError('Strictly positive complete creation floors required')
    binding = {'RA_calibration_fingerprint': calibration.fingerprint,
        'threshold': THRESHOLD, 'ranking_fingerprint': ranking.fingerprint,
        'floor_source_sha256': floor_source_sha256, 'P_mode': 'ROTATION_050',
        'early_floor': early, 'late_floor': late, 'global_floor_control': global_floor,
        'phase_boundary': 25, 'borrowed_D_drift_ratio': 1.,
        'maximum_consecutive_P': 2, 'P_future_drift_empirically_calibrated': False}
    prior = CreationPhasePrior(digest(binding), global_floor, 1.,
        early_creation_floor=early, late_creation_floor=late, boundary=25)
    c = ranking.for_reuse_mode('C')
    no_p = replace(c, P=None, fingerprint=digest({'role': 'NO_P_ACTUAL_C_D',
        'measured_cost_fingerprint': c.fingerprint}))
    # This explicit control forces actual D even when a zero proxy permits C.
    # Only this route uses an ordering override; the measured table is intact.
    dense = replace(c, C=2*c.D, P=None, fingerprint=digest({
        'role': 'DENSE_CONTROL_ORDERING_OVERRIDE_NOT_MEASURED_C_TIME',
        'measured_cost_fingerprint': c.fingerprint}))
    specs = {}
    for method in METHODS:
        cost, p = c, prior
        if method in ('SOURCE_RA', 'DYNAMIC_NO_P'):
            cost, p = no_p, None
        elif method == 'DENSE_CONTROL':
            cost, p = dense, None
        elif method == 'A_CPD_W1_ONE_PHASE':
            cost = ranking.for_reuse_mode('A_W1_ONE_PHASE')
        elif method == 'A_CPD_BETA1_ONE_PHASE':
            cost = ranking.for_reuse_mode('A_BETA1_ONE_PHASE')
        specs[method] = {'threshold': THRESHOLD, 'costs': cost,
            'partial_prior': p, 'working_epoch_strategy': strategy}
    evidence = {**binding, 'strategy': strategy,
        'parameter_binding_fingerprint': digest({**binding, 'strategy': strategy}),
        'all_eight_methods': {m: {'threshold': v['threshold'], 'costs': asdict(v['costs']),
            'partial_prior': None if v['partial_prior'] is None else asdict(v['partial_prior']),
            'working_epoch_strategy': strategy} for m, v in specs.items()},
        'cost_boundary': BOUNDARY, 'cost_role': 'ACTION_ORDER_ONLY_NOT_TOTAL_PAIR_OR_END_TO_END_TIME',
        'dense_control_ordering_override_not_measured_C_cost': True,
        'P_or_C_updates_actual_D_calibration_anchor': False,
        'future_P_drift_fitted': False, 'online_teacher_calls': 0,
        'shared_A_phase_boundary': 25, 'shared_A_strength': [1., .5],
        'model_or_controller_installed': False}
    return specs, evidence
