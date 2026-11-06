"""Full32 and aliased25 tiny production collections; synthetic budget policy."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card, make_requests, execute, inspect_original
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.wc_time_collection_r1 import atomic

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'


def cpu_card(flow, alias):
    proposal = json.loads((ROOT / PROPOSAL).read_text())
    base = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    policy = (proposal['new_policies']['SU19_CFG_C'] if alias else base['roles']['UNIFORM19_C']['policy'])
    bound = map_physical_slots(proposal, policy)
    bound.update(CPU_fixture_only=True, status='CPU_FIXTURE_BINDING_ONLY',
                 proposal_scope_sha256=proposal['scope_sha256'],
                 original_freeze_sha256=digest({'DECLARED_CPU_SYNTHETIC_POLICY': policy}),
                 actual_original_budget_freeze_read=False)
    bound['binding_sha256'] = digest(bound)
    card = request_card(proposal, bound, base)
    card['roles']['ALLD']['settings']['worldcache_flow_enabled'] = flow
    card['scope_sha256'] = digest({k: v for k, v in card.items() if k != 'scope_sha256'})
    return card, bound


def body(inference, selected, wc, rf, common, unused_initial, profile, root,
         native, flow, inference_module, host, samples):
    import check_wc_time_card_r1 as fixture
    model, net = inference.pipe.model, inference.pipe.model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']), type(net), dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    origin = initial.fingerprint()
    ra = json.loads((ROOT / 'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    originals = (model.generate_samples_from_batch, model.decode, inference.pipe.generate_vid2world, net.forward)
    frame = [None]
    writer = inference_module.save_img_or_video

    def observed_writer(video, path, fps):
        frame[0] = np.array(video, copy=True)
        return writer(video, path, fps)

    def restored():
        assert (model.generate_samples_from_batch, model.decode, inference.pipe.generate_vid2world, net.forward) == originals
        assert '_cara_paper_timing_active_r1' not in vars(model)

    def before(slot):
        restored()
        initial.restore()
        assert initial.fingerprint() == origin

    def snapshot(out):
        return (out['final_latent'].clone(), frame[0].copy(), torch.get_rng_state().clone())

    def equal(a, b):
        assert torch.equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and torch.equal(a[2], b[2])

    results = []
    settings_calls = []
    original_apply = wc.apply_worldcache
    settings = cpu_card(flow, False)[0]['roles']['ALLD']['settings']

    def checked_apply(net, **kw):
        assert kw == {k.removeprefix('worldcache_'): v for k, v in settings.items()}
        settings_calls.append(dict(kw))
        return original_apply(net, **kw)

    try:
        with clean.patched(inference_module, 'save_img_or_video', observed_writer), clean.patched(wc, 'apply_worldcache', checked_apply):
            references = {}
            for alias in (False, True):
                card, bound = cpu_card(flow, alias)
                allocation = root / ('alias25' if alias else 'full32')
                allocation.mkdir()
                kwargs = dict(inference=inference, samples=samples, common=common, ra_binding=ra, host=host)
                def make():
                    return make_requests(card, bound, cpu_validation=True, **kwargs)
                # Independent calls model the fixed-reference comparison boundary.
                # Their tiny outputs are not the real historical A32/B36 videos.
                if not alias:
                    reference_entry = make()
                    for slot in (s for s in card['physical_matrix'] if s['section'] == 'B_REPLAY_CONTROL'):
                        before(slot)
                        out = reference_entry(slot, allocation / ('reference_' + slot['id']))
                        references[(slot['member'], slot['role'])] = snapshot(out)
                        restored()
                seen = {}
                inner = make()
                class Observed:
                    def __getattr__(self, name): return getattr(inner, name)
                    def __call__(self, slot, output):
                        out = inner(slot, output)
                        seen[slot['id']] = snapshot(out)
                        restored()
                        return out
                collection = allocation / 'collection.json'
                state = execute(Observed(), allocation / 'B', before_request=before,
                                save=lambda value: atomic(collection, value))
                assert len(seen) == len(state['rows']) == (25 if alias else 32)
                recovery = inspect_original(card, collection, cpu_validation=True)
                assert recovery['counts']['COMPLETE'] == len(seen)
                calls_before = len(seen)
                try:
                    execute(make(), allocation / 'B', before_request=before,
                            save=lambda value: atomic(collection, value))
                except FileExistsError: pass
                else: raise AssertionError('Existing whole allocation replayed')
                assert len(seen) == calls_before
                identity_checks = repeats = 0
                by_key = {(s['section'], s['member'], s['role']): s['id'] for s in card['physical_matrix']}
                for slot in card['physical_matrix']:
                    value = seen[slot['id']]
                    if slot['section'] == 'B_REPLAY_CONTROL':
                        equal(value, references[(slot['member'], slot['role'])]); identity_checks += 1
                    if slot['section'] == 'B_ALLD_EQUIVALENCE':
                        equal(value, seen[by_key[('B_WARM', slot['member'], 'NATIVE35')]]); identity_checks += 1
                    if slot['section'] == 'B_REPEAT':
                        equal(value, seen[by_key[('B_FORMAL', slot['member'], slot['role'])]]); repeats += 1
                assert identity_checks == 9 and repeats == (4 if alias else 6)
                # Corrupt an actual producer artifact and reject recovery without execution.
                artifact = Path(state['rows'][0]['result']['endpoint_video_artifact']['path'])
                original = artifact.read_bytes(); artifact.write_bytes(original + b'corrupt')
                try:
                    try: inspect_original(card, collection, cpu_validation=True)
                    except ValueError: pass
                    else: raise AssertionError('Changed artifact accepted')
                finally: artifact.write_bytes(original)
                failures = []
                if not alias:
                    for fault in ('refusal', 'decode', 'writer'):
                        failed = allocation / fault; failed.mkdir()
                        failure_entry = make()
                        def fail(*args, **kw): raise OSError('DECLARED_ENDPOINT_' + fault)
                        owner, field, fn = ((inference, 'generate', lambda *a, **k: []) if fault == 'refusal'
                            else (model, 'decode', fail) if fault == 'decode'
                            else (inference_module, 'save_img_or_video', fail))
                        with clean.patched(owner, field, fn):
                            try:
                                execute(failure_entry, failed / 'B', before_request=lambda slot: initial.restore(),
                                        save=lambda value: atomic(failed / 'collection.json', value))
                            except (ValueError, OSError): pass
                            else: raise AssertionError('Failure did not stop collection')
                        restored()
                        recovery_failed = inspect_original(card, failed / 'collection.json', cpu_validation=True)
                        assert recovery_failed['counts'] == dict(COMPLETE=0, TECH_FAILED=1, RUNNING=0, NOT_REACHED=31)
                        assert len(failure_entry.seen) == 1
                        try: failure_entry(card['physical_matrix'][0], failed / 'retry')
                        except ValueError: pass
                        else: raise AssertionError('Failed slot replayed')
                        failures.append(fault)
                    # A saved RUNNING state is ambiguous; the reader cannot resume it.
                    pending = copy.deepcopy(state)
                    pending['status'] = 'RUNNING'
                    for i, row in enumerate(pending['rows']): row['status'] = 'RUNNING' if i == 0 else 'NOT_REACHED'
                    atomic(allocation / 'unknown.json', pending)
                    unknown = inspect_original(card, allocation / 'unknown.json', cpu_validation=True)
                    assert unknown['status'] == 'ORIGINAL_RUNNING_OR_UNKNOWN_NO_REPLAY' and not unknown['dispatch_allowed']
                try: make_requests(card, bound, cpu_validation=False, **kwargs)
                except ValueError: pass
                else: raise AssertionError('CPU fixture entered production')
                results.append(dict(status='PASS', flow=flow, aliased_budget=alias,
                    paths=len(seen), clean_samples=sum(s['eligible_clean_time'] for s in card['physical_matrix']),
                    logical_quality_positions=len(card['formal_matrix']), synthetic_identity_checks=identity_checks,
                    exact_repeats=repeats, failures=failures, scope_sha256=card['scope_sha256'],
                    recovery_without_callback=True, existing_output_rejected=True, changed_artifact_rejected=True,
                    original_methods_restored=True, CPU_fixture_GPU_refused=True,
                    original_budget_outputs_read=False, actual_historical_RGB_acceptance=False))
    finally:
        initial.restore()
    restored()
    assert len(settings_calls) == 49
    return [dict(status='PASS', flow=flow, cases=results, independent_reference_calls=8,
                 verified_policy_settings_installs=len(settings_calls), effective_settings=settings,
                 complete_production_paths=57, Cosmos_weights_loaded=False, actual_budget_policy_bound=False)]


def run(runtime, artifact_root, host, samples):
    import check_wc_time_card_r1 as fixture
    previous = fixture.body
    fixture.body = body
    try: return fixture.run(runtime, artifact_root, host, samples)
    finally: fixture.body = previous
