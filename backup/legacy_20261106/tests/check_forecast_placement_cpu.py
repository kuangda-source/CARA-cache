"""Complete pinned sampler controls for explicit oracle S placement."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile

from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.forecast_placement import optimize, replay
from wcomr.prepared_input import RNGState
from wcomr.selective_output import run_selective_output
from wcomr.selective_refresh_diagnostic import SelectiveFixedRefreshAdapter
from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy
from wcomr.stage_witness import StageWitness


def exercise(*,inference,samples,wc,settings,inference_module,mode_setup,kernel,flow):
    spec=importlib.util.spec_from_file_location('forecast_observer',
        Path(__file__).with_name('check_fixed_refresh_diagnostic_cpu.py'))
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    context=('CPU_FORECAST_PLACEMENT:human','toy','condition:human')
    args=(inference,samples[1],wc,settings,inference_module,mode_setup)
    entry=RNGState()
    entry.restore()
    source,rows,error=observer.observed_pair(*args,lambda kind,ctx:None,context)
    assert error is None
    calls=tuple(p['deep_executed'] for p in source['phases'][0]['trace'])
    mask=FixedRefreshMask('human','toy','condition:human',calls,
        hashlib.sha256(repr(calls).encode()).hexdigest())
    entry.restore()
    full,_,error=observer.observed_pair(*args,
        lambda kind,ctx:None if kind=='official' else SelectiveFixedRefreshAdapter(ctx,mask,
            SparseRefreshPolicy((1,3)),sparse=True,fallback_layers=(2,),kernel=kernel),context)
    assert error is None
    events=full['phases'][1]['refresh_provenance']['events']
    counts=[sum(e['selection_eligible'] and e['cfg']==cfg for e in events) for cfg in (0,1)]
    quotas=[(n+1)//2 for n in counts]
    opt=[optimize(events,(1,3),quotas,keep_first_S=v) for v in (True,False)]
    policies=(SparseRefreshPolicy((1,3),2),)+tuple(SparsePlacementPolicy((1,3),
        per_cfg_eligible_ordinals=tuple(tuple(v) for v in q['policy']['per_cfg_eligible_ordinals'])) for q in opt)
    entry.restore()
    legacy,legacy_rows,error=observer.observed_pair(*args,
        lambda kind,ctx:None if kind=='official' else SelectiveFixedRefreshAdapter(ctx,mask,
            policies[0],sparse=True,fallback_layers=(2,),kernel=kernel),context)
    assert error is None
    checks=[];net=inference.pipe.model.net
    originals=(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
        inference.pipe.model.decode,inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
    for scenario in ('complete_six','DD_mask_mismatch','first_placement_kernel_failure','legacy_reference_mismatch'):
        selected=mask
        if scenario=='DD_mask_mismatch':
            changed=list(calls);changed[14:16]=[True,True];changed[22:24]=[False,False]
            selected=FixedRefreshMask('human','toy','condition:human',tuple(changed),mask.source_receipt_sha256)
        def operation(*args,**kwargs):
            value,metadata=kernel(*args,**kwargs)
            if (scenario=='first_placement_kernel_failure'
                    and net._wc_refresh_adapter.policy==policies[1]):
                value=value.clone();value.flatten()[0]=float('nan')
            return value,metadata
        restored=[]
        def roundtrip(module,args,value):
            adapter=getattr(net,'_wc_refresh_adapter',None)
            if isinstance(adapter,SelectiveFixedRefreshAdapter) and adapter.ledger.call==23:
                state=adapter.snapshot();saved=list(adapter.eligible_refreshes)
                adapter.eligible_refreshes=[93,87];adapter.restore(state)
                assert adapter.eligible_refreshes==saved
                wrong=dict(state,selective_refresh_state={
                    'policy':policies[0].to_dict() if adapter.policy!=policies[0] else policies[1].to_dict(),
                    'eligible_refreshes':saved})
                try:adapter.restore(wrong)
                except ValueError:pass
                else:raise AssertionError('Different placement policy restored')
                assert adapter.eligible_refreshes==saved
                restored.append(adapter.policy.to_dict())
        hook=net.register_forward_hook(roundtrip)
        stages=StageWitness()
        stages.wrap(inference.pipe.model,'generate_samples_from_batch',
            after=lambda value:stages.record('sample_return',value))
        stages.wrap(inference.pipe.model,'decode',
            after=lambda value:stages.record('decode_output',value))
        stages.wrap(inference_module.guardrail_presets,'run_video_guardrail',
            after=lambda value:stages.record('guardrail_output',value))
        stages.wrap(inference_module,'save_img_or_video',
            before=lambda args,kwargs:stages.record('save_input',args[0]))
        state,error={},None;entry.restore()
        with tempfile.TemporaryDirectory(prefix='forecast-placement-cpu-') as directory:
            try:
                run_selective_output(inference,samples[1],wc,settings,selected,policies,
                    state=state,save=lambda:None,output=Path(directory),inference_module=inference_module,
                    context=context,mode_setup=mode_setup,fallback=(2,),kernel=operation,
                    expected_video=(93,16,16),comparison='forecast_placement',
                    expected_D_sha256=legacy['phases'][0]['artifacts'][0]['sha256'],
                    expected_full_S_sha256=('0'*64 if scenario=='legacy_reference_mismatch' else
                        legacy['phases'][1]['artifacts'][0]['sha256']))
            except ValueError as exc:error=str(exc)
            finally:
                hook.remove();stages.close()
            assert state['planned_output_files']==state['planned_total_phases']==6
            assert originals==(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
                inference.pipe.model.decode,inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
            assert not hasattr(net,'_wc_refresh_adapter') and all(float(b)==0 for b in net.buffers())
            if scenario!='complete_six':
                assert error and state['status']=='TECH_BLOCKED_FORECAST_PLACEMENT_SIX_OUTPUT_DENOMINATOR_PRESERVED'
                if scenario=='DD_mask_mismatch':
                    assert not state['measurement']['phases'] and len(list(Path(directory).rglob('*.mp4')))==2
                else:
                    assert len(state['measurement']['phases'])==3
                    assert state['measurement']['phases'][-1]['status']=='TECH_BLOCKED'
                    assert len(list(Path(directory).rglob('*.mp4')))==4
                checks.append({'flow':flow,'scenario':scenario,'six_denominator_and_prior_outputs_preserved':True,'error':error})
                continue
            assert error is None,error
            assert state['status']=='SIX_FORECAST_PLACEMENT_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
            phases=state['dense_control']['phases']+state['measurement']['phases']
            assert len(list(Path(directory).rglob('*.mp4')))==6 and len(restored)==3
            assert all(state['dense_control']['nine_checks'].values()) and all(state['dense_control']['pipeline_checks'].values())
            assert all(p['prepare_calls']==1 and p['solver_steps']==36 and p['CFG_calls']==72 for p in phases)
            assert all(tuple(v['deep_executed'] for v in p['trace'])==calls for p in phases)
            assert phases[0]['artifacts']==phases[1]['artifacts']==phases[2]['artifacts']
            measure=state['measurement']['phases']
            assert measure[1]['trace']==legacy['phases'][1]['trace']
            assert measure[1]['pipeline_events']==legacy['phases'][1]['pipeline_events']
            assert len(stages.events)==24
            assert stages.events[12:16]==legacy_rows[1]['pipeline']
            topology=[]
            for phase,policy in zip(measure[1:],policies):
                report=phase['refresh_provenance'];assert report['selection_policy']==policy.to_dict()
                assert report['selection_counters']==[0,0]
                result=replay(report['events'],policy,verify_actual=True)
                assert result['S_per_CFG']==quotas
                for e in report['events']:
                    if e['sparse_layers']:
                        assert e['sparse_layers']==[1,3] and e['source']['kind']=='sparse'
                        assert not e['inserted_into_true_dense_history']
                    elif 'source' in e:
                        assert e['source']['kind']=='dense' and e['inserted_into_true_dense_history']
                    assert all(v['kind']=='dense' for v in e['true_dense_before'])
                assert all(e['action']=='dense' for e in report['events'][:14]+report['events'][70:])
                topology.append(result)
            assert topology[1]['S_calls'][:2]==topology[0]['S_calls'][:2]
            for actual,planned in zip(topology[1:],opt):
                assert actual==planned['replay']
            checks.append({'flow':flow,'scenario':scenario,'six_complete36_CFG72_prepare1':True,
                'legacy_alternating_exact_sampler_pipeline_regression':True,
                'legacy_actual_sampler_decode_guardrail_write_tensor_hashes_match':True,
                'first_S_matching_and_equal_S_per_CFG':quotas,
                'actual_source_replay_matches_frozen_placements':topology,
                'snapshot_counter_restore_and_wrong_policy_rejection':True,
                'true_D_isolation_and_native70_reset':True,'real_sparse_kernel_or_video':False})
    return checks


def run(runtime):
    spec=importlib.util.spec_from_file_location('forecast_pinned_fixture',Path(__file__).with_name('check_full_sampling.py'))
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    result=fixture.run(runtime,exercise=exercise)
    result['status']='FORECAST_PLACEMENT_SIX_OUTPUT_PINNED_CPU_PASS_NOT_VIDEO'
    result['limits']+=' Explicit positions here use toy trace ordinals, CPU stand-in S and mock writer; human oracle positions need a separately frozen GPU card.'
    return result
