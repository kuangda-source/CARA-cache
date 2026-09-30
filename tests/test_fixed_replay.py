import copy
import types
import pytest
import torch
from wcomr.fixed_replay import FixedReplay, build_replay_forward
from wcomr.measurement import BlockCounts
from wcomr.shadow_forward import ShadowProbe
from test_integration import model, run, upstream


def measured(net, count):
    counts = BlockCounts(net.blocks, cache_model=net)
    try:
        outputs = run(net, count)
        return outputs, copy.deepcopy(counts.trace)
    finally:
        counts.close()


def install(net, replay):
    net.forward = types.MethodType(build_replay_forward(upstream()['worldcache_mini_train_dit_forward'], replay), net)


def test_official_replay_preserves_outputs_trace_and_rng_with_horizon_reset():
    expected, trace = measured(model(), 22)
    replay = FixedReplay(trace); replay.begin_request('official')
    net = model(); install(net, replay)
    rng = torch.random.get_rng_state().clone()
    outputs, actual = measured(net, 22)
    assert all(torch.equal(a, b) for a, b in zip(expected, outputs))
    assert actual == trace and torch.equal(rng, torch.random.get_rng_state())
    assert replay.finish()['mode'] == 'official' and replay.cycle == 2
    with pytest.raises(RuntimeError, match='exhausted'):
        run(net, 1)


def test_scalar_uses_explicit_recent_params_own_full_anchors_and_fixed_schedule():
    expected, trace = measured(model(), 20)
    replay = FixedReplay(trace, 'scalar', {'decay': 0, 'ridge': 1e-6})
    replay.begin_request('scalar')
    # A negative threshold would naturally compute every step, but the frozen
    # reference schedule must still be replayed exactly.
    net = model(threshold=-1); install(net, replay)
    outputs, actual = measured(net, 20)
    assert actual == trace
    assert any(not torch.equal(a, b) for a, b in zip(expected, outputs))
    records = replay.finish()['records']
    assert any(r['natural_skip'] is False and not r['planned_full'] for r in records)
    assert all(r['prediction']['reason'] == 'scalar' and
               all(step < r['cache_counter_before'] for step in r['prediction']['history']['anchor_steps'])
               for r in records if not r['planned_full'])
    assert replay.params['decay'] == 0
    # Reset is explicit; no anchors from the previous request survive.
    net.cnt = 0; replay.begin_request('next'); run(net, 1)
    assert replay.calibrators[0].receipt()['anchor_steps'] == [0]
    assert not replay.calibrators[1].anchors


def test_replay_fail_closed_on_counter_expert_early_skip_or_incomplete_request():
    _, trace = measured(model(), 20)
    replay = FixedReplay(trace); replay.begin_request('bad-counter')
    net = model(); install(net, replay); net.cnt = 1
    with pytest.raises(RuntimeError, match='counter'):
        run(net, 1)
    replay.begin_request('expert'); net.cnt = 0; run(net, 1); net._w1_expert_key = 'changed'
    with pytest.raises(RuntimeError, match='expert'):
        run(net, 1)
    with pytest.raises(RuntimeError, match='incomplete'):
        replay.finish()
    trace[0]['deep_executed'] = False
    replay = FixedReplay(trace); replay.begin_request('impossible'); net = model(); install(net, replay)
    with pytest.raises(RuntimeError, match='Execution differs'):
        run(net, 1)


@pytest.mark.parametrize('mode', ['official', 'scalar'])
def test_shadow_invariance_on_own_replay_trajectory_and_cache_after_horizon_reset(mode):
    _, trace = measured(model(), 22)
    nets = [model().eval(), model().eval()]
    controllers = [FixedReplay(trace, mode, {'decay': 0}) for _ in nets]
    probe = ShadowProbe([8, 9, 10, 11, 12]); probe.begin_request('own')
    for i, (net, controller) in enumerate(zip(nets, controllers)):
        controller.begin_request('own')
        net.forward = types.MethodType(build_replay_forward(upstream()['worldcache_mini_train_dit_forward'],
            controller, probe if i == 1 else None), net)
    results = []
    rng = torch.random.get_rng_state().clone()
    # The next input depends on each arm's own previous output, not a stored
    # official latent sequence. Shadow remains score-only in this closed loop.
    for net in nets:
        counts = BlockCounts(net.blocks, cache_model=net)
        x = torch.ones(1, 2, 2, 2, 3)
        outputs = []
        try:
            for _ in range(22):
                x = net(x, torch.ones(1), torch.ones(1)) * .98
                outputs.append(x.clone())
            results.append((outputs, copy.deepcopy(counts.trace)))
        finally:
            counts.close()
    assert all(torch.equal(a, b) for a, b in zip(results[0][0], results[1][0]))
    assert results[0][1] == results[1][1] == trace
    assert controllers[0].finish() == controllers[1].finish()
    assert torch.equal(rng, torch.random.get_rng_state())
    for field in ['residual_cache', 'probe_residual_cache', 'previous_input', 'previous_output', 'previous_internal_states']:
        for a, b in zip(getattr(nets[0], field), getattr(nets[1], field)):
            assert (a is None and b is None) or torch.equal(a, b)
    assert [r['call'] for r in probe.records] == [8, 9, 10, 11, 12]
    assert all(r['metrics']['velocity']['status'] == 'OK' for r in probe.records)
    probe.begin_request('different'); controllers[1].begin_request('own')
    with pytest.raises(RuntimeError, match='identities differ'):
        run(nets[1], 1)
