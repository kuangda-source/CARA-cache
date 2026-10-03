"""Startup integration must cover native default training=True, not only eval toys."""
import torch

from wcomr.h0_mode import establish_shared_eval, mode_snapshot, verify_shared_eval


def test_default_mode_setup_preserves_data_buffers_and_rng():
    model = torch.nn.Sequential(torch.nn.Linear(4, 4), torch.nn.LayerNorm(4))
    model.register_buffer('counter', torch.tensor(3))
    before = {k: v.detach().clone() for k, v in model.state_dict().items()}
    rng = torch.random.get_rng_state().clone()
    assert mode_snapshot(model)['training_modules'] == 3
    receipt = establish_shared_eval(model)
    assert receipt['after']['training_modules'] == 0
    assert all(torch.equal(before[k], v) for k, v in model.state_dict().items())
    assert torch.equal(rng, torch.random.get_rng_state())
    verify_shared_eval(model, receipt)
    assert establish_shared_eval(model)['after'] == receipt['after']


def test_train_override_rejected_before_any_mode_change():
    class Mutating(torch.nn.Linear):
        def train(self, mode=True):
            self.weight.data.zero_()
            return super().train(mode)
    model = torch.nn.Sequential(torch.nn.Linear(2, 2), Mutating(2, 2))
    flags = mode_snapshot(model)
    value = model[1].weight.detach().clone()
    try:
        establish_shared_eval(model)
    except ValueError as error:
        assert 'unreviewed train override' in str(error)
    else:
        raise AssertionError('Unsafe mode override accepted')
    assert flags == mode_snapshot(model)
    assert torch.equal(value, model[1].weight)


def test_native_topology_and_later_mode_drift_rejected():
    model = torch.nn.Sequential(torch.nn.Linear(2, 2))
    expected = mode_snapshot(model)['module_types']
    model.add_module('dropout', torch.nn.Dropout(.2))
    try:
        establish_shared_eval(model, expected)
    except ValueError as error:
        assert 'topology differs' in str(error)
    else:
        raise AssertionError('Changed native topology accepted')
    del model.dropout
    receipt = establish_shared_eval(model, expected)
    model[0].train()
    try:
        verify_shared_eval(model, receipt)
    except ValueError as error:
        assert 'mode or topology changed' in str(error)
    else:
        raise AssertionError('Later mode drift accepted')
