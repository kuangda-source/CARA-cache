"""Pinned six-output CPU composition and real-source/cadence controls."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.fixed_refresh_diagnostic import FixedRefreshDiagnosticAdapter
from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.light_sampling import run_light_pair
from wcomr.prepared_input import RNGState
from wcomr.selective_output import run_selective_output
from wcomr.selective_refresh_diagnostic import SelectiveFixedRefreshAdapter
from wcomr.selective_refresh_policy import SparseRefreshPolicy


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow):
    spec=importlib.util.spec_from_file_location('selective_fixed_observer',
        Path(__file__).with_name('check_fixed_refresh_diagnostic_cpu.py'))
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    context=('CPU_SELECTIVE:human','toy','condition:human')
    args=(inference,samples[1],wc,settings,inference_module,mode_setup)
    source,rows,error=observer.observed_pair(*args,lambda kind,ctx:None,context)
    assert error is None
    calls=tuple(p['deep_executed'] for p in source['phases'][0]['trace'])
    mask=FixedRefreshMask('human','toy','condition:human',calls,
        hashlib.sha256(repr(calls).encode()).hexdigest())
    policies=(SparseRefreshPolicy((1,3)),SparseRefreshPolicy((1,)),SparseRefreshPolicy((1,3),2))
    entry_rng=RNGState()
    entry_rng.restore()
    legacy,legacy_rows,error=observer.observed_pair(*args,
        lambda kind,ctx:FixedRefreshDiagnosticAdapter(ctx,mask,sparse=kind=='candidate',fallback_layers=(2,),kernel=kernel),context)
    assert error is None
    checks=[]
    net=inference.pipe.model.net
    originals=(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
               inference.pipe.model.decode,inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
    for scenario in ('complete_six','DD_mask_mismatch','small_S_kernel_failure','legacy_S_reference_mismatch'):
        selected=mask
        if scenario=='DD_mask_mismatch':
            changed=list(calls);changed[14:16]=[True,True];changed[22:24]=[False,False]
            selected=FixedRefreshMask('human','toy','condition:human',tuple(changed),mask.source_receipt_sha256)
        def operation(*a,**kw):
            value,metadata=kernel(*a,**kw)
            adapter=net._wc_refresh_adapter
            if scenario=='small_S_kernel_failure' and adapter.policy.sparse_layers==(1,):
                value=value.clone();value.flatten()[0]=float('nan')
            return value,metadata
        restored=[]
        def snapshot_control(module,args,value):
            adapter=getattr(net,'_wc_refresh_adapter',None)
            if isinstance(adapter,SelectiveFixedRefreshAdapter) and adapter.ledger.call==23:
                snapshot=adapter.snapshot();saved=list(adapter.eligible_refreshes)
                adapter.eligible_refreshes=[99,88];adapter.restore(snapshot)
                assert adapter.eligible_refreshes==saved
                bad=dict(snapshot,selective_refresh_state={'policy':adapter.policy.to_dict(),'eligible_refreshes':[-1,0]})
                try:adapter.restore(bad)
                except ValueError:pass
                else:raise AssertionError('Negative selector history accepted')
                assert adapter.eligible_refreshes==saved
                restored.append(adapter.policy.to_dict())
        handle=net.register_forward_hook(snapshot_control)
        state,error={},None
        entry_rng.restore()
        with tempfile.TemporaryDirectory(prefix='selective-six-cpu-') as directory:
            try:
                run_selective_output(inference,samples[1],wc,settings,selected,policies,
                    state=state,save=lambda:None,output=Path(directory),inference_module=inference_module,
                    context=context,mode_setup=mode_setup,fallback=(2,),kernel=operation,expected_video=(93,16,16),
                    expected_D_sha256=legacy['phases'][0]['artifacts'][0]['sha256'],
                    expected_full_S_sha256=('0'*64 if scenario=='legacy_S_reference_mismatch' else
                        legacy['phases'][1]['artifacts'][0]['sha256']))
            except ValueError as exc:error=str(exc)
            finally:handle.remove()
            assert state['planned_total_phases']==state['planned_output_files']==6
            assert originals==(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
                inference.pipe.model.decode,inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
            assert not hasattr(net,'_wc_refresh_adapter') and all(float(b)==0 for b in net.buffers())
            if scenario!='complete_six':
                assert error and state['status']=='TECH_BLOCKED_SELECTIVE_SIX_OUTPUT_DENOMINATOR_PRESERVED'
                if scenario=='DD_mask_mismatch':
                    assert not state['measurement']['phases'] and len(list(Path(directory).rglob('*.mp4')))==2
                else:
                    assert len(state['measurement']['phases'])==3
                    assert state['measurement']['phases'][-1]['status']=='TECH_BLOCKED'
                    assert len(list(Path(directory).rglob('*.mp4')))==4
                checks.append({'flow':flow,'scenario':scenario,'error':error,'six_denominator_and_prior_outputs_preserved':True})
                continue
            assert error is None,error
            assert state['status']=='SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
            assert len(list(Path(directory).rglob('*.mp4')))==6 and len(restored)==3
            assert all(state['dense_control']['nine_checks'].values()) and all(state['dense_control']['pipeline_checks'].values())
            phases=state['dense_control']['phases']+state['measurement']['phases']
            assert all(p['prepare_calls']==1 and p['solver_steps']==36 and p['CFG_calls']==72 for p in phases)
            assert all(tuple(t['deep_executed'] for t in p['trace'])==calls for p in phases)
            assert phases[0]['artifacts']==phases[1]['artifacts']==phases[2]['artifacts']
            measure=state['measurement']['phases']
            # Regression is the actual sampler boundary and every pipeline witness,
            # rather than the possibly saturated toy decoder's mock file.
            assert measure[1]['pipeline_events']==legacy['phases'][1]['pipeline_events']
            assert measure[1]['trace']==legacy['phases'][1]['trace']
            assert measure[0]['pipeline_events']==legacy['phases'][0]['pipeline_events']
            assert not state['measurement']['diagnostic_observers']
            source_counts=[]
            for phase,policy in zip(measure[1:],policies):
                report=phase['refresh_provenance'];events=report['events'];history=[[],[]];ordinals=[0,0]
                assert report['selection_policy']==policy.to_dict() and report['selection_counters']==[0,0]
                sparse_calls,dense_calls=[],[]
                for e in events:
                    branch=e['cfg'];assert e['true_dense_before']==history[branch]
                    eligible=not e['official_skipped'] and not e['warm_start'] and e['two_past_true_dense'] and e['paid_probe']
                    assert e['selection_eligible']==eligible
                    chosen=False
                    if eligible:
                        ordinals[branch]+=1
                        assert e['selection_eligible_ordinal']==ordinals[branch]
                        chosen=(ordinals[branch]-1)%policy.every==0
                    else:assert e['selection_eligible_ordinal'] is None
                    assert e['selection_sparse_chosen']==chosen
                    if chosen:
                        assert e['sparse_layers']==list(policy.sparse_layers) and e['source']['kind']=='sparse'
                        assert not e['inserted_into_true_dense_history'];sparse_calls.append(e['call'])
                    elif 'source' in e:
                        assert not e['sparse_layers'] and e['source']['kind']=='dense' and e['inserted_into_true_dense_history']
                        history[branch]=(history[branch]+[e['source']])[-2:];dense_calls.append(e['call'])
                    if e['native_cycle_reset']:history=[[],[]];ordinals=[0,0]
                assert sparse_calls and all(e['action']=='dense' for e in events[:14]+events[70:])
                assert not events[70]['references_read'] and not events[71]['references_read']
                source_counts.append({'policy':policy.to_dict(),'sparse_calls':sparse_calls,'true_D_refresh_calls':dense_calls})
            assert source_counts[0]['sparse_calls']==source_counts[1]['sparse_calls']
            assert set(source_counts[2]['sparse_calls'])<set(source_counts[0]['sparse_calls'])
            assert len(source_counts[2]['true_D_refresh_calls'])>len(source_counts[0]['true_D_refresh_calls'])
            checks.append({'flow':flow,'scenario':scenario,'complete36_72_prepare_phases':6,'strict_DD_three_D_files_equal':True,
                'full_S_exact_legacy_sampler_and_pipeline_regression':True,'selected_layers_and_branch_cadence_actual_events':source_counts,
                'true_D_between_sparse_refreshes_on_own_trajectory':True,'selector_checkpoint_restore_and_negative_history_rejection':True,
                'real_kernel_and_video':False})
    for sequence,policy in [(('official','candidate','candidate'),'balanced'),
                            (('candidate','official'),'reference_then_candidates'),
                            (('official','candidate'),'unknown')]:
        state={}
        try:
            run_light_pair(inference,samples[1],wc,settings,state=state,save=lambda:None,output=Path('/UNUSED'),
                inference_module=inference_module,context=context,mode_setup=mode_setup,sequence=sequence,sequence_policy=policy)
        except ValueError:pass
        else:raise AssertionError('Invalid measurement sequence accepted')
        assert state=={}
        checks.append({'flow':flow,'scenario':'reject_sequence_'+policy,'no_partial_execution':True})
    return checks


def run(runtime):
    spec=importlib.util.spec_from_file_location('pinned_selective_fixture',Path(__file__).with_name('check_full_sampling.py'))
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    result=fixture.run(runtime,exercise=exercise)
    result['status']='SELECTIVE_SIX_OUTPUT_PINNED_CPU_CONTROLS_PASS_NOT_GPU_FIDELITY'
    result['limits']+=' Sparse branches here use explicit CPU output stand-ins; selection/cadence success is not video quality or speed.'
    return result
