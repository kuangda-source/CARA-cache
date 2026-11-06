"""Affected F18 policies through the accepted tiny paired CLI/model/sampler."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_requests_r2 import Requests
from wcomr.cara_fast_spec_r1 import digest, profile_from, uniform_mask, policy_from_mask
from wcomr.full_sampling import CompleteStateRoundtrip

ROOT = Path(__file__).resolve().parents[1]
ROLES = ('F18_C', 'F18_A1', 'UNIFORM18_C')


def cpu_fragment():
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    parent_scope = card.pop('scope_sha256')
    profile = profile_from(card['profile'])
    dense, _ = uniform_mask(card['schedule'], profile, 18)
    card['roles']['UNIFORM18_C'] = dict(kind='policy', requested_steps=35,
        policy=policy_from_mask(profile, dense))
    slots = []
    for member_index, member in enumerate(card['CHECK']):
        for role in ROLES:
            for mode in ('ON', 'OFF', 'AUDIT'):
                slots.append(dict(id=f'CPU_F18_{member_index}_{role}_{mode}', phase='B',
                    purpose='CPU_FRAGMENT_'+mode, member=member, role=role, seed=0,
                    timing_enabled=mode!='OFF', audit_enabled=mode=='AUDIT',
                    eligible_clean_time=mode!='AUDIT'))
    for role in ROLES:
        for fault in ('refusal', 'decode', 'writer'):
            slots.append(dict(id='CPU_F18_FAIL_'+role+'_'+fault, phase='B',
                purpose='CPU_FRAGMENT_FAILURE', member=card['CHECK'][0], role=role, seed=0,
                timing_enabled=True, audit_enabled=False, eligible_clean_time=True))
    card.update(parent_scope_sha256=parent_scope, physical_matrix=slots,
        formal_matrix=[s for s in slots if s['purpose']=='CPU_FRAGMENT_ON'],
        CPU_FRAGMENT_ONLY=True, GPU_dispatch_ready=False)
    card['scope_sha256'] = digest(card)
    return card


def body(inference, selected, wc, rf, common, unused_initial, profile, root,
         native, flow, inference_module, host, samples):
    import check_wc_time_card_r1 as fixture
    card = cpu_fragment()
    assert len(card['physical_matrix']) == 27 and len(card['formal_matrix']) == 6
    binding = json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    model, net = inference.pipe.model, inference.pipe.model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']), type(net), dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    kwargs = dict(inference=inference, samples=samples, card=card, common=common,
        ra_binding=binding, host=host, cpu_validation=True)
    frozen = dict(scope_sha256=card['scope_sha256'], phase_A_GPU_released=True,
        CPU_FIXTURE_ONLY=True, selected={family:dict(candidate=values[0])
            for family, values in card['finite_grids'].items()})
    originals = (model.generate_samples_from_batch, model.decode,
        inference.pipe.generate_vid2world, net.forward)
    last_frame = [None]
    original_writer = inference_module.save_img_or_video

    def writer(video, path, fps):
        last_frame[0] = np.array(video, copy=True)
        return original_writer(video, path, fps)

    def restored():
        assert (model.generate_samples_from_batch, model.decode,
            inference.pipe.generate_vid2world, net.forward) == originals
        assert '_cara_paper_timing_active_r1' not in vars(model)

    records, failures = {}, []
    with clean.patched(inference_module, 'save_img_or_video', writer):
        entry = Requests(**kwargs, frozen=frozen)
        for slot in (s for s in card['physical_matrix'] if s['purpose']!='CPU_FRAGMENT_FAILURE'):
            initial.restore()
            out = entry(slot, root/slot['id'])
            assert out['status']=='COMPLETE' and out['solver_steps']==out['guided_pairs']==36
            policy = card['roles'][slot['role']]['policy']
            history = out['semantic_history']
            assert [h['actual'] for h in history] == policy['actions']
            assert all(h['fallback_reason'] is None for h in history)
            assert sum(h['actual']=='D' for h in history)==18
            if slot['role']=='F18_A1':
                assert [h['step'] for h in history if h['actual']=='A']==[8,11,13,15,17,19]
                assert history[8]['actual']=='C'
                assert history[7]['source_history']['past_D_steps']==[[6,7],[6,7]]
                assert history[8]['source_history']['past_D_steps']==[[6,7],[6,7]]
            if slot['timing_enabled']:
                assert 0 < out['T_DD'] <= out['core_seconds'] <= out['T_request']
            if slot['audit_enabled']:
                assert len(out['guided'])==36 and out['in_timing_guided_copies']==36
            else:
                assert 'guided' not in out
                assert all(out[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
            records[(slot['member'],slot['role'],slot['purpose'])] = dict(
                result=copy.deepcopy(out), RGB=last_frame[0].copy(), RNG=torch.get_rng_state().clone())
            restored()
        for member in card['CHECK']:
            for role in ROLES:
                on = records[(member,role,'CPU_FRAGMENT_ON')]
                for mode in ('OFF','AUDIT'):
                    other = records[(member,role,'CPU_FRAGMENT_'+mode)]
                    assert torch.equal(on['result']['final_latent'],other['result']['final_latent'])
                    assert on['result']['semantic_history']==other['result']['semantic_history']
                    assert np.array_equal(on['RGB'],other['RGB']) and torch.equal(on['RNG'],other['RNG'])
        for slot in (s for s in card['physical_matrix'] if s['purpose']=='CPU_FRAGMENT_FAILURE'):
            fault = slot['id'].rsplit('_',1)[1]
            initial.restore(); entry = Requests(**kwargs, frozen=frozen)
            def fail(*args, **kwargs):
                raise OSError('DECLARED_F18_'+fault)
            owner, field, fn = ((inference,'generate',lambda *a,**k:[]) if fault=='refusal'
                else (model,'decode',fail) if fault=='decode'
                else (inference_module,'save_img_or_video',fail))
            with clean.patched(owner, field, fn):
                try:
                    out = entry(slot, root/slot['id'])
                except OSError:
                    assert fault!='refusal'
                else:
                    assert fault=='refusal' and out['status']=='TEXT_REJECTED' and out['T_DD'] is None
            restored()
            try:
                entry(slot, root/'forbidden-replay')
            except ValueError:
                pass
            else:
                raise AssertionError('Failed F18 CPU attempt replayed')
            failures.append(slot['role']+':'+fault)
        slot = card['formal_matrix'][0]
        for options in ({**kwargs, 'cpu_validation':False}, kwargs):
            try:
                Requests(**options)(slot,root/'missing-context-or-freeze')
            except ValueError:
                pass
            else:
                raise AssertionError('Unbound context or missing freeze accepted')
    initial.restore()
    return [dict(validation='F18_AFFECTED_PRODUCTION_CPU_FRAGMENT', flow=flow,
        parent_scope_sha256=card['parent_scope_sha256'], CPU_fragment_scope_sha256=card['scope_sha256'],
        registered_CPU_positions=27, successful_tiny_paths=len(records),
        formal_CHECK_positions=6, roles=list(ROLES), failures=failures,
        full36_and_exact_actions=True, F18_A1_step9_C_from_D7_preserved=True,
        ON_OFF_and_clean_audit_latent_RGB_RNG_exact=True, clean_research_counters_zero=True,
        cleanup_no_replay_and_context_guards=True, Cosmos_weights_loaded=False,
        real_video_quality_or_speed_result=False, whole_GPU_card_accepted=False)]


def run(runtime, artifact_root, host, samples):
    import check_wc_time_card_r1 as fixture
    fixture.body = body
    return fixture.run(runtime, artifact_root, host, samples)
