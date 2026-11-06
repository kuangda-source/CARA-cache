"""Actual controller rejects malformed timing arms before phase preparation."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.selective_output import run_selective_output
from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy


def run(manifest):
    data = manifest['fixed_mask']
    mask = FixedRefreshMask(data['sample_name'], data['model_id'], data['condition_id'],
        tuple(data['dense_calls']), data['source_receipt_sha256'])
    context = ('CPU_TIMING_PREFLIGHT:human_199', data['model_id'], data['condition_id'])
    arms = {a['name']: a for a in manifest['arms']}
    layers = tuple(arms['E0L0']['policy']['sparse_layers'])
    def placement(slots, group=layers):
        return SparsePlacementPolicy(group, per_cfg_eligible_ordinals=tuple(tuple(v) for v in slots))
    policies = (SparseRefreshPolicy(layers, 2),) + tuple(
        placement(arms[n]['policy']['per_cfg_eligible_ordinals']) for n in ('E0L0', 'E1L1'))
    inference = SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(
        net=SimpleNamespace(probe_depth=2, blocks=[None] * 28))))
    sample = SimpleNamespace(name='human_199')
    checks = []
    cases = ('common_quota', 'both_quota', 'first_in_common', 'first_missing',
        'late_before_common', 'common_not_subset', 'out_of_range', 'wrong_layers',
        'wrong_legacy_cadence', 'periodic_new_arm', 'wrong_CFG', 'forecast_mode',
        'layer_mode', 'unknown_mode', 'bad_D_digest', 'bad_legacy_digest', 'existing_identity')
    for case in cases:
        chosen = list(policies); state = {}; comparison = 'timing_factorial'
        digest = legacy_digest = '4' * 64
        common = policies[1].per_cfg_eligible_ordinals
        both = policies[2].per_cfg_eligible_ordinals
        if case == 'common_quota': chosen[1] = placement((common[0][:-1], common[1]))
        elif case == 'both_quota': chosen[2] = placement((both[0][:-1], both[1]))
        elif case == 'first_in_common': chosen[1] = placement(((1,) + common[0][1:], common[1]))
        elif case == 'first_missing': chosen[2] = placement(((2,) + both[0][1:], both[1]))
        elif case == 'late_before_common': chosen[2] = placement(((1, 2) + common[0], both[1]))
        elif case == 'common_not_subset': chosen[2] = placement((both[0][:-2] + (9, 10), both[1]))
        elif case == 'out_of_range': chosen[2] = placement((both[0][:-1] + (100,), both[1]))
        elif case == 'wrong_layers': chosen[2] = placement(both, (2, 3, 5))
        elif case == 'wrong_legacy_cadence': chosen[0] = SparseRefreshPolicy(layers, 1)
        elif case == 'periodic_new_arm': chosen[1] = SparseRefreshPolicy(layers)
        elif case == 'wrong_CFG': chosen[1] = placement(common[::-1])
        elif case == 'forecast_mode': comparison = 'forecast_placement'
        elif case == 'layer_mode': comparison = 'layer_cadence'
        elif case == 'unknown_mode': comparison = 'unregistered'
        elif case == 'bad_D_digest': digest = 'bad-SHA'
        elif case == 'bad_legacy_digest': legacy_digest = 'bad-SHA'
        else: state = {'measurement': {'existing': 'preserve'}}
        before = deepcopy(state)
        saves = []
        try:
            run_selective_output(inference, sample, None, {}, mask, tuple(chosen),
                state=state, save=lambda: saves.append(True), output=Path('/NO_GENERATION'),
                inference_module=None, context=context, mode_setup=None, comparison=comparison,
                expected_D_sha256=digest, expected_full_S_sha256=legacy_digest)
        except ValueError as error:
            checks.append({'case': case, 'error': str(error), 'no_phase_started': state == before})
        else: raise AssertionError('Invalid timing preflight accepted: ' + case)
        assert state == before and not saves
    return {'status': 'TIMING_FACTORIAL_CURRENT_CONTROLLER_PREFLIGHT17_CPU_PASS',
        'CPU_only': True, 'checks': checks, 'actual_weights_or_video': False,
        'limits': 'Current controller guards with geometry/sample stubs; no asset, GPU or quality admission.'}
