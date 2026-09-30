"""Validate the explicitly approved public-code sampling protocol."""


def validate_schedule(observed, counts, policy, mode):
    pairs = {'scheduler_class': 'scheduler_class', 'requested_steps': 'requested_steps',
             'actual_schedule_steps': 'actual_steps', 'timesteps': 'timesteps',
             'use_kerras_sigma': 'use_kerras_sigma'}
    for actual, expected in pairs.items():
        if observed[actual] != policy[expected]:
            raise RuntimeError(f'Frozen sampling protocol mismatch: {actual}')
    if counts['denoiser_calls'] != policy['cfg_calls']:
        raise RuntimeError(f'CFG count mismatch: {counts}')
    if mode == 'native' and counts['skipped_deep_calls']:
        raise RuntimeError('Native unexpectedly skipped deep computation')
    if mode == 'worldcache' and observed['worldcache_horizon'] != policy['worldcache_horizon']:
        raise RuntimeError('WorldCache public-code horizon changed')
