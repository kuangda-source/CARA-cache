"""Provenance, same-CFG age, inference-mode and truth isolation controls."""
from types import SimpleNamespace

import torch

from wcomr.h1_reference import HeldReference, ReferenceIdentity
from wcomr.mid_coverage import tree_digest


def fixture(kind='dense', branch=0):
    value = torch.arange(24, dtype=torch.float32).reshape(1, 2, 2, 2, 3) / 24 + .1
    identity = ReferenceIdentity('request', 'model', 'condition', branch, (2, 28),
                                 17, 33 + branch, kind)
    reference = HeldReference(identity, prior_dense_counter=22 + branch,
        prior_residual=value, prior_probe_residual=value * .2,
        residual=value * 2, probe_residual=value * .3,
        deployment_full_verified=kind == 'dense')
    net = SimpleNamespace(cnt=34 + branch, previous_internal_states=[value, value],
        previous_input=[value, value], residual_cache=[value, value],
        residual_window=[[value, value], [value, value]],
        probe_residual_window=[[value, value], [value, value]],
        worldcache_osi_enabled=True, worldcache_flow_enabled=False,
        worldcache_flow_scale=1)
    reference.bind_policy(net)
    return reference, net, value


def test_private_prediction_never_writes_deployed_windows_or_rng():
    for kind in ('dense', 'matched_full', 'sparse'):
        reference, net, value = fixture(kind)
        before = tree_digest(vars(net))
        rng = torch.random.get_rng_state().clone()

        def predictor(proxy, original, probe, branch):
            proxy.previous_input[branch] = original + 3
            proxy.previous_internal_states[branch] = probe + 4
            assert len(proxy.residual_window[branch]) == 2
            return original + proxy.residual_cache[branch]

        output = reference.predict(net, predictor, original_input=value, probe=value,
            solver_step=18, context=('request', 'model', 'condition', 0, (2, 28)))
        assert torch.equal(output, value + reference.values[2])
        assert before == tree_digest(vars(net))
        assert torch.equal(rng, torch.random.get_rng_state())
        assert not reference.provenance()['inserted_into_online_cache_or_calibrator']
        assert reference.provenance()['source_is_approximate'] == (kind != 'dense')
        reference.check_immutable(digest=True)


def test_context_cfg_and_age_drift_fail_before_predictor():
    reference, net, value = fixture()
    called = []
    predictor = lambda *args: called.append(1)
    base = ('request', 'model', 'condition', 0, (2, 28))
    for context in [('other', *base[1:]), ('request', 'other', *base[2:]),
                    ('request', 'model', 'other', *base[3:]),
                    (*base[:3], 1, base[4]), (*base[:4], (2, 14))]:
        try:
            reference.predict(net, predictor, original_input=value, probe=value,
                              solver_step=18, context=context)
        except ValueError:
            pass
        else:
            raise AssertionError('Mismatched provenance accepted')
    for step, counter in ((17, 32), (22, 42), (18, 35)):
        net.cnt = counter
        try:
            reference.predict(net, predictor, original_input=value, probe=value,
                              solver_step=step, context=base)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid same-CFG age accepted')
    assert not called


def test_approximate_source_cannot_claim_dense_and_prior_must_be_past():
    reference, _, value = fixture()
    for kind, verified, prior in (('sparse', True, 22), ('matched_full', True, 22),
                                  ('dense', False, 22), ('dense', True, 32),
                                  ('dense', True, 23)):
        identity = ReferenceIdentity('r', 'm', 'c', 0, (2, 28), 17, 33, kind)
        try:
            HeldReference(identity, prior_dense_counter=prior,
                prior_residual=value, prior_probe_residual=value,
                residual=value, probe_residual=value, deployment_full_verified=verified)
        except ValueError:
            pass
        else:
            raise AssertionError('False dense/past provenance accepted')


def test_reference_mutation_and_policy_change_are_rejected():
    reference, net, value = fixture()
    net.worldcache_flow_enabled = True
    try:
        reference.predict(net, lambda *x: None, original_input=value, probe=value,
            solver_step=18, context=('request', 'model', 'condition', 0, (2, 28)))
    except ValueError:
        pass
    else:
        raise AssertionError('Changed common policy accepted')
    reference.values[2].add_(.1)
    try:
        reference.check_immutable()
    except ValueError:
        pass
    else:
        raise AssertionError('Mutated reference accepted')


def test_outer_inference_mode_keeps_versioned_private_snapshots():
    with torch.inference_mode():
        reference, net, value = fixture('sparse', branch=1)
        assert all(not tensor.is_inference() for tensor in reference.values)
        output = reference.predict(net, lambda n, x, p, b: x + n.residual_cache[b],
            original_input=value, probe=value, solver_step=18,
            context=('request', 'model', 'condition', 1, (2, 28)))
        assert torch.isfinite(output).all()
        reference.check_immutable(digest=True)


def test_integer_identity_age_and_one_time_policy_contract():
    from dataclasses import replace
    reference, net, value = fixture()
    for identity in (replace(reference.identity, solver_step=17.0),
                     replace(reference.identity, source_call=33.0),
                     replace(reference.identity, cfg_slot=False),
                     replace(reference.identity, group=(True, 28))):
        try:
            identity.validate()
        except ValueError:
            pass
        else:
            raise AssertionError('Noncanonical identity accepted')
    for cap in (False, 0, 4.0):
        try:
            HeldReference(reference.identity, prior_dense_counter=22,
                prior_residual=value, prior_probe_residual=value,
                residual=value, probe_residual=value,
                deployment_full_verified=True, max_age=cap)
        except ValueError:
            pass
        else:
            raise AssertionError('Noninteger or invalid age cap accepted')
    try:
        reference.bind_policy(net)
    except ValueError:
        pass
    else:
        raise AssertionError('Previously frozen policy rebound')
