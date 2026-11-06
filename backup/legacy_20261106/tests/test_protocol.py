import json
from pathlib import Path
import pytest
from wcomr.protocol import validate_schedule


def test_approved_schedule_requires_actual_grid_counts_and_unchanged_wc_horizon():
    policy = json.loads((Path(__file__).parents[1] / 'manifests/f1_runtime_protocol.json').read_text())
    observation = {'scheduler_class': policy['scheduler_class'], 'requested_steps': 35,
                   'actual_schedule_steps': 36, 'timesteps': policy['timesteps'],
                   'use_kerras_sigma': True, 'worldcache_horizon': 70}
    counts = {'denoiser_calls': 72, 'full_calls': 42, 'skipped_deep_calls': 30}
    validate_schedule(observation, counts, policy, 'worldcache')
    with pytest.raises(RuntimeError, match='CFG count'):
        validate_schedule(observation, dict(counts, denoiser_calls=70), policy, 'worldcache')
    with pytest.raises(RuntimeError, match='horizon'):
        validate_schedule(dict(observation, worldcache_horizon=72), counts, policy, 'worldcache')
    with pytest.raises(RuntimeError, match='timesteps'):
        validate_schedule(dict(observation, timesteps=list(reversed(policy['timesteps']))), counts, policy, 'worldcache')
    with pytest.raises(RuntimeError, match='Native'):
        validate_schedule(observation, counts, policy, 'native')
