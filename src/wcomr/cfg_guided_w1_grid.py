"""Scene-equal offline shared-alpha selection for the registered guided W1 grid.

Moments must come from same-state teacher/old/new velocity outputs. This module
does not collect them, run teachers online, fuse hidden features, or fit a router.
"""
from collections import defaultdict
import math


GRID = (0.0, 0.5, 1.0)


def select_shared_alpha(records):
    """Minimize E[mean(e_g^0 + alpha*q_g)^2], equally weighting scenes.

For each actual state, e_g^0 = 8*(v_c^0-v_c^F)-7*(v_u^0-v_u^F)
and q_g = 8*(v_c^1-v_c^0)-7*(v_u^1-v_u^0). Compute these guided
vectors before reducing their moments. Do not add two branch MSEs instead.
There is no branch regularizer or fitted continuous coefficient in this version.
"""
    if not records:
        return {'status': 'NO_CAL_MOMENTS_FALLBACK_ORIGINAL', 'selected_alpha': 0.0,
                'grid': list(GRID), 'scenes': 0, 'states': 0, 'grid_losses': [],
                'moments_are_same_state_teacher_proven': False}
    groups = defaultdict(list);identities = set()
    for record in records:
        scene, state = record['scene'], record['state']
        if not isinstance(scene, str) or not scene or not isinstance(state, str) or not state:
            raise ValueError('Explicit actual scene/state identities required')
        if (scene, state) in identities:
            raise ValueError('Repeated state is not an independent CAL observation')
        identities.add((scene, state))
        values = [record[k] for k in ('base_guided_MSE', 'guided_error_update_mean_dot', 'guided_update_mean_square')]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError('Finite same-coordinate guided moments required')
        e, dot, q = values
        if e < 0 or q < 0 or dot * dot > e * q + 1e-12 * max(1.0, e * q):
            raise ValueError('Guided moments violate squared-norm/Cauchy identity')
        groups[scene].append((e, dot, q))
    losses = []
    for alpha in GRID:
        scenes = []
        for scene in sorted(groups):
            values = [e + 2 * alpha * dot + alpha * alpha * q for e, dot, q in groups[scene]]
            # Cancellation can leave a tiny negative floating-point residual.
            # Preserve meaningful negative values as an error, never as a gain.
            if any(v < -1e-12 * max(1.0, e, q) for v, (e, _, q) in zip(values, groups[scene])):
                raise ValueError('Squared guided objective is meaningfully negative')
            scenes.append({'scene': scene, 'states': len(values),
                           'mean_guided_MSE': math.fsum(max(0.0, v) for v in values) / len(values)})
        losses.append({'alpha': alpha, 'scene_equal_guided_MSE': math.fsum(s['mean_guided_MSE'] for s in scenes) / len(scenes),
                       'per_scene': scenes})
    selected = min(losses, key=lambda row: (row['scene_equal_guided_MSE'], row['alpha']))
    return {'status': 'OFFLINE_GUIDED_MOMENT_GRID_SELECTION_NOT_DEPLOYMENT_OR_VIDEO_RESULT',
        'selected_alpha': selected['alpha'], 'grid': list(GRID), 'scenes': len(groups),
        'states': len(records), 'grid_losses': losses,
        'same_alpha_for_both_CFG_branches': True, 'actual_CFG_coefficients': [8, -7],
        'branch_regularizer': 0.0, 'scene_equal_weighting': True,
        'tie_break': 'SMALLEST_ALPHA_RETAINS_MORE_ORIGINAL_OUTPUT',
        'moments_are_same_state_teacher_proven': False}
