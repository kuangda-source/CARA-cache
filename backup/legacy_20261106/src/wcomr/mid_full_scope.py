"""Independent full104 scope and measured cost admission. No Torch import."""

def validate_full_scope(config):
    if (config['card'] != 'WC-MID-FULL-COVERAGE-R4-20261003-A'
            or config['max_gpu_wall_seconds'] != 1800
            or config['capture_calls'] != [25, 26, 35, 36]
            or config['capture_layers'] != list(range(2, 28))
            or config['stop_after_solver_steps'] != 18 or config['state_steps'] != [13, 18]
            or config['phases'] != ['baseline_prefix', 'observed_prefix']
            or config['policy'] != {'sim': .1, 'cdf': .98}
            or config['warmups'] != 1 or config['repeats'] != 3
            or config['pv_skipping'] is not False or config['deployment_sparse'] is not False):
        raise ValueError('Independent full104/strict nine-gate scope changed')
    return {(c, l) for c in config['capture_calls'] for l in config['capture_layers']}


def cost_gate(config):
    estimate = config['cost_admission']
    if (estimate['planning_envelope_seconds'] + estimate['shutdown_settlement_margin_seconds']
            > config['max_gpu_wall_seconds']):
        raise ValueError('Measured full104 cost envelope exceeds independent1800s cap; no GPU submission')
