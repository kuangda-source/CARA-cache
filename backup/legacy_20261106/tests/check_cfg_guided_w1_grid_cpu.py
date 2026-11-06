"""Check guided coupling and unequal per-scene state counts with scalar controls."""
import importlib.util
import math
from pathlib import Path


def main():
    spec = importlib.util.spec_from_file_location('guided_grid', Path(__file__).parents[1] / 'src/wcomr/cfg_guided_w1_grid.py')
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def moment(scene, state, ec, eu, qc, qu):
        eg, qg = 8 * ec - 7 * eu, 8 * qc - 7 * qu
        return {'scene': scene, 'state': state, 'base_guided_MSE': eg * eg,
            'guided_error_update_mean_dot': eg * qg, 'guided_update_mean_square': qg * qg}
    # Both branch errors improve at alpha=1, but their guided error grows.
    coupling = moment('coupled', 'one', 1, 1, -1, -.5)
    assert (1 - 1) ** 2 < 1 and (1 - .5) ** 2 < 1
    a = module.select_shared_alpha([coupling]);assert a['selected_alpha'] == 0
    assert a['grid_losses'][-1]['scene_equal_guided_MSE'] > a['grid_losses'][0]['scene_equal_guided_MSE']
    half = moment('shared', 'one', 1, 1, -.4, -1.2 / 7)
    b = module.select_shared_alpha([half]);assert b['selected_alpha'] == .5
    assert math.isclose(b['grid_losses'][1]['scene_equal_guided_MSE'], 0, abs_tol=1e-12)
    # Four states from one scene must not outvote the other scene's one state.
    many = [moment('many', str(i), .125, 0, -.125, 0) for i in range(4)]
    one = moment('one', '0', 0, 0, .25, 0)
    equal = module.select_shared_alpha(many + [one]);assert equal['selected_alpha'] == 0
    pooled = [sum(r['base_guided_MSE'] + 2 * alpha * r['guided_error_update_mean_dot'] + alpha ** 2 * r['guided_update_mean_square'] for r in many + [one]) / 5 for alpha in module.GRID]
    assert module.GRID[pooled.index(min(pooled))] == .5
    assert module.select_shared_alpha([])['selected_alpha'] == 0
    flat = moment('flat', '0', .125, 0, 0, 0)
    assert module.select_shared_alpha([flat])['selected_alpha'] == 0
    refused = []
    for name, records in [('duplicate', [half, half]), ('nonfinite', [{**half, 'guided_update_mean_square': float('nan')}]),
            ('negative_norm', [{**half, 'base_guided_MSE': -1}]),
            ('incompatible_moments', [{**half, 'guided_error_update_mean_dot': 10}])]:
        try:module.select_shared_alpha(records)
        except ValueError:refused.append(name)
        else:raise AssertionError('Invalid CAL moments accepted: ' + name)
    print({'status': 'SYNTHETIC_SCALAR_GUIDED_GRID_CPU_CONTROLS_ONLY_NOT_REAL_CALIBRATION',
        'branch_improvement_can_harm_guided_error': True, 'shared_half_optimum': b['selected_alpha'],
        'scene_equal_selection': equal['selected_alpha'], 'pooled_selection_would_differ': .5,
        'empty_or_zero_update_fallback_original': True, 'refusals': refused,
        'Torch_imported': False, 'GPU_submissions': 0, 'deployment_installed': False})


if __name__ == '__main__':
    main()
