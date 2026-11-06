"""Full112-path design on both pinned sampler routes, with tiny CPU weights."""
import json
from pathlib import Path

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_budget_calibration_r1 import Calibration, ProductionRequestsCPU
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_budget_search_journal_r1 import OriginalQueryUnknown
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.production_sampling import PolicyReadout, ReadoutFailure

ROOT=Path(__file__).resolve().parents[1]


def body(inference,selected,wc,rf,common,unused_initial,profile,root,
         native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as fixture
    card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    design=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_14GPUH_DESIGN_R1.json').read_text())
    config=SearchConfig(**design['proposed_search_config'])
    assert config.max_evaluations==51 and design['new_GPU_paths']==112
    root.mkdir(parents=True,exist_ok=True)
    model,net=inference.pipe.model,inference.pipe.model.net
    net.__class__=fixture.load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale=.001
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    binding=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    executor=ProductionRequestsCPU(card=card,inference=inference,samples=samples,common=common,
        ra_binding=binding,host=host,before_request=initial.restore)
    options=dict(card=card,config=config,context_sha256=digest(dict(CPU_fixture=True,flow=flow,
        scope=card['scope_sha256'],design=design)),RGB_shape=[3,93,16,16],execute=executor,cpu_validation=True)
    originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,
               net.forward,inference_module.save_img_or_video)
    def restored():
        assert originals==(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,
                           net.forward,inference_module.save_img_or_video)
    entry=Calibration(root=root/'complete',**options,create=True)
    result=entry.run(allow_new=True)
    assert result['complete'] and result['complete_physical_paths']==112 and result['new_physical_calls']==112
    assert result['search']['SA_iterations_completed']==30 and result['search']['HC_iterations_completed']==1
    assert result['search']['completed_cohort_evaluations']==51
    restored()
    recovered=Calibration(root=root/'complete',**options).run()
    assert recovered['complete'] and recovered['new_physical_calls']==0
    assert recovered['search']['queries']==result['search']['queries']
    assert recovered['search']['journal']['new_callback_calls']==0
    failures=[]
    for fault in ('first_writer','second_FIT_refusal','policy_fallback'):
        entry=Calibration(root=root/fault,**options,create=True)
        if fault=='first_writer':
            def fail(*args,**kwargs):raise OSError('Declared complete calibration writer failure')
            with clean.patched(inference_module,'save_img_or_video',fail):
                try:entry.run(allow_new=True)
                except OSError:pass
                else:raise AssertionError('Writer failure accepted')
            assert entry.physical_calls==1
            try:Calibration(root=root/fault,**options).run(allow_new=True)
            except OriginalQueryUnknown:pass
            else:raise AssertionError('Unknown original control repeated')
        else:
            if fault=='second_FIT_refusal':
                original=inference.generate
                def inject(samples,output_dir,**kwargs):
                    if 'query-000001-FIT1' in str(output_dir):return []
                    return original(samples,output_dir=output_dir,**kwargs)
                owner,field,hook=inference,'generate',inject
            else:
                original=PolicyReadout.end
                def inject(self,actual,action):
                    # Controls use the same policy route, so inject only after
                    # all ten control paths have already completed.
                    if entry.physical_calls>10 and action=='CC' and not self.forced_dense:
                        raise ReadoutFailure('Declared complete calibration fixed19D failure')
                    return original(self,actual,action)
                owner,field,hook=PolicyReadout,'end',inject
            with clean.patched(owner,field,hook):failed=entry.run(allow_new=True)
            assert not failed['complete'] and failed['search']['completed_cohort_evaluations']==0
            assert entry.physical_calls==(12 if fault=='second_FIT_refusal' else 11)
            recovered=Calibration(root=root/fault,**options).run(allow_new=True)
            assert not recovered['complete'] and recovered['new_physical_calls']==0
        failures.append(dict(kind=fault,physical_attempts=entry.physical_calls,no_replay=True))
        restored()
    initial.restore()
    return [dict(validation='FULL112_CALIBRATION_PRODUCTION_ROUTES_CPU',flow=flow,
        complete_design_paths=112,complete_two_FIT_queries=51,SA_iterations=30,HC_iterations=1,HC_neighbors=20,
        complete93_frame_RGB=True,Native_allD_timing_RGB_and_CPU_RNG_equal=True,
        successful_physical_paths=133,declared_failure_attempts=3,total_physical_attempts=136,
        original_complete_recovery_without_generation=True,failures=failures,hooks_restored=True,
        Cosmos_model_weights_loaded=False,real_GPU_executed=False,whole_GPU_card_accepted=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    fixture.body=body
    return fixture.run(runtime,artifact_root,host,samples)
