"""Pinned-body stage-window integration, with explicit CPU-only boundaries."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import torch

from wcomr.prepared_input import RNGState
from wcomr.stage_output import run_stage_output
from wcomr.stage_refresh import StageRefreshAdapter
from wcomr.stage_refresh_policy import StageRefreshPolicy


def exercise(*,inference,samples,wc,settings,inference_module,mode_setup,kernel,flow):
    net=inference.pipe.model.net
    policies=(StageRefreshPolicy((1,3)),StageRefreshPolicy((1,3),2))
    contexts=[('CPU_STAGE:'+s.name,'toy','condition:'+s.name) for s in samples]
    original_prepare=net.prepare_embedded_sequence
    original_decode=inference.pipe.model.decode
    originals=(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
               inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
    # Force several native full decisions in this CPU window so the cadence is
    # exercised; this controlled toy is not evidence of real adaptive feedback.
    def prepare(*a,**kw):
        value=original_prepare(*a,**kw)
        if 23 <= net.cnt//2+1 <= 27:net.worldcache_rel_l1_thresh=-1
        return value
    net.prepare_embedded_sequence=prepare
    entry=RNGState();historical=None;checks=[]
    try:
        for case in ('complete','bridge_complete','DD_mismatch','second_S_failure','wrong_D_bridge'):
            entry.restore();count=[0];restored=[];state={};error=None
            def decode(*a,**kw):
                count[0]+=1;value=original_decode(*a,**kw)
                return value+.01 if case=='DD_mismatch' and count[0]==2 else value
            inference.pipe.model.decode=decode
            def operation(*a,**kw):
                value,metadata=kernel(*a,**kw);adapter=net._wc_refresh_adapter
                if case=='second_S_failure' and adapter.ledger.context[0].endswith(':human') and adapter.policy.every==2:
                    value=value.clone();value.flatten()[0]=float('nan')
                return value,metadata
            def checkpoint(module,args,value):
                adapter=getattr(net,'_wc_refresh_adapter',None)
                if isinstance(adapter,StageRefreshAdapter) and adapter.sparse and adapter.ledger.call==45:
                    saved=adapter.snapshot();before=list(adapter.eligible_refreshes)
                    adapter.eligible_refreshes=[999,999];adapter.restore(saved)
                    assert adapter.eligible_refreshes==before
                    for invalid in ([-1,0],[99,0],[True,0]):
                        bad=copy.deepcopy(saved);bad['stage_refresh_state']['eligible_refreshes']=invalid
                        try:adapter.restore(bad)
                        except ValueError:pass
                        else:raise AssertionError('Invalid stage checkpoint accepted')
                        assert adapter.eligible_refreshes==before
                    restored.append(before)
            hook=net.register_forward_hook(checkpoint)
            bridge=historical if case=='bridge_complete' else {s.name:'0'*64 for s in samples} if case=='wrong_D_bridge' else None
            with tempfile.TemporaryDirectory(prefix='online-stage-eight-cpu-') as directory:
                try:
                    run_stage_output(inference,samples,wc,settings,policies,state=state,save=lambda:None,
                        output=Path(directory),inference_module=inference_module,contexts=contexts,
                        mode_setup=mode_setup,fallback=(2,),kernel=operation,expected_video=(93,16,16),
                        expected_D_sha256=bridge)
                except ValueError as exc:error=str(exc)
                finally:hook.remove()
                assert state['planned_total_phases']==state['planned_output_files']==8
                assert state['online_policy'] and not state['uses_future_trace'] and not state['official_skip_predicate_replaced']
                assert originals==(net.forward,inference.pipe.model.denoise,inference.pipe.model.sample_scheduler.step,
                    inference.pipe._get_data_batch_input,inference_module.save_img_or_video)
                assert not hasattr(net,'_wc_refresh_adapter') and all(float(b)==0 for b in net.buffers())
                requests=state['measurements']['requests'];dd=state['dense_control']
                if case in ('DD_mismatch','second_S_failure','wrong_D_bridge'):
                    assert error and state['status']=='TECH_BLOCKED_ONLINE_STAGE_EIGHT_OUTPUT_DENOMINATOR_PRESERVED'
                    if case=='DD_mismatch':
                        assert not requests and len(list(Path(directory).rglob('*.mp4')))==2
                    elif case=='wrong_D_bridge':
                        assert len(requests)==1 and len(requests[0]['phases'])==2
                        assert requests[0]['phases'][1]['status']=='TECH_BLOCKED'
                        assert len(list(Path(directory).rglob('*.mp4')))==3
                        assert 'before sparse candidates' in error
                    else:
                        assert len(requests)==2 and len(requests[0]['phases'])==3
                        assert requests[0]['status']=='THREE_ONLINE_STAGE_OUTPUTS_REQUIRE_METRICS'
                        assert len(requests[1]['phases'])==3 and requests[1]['phases'][-1]['status']=='TECH_BLOCKED'
                        assert len(list(Path(directory).rglob('*.mp4')))==7
                    checks.append({'flow':flow,'case':case,'error':error,'planned_outputs':8,
                                   'prior_outputs_denominator_and_cleanup_preserved':True});continue
                assert error is None,error
                assert state['status']=='EIGHT_ONLINE_STAGE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
                assert all(dd['nine_checks'].values()) and all(dd['pipeline_checks'].values())
                assert len(requests)==2 and len(list(Path(directory).rglob('*.mp4')))==8
                assert len(restored)==4
                all_phases=dd['phases']+[p for q in requests for p in q['phases']]
                assert all(p['solver_steps']==36 and p['CFG_calls']==72 and p['prepare_calls']==1 for p in all_phases)
                assert requests[0]['phases'][0]['artifacts']==dd['phases'][0]['artifacts']==dd['phases'][1]['artifacts']
                historical={s.name:q['phases'][0]['artifacts'][0]['sha256'] for s,q in zip(samples,requests)}
                actual=[]
                for q in requests:
                    for phase,policy in zip(q['phases'][1:],policies):
                        report=phase['refresh_provenance'];events=report['events'];ordinals=[0,0];history=[[],[]]
                        assert report['online_policy'] and not report['uses_future_trace'] and not report['official_skip_predicate_replaced']
                        assert report['selection_policy']==policy.to_dict() and report['selection_counters']==[0,0]
                        sparse=[]
                        for e,t in zip(events,phase['trace']):
                            cfg=e['cfg'];step=(e['call']+1)//2
                            assert e['solver_step']==step and e['official_skipped']==(not t['deep_executed'])
                            assert 'fixed_diagnostic_mask' not in e and 'selected_fixed_skip' not in e
                            assert e['true_dense_before']==history[cfg]
                            eligible=not e['official_skipped'] and not e['warm_start'] and e['two_past_true_dense'] and e['paid_probe']
                            inside=23<=step<=27;chosen=False
                            assert e['selection_eligible']==eligible and e['selection_in_window']==inside
                            if eligible and inside:
                                ordinals[cfg]+=1;chosen=(ordinals[cfg]-1)%policy.every==0
                                assert e['selection_window_eligible_ordinal']==ordinals[cfg]
                            else:assert e['selection_window_eligible_ordinal'] is None
                            assert e['selection_sparse_chosen']==chosen
                            assert bool(e['sparse_layers'])==chosen
                            if chosen:
                                assert e['sparse_layers']==[1,3] and e['source']['kind']=='sparse'
                                assert not e['inserted_into_true_dense_history'];sparse.append(e['call'])
                            elif 'source' in e:
                                assert e['source']['kind']=='dense' and e['inserted_into_true_dense_history']
                                history[cfg]=(history[cfg]+[e['source']])[-2:]
                            if e['native_cycle_reset']:history=[[],[]];ordinals=[0,0]
                        assert sparse==([45,46,47,48,49,50,51,52,53,54] if policy.every==1 else [45,46,49,50,53,54])
                        assert all(e['action']=='dense' for e in events[:14]+events[70:])
                        assert not events[70]['references_read'] and not events[71]['references_read']
                        actual.append({'sample':q['sample_name'],'policy':policy.to_dict(),'CPU_sparse_calls':sparse})
                checks.append({'flow':flow,'case':case,'planned_outputs':8,'strict_DD_and_all36_72_prepare1':True,
                    'actual_window_cadence_true_D_isolation_native70_and_restore':actual,
                    'historical_D_gate_before_any_S':case=='bridge_complete','real_kernel_or_video':False})
    finally:
        net.prepare_embedded_sequence=original_prepare;inference.pipe.model.decode=original_decode
    return checks


def run(runtime):
    spec=importlib.util.spec_from_file_location('stage_pinned_fixture',Path(__file__).with_name('check_full_sampling.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    r=m.run(runtime,exercise=exercise)
    r['status']='ONLINE_STAGE_EIGHT_OUTPUT_PINNED_CPU_PASS_NOT_GPU_OR_ADAPTIVE_FEEDBACK'
    r['limits']+=' CPU native full/skip points are forced via toy thresholds; not proof of real adaptive feedback, sparse kernel, encoded videos, quality or speed.'
    return r
