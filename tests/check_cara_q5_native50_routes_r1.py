"""Actual requested50 grid and Native/all-D51 through the pinned CPU pipeline."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, profile_from
from wcomr.cara_q5_native50_r1 import request_class
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
from wcomr.policy_generator_r1 import p2_native_sampling, production_sampling
from wcomr.policy_generator_r1.interval_grammar import Edge, compile_policy

ROOT = Path(__file__).resolve().parents[1]
ROLES = ('NATIVE50', 'ALLD50')


def cpu_fragment(schedule):
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    parent_scope = card.pop('scope_sha256')
    allD = copy.deepcopy(card['roles']['ALLD']); allD['requested_steps'] = 50
    allD['settings']['worldcache_num_steps'] = 50
    card['roles'].update(ALLD=allD, ALLD50=allD, NATIVE50=dict(kind='native', requested_steps=50))
    slots = []
    for member_index, member in enumerate(row['name'] for row in card['inputs']):
        for role in ROLES:
            for mode in ('ON','OFF','AUDIT'):
                slots.append(dict(id=f'CPU_Q5_{member_index}_{role}_{mode}', phase='B',
                    purpose='CPU_GRID_'+mode, member=member, role=role, seed=0,
                    timing_enabled=mode!='OFF', audit_enabled=mode=='AUDIT', eligible_clean_time=mode!='AUDIT'))
    for role in ROLES:
        for fault in ('refusal','decode','writer'):
            slots.append(dict(id='CPU_Q5_FAIL_'+role+'_'+fault, phase='B', purpose='CPU_GRID_FAILURE',
                member=card['FIT'][0], role=role, seed=0, timing_enabled=True,
                audit_enabled=False, eligible_clean_time=True))
    card.update(parent_scope_sha256=parent_scope, schedule=schedule, schedules=[schedule], physical_matrix=slots,
        formal_matrix=[s for s in slots if s['purpose']=='CPU_GRID_ON'],
        CPU_NATIVE_GRID_COMPONENT_ONLY=True, sparse_profile_still_full36=True, GPU_dispatch_ready=False)
    card['scope_sha256'] = digest(card)
    return card


def body(inference, selected, wc, rf, common, unused_initial, profile, root,
         native, flow, inference_module, host, samples):
    import check_wc_time_card_r1 as fixture
    model, net = inference.pipe.model, inference.pipe.model.net
    grid = copy.deepcopy(model.sample_scheduler)
    grid.set_timesteps(50, device='cpu', shift=5., use_kerras_sigma=True)
    schedule = dict(requested_steps=50, actual_updates=len(grid.timesteps),
        timesteps=grid.timesteps.tolist(), sigmas=grid.sigmas.tolist())
    assert schedule['actual_updates']==51 and len(schedule['sigmas'])==52 and schedule['sigmas'][-1]==0
    assert all(a>b for a,b in zip(schedule['sigmas'],schedule['sigmas'][1:]))
    card = cpu_fragment(schedule)
    assert len(card['physical_matrix'])==30 and len(card['formal_matrix'])==8
    cls, derivation = request_class()
    assert derivation['original_request_bytecode_identical'] and derivation['original_module_globals_unchanged']
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']), type(net), dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    binding = json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    kwargs = dict(inference=inference, samples=samples, card=card, common=common,
        ra_binding=binding, host=host, cpu_validation=True)
    frozen = dict(scope_sha256=card['scope_sha256'], phase_A_GPU_released=True, CPU_FIXTURE_ONLY=True)
    originals = (model.generate_samples_from_batch, model.decode, inference.pipe.generate_vid2world, net.forward)
    last_frame=[None]; original_writer=inference_module.save_img_or_video

    def writer(video,path,fps):
        last_frame[0]=np.array(video,copy=True)
        return original_writer(video,path,fps)

    def restored():
        assert (model.generate_samples_from_batch, model.decode, inference.pipe.generate_vid2world, net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)

    # The original adapters remain closed to the new domain.
    sample50=request_variant(samples[card['FIT'][0]],seed=0,num_steps=50)
    try:p2_native_sampling.execute(inference,sample50,schedule=schedule)
    except ValueError as error:assert '18..35' in str(error)
    else:raise AssertionError('Old Native adapter was broadened')
    unsupported=copy.deepcopy(card['profile']);unsupported.update(horizon=51,protected_dense=list(range(1,8))+[51])
    sparse_profile=profile_from(unsupported)
    all_dense=compile_policy(sparse_profile,[Edge(t,t+1) for t in range(1,52)])
    try:production_sampling.validate_policy(sparse_profile,all_dense)
    except ValueError as error:assert 'only the accepted full36' in str(error)
    else:raise AssertionError('Old sparse adapter was broadened')

    records, failures = {}, []
    with clean.patched(inference_module,'save_img_or_video',writer):
        entry=cls(**kwargs,frozen=frozen)
        for slot in (s for s in card['physical_matrix'] if s['purpose']!='CPU_GRID_FAILURE'):
            initial.restore();counts=[0,0]
            def count(i):
                def hook(*args):counts[i]+=1
                return hook
            hooks=[net.blocks[0].register_forward_pre_hook(count(0)),net.blocks[-1].register_forward_pre_hook(count(1))]
            try:out=entry(slot,root/slot['id'])
            finally:
                for hook in hooks:hook.remove()
            assert out['status']=='COMPLETE' and out['solver_steps']==out['guided_pairs']==51 and counts==[102,102]
            assert out['scheduler_timesteps']==schedule['timesteps']
            assert model.sample_scheduler.sigmas.tolist()==schedule['sigmas']
            if slot['role']=='NATIVE50':assert out['full_block_calls']==[102,102] and not out['cache_installed']
            else:assert out['actions']==['DD']*51
            if slot['timing_enabled']:assert 0 < out['T_DD'] <= out['core_seconds'] <= out['T_request']
            if slot['audit_enabled']:assert len(out['guided'])==51 and out['in_timing_guided_copies']==51
            else:
                assert 'guided' not in out
                assert all(out[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
            records[(slot['member'],slot['role'],slot['purpose'])]=dict(result=copy.deepcopy(out),
                RGB=last_frame[0].copy(),RNG=torch.get_rng_state().clone())
            restored()
        for member in (row['name'] for row in card['inputs']):
            reference=records[(member,'NATIVE50','CPU_GRID_ON')]
            for role in ROLES:
                for mode in ('ON','OFF','AUDIT'):
                    record=records[(member,role,'CPU_GRID_'+mode)]
                    assert torch.equal(reference['result']['final_latent'],record['result']['final_latent'])
                    assert np.array_equal(reference['RGB'],record['RGB']) and torch.equal(reference['RNG'],record['RNG'])
            left,right=(records[(member,role,'CPU_GRID_AUDIT')]['result']['guided'] for role in ROLES)
            assert all(torch.equal(a,b) for a,b in zip(left,right))
        for slot in (s for s in card['physical_matrix'] if s['purpose']=='CPU_GRID_FAILURE'):
            fault=slot['id'].rsplit('_',1)[1];initial.restore();entry=cls(**kwargs,frozen=frozen)
            def fail(*args,**kw):raise OSError('DECLARED_Q5_'+fault)
            owner,field,fn=((inference,'generate',lambda *a,**k:[]) if fault=='refusal' else
                (model,'decode',fail) if fault=='decode' else (inference_module,'save_img_or_video',fail))
            with clean.patched(owner,field,fn):
                try:out=entry(slot,root/slot['id'])
                except OSError as error:assert fault!='refusal' and str(error)=='DECLARED_Q5_'+fault
                else:assert fault=='refusal' and out['status']=='TEXT_REJECTED' and out['T_DD'] is None
            restored()
            try:entry(slot,root/'forbidden-replay')
            except ValueError:pass
            else:raise AssertionError('Failed Q5 CPU attempt replayed')
            failures.append(slot['role']+':'+fault)
    initial.restore()
    return [dict(validation='Q5_NATIVE50_ACTUAL_GRID_CPU_COMPONENT',flow=flow,
        schedule=schedule,CPU_fragment_scope_sha256=card['scope_sha256'],registered_CPU_positions=30,
        successful_tiny_paths=len(records),Native_reference_members=4,allD_control_members=4,
        roles=list(ROLES),failures=failures,derivation=derivation,
        actual51_CFG102_and_full_block_witness=True,Native_allD_ON_OFF_audit_latent_RGB_RNG_exact=True,
        all51_audited_guided_outputs_equal=True,clean_research_counters_zero=True,
        cleanup_and_no_replay=True,old_Native_range_unchanged=True,sparse36_adapter_still_rejects51=True,
        Cosmos_weights_loaded=False,real_model_quality_or_speed_result=False,whole_Q5_GPU_card_accepted=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    fixture.body=body
    return fixture.run(runtime,artifact_root,host,samples)
