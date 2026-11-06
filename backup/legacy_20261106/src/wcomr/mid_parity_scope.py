"""Independent r3 technical gate. No Torch import during scope validation."""
def validate_parity_scope(config):
    if (config['card'] != 'WC-INPUT-STATE-PARITY-R3-20261003-A'
            or config['max_gpu_wall_seconds'] != 1200
            or config['capture_calls'] != [25, 26] or config['capture_layers'] != [2]
            or config['stop_after_solver_steps'] != 13 or config['state_steps'] != [13]
            or config['phases'] != ['baseline_prefix', 'observed_prefix']
            or config['policy'] != {'sim': .1, 'cdf': .98}
            or config['warmups'] != 1 or config['repeats'] != 3
            or config['pv_skipping'] is not False or config['deployment_sparse'] is not False):
        raise ValueError('r3 shortest-prefix/real-observer scope changed')
    return {(c, l) for c in config['capture_calls'] for l in config['capture_layers']}
