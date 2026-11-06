#!/usr/bin/env python3
"""Independent adaptive-window/source/video audit; no quality acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('light_primitives',Path(__file__).with_name('audit_wc_light_output_receipts.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FULL=[v for v in range(2,28) if v not in (6,23,27)]
SAMPLES=['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191','human_199']
D_SHA={SAMPLES[0]:'fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379',
       SAMPLES[1]:'4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb'}


def stage_provenance(phase, context, *, sparse_allowed):
    result=base.provenance_audit(phase,context,sparse_allowed=sparse_allowed)
    report=phase['refresh_provenance'];policy=report['selection_policy']
    assert report['online_policy'] and not report['uses_future_trace']
    assert not report['official_skip_predicate_replaced'] and not report['causal_refresh_value_labels']
    assert 'fixed_mask' not in report
    assert policy['cadence']=='FIRST_IN_WINDOW_ELIGIBLE_THEN_EVERY_K_PER_CFG_NATIVE_RESET'
    assert policy['selection_role']=='CURRENT_SOLVER_STEP_AND_PAST_CFG_COUNTER_ONLY_CAL_TUNED'
    assert not policy['requires_future_mask'] and not policy['changes_official_cache_predicate']
    assert policy['sparse_layers']==FULL and type(policy['every']) is int and policy['every'] in (1,2)
    assert (policy['first_solver_step'],policy['last_solver_step'])==(23,27)
    counts=[0,0];all_counts=[0,0]
    for event in report['events']:
        assert event['selection_policy']==policy
        assert event['online_policy'] and not event['uses_future_trace']
        assert event['warm_start']==(event['counter']<14)
        assert event['two_past_true_dense']==(len(event['true_dense_before'])>=2)
        inside=23<=event['solver_step']<=27
        eligible=(sparse_allowed and not event['official_skipped'] and not event['warm_start']
                  and event['two_past_true_dense'] and event['paid_probe'])
        assert event['selection_in_window']==inside and event['selection_eligible']==eligible
        ordinal=None;chosen=False
        if eligible and inside:
            counts[event['cfg']]+=1;all_counts[event['cfg']]+=1
            ordinal=counts[event['cfg']]
            chosen=(ordinal-1)%policy['every']==0
        assert event['selection_window_eligible_ordinal']==ordinal
        assert event['selection_sparse_chosen']==chosen==bool(event['sparse_layers'])
        if not inside and not event['official_skipped']:
            assert event['action']=='dense' and event['source']['kind']=='dense'
        if eligible and not chosen:
            assert event['action']=='dense' and event['inserted_into_true_dense_history']
        if event['native_cycle_reset']:counts=[0,0]
    assert counts==report['selection_counters']==[0,0]
    assert report['required_dense_fallback_layers']==[6,23,27]
    assert len(result['sparse_CFG_calls'])<= (10 if policy['every']==1 else 6)
    result.update(window=[23,27],every=policy['every'],window_eligible_per_CFG=all_counts,
                  online_current_step_only=True,actual_deep_count_not_fixed=True)
    return result


def binding(receipt):
    assert receipt['run_card']=='WC-ONLINE-STAGE-R1-20261004-A'
    assert receipt['scope']['run_id']=='wc-online-stage-r1'
    assert receipt['scope']['sample_names']==SAMPLES
    assert receipt['scope']['expected_D_sha256']==D_SHA
    assert receipt['planned_total_phases']==receipt['planned_output_files']==8
    assert receipt['role']=='TWO_EXPOSED_CAL_CURRENT_STAGE_ADAPTIVE_WC_NOT_CONF_OR_FRONTIER'
    assert receipt['online_policy'] and not receipt['uses_future_trace']
    assert not receipt['official_skip_predicate_replaced'] and 'fixed_mask' not in receipt
    assert len(receipt['stage_policies'])==2
    for policy,every in zip(receipt['stage_policies'],(1,2)):
        assert policy['sparse_layers']==FULL and policy['every']==every
        assert (policy['first_solver_step'],policy['last_solver_step'])==(23,27)
    contexts=receipt['reference_contexts']
    assert len(contexts)==2 and contexts[0][1]==contexts[1][1]
    assert [c[0] for c in contexts]==['wc-online-stage-r1:'+s for s in SAMPLES]


def control(receipt,directory):
    binding(receipt)
    result=base.dense_control(receipt,directory)
    phases=receipt['dense_control']['phases']
    result['files'][1]['provenance']=stage_provenance(phases[1],receipt['dense_control']['context'],sparse_allowed=False)
    assert result['files'][0]['sha256']==result['files'][1]['sha256']==D_SHA[SAMPLES[0]]
    result.update(status='ONLINE_STAGE_DD_TWO_OUTPUT_AUDIT_PASS_EIGHT_CARD_PENDING',
                  planned_phases=8,planned_outputs=8)
    return result


def audit(receipt,directory):
    binding(receipt)
    if receipt['status']!='EIGHT_ONLINE_STAGE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT':
        return {'status':'INCOMPLETE_ONLINE_STAGE_EIGHT_CARD_NOT_ACCEPTED','planned_outputs':8,
                'runner_status':receipt['status'],'error':receipt.get('error'),
                'present_files':[str(p) for p in directory.rglob('*.mp4')],
                'files':[],'quality_acceptance':False}
    result=control(receipt,directory);groups=[];first_sparse_seen=False
    requests=receipt['measurements']['requests']
    assert [q['sample_name'] for q in requests]==SAMPLES
    assert receipt['measurements']['status']=='SIX_ADAPTIVE_WC_AND_STAGE_OUTPUTS_REQUIRE_METRICS'
    for q,context in zip(requests,receipt['reference_contexts']):
        assert q['status']=='THREE_ONLINE_STAGE_OUTPUTS_REQUIRE_METRICS'
        assert q['planned_phases']==q['planned_outputs']==len(q['phases'])==3
        assert q['sequence']==['official','candidate','candidate']==[p['kind'] for p in q['phases']]
        assert q['sequence_policy']=='reference_then_candidates' and q['context']==context
        assert q['variant_names']==['adaptive_WC','stage_every1','stage_every2']
        assert not q['diagnostic_observers'] and q['performance_sample'] and q['fresh_prepare_per_phase']
        assert not q['checkpoint_restore'] and not q['per_forward_tensor_diagnostic_hashes']
        assert q['refresh_condition_content_hashes_retained'] and q['refresh_ledger_and_kernel_checks_counted_in_wall']
        assert q['timing_wrappers_CUDA_boundary_sync_only']
        files=[]
        for i,p in enumerate(q['phases']):
            assert p['index']==i and 'observers' not in p
            assert p['sampling']==receipt['dense_control']['phases'][0]['sampling']
            if i:assert p['refresh_provenance']['selection_policy']==receipt['stage_policies'][i-1]
            path=directory/'measurement'/q['sample_name']/(str(i).zfill(3)+'_'+p['kind'])/(q['sample_name']+'.mp4')
            f=base.phase_audit(p,path,context=context,sparse_allowed=i>0,provenance_validator=stage_provenance)
            sparse=i>0 and bool(f['provenance']['sparse_CFG_calls'])
            f.update(variant=q['variant_names'][i],performance_sample=True,
                     first_sparse_pipeline_in_card=sparse and not first_sparse_seen)
            first_sparse_seen=first_sparse_seen or sparse;files.append(f)
        assert files[0]['sha256']==D_SHA[q['sample_name']]
        baseline=files[0]['pipeline_wall_seconds']
        groups.append({'sample_name':q['sample_name'],'files':files,'all_runs_included':True,
            'single_ordered_run_not_replicated_speed':True,
            'descriptive_timings':[{'variant':f['variant'],'seconds':f['pipeline_wall_seconds'],
                'WC_over_variant':baseline/f['pipeline_wall_seconds'],
                'wall_reduction_fraction':1-f['pipeline_wall_seconds']/baseline} for f in files]})
        result['files'].extend(files)
    assert len(result['files'])==len(list(directory.rglob('*.mp4')))==8
    result.update(status='EIGHT_ONLINE_STAGE_ADAPTIVE_SOURCE_POLICY_VIDEO_AUDIT_PASS_NOT_QUALITY',
        measurement_outputs=6,measurement_groups=groups,first_sparse_use_preserved=first_sparse_seen,
        independent_confirmation=False,deployment_speed_claim=False,
        limits=['Two exposed CAL inputs, one ordered run per variant; no CONF or replicated speed result.',
                'Adaptive WC feedback may change the deep/cache trajectory. No oracle mask or fixed S quota.',
                'D/D observer timing excluded; all six measurement timings include necessary online overhead.',
                'Encoded fidelity to official WC is not Native, semantic or physics acceptance.'])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','receipt','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--control-only',action='store_true');args=parser.parse_args()
    r=json.loads(args.receipt.read_text());result=(control if args.control_only else audit)(r,args.directory)
    result.update(receipt_sha256=base.sha(args.receipt),audit_code_sha256=base.sha(Path(__file__)),
        reused_primitives_sha256=base.sha(Path(__file__).with_name('audit_wc_light_output_receipts.py')))
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'files':len(result['files']),'quality_acceptance':False}))
