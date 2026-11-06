"""Three affected Uniform19 policies: tiny paired execution and old-entry parity."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_requests_r2 import Requests
from wcomr.cara_fast_spec_r1 import digest, profile_from, policy_from_mask
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_fixed_mask_r1 import execute_fixed

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_NUMERIC_CPU_R1_20261031.json'


def cpu_fragment():
    contract = json.loads((ROOT/CONTRACT).read_text())
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    parent = card.pop('scope_sha256')
    assert card['FIT'] == contract['FIT'] and card['profile'] == contract['profile']
    profile = profile_from(card['profile'])
    roles = contract['roles']
    for role, dense in roles.items():
        card['roles'][role] = dict(kind='policy', requested_steps=35, policy=policy_from_mask(profile,dense))
    slots = []
    for i, member in enumerate(contract['FIT']):
        for role in roles:
            for mode in contract['modes']:
                slots.append(dict(id=f'CPU_S_INIT_{i}_{role}_{mode}', phase='B',
                    purpose=mode, member=member, role=role, seed=0,
                    timing_enabled=mode!='OFF', audit_enabled=mode=='AUDIT',
                    eligible_clean_time=mode!='AUDIT'))
    for role in roles:
        for fault in ('refusal','decode','writer'):
            slots.append(dict(id=f'CPU_S_INIT_FAIL_{role}_{fault}',phase='B',
                purpose='FAILURE',member=contract['FIT'][0],role=role,seed=0,
                timing_enabled=True,audit_enabled=False,eligible_clean_time=True))
    card.update(parent_scope_sha256=parent,physical_matrix=slots,
        formal_matrix=[s for s in slots if s['purpose']=='ON'],
        CPU_FRAGMENT_ONLY=True,GPU_dispatch_ready=False)
    card['scope_sha256'] = digest(card)
    return card,contract


def body(inference,selected,wc,rf,common,unused_initial,profile,root,
         native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as fixture
    card,contract = cpu_fragment()
    model,net = inference.pipe.model,inference.pipe.model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    binding = json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    kwargs = dict(inference=inference,samples=samples,card=card,common=common,
        ra_binding=binding,host=host,cpu_validation=True)
    frozen = dict(scope_sha256=card['scope_sha256'],phase_A_GPU_released=True,
                  CPU_FIXTURE_ONLY=True,selected={})
    originals = (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    frames = [None]
    original_writer = inference_module.save_img_or_video
    def writer(video,path,fps):
        frames[0] = np.array(video,copy=True)
        return original_writer(video,path,fps)
    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)
    def equal(a,b,guided=False):
        assert torch.equal(a['result']['final_latent'],b['result']['final_latent'])
        assert np.array_equal(a['RGB'],b['RGB']) and torch.equal(a['RNG'],b['RNG'])
        if guided:
            assert len(a['result']['guided'])==len(b['result']['guided'])==36
            assert all(torch.equal(x,y) for x,y in zip(a['result']['guided'],b['result']['guided']))
    def saved(out):
        return dict(result=copy.deepcopy(out),RGB=frames[0].copy(),RNG=torch.get_rng_state().clone())
    params = json.loads((ROOT/'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    previous = json.loads((ROOT/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json').read_text())
    calibration = Calibration('DECLARED_CPU_INITIALIZATION_HISTORY',
        {(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+28,36)+1)},
        {n:1. for n in range(1,37)})
    spec = dict(threshold=2.,costs=Costs('DECLARED_CPU_ONLY',params['source_A_cost_seconds']['D'],
        params['cost_seconds']['D'],params['cost_seconds']['P']),
        partial_prior=CreationPhasePrior('DECLARED_CPU_ONLY',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    records,comparisons,failures = {},[],[]
    try:
        with clean.patched(inference_module,'save_img_or_video',writer):
            entry = Requests(**kwargs,frozen=frozen)
            for slot in (s for s in card['physical_matrix'] if s['purpose']!='FAILURE'):
                initial.restore()
                out = entry(slot,root/slot['id'])
                policy = card['roles'][slot['role']]['policy']
                assert out['status']=='COMPLETE' and out['solver_steps']==out['guided_pairs']==36
                assert [h['actual'] for h in out['semantic_history']]==policy['actions']
                assert all(h['fallback_reason'] is None for h in out['semantic_history'])
                assert sum(a=='D' for a in policy['actions'])==19
                for step,h in enumerate(out['semantic_history'],1):
                    if h['actual']=='C':
                        past=[t for t,a in enumerate(policy['actions'][:step-1],1) if a=='D'][-2:]
                        assert h['source_history']['past_D_steps']==[past,past]
                    assert h['source_history']['teacher_calls']==0
                if slot['timing_enabled']:
                    assert 0 < out['T_DD'] <= out['core_seconds'] <= out['T_request']
                if slot['audit_enabled']:
                    assert len(out['guided'])==36 and out['in_timing_guided_copies']==36
                else:
                    assert 'guided' not in out
                    assert all(out[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
                records[(slot['member'],slot['role'],slot['purpose'])]=saved(out)
                restored()
            for member in contract['FIT']:
                for role in contract['roles']:
                    on=records[(member,role,'ON')]
                    for mode in ('OFF','AUDIT'):
                        other=records[(member,role,mode)]
                        equal(on,other)
                        assert on['result']['semantic_history']==other['result']['semantic_history']
                    policy=card['roles'][role]['policy']
                    initial.restore()
                    old=execute_fixed(inference,request_variant(samples[member],seed=0,num_steps=35),
                        replay_plan=policy['actions'],table_parameters=params,previous_parameters=previous,
                        **{**common,'calibration':calibration,'specs':{'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec},
                           'output':root/(member+'_'+role+'_OLD'),'audit':True})
                    assert old['status']=='COMPLETE' and old['solver_steps']==old['guided_pairs']==36
                    equal(records[(member,role,'AUDIT')],saved(old),guided=True)
                    for step,h in enumerate(old['source_history'],1):
                        if policy['actions'][step-1]=='C':
                            past=[t for t,a in enumerate(policy['actions'][:step-1],1) if a=='D'][-2:]
                            assert h['true_D_before']==h['true_D_after']==[past,past]
                    restored()
                    comparisons.append(dict(member=member,role=role,policy_fingerprint=policy['fingerprint'],
                        all36_guided_old_new_equal=True,final_latent_RGB_RNG_old_new_equal=True,
                        ON_OFF_AUDIT_exact=True,strict_true_D_history=True))
            for slot in (s for s in card['physical_matrix'] if s['purpose']=='FAILURE'):
                fault=slot['id'].rsplit('_',1)[1]
                initial.restore();entry=Requests(**kwargs,frozen=frozen)
                def fail(*args,**kw):
                    raise OSError('DECLARED_S_INIT_'+fault)
                owner,field,fn=((inference,'generate',lambda *a,**k:[]) if fault=='refusal'
                    else (model,'decode',fail) if fault=='decode'
                    else (inference_module,'save_img_or_video',fail))
                with clean.patched(owner,field,fn):
                    try:
                        out=entry(slot,root/slot['id'])
                    except OSError:
                        assert fault!='refusal'
                    else:
                        assert fault=='refusal' and out['status']=='TEXT_REJECTED' and out['T_DD'] is None
                restored()
                try:
                    entry(slot,root/'forbidden-replay')
                except ValueError:
                    pass
                else:
                    raise AssertionError('Failed CPU attempt replayed')
                failures.append(slot['role']+':'+fault)
    finally:
        initial.restore()
    return [dict(status='PASS',flow=flow,scope_sha256=card['scope_sha256'],
        production_paths=len(records),old_fixed_paths=len(comparisons),comparisons=comparisons,
        failures=failures,registered_CPU_positions=len(card['physical_matrix']),
        Cosmos_weights_loaded=False,real_video_quality_or_speed_result=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    previous=fixture.body
    fixture.body=body
    try:
        return fixture.run(runtime,artifact_root,host,samples)
    finally:
        fixture.body=previous
