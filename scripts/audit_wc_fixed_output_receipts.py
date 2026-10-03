#!/usr/bin/env python3
"""Independent four-output fixed-mask audit; CPU only, no quality acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('light_receipt_primitives',
    Path(__file__).with_name('audit_wc_light_output_receipts.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
CARD = 'WC-FIXED-HUMAN-R1-20261004-A'
MASK_ROLE = 'OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'


def binding(receipt):
    assert receipt['run_card'] == CARD
    assert receipt['scope']['run_id'] == 'wc-fixed-human-r1'
    assert receipt['planned_total_phases'] == receipt['planned_output_files'] == 4
    assert receipt['role'] == 'OFFLINE_FIXED_MASK_FIDELITY_DIAGNOSTIC_NOT_DEPLOYMENT_POLICY'
    assert receipt['scope']['sample_names'] == ['human_199']
    context = receipt['reference_context']
    assert context == receipt['reference_contexts'][0]
    mask = receipt['fixed_mask']
    assert mask['role'] == MASK_ROLE and mask['sample_name'] == 'human_199'
    assert context == ['wc-fixed-human-r1:human_199', mask['model_id'], mask['condition_id']]
    calls = mask['dense_calls']
    assert len(calls) == 72 and all(type(v) is bool for v in calls) and sum(calls) == 38
    assert mask['horizon'] == 70 and mask['warm_calls'] == 14
    assert all(calls[:14] + calls[70:])
    assert mask['source_receipt_sha256'] == receipt['scope']['mask_source_receipt_sha256'] == '29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae'
    return context, mask


def fixed_provenance(phase, context, mask, *, sparse_allowed):
    report = phase['refresh_provenance']
    assert report['fixed_mask'] == mask
    assert report['online_policy'] is False and report['causal_refresh_value_labels'] is False
    assert [p['deep_executed'] for p in phase['trace']] == mask['dense_calls']
    for e, dense in zip(report['events'], mask['dense_calls']):
        assert e['fixed_diagnostic_mask'] is True
        assert e['selected_fixed_skip'] == (not dense)
        assert e['original_predicate_on_this_arm_state'] is None or type(e['original_predicate_on_this_arm_state']) is bool
    return base.provenance_audit(phase, context, sparse_allowed=sparse_allowed)


def control(receipt, directory):
    context, mask = binding(receipt)
    result = base.dense_control(receipt, directory)
    a, b = receipt['dense_control']['phases']
    assert [p['deep_executed'] for p in a['trace']] == mask['dense_calls']
    result['files'][1]['provenance'] = fixed_provenance(b, context, mask, sparse_allowed=False)
    result.update(status='FIXED_DD_TWO_OUTPUT_AUDIT_PASS_FOUR_CARD_PENDING',
        planned_phases=4, planned_outputs=4, fixed_mask=mask, reference_context=context)
    return result


def audit(receipt, directory):
    binding(receipt)
    if receipt['status'] != 'FOUR_FIXED_DIAGNOSTIC_OUTPUTS_COMPLETE_REQUIRES_INDEPENDENT_AUDIT':
        return {'status':'INCOMPLETE_FIXED_FOUR_CARD_NOT_ACCEPTED', 'planned_outputs':4,
            'runner_status':receipt['status'], 'error':receipt.get('error'),
            'present_files':[str(p) for p in directory.rglob('*.mp4')], 'files':[], 'quality_acceptance':False}
    result = control(receipt, directory)
    context, mask = result['reference_context'], result['fixed_mask']
    q = receipt['measurement']
    assert q['status'] == 'FIXED_D_S_TWO_COMPLETE_OUTPUTS_REQUIRES_METRICS'
    assert q['planned_phases'] == q['planned_outputs'] == len(q['phases']) == 2
    assert q['sequence'] == ['official', 'candidate'] == [p['kind'] for p in q['phases']]
    assert q['context'] == context
    assert q['diagnostic_observers'] is False and q['performance_sample'] is True
    assert q['fresh_prepare_per_phase'] is True and q['checkpoint_restore'] is False
    assert q['per_forward_tensor_diagnostic_hashes'] is False
    assert q['refresh_condition_content_hashes_retained'] is True
    assert q['refresh_ledger_and_kernel_checks_counted_in_wall'] is True
    assert q['timing_wrappers_CUDA_boundary_sync_only'] is True
    files = []
    for index, phase in enumerate(q['phases']):
        assert phase['index'] == index and 'observers' not in phase
        assert phase['sampling'] == receipt['dense_control']['phases'][0]['sampling']
        path = directory/'measurement'/'human_199'/(str(index).zfill(3)+'_'+phase['kind'])/'human_199.mp4'
        info = base.phase_audit(phase, path, context=context, sparse_allowed=index == 1)
        info['provenance'] = fixed_provenance(phase, context, mask, sparse_allowed=index == 1)
        info['performance_sample'] = True
        files.append(info)
    assert result['files'][0]['sha256'] == result['files'][1]['sha256'] == files[0]['sha256']
    result['files'].extend(files)
    assert len(result['files']) == len(list(directory.rglob('*.mp4'))) == 4
    assert all(f['deep_CFG_calls'] == 38 for f in result['files'])
    assert files[1]['provenance']['sparse_attention_operators'] > 0
    d, s = [f['pipeline_wall_seconds'] for f in files]
    result.update(status='FOUR_FIXED_OUTPUT_SOURCE_MASK_VIDEO_AND_COST_STRUCTURE_PASS_NOT_QUALITY',
        measurement_outputs=2, measurement_files=files,
        descriptive_fixed_dense_seconds=d, descriptive_fixed_sparse_seconds=s,
        descriptive_dense_over_sparse_wall=d/s, descriptive_wall_reduction=1-s/d,
        quality_acceptance=False, independent_confirmation=False, deployment_speed_claim=False,
        limits=['One exposed human input/seed with an offline official trace, not online routing or CONF.',
                'Single D/S pair; diagnostic D/D wall excluded; first sparse use retained.',
                'Three dense files match; all four traces share38 deep calls.',
                'Encoded fidelity to WC is not Native, semantic or physics acceptance.',
                'Host substage wall is not isolated CUDA latency.'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('directory', 'receipt', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--control-only', action='store_true')
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    result = (control if args.control_only else audit)(receipt, args.directory)
    result.update(receipt_sha256=base.sha(args.receipt), audit_code_sha256=base.sha(Path(__file__)),
        reused_primitives_sha256=base.sha(Path(__file__).with_name('audit_wc_light_output_receipts.py')))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'], 'files':len(result['files']), 'quality_acceptance':False}))
