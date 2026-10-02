from types import SimpleNamespace
import random
import numpy as np
import pytest
import torch
from wcomr.mid_coverage import StateRoundtrip, scope_gate, compare_prefix


def test_roundtrip_restores_both_cfg_histories_solver_extra_field_output_and_rng():
    value = torch.arange(8.).reshape(2, 4)
    net = SimpleNamespace(cnt=26, residual_cache=[value, value + 1], residual_window=[[value], [value + 2]])
    solver = SimpleNamespace(model_outputs=[value + 3, None], _step_index=13,
                             last_sample=value + 4, extra_mutable={'order': [1, 2]})
    method = lambda x: x
    solver.step = method
    generator = torch.Generator().manual_seed(12)
    saved = StateRoundtrip(net, solver, value, generators=[generator])
    before = saved.fingerprint()
    net.cnt = 1; net.residual_cache[0].add_(9)
    solver.model_outputs[0].zero_(); solver.extra_mutable['order'].append(3)
    solver.unexpected_field = True
    random.random(); np.random.random(); torch.rand(3)
    torch.rand(3, generator=generator)
    output = saved.restore()
    assert saved.fingerprint() == before and torch.equal(output, torch.arange(8.).reshape(2, 4))
    assert net.cnt == 26 and not hasattr(solver, 'unexpected_field')
    assert solver.step is method
    net.residual_cache[0].zero_()
    assert not torch.equal(net.residual_cache[0], saved.net_state['residual_cache'][0])


def test_new_card_does_not_accept_old_cap_extra_scope_inflight_or_exhaustion():
    base = {'cap_gpu_hours':12,'used_gpu_hours':3.9117525685110333,'budget_authorization_ref':'record'}
    scope_gate(base,1200)
    for change, seconds in [({'cap_gpu_hours':4},1200), ({},1201),
                            ({'other_inflight':{}},1200), ({'used_gpu_hours':11.9},1200),
                            ({'budget_authorization_ref':None},1200)]:
        with pytest.raises(ValueError):scope_gate(dict(base,**change),seconds)


def test_prefix_parity_refuses_cache_or_solver_drift():
    base = {k:[] for k in ['output_hashes','trace','block_counts','state_fingerprints','sampling']}
    assert all(compare_prefix(base,base).values())
    for k in base:
        with pytest.raises(ValueError):compare_prefix(base,dict(base,**{k:[1]}))
