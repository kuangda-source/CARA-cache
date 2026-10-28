"""Affected new layout/selection routes in the existing pinned CPU fixture."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_requests_r1 import Requests
from wcomr.full_sampling import CompleteStateRoundtrip

ROOT=Path(__file__).resolve().parents[1]


def body(inference,selected,wc,rf,common,unused_initial,profile,root,native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as base
    card=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
    binding=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    model=inference.pipe.model;net=model.net
    net.__class__=base.load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale=.001
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    kw=dict(inference=inference,samples=samples,card=card,common=common,ra_binding=binding,host=host,cpu_validation=True)
    frozen=dict(scope_sha256=card['scope_sha256'],phase_A_GPU_released=True,CPU_FIXTURE_ONLY=True,
                selected={k:dict(candidate=v[0]) for k,v in card['finite_grids'].items()})
    originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)
    last=[None];old_write=inference_module.save_img_or_video
    def writer(video,path,fps):last[0]=np.array(video,copy=True);return old_write(video,path,fps)
    results={};roles=set();registered=0
    with clean.patched(inference_module,'save_img_or_video',writer):
        entry=Requests(**kw,frozen=frozen)
        for slot in card['physical_matrix']:
            initial.restore();out=entry(slot,root/slot['id']);registered+=1
            role=card['roles'][out['concrete_role']];roles.add(out['concrete_role'])
            updates=next(s['actual_updates'] for s in card['schedules'] if s['requested_steps']==role['requested_steps'])
            assert out['status']=='COMPLETE' and out['solver_steps']==out['guided_pairs']==updates
            if slot['timing_enabled']:assert 0<out['T_DD']<=out['core_seconds']<=out['T_request']
            if role['kind']=='policy':assert [h['actual'] for h in out['semantic_history']]==role['policy']['actions']
            if role['kind']=='allD':assert out['actions']==['DD']*36
            if slot['member']==card['FIT'][0] and slot['timing_enabled'] and out['concrete_role'] not in results:
                results[out['concrete_role']]=(copy.deepcopy(out),last[0].copy(),torch.get_rng_state().clone(),slot)
            restored()
        for name,(on,rgb,rng,slot) in results.items():
            initial.restore();off=Requests(**kw,frozen=frozen)(slot,root/('OFF_'+name),timing=False)
            assert torch.equal(on['final_latent'],off['final_latent'])
            assert all(torch.equal(a,b) for a,b in zip(on['guided'],off['guided']))
            assert on.get('semantic_history')==off.get('semantic_history') and on.get('actions')==off.get('actions')
            assert np.array_equal(rgb,last[0]) and torch.equal(rng,torch.get_rng_state());restored()
        assert torch.equal(results['NATIVE35'][0]['final_latent'],results['ALLD'][0]['final_latent'])
        assert np.array_equal(results['NATIVE35'][1],results['ALLD'][1])
        f18=[]
        # F18 is a separate CPU identifiability check, excluded from the GPU card.
        for name in ('F18_C','F18_A1'):
            slot=dict(card['physical_matrix'][0],role=name)
            entry=Requests(**kw,frozen=frozen);entry.slots[slot['id']]=slot
            initial.restore();out=entry(slot,root/name)
            assert [h['actual'] for h in out['semantic_history']]==card['roles'][name]['policy']['actions']
            assert out['semantic_history'][8]['actual']=='C';f18.append(name);restored()
        faults=[]
        for name in ('F19_A1','WC_T008','RA_T15','NATIVE22'):
            slot=next(s for s in card['physical_matrix'] if s['role']==name)
            for fault in ('refusal','decode','writer'):
                initial.restore();entry=Requests(**kw,frozen=frozen)
                def fail(*a,**k):raise OSError('DECLARED_FAILURE')
                owner,field,fn=(inference,'generate',lambda *a,**k:[]) if fault=='refusal' else (model,'decode',fail) if fault=='decode' else (inference_module,'save_img_or_video',fail)
                with clean.patched(owner,field,fn):
                    try:out=entry(slot,root/(name+'_'+fault))
                    except OSError:assert fault!='refusal'
                    else:assert fault=='refusal' and out['status']=='TEXT_REJECTED' and out['T_DD'] is None
                restored()
                try:entry(slot,root/'retry')
                except ValueError:pass
                else:raise AssertionError('Failed slot retried')
                faults.append(name+':'+fault)
        bslot=next(s for s in card['physical_matrix'] if s['phase']=='B')
        try:Requests(**kw)(bslot,root/'missing-freeze')
        except ValueError:pass
        else:raise AssertionError('Unfrozen B accepted')
        try:Requests(**{**kw,'cpu_validation':False})
        except ValueError:pass
        else:raise AssertionError('Preparation-only GPU entry accepted')
    initial.restore()
    return [dict(flow=flow,registered_paths=registered,OFF_ON_pairs=len(results),concrete_roles=sorted(roles),
                 native_allD_exact=True,F18_CPU_only=f18,faults=faults,no_replay=True,
                 missing_freeze_refused=True,preparation_GPU_refused=True,Cosmos_weights_loaded=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as base
    base.body=body
    return base.run(runtime,artifact_root,host,samples)
