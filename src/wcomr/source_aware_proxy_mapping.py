"""Empirical creation-error mapping into a bound WC/RA probe scale.

This is a unit anchoring heuristic, not an error bound or a calibration of
future drift after P. It never supplies clean costs or installs a policy.
"""
import math
from statistics import median

from .cfg_ra_joint_control import finite_nonnegative, guided_proxy


def map_creation_error(*, scene, step, anchor, packets, rho,
                       C_guided_MSE, P_guided_MSE, mode):
    if (not isinstance(scene, str) or not scene or type(step) is not int
            or type(anchor) is not int or not 1 <= anchor < step <= 36
            or not isinstance(mode, str) or not mode
            or len(packets) != 2 or [p.get('slot') for p in packets] != [0, 1]
            or [p.get('counter') for p in packets] != [2*(step-1) % 70, (2*(step-1) % 70)+1]):
        raise ValueError('Bound same-state origin and ordered actual paid pair required')
    if (not finite_nonnegative(C_guided_MSE) or not finite_nonnegative(P_guided_MSE)):
        raise ValueError('Finite nonnegative actual post-RF guided MSE required')
    local = guided_proxy(packets[0]['delta_y'], packets[1]['delta_y'], rho)
    defined = C_guided_MSE > 0 and local > 0
    ratio = math.sqrt(P_guided_MSE/C_guided_MSE) if defined else None
    floor = local*ratio if defined else None
    if floor is not None and not finite_nonnegative(floor):
        raise ValueError('Nonfinite mapped creation prior')
    return {'scene': scene, 'step': step, 'anchor_before': anchor, 'mode': mode,
        'actual_C_guided_MSE': C_guided_MSE, 'actual_P_guided_MSE': P_guided_MSE,
        'conditional_paid_delta_y': packets[0]['delta_y'],
        'unconditional_paid_delta_y': packets[1]['delta_y'],
        'borrowed_dense_source_rho_prior': rho, 'C_local_WC_PAID_DELTA_Y_proxy': local,
        'relative_post_RF_guided_error_norm': ratio,
        'empirically_mapped_creation_floor_proxy': floor,
        'defined': defined, 'undefined_reason': None if defined else 'ZERO_C_MSE_OR_ZERO_C_PROXY',
        'units': 'WC_PAID_DELTA_Y', 'actual_RF_to_hidden_error_bound': False,
        'P_source_future_drift_measured': False}


def summarize_modes(rows, *, modes, origins):
    if (len(set(modes)) != len(modes) or len(set(origins)) != len(origins)
            or not modes or not origins
            or len(rows) != len(modes)*len(origins)
            or {(r['scene'],r['step'],r['mode']) for r in rows}
                != {(s,t,m) for s,t in origins for m in modes}):
        raise ValueError('Complete unique registered origins by modes required')
    summaries = []
    for mode in modes:
        selected = [r for r in rows if r['mode'] == mode]
        floors = [r['empirically_mapped_creation_floor_proxy'] for r in selected if r['defined']]
        if any(not finite_nonnegative(v) for v in floors):
            raise ValueError('Invalid mapped floor')
        complete = len(floors) == len(origins)
        value = median(floors) if complete else None
        summaries.append({'mode': mode, 'registered_origins': len(origins),
            'defined_origins': len(floors), 'complete_origin_denominator_preserved': complete,
            'median_mapped_creation_floor_proxy': value,
            'range_mapped_creation_floor_proxy': [min(floors),max(floors)] if floors else None,
            'positive_first_development_prior_available': value is not None and value > 0,
            'per_registered_step': [{'step': t, 'origins': len([r for r in selected if r['step'] == t]),
                'defined_origins': len([r for r in selected if r['step'] == t and r['defined']]),
                'individual_floor_proxy': [r['empirically_mapped_creation_floor_proxy']
                    for r in sorted(selected,key=lambda r:r['scene']) if r['step'] == t]}
                for t in sorted({t for _,t in origins})],
            'future_drift_ratio': None, 'clean_C_A_P_D_costs': None,
            'selected_for_production': False})
    return summaries
