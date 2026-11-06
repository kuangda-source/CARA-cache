"""One complete46 tiny CPU collection using four actual accepted policies."""
import copy
import json
from pathlib import Path
import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_endpoint7_plan_r1 import NEW_ROLES
from wcomr.cara_fast_requests_r2 import Requests
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_execution_r1 import execute, inspect_original
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.wc_time_collection_r1 import atomic
ROOT=Path(__file__).resolve().parents[1]
MANIFEST='plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'

def body(inference,selected,wc,rf,common,unused_initial,profile,root,native,flow,inference_module,host,samples):
    # One full composition on the registered flow-enabled configuration only.
    if not flow:return [dict(status='SKIPPED_UNCHANGED_FLOW_OFF',flow=False)]
    import check_wc_time_card_r1 as fixture
    model,net=inference.pipe.model,inference.pipe.model.net
    net.__class__=fixture.load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale=.001
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    card=json.loads((ROOT/MANIFEST).read_text()); original_scope=card['scope_sha256']
    card['CPU_fixture_only']=True
    card['scope_sha256']=digest({k:v for k,v in card.items() if k!='scope_sha256'})
    ra=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)
    def before(slot):restored();initial.restore()
    def make():
        return Requests(inference=inference,samples=samples,card=card,common=common,ra_binding=ra,host=host,
            cpu_validation=True,frozen=dict(scope_sha256=card['scope_sha256'],phase_A_GPU_released=True,selected={}))
    frames=[None]; writer=inference_module.save_img_or_video
    def observed(video,path,fps):frames[0]=np.array(video,copy=True);return writer(video,path,fps)
    def snapshot(out):return out['final_latent'].clone(),frames[0].copy(),torch.get_rng_state().clone()
    def equal(a,b):assert torch.equal(a[0],b[0]) and np.array_equal(a[1],b[1]) and torch.equal(a[2],b[2])
    allocation=root/'endpoint7-full46';allocation.mkdir(parents=True)
    seen={};inner=make()
    class Observed:
        def __getattr__(self,name):return getattr(inner,name)
        def __call__(self,slot,path):
            out=inner(slot,path);seen[slot['id']]=snapshot(out);restored();return out
    try:
        with clean.patched(inference_module,'save_img_or_video',observed):
            path=allocation/'collection.json'
            state=execute(Observed(),allocation/'B',before_request=before,save=lambda value:atomic(path,value))
            assert len(state['rows'])==len(seen)==46
            keys={(s['purpose'],s['member'],s['role']):s['id'] for s in card['physical_matrix']}
            repeats=0
            for slot in card['physical_matrix']:
                if slot['purpose']=='REPEAT':
                    section='FORMAL' if slot['role'] in NEW_ROLES else 'REPLAY_CONTROL'
                    equal(seen[slot['id']],seen[keys[(section,slot['member'],slot['role'])]]);repeats+=1
                if slot['purpose']=='ALLD_EQUIVALENCE':
                    equal(seen[slot['id']],seen[keys[('WARM',slot['member'],'NATIVE35')]])
            assert repeats==10
            for role in ('NATIVE35',)+NEW_ROLES:
                slot=next(s for s in card['physical_matrix'] if s['purpose']=='WARM' and s['role']==role)
                before(slot);off=make()(slot,allocation/('OFF_'+role),timing=False)
                equal(seen[slot['id']],snapshot(off));restored()
            recovered=inspect_original(card,path,cpu_validation=True)
            assert recovered['counts']['COMPLETE']==46
            try:execute(make(),allocation/'B',before_request=before,save=lambda v:atomic(path,v))
            except FileExistsError:pass
            else:raise AssertionError('Complete collection replay allowed')
            # Production admission is deliberately unavailable for the prospective seven-role card.
            denied=make();denied.cpu_validation=False
            try:execute(denied,allocation/'forbidden',before_request=before,save=lambda v:None)
            except ValueError as e:assert 'CPU preparation only' in str(e)
            else:raise AssertionError('Unadmitted new GPU scope accepted')
            failroot=allocation/'failure';failroot.mkdir();failed=make()
            with clean.patched(inference,'generate',lambda *a,**k:[]):
                try:execute(failed,failroot/'B',before_request=before,save=lambda v:atomic(failroot/'collection.json',v))
                except ValueError:pass
                else:raise AssertionError('Refused first request did not stop')
            recovery=inspect_original(card,failroot/'collection.json',cpu_validation=True)
            assert recovery['counts']==dict(COMPLETE=0,TECH_FAILED=1,RUNNING=0,NOT_REACHED=45)
    finally:initial.restore()
    restored()
    return [dict(status='PASS',flow=True,complete_production_paths=46,extra_timing_OFF_paths=5,
        same_latent_RGB_RNG_ON_OFF=True,repeat_identity_controls=10,true_Native_allD_equal=True,
        original_source_scope_sha256=original_scope,CPU_scope_sha256=card['scope_sha256'],
        actual_frozen_policies={r:card['roles'][r]['policy']['fingerprint'] for r in NEW_ROLES},
        recovery_without_callback=True,replay_refused=True,failure_denominator=46,
        new_GPU_scope_refused=True,Cosmos_weights_loaded=False,actual_historical_RGB_accepted=False)]

def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    previous=fixture.body;fixture.body=body
    try:return fixture.run(runtime,artifact_root,host,samples)
    finally:fixture.body=previous
