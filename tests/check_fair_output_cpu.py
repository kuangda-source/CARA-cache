"""All14 fair-output composition plus failure preservation with pinned CPU bodies."""
import importlib.util
from pathlib import Path
import tempfile

from wcomr.fair_output import run_fair_output
from wcomr.prepared_input import RNGState
from wcomr.stage_refresh_policy import StageRefreshPolicy


def composition(*,inference,samples,wc,settings,inference_module,mode_setup,kernel,flow):
    net=inference.pipe.model.net
    policy=StageRefreshPolicy((1,3),every=1,first_solver_step=23,last_solver_step=27)
    contexts=[('CPU_FAIR14:'+s.name,'toy_model','condition:'+s.name) for s in samples]
    prepare=inference.pipe._get_data_batch_input
    decode=inference.pipe.model.decode
    write=inference_module.save_img_or_video
    originals=(net.forward,inference.pipe.worldcache_enabled,inference.pipe.model.denoise,
               inference.pipe.model.sample_scheduler.step,inference.pipe.model.generate_samples_from_batch)
    hooks=(len(net._forward_hooks),len(net._forward_pre_hooks))
    entry=RNGState();historical=None;checks=[]
    cases=('complete',) if not flow else ('complete','bridge_complete','DD_mismatch',
                                        'second_native23_writer_failure','wrong_WC_bridge')
    try:
        for case in cases:
            entry.restore();count=[0];state={};error=None
            before_settings={name:getattr(net,name) for name in set(settings)|{'worldcache_enabled'}}
            def prepared(*a,**k):
                value=prepare(*a,**k);count[0]+=1;return value
            def decoded(*a,**k):
                value=decode(*a,**k)
                return value+.01 if case=='DD_mismatch' and count[0]==2 else value
            def written(*a,**k):
                if case=='second_native23_writer_failure' and count[0]==10:return
                return write(*a,**k)
            inference.pipe._get_data_batch_input=prepared
            inference.pipe.model.decode=decoded
            inference_module.save_img_or_video=written
            bridge=historical if case=='bridge_complete' else {s.name:'0'*64 for s in samples} if case=='wrong_WC_bridge' else None
            with tempfile.TemporaryDirectory(prefix='fair14-composition-cpu-') as directory:
                try:
                    run_fair_output(inference,samples,wc,settings,policy,state=state,save=lambda:None,
                        output=Path(directory),inference_module=inference_module,contexts=contexts,
                        mode_setup=mode_setup,fallback=(2,),kernel=kernel,expected_video=(93,16,16),
                        expected_WC_sha256=bridge)
                except ValueError as exc:error=str(exc)
                assert state['planned_total_phases']==state['planned_output_files']==14
                requests=state['measurements']['requests'];dd=state['dense_control']
                if case in ('complete','bridge_complete'):
                    assert error is None,error
                    assert state['status']=='FOURTEEN_COMPLETE_FAIR_OUTPUTS_REQUIRE_AUDIT_NOT_FRONTIER_ACCEPTANCE'
                    assert len(requests)==2 and len(list(Path(directory).rglob('*.mp4')))==14
                    assert all(dd['nine_checks'].values()) and all(dd['pipeline_checks'].values())
                    for request in requests:
                        phases=request['phases']
                        assert [p['workpoint']['name'] for p in phases]==['native35','native23','wc004','wc006','wc008','stage_every1']
                        assert [p['solver_steps'] for p in phases]==[36,24,36,36,36,36]
                        assert [p['CFG_calls'] for p in phases]==[72,48,72,72,72,72]
                        assert all(p['prepare_calls']==1 for p in phases)
                        assert all(not p.get('observers') for p in phases)
                        assert all(v['deep_executed'] for p in phases[:2] for v in p['trace'])
                        assert phases[-1]['refresh_provenance']['online_policy']
                        assert not phases[-1]['refresh_provenance']['uses_future_trace']
                    historical={s.name:q['phases'][3]['artifacts'][0]['sha256'] for s,q in zip(samples,requests)}
                    checks.append({'flow':flow,'case':case,'planned_outputs':14,
                        'strict_fresh_DD_all_nine_and_pipeline':True,
                        'two_complete_CAL_each_all6_workpoints':True,
                        'Native35_36_72_Native23_24_48_then_WC35_36_72_reset':True,
                        'six_workpoints_no_tensor_diagnostic_observers':True,
                        'CPU_toy_mock_mask_block_embedding_decoder_writer_not_GPU':True})
                else:
                    assert error and state['status']=='TECH_BLOCKED_FAIR_FOURTEEN_OUTPUT_DENOMINATOR_PRESERVED'
                    if case=='DD_mismatch':
                        assert not requests and count[0]==2
                        assert dd['status']=='TECH_BLOCKED_DD_MEASUREMENTS_NOT_STARTED'
                    elif case=='wrong_WC_bridge':
                        assert len(requests)==1 and len(requests[0]['phases'])==4
                        assert requests[0]['phases'][-1]['status']=='TECH_BLOCKED'
                        assert not any(p['workpoint']['mode']=='stage' for q in requests for p in q['phases'])
                    else:
                        assert len(requests)==2 and len(requests[0]['phases'])==6
                        assert requests[0]['status'].startswith('SIX_COMPLETE')
                        assert len(requests[1]['phases'])==2 and requests[1]['phases'][1]['status']=='TECH_BLOCKED'
                        assert len(list(Path(directory).rglob('*.mp4')))==9
                    checks.append({'flow':flow,'case':case,'error':error,'planned_outputs':14,
                                   'prior_outputs_and_full14_denominator_preserved':True})
            assert originals==(net.forward,inference.pipe.worldcache_enabled,inference.pipe.model.denoise,
               inference.pipe.model.sample_scheduler.step,inference.pipe.model.generate_samples_from_batch)
            assert before_settings=={name:getattr(net,name) for name in before_settings}
            assert hooks==(len(net._forward_hooks),len(net._forward_pre_hooks))
            assert not hasattr(net,'_wc_refresh_adapter') and all(float(b)==0 for b in net.buffers())
        return checks
    finally:
        inference.pipe._get_data_batch_input=prepare
        inference.pipe.model.decode=decode
        inference_module.save_img_or_video=write


def run(runtime):
    runtime=Path(runtime)
    path=Path(__file__).with_name('check_fair_sampling_cpu.py')
    spec=importlib.util.spec_from_file_location('fair_native_fixture',path)
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    path=Path(__file__).with_name('check_full_sampling.py')
    spec=importlib.util.spec_from_file_location('fair14_pinned_fixture',path)
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    r=fixture.run(runtime,exercise=lambda **kwargs:native.exercise(runtime=runtime,
        extra_exercise=composition,**kwargs))
    r['upstream_sha256'].update(native.NATIVE_SOURCES)
    r['status']='ALL14_FAIR_AND_NATIVE_DIRECT_REFERENCE_PINNED_CPU_PASS_NOT_REAL_VIDEO_OR_GPU_PARITY'
    r['limits']+=' Unchanged native LVG and base forward bodies with explicit CPU mask/patch embedding/positional Toy blocks. All14 mock outputs are not real weights, kernels, encoded videos, GPU parity, quality or speed.'
    return r
