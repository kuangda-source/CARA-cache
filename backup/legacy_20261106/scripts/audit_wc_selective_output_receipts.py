#!/usr/bin/env python3
"""Independent six-output policy/source/video audit; never quality acceptance."""
import argparse
import importlib.util
import json
import math
from pathlib import Path

spec=importlib.util.spec_from_file_location('light_primitives',Path(__file__).with_name('audit_wc_light_output_receipts.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FULL=[v for v in range(2,28) if v not in (6,23,27)]
D_SHA='4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb'
S_SHA='8113659676684a91ce1e8d070e9893f7d1fa3d2f6e8e58191b1218a1f1ac90e1'


def provenance_audit(phase, context, *, sparse_allowed):
    report = phase['refresh_provenance']
    assert report['context'] == context and report['group'] == [2, 28] and report['epoch'] == 1
    policy = report.get('selection_policy')
    ordinals = [0, 0]
    if policy is not None:
        assert policy['cadence'] == 'FIRST_ELIGIBLE_THEN_EVERY_K_PER_CFG_RESET_WITH_NATIVE_CYCLE'
        assert policy['selection_role'] == 'OFFLINE_FROZEN_LAYER_CADENCE_NOT_ONLINE_RISK_OR_REFRESH_ROUTING'
        assert type(policy['every']) is int and policy['every'] > 0
        assert policy['sparse_layers'] and policy['sparse_layers'] == sorted(set(policy['sparse_layers']))
        assert set(policy['sparse_layers']).issubset(FULL)
    rows = report['events']
    assert len(rows) == 72 and rows[69]['native_cycle_reset']
    assert not rows[70]['references_read'] and not rows[71]['references_read']
    assert all(e['action'] == 'dense' for e in rows[:14] + rows[70:])
    sparse, hits, operators, sources = [], [], 0, {}
    true_history = [[], []]
    for call, (e, trace) in enumerate(zip(rows, phase['trace']), 1):
        assert e['call'] == call and e['solver_step'] == (call + 1) // 2 and e['cfg'] == (call - 1) % 2
        assert e['counter'] == trace['cache_counter_before']
        assert e['official_skipped'] == (not trace['deep_executed'])
        assert e['epoch'] == (0 if call <= 70 else 1)
        assert e['true_dense_before'] == true_history[e['cfg']]
        if policy is not None:
            assert e['selection_policy'] == policy
            assert e['warm_start'] == (e['counter'] < 14)
            assert e['two_past_true_dense'] == (len(true_history[e['cfg']]) >= 2)
            eligible = not e['official_skipped'] and not e['warm_start'] and e['two_past_true_dense'] and e['paid_probe']
            assert e['selection_eligible'] == eligible
            chosen = False
            if eligible:
                ordinals[e['cfg']] += 1
                assert e['selection_eligible_ordinal'] == ordinals[e['cfg']]
                chosen = (ordinals[e['cfg']] - 1) % policy['every'] == 0
            else:
                assert e['selection_eligible_ordinal'] is None
            assert e['selection_sparse_chosen'] == chosen
            assert bool(e['sparse_layers']) == chosen
            if eligible and not chosen:
                assert e['action'] == 'dense' and e['source']['kind'] == 'dense' and e['inserted_into_true_dense_history']
        for ref in e['references_read'] + e['true_dense_before']:
            assert ref['context'] == context and ref['group'] == [2, 28]
            assert ref['cfg'] == e['cfg'] and ref['epoch'] == e['epoch'] and ref['call'] < call
            assert ref == sources[ref['call']], 'Reference differs from its actual prior refresh event'
        assert all(ref['kind'] == 'dense' for ref in e['true_dense_before'])
        if e['action'] == 'cache' and any(ref['kind'] == 'sparse' for ref in e['references_read']):
            hits.append(call)
        if 'source' in e:
            source = e['source']
            assert source['context'] == context and source['group'] == [2, 28]
            assert source['cfg'] == e['cfg'] and source['epoch'] == e['epoch'] and source['call'] == call
            assert source['probe_exact_operator'] is True
            assert trace['deep_executed'] and not e['official_skipped']
            sources[call] = source
        if e['sparse_layers']:
            assert sparse_allowed and e['action'] == 'sparse'
            assert e['paid_probe'] and e['two_past_true_dense'] and len(e['true_dense_before']) == 2
            assert not e['warm_start'] and not e['inserted_into_true_dense_history']
            assert e['source']['kind'] == 'sparse'
            assert policy is not None and e['sparse_layers'] == policy['sparse_layers']
            assert [v['layer'] for v in e['operator_metadata']] == e['sparse_layers']
            for op in e['operator_metadata']:
                assert 'CPU_STAND_IN_NOT_SPARSE_KERNEL' not in json.dumps(op)
                assert 0 < op['selected_fraction'] <= 1 and math.isfinite(op['selected_fraction'])
                assert op['executed_fraction'] == op['selected_fraction']
            sparse.append(call)
            operators += len(e['operator_metadata'])
        elif 'source' in e:
            assert e['source']['kind'] == 'dense' and e['inserted_into_true_dense_history']
        if 'source' in e and e['source']['kind'] == 'dense':
            true_history[e['cfg']] = (true_history[e['cfg']] + [e['source']])[-2:]
        if e['native_cycle_reset']:
            assert call == 70
            true_history = [[], []]
            ordinals = [0, 0]
    assert all(ref['kind'] == 'dense' for w in report['true_dense_history'] for ref in w)
    assert true_history == report['true_dense_history']
    if policy is not None:
        assert report['selection_counters'] == ordinals == [0, 0]
        assert report['required_dense_fallback_layers'] == [6, 23, 27]
    return {'status': 'SOURCE_CFG_GROUP_EPOCH_WARM_FALLBACK_TRUE_DENSE_ISOLATION_PASS',
            'sparse_CFG_calls': sparse, 'sparse_attention_operators': operators,
            'cache_calls_reading_approximate': hits}


def binding(r):
    assert r['run_card']=='WC-SELECTIVE-HUMAN-R1-20261004-A'
    assert r['scope']['run_id']=='wc-selective-human-r1'
    assert r['planned_total_phases']==r['planned_output_files']==6
    assert r['role']=='OFFLINE_SELECTIVE_FIXED_MASK_DIAGNOSTIC_NOT_DEPLOYMENT_POLICY'
    assert r['scope']['sample_names']==['human_199']
    context=r['reference_context'];mask=r['fixed_mask']
    assert context==r['reference_contexts'][0]==['wc-selective-human-r1:human_199',mask['model_id'],mask['condition_id']]
    assert mask['role']=='OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'
    assert mask['source_receipt_sha256']==r['scope']['mask_source_receipt_sha256']=='29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae'
    assert mask['horizon']==70 and mask['warm_calls']==14
    assert len(mask['dense_calls'])==72 and sum(mask['dense_calls'])==38 and all(type(v) is bool for v in mask['dense_calls'])
    assert all(mask['dense_calls'][:14]+mask['dense_calls'][70:])
    expected=[{'sparse_layers':FULL,'every':1},{'sparse_layers':[2,3,5],'every':1},{'sparse_layers':FULL,'every':2}]
    assert len(r['policies'])==3
    for actual,target in zip(r['policies'],expected):
        assert all(actual[k]==v for k,v in target.items())
    return context,mask


def phase_provenance(p,context,mask,*,sparse_allowed):
    report=p['refresh_provenance']
    assert report['fixed_mask']==mask and report['online_policy'] is False and report['causal_refresh_value_labels'] is False
    assert [v['deep_executed'] for v in p['trace']]==mask['dense_calls']
    assert len(report['events'])==72
    for e,dense in zip(report['events'],mask['dense_calls']):
        assert e['fixed_diagnostic_mask'] is True and e['selected_fixed_skip']==(not dense)
    return provenance_audit(p,context,sparse_allowed=sparse_allowed)


def control(r,directory):
    context,mask=binding(r)
    result=base.dense_control(r,directory)
    assert result['files'][0]['sha256']==result['files'][1]['sha256']==D_SHA
    a,b=r['dense_control']['phases'];assert [v['deep_executed'] for v in a['trace']]==mask['dense_calls']
    result['files'][1]['provenance']=phase_provenance(b,context,mask,sparse_allowed=False)
    result.update(status='SELECTIVE_DD_TWO_OUTPUT_AUDIT_PASS_SIX_CARD_PENDING',planned_phases=6,planned_outputs=6,
                  fixed_mask=mask,reference_context=context)
    return result


def audit(r,directory):
    binding(r)
    if r['status']!='SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT':
        return {'status':'INCOMPLETE_SELECTIVE_SIX_CARD_NOT_ACCEPTED','planned_outputs':6,
            'runner_status':r['status'],'error':r.get('error'),'present_files':[str(p) for p in directory.rglob('*.mp4')],
            'files':[],'quality_acceptance':False}
    result=control(r,directory);context,mask=result['reference_context'],result['fixed_mask'];q=r['measurement']
    assert q['status']=='SELECTIVE_D_AND_THREE_S_OUTPUTS_REQUIRE_METRICS'
    assert q['planned_phases']==q['planned_outputs']==len(q['phases'])==4
    assert q['sequence']==['official','candidate','candidate','candidate']==[p['kind'] for p in q['phases']]
    assert q['sequence_policy']=='reference_then_candidates' and q['context']==context
    assert q['variant_names']==['fixed_D','full_S','small_S','cadenced_S']
    assert not q['diagnostic_observers'] and q['performance_sample'] and q['fresh_prepare_per_phase']
    assert not q['checkpoint_restore'] and not q['per_forward_tensor_diagnostic_hashes']
    assert q['refresh_condition_content_hashes_retained'] and q['refresh_ledger_and_kernel_checks_counted_in_wall']
    assert q['timing_wrappers_CUDA_boundary_sync_only']
    files=[]
    for i,p in enumerate(q['phases']):
        assert p['index']==i and 'observers' not in p
        assert p['sampling']==r['dense_control']['phases'][0]['sampling']
        if i:assert p['refresh_provenance']['selection_policy']==r['policies'][i-1]
        path=directory/'measurement'/'human_199'/(str(i).zfill(3)+'_'+p['kind'])/'human_199.mp4'
        validator=lambda phase,ctx,**kw:phase_provenance(phase,ctx,mask,**kw)
        info=base.phase_audit(p,path,context=context,sparse_allowed=i>0,provenance_validator=validator)
        if not i:info['provenance']=validator(p,context,sparse_allowed=False)
        info.update(variant=q['variant_names'][i],performance_sample=True)
        files.append(info)
    assert files[0]['sha256']==D_SHA and files[1]['sha256']==S_SHA
    result['files'].extend(files)
    assert len(result['files'])==len(list(directory.rglob('*.mp4')))==6
    assert all(p['deep_CFG_calls']==38 for p in result['files'])
    assert all(p['provenance']['sparse_attention_operators']>0 for p in files[1:])
    assert files[1]['provenance']['sparse_CFG_calls']==files[2]['provenance']['sparse_CFG_calls']
    assert set(files[3]['provenance']['sparse_CFG_calls'])<set(files[1]['provenance']['sparse_CFG_calls'])
    dense=files[0]['pipeline_wall_seconds']
    result.update(status='SIX_SELECTIVE_SOURCE_POLICY_MASK_VIDEO_AUDIT_PASS_NOT_QUALITY',measurement_outputs=4,
        measurement_files=files,descriptive_timings=[{'variant':p['variant'],'seconds':p['pipeline_wall_seconds'],
            'D_over_variant':dense/p['pipeline_wall_seconds'],'wall_reduction_fraction':1-p['pipeline_wall_seconds']/dense} for p in files],
        quality_acceptance=False,independent_confirmation=False,deployment_speed_claim=False,
        limits=['One exposed human seed0, offline38-deep mask, one run per variant; no CONF or replicated speed result.',
            'Exact historical D/full-S references are reuse/implementation controls, not independent quality confirmation.',
            'D/D observer timing excluded; all four measurement phases include necessary selection/source/kernel costs.',
            'Whole-group mixed-layer residual remains approximate; true-D cadence sources are on this arm trajectory.',
            'WC-relative encoded proxies are not Native, semantic or physics acceptance.'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('directory','receipt','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--control-only',action='store_true');a=p.parse_args()
    r=json.loads(a.receipt.read_text());result=(control if a.control_only else audit)(r,a.directory)
    result.update(receipt_sha256=base.sha(a.receipt),audit_code_sha256=base.sha(Path(__file__)),
        reused_primitives_sha256=base.sha(Path(__file__).with_name('audit_wc_light_output_receipts.py')))
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'files':len(result['files']),'quality_acceptance':False}))
