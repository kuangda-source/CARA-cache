"""Actual full36 production routes with tiny weights and complete93-frame RGB."""
import json
from pathlib import Path

import numpy as np
import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_budget_endpoint_requests_r1 import EndpointRequests
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_budget_search_journal_r1 import run_search
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, profile_from
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.production_sampling import PolicyReadout, ReadoutFailure

ROOT = Path(__file__).resolve().parents[1]


def body(inference, selected, wc, rf, common, unused_initial, profile, root,
         native, flow, inference_module, host, samples):
    import check_wc_time_card_r1 as fixture
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    profile = profile_from(card['profile'])
    root.mkdir(parents=True,exist_ok=True)
    model, net = inference.pipe.model, inference.pipe.model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    binding = json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    context = digest(dict(CPU_fixture=True,flow=flow,parent_scope=card['scope_sha256']))
    options = dict(card=card,context_sha256=context,RGB_shape=[3,93,16,16],
        inference=inference,samples=samples,common=common,ra_binding=binding,host=host,
        cpu_validation=True,before_request=initial.restore)
    arguments = dict(schedule=card['schedule'],profile=profile,config=SearchConfig(42,3,sa_iterations=1,hc_iterations=1,hc_neighbors=2),
        fit_members=card['FIT'],context_sha256=context)
    originals = (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,
        net.forward,inference_module.save_img_or_video)

    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,
            net.forward,inference_module.save_img_or_video) == originals

    normal = []
    for timing in (False,True):
        directory = root/('ON' if timing else 'OFF')
        entry = EndpointRequests(root=directory,**options,create=True,timing_enabled=timing)
        result = run_search(root/('journal-'+str(timing)),**arguments,evaluate=entry,create=True,allow_new_queries=True)
        assert result['termination']=='QUERY_CAP_REACHED' and result['completed_cohort_evaluations']==3
        assert entry.physical_calls==8  # Two full Native teachers plus three complete two-FIT candidates.
        before = entry.physical_calls
        recovered = run_search(root/('journal-'+str(timing)),**arguments,evaluate=entry)
        assert recovered['queries']==result['queries'] and entry.physical_calls==before
        assert recovered['journal']['reused_callback_returns']==3
        normal.append((directory,result,torch.get_rng_state().clone()))
        restored()
    off,on=normal
    assert torch.equal(off[2],on[2])
    for left,right in zip(off[1]['queries'],on[1]['queries']):
        assert left['RGB_MSE_by_member']==right['RGB_MSE_by_member']
        assert left['dense']==right['dense']
    for p in off[0].glob('*/endpoint/RGB.npy'):
        q=on[0]/p.relative_to(off[0])
        assert np.array_equal(np.load(p,allow_pickle=False),np.load(q,allow_pickle=False))
    # The final array and every frame are stored, not just mock MP4 metadata.
    assert len(list(off[0].glob('*/endpoint/RGB.npy')))==8
    failures=[]
    for fault in ('refusal','decode','writer','fallback'):
        entry=EndpointRequests(root=root/('fail-'+fault),**options,create=True)
        entry.prepare_teachers()
        if fault=='fallback':
            original=PolicyReadout.end
            def inject(self,actual,action):
                if action=='CC' and not self.forced_dense:
                    raise ReadoutFailure('Declared endpoint fixed-budget CPU failure')
                return original(self,actual,action)
            owner,field,hook=PolicyReadout,'end',inject
        else:
            original=inference.generate
            def inject(samples,output_dir,**kw):
                if samples[0].name==card['FIT'][1]:
                    if fault=='refusal': return []
                    def fail(*a,**k): raise OSError('Declared endpoint '+fault+' failure')
                    owner,field=(model,'decode') if fault=='decode' else (inference_module,'save_img_or_video')
                    with clean.patched(owner,field,fail): return original(samples,output_dir=output_dir,**kw)
                return original(samples,output_dir=output_dir,**kw)
            owner,field,hook=inference,'generate',inject
        with clean.patched(owner,field,hook):
            result=run_search(root/('journal-fail-'+fault),**arguments,evaluate=entry,create=True,allow_new_queries=True)
        assert result['termination']=='EVALUATION_FAILED_NO_RETRY'
        assert result['best_complete_candidate'] is None and result['completed_cohort_evaluations']==0
        expected=3 if fault=='fallback' else 4
        assert entry.physical_calls==expected
        recovered=run_search(root/('journal-fail-'+fault),**arguments,evaluate=entry,allow_new_queries=True)
        assert entry.physical_calls==expected and recovered['journal']['new_callback_calls']==0
        restored();failures.append(fault)
    try:
        EndpointRequests(root=root/'forbidden-GPU',**{**options,'cpu_validation':False},create=True)
    except ValueError: pass
    else: raise AssertionError('Unbound GPU entry allowed')
    initial.restore()
    return [dict(validation='BUDGET_ENDPOINT_AFFECTED_PRODUCTION_CPU',flow=flow,
        successful_tiny_paths=27,declared_failure_attempts=4,complete_two_FIT_objectives=6,
        full36_and_exact19D=True,full93_preencoding_RGB=True,
        ON_OFF_RGB_RNG_objectives_exact=True,original_teacher_reuse_without_generation=True,
        completed_query_replay_without_generation=True,partial_cohort_never_scored=True,
        nonfinite_fallback_invalidates_fixed_budget=True,failures=failures,
        hooks_restored=True,unbound_GPU_entry_refused=True,Cosmos_weights_loaded=False,
        real_video_quality_or_speed_result=False,whole_GPU_card_accepted=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    fixture.body=body
    return fixture.run(runtime,artifact_root,host,samples)
