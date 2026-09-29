import pytest
import torch
from wcomr.measurement import StageTimes, BlockCounts


def test_wrapping_preserves_results_exception_and_restore():
    class Owner:
        def call(self, x, fail=False):
            if fail:
                raise ValueError('original error')
            return x
    owner = Owner()
    original = owner.call
    ticks = iter([1.0, 3.0, 4.0, 7.0])
    synced = []
    measurement = StageTimes(lambda: synced.append(True), lambda: next(ticks))
    measurement.wrap(owner, 'call', 'stage')
    value = object()
    assert owner.call(value) is value
    with pytest.raises(ValueError, match='original error'):
        owner.call(value, fail=True)
    assert measurement.values == {'stage': {'calls': 2, 'seconds': 5.0}}
    assert len(synced) == 4
    measurement.close()
    assert owner.call == original
    measurement.reset()
    assert measurement.values == {}


def test_counts_observe_actual_full_and_skipped_calls_without_changing_rng():
    blocks = torch.nn.ModuleList([torch.nn.Linear(3, 3), torch.nn.Linear(3, 3)])
    x = torch.ones(2, 3)
    expected = blocks[1](blocks[0](x))
    rng = torch.get_rng_state().clone()
    counts = BlockCounts(blocks)
    actual = blocks[1](blocks[0](x))
    blocks[0](x)  # a separate probe whose deep block is skipped
    assert torch.equal(expected, actual)
    assert torch.equal(rng, torch.get_rng_state())
    assert counts.result() == {'denoiser_calls': 2, 'full_calls': 1, 'skipped_deep_calls': 1}
    counts.reset()
    assert counts.result()['denoiser_calls'] == 0
    counts.close()
    blocks[0](x)
    assert counts.first == 0
