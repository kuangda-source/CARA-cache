#!/usr/bin/env python3
"""Independent CPU receipt/encoded-video integrity audit, never a speed claim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

KEYS = ['input_hashes', 'output_hashes', 'trace', 'block_counts',
        'state_fingerprints', 'sampling', 'named_inputs', 'conditions', 'field_signatures']
PIPELINE = ['pipeline_events', 'artifacts', 'flags_before', 'flags_after', 'rng_after']
STEPS = [13, 21, 33, 35, 36]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def phase_audit(phase, path):
    assert phase['status'] == 'COMPLETE_SAMPLE_RETURNED'
    assert phase['solver_steps'] == 36 and phase['actual_cfg_calls_entered'] == 72
    assert len(phase['input_hashes']) == len(phase['output_hashes']) == 72
    assert [p['cache_counter_before'] for p in phase['trace']] == list(range(70)) + [0, 1]
    assert all(p['deep_executed'] for p in phase['trace'][-2:])
    assert phase['sampling']['actual_schedule_steps'] == 36
    assert phase['sampling']['worldcache_horizon'] == 70
    assert phase['sampling']['use_kerras_sigma'] is True
    assert [p['solver_step'] for p in phase['field_signatures']] == STEPS
    assert all('refresh.provenance' not in p['components'] for p in phase['field_signatures'])
    if phase['phase'] == 'restored_full':
        assert [p['solver_step'] for p in phase['roundtrips']] == STEPS
        assert [p['solver_step'] for p in phase['refresh_field_signatures']] == STEPS
    else:
        assert phase['refresh_field_signatures'] == []
    events = phase['pipeline_events']
    assert [v['stage'] for v in events] == ['sample_return', 'decode_input', 'decode_output',
                                          'guardrail_input', 'guardrail_output', 'save_input']
    assert events[2]['value']['shape'] == [1, 3, 93, 432, 768]
    assert events[3]['value']['shape'] == events[4]['value']['shape'] == [93, 432, 768, 3]
    assert events[5]['value']['shape'] == [3, 93, 432, 768]
    assert all(v['value'].get('finite') is True for v in events)
    artifact, = phase['artifacts']
    assert path.name == artifact['name'] and path.stat().st_size == artifact['bytes']
    assert sha(path) == artifact['sha256']
    command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,nb_read_frames', '-of', 'json', str(path)]
    probe = json.loads(subprocess.check_output(command, text=True, timeout=60))['streams'][0]
    assert probe['width'] == 768 and probe['height'] == 432 and int(probe['nb_read_frames']) == 93
    a, b = [int(v) for v in probe['r_frame_rate'].split('/')]
    assert a / b == 16
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0',
        '-f', 'null', '-'], capture_output=True, text=True, timeout=90)
    assert decoded.returncode == 0 and not decoded.stderr.strip(), decoded.stderr
    result = {'path': str(path), 'sha256': artifact['sha256'], 'bytes': artifact['bytes'],
              'ffprobe': probe, 'full93_decode': True, 'solver_updates': 36, 'CFG_calls': 72}
    if 'refresh_provenance' in phase:
        provenance = phase['refresh_provenance']
        rows = provenance['events']
        assert provenance['group'] == [2, 28] and provenance['epoch'] == 1
        assert len(rows) == 72 and rows[69]['native_cycle_reset']
        assert not rows[70]['references_read'] and not rows[71]['references_read']
        assert all(v['action'] == 'dense' for v in rows[:14] + rows[70:])
        sparse = []
        approximate_hits = []
        for call, (row, trace) in enumerate(zip(rows, phase['trace']), 1):
            assert row['call'] == call and row['cfg'] == (call - 1) % 2
            assert row['counter'] == trace['cache_counter_before']
            assert row['official_skipped'] == (not trace['deep_executed'])
            for reference in row['references_read']:
                assert reference['call'] < call and reference['cfg'] == row['cfg']
                assert reference['epoch'] == row['epoch'] and reference['group'] == [2, 28]
                assert reference['context'] == provenance['context']
            if row['action'] == 'cache' and any(v['kind'] == 'sparse' for v in row['references_read']):
                approximate_hits.append(call)
            if row['sparse_layers']:
                sparse.append(call)
                assert row['action'] == 'sparse' and row['paid_probe'] and row['two_past_true_dense']
                assert not row['warm_start'] and not row['inserted_into_true_dense_history']
                assert row['source']['kind'] == 'sparse'
                assert row['sparse_layers'] == [v for v in range(2, 28) if v not in (6, 23, 27)]
                for metadata in row['operator_metadata']:
                    assert 'CPU_STAND_IN_NOT_SPARSE_KERNEL' not in metadata
                    assert 0 < metadata['selected_fraction'] <= 1
                    assert metadata['executed_fraction'] == metadata['selected_fraction']
            elif 'source' in row:
                assert row['source']['kind'] == 'dense' and row['inserted_into_true_dense_history']
            assert all(v['kind'] == 'dense' for v in row['true_dense_before'])
        assert all(v['kind'] == 'dense' for window in provenance['true_dense_history'] for v in window)
        result['sparse_calls'] = sparse
        result['cache_hits_with_approximate_reference'] = approximate_hits
        result['provenance'] = 'SOURCE_CFG_GROUP_EPOCH_WARM_FALLBACK_TRUE_DENSE_ISOLATION_PASS'
    return result


def audit_dense_control(receipt, directory):
    """Verify the completed control while retaining the entire six-output scope."""
    control = receipt['dense_control']
    assert control['status'] == 'OFFICIAL_DENSE_ADAPTER_FULL_PIPELINE_DD_GATE_PASS'
    left, right = control['phases']
    assert all(left[k] == right[k] for k in KEYS + PIPELINE)
    prepared = control['prepared_input_calls']
    assert len(prepared) == 2 and prepared[0]['prepared'] == prepared[1]['prepared']
    sample = receipt['scope']['sample_names'][0]
    files = [phase_audit(phase, directory / 'dense-control' / sample /
        phase['phase'] / (sample + '.mp4')) for phase in control['phases']]
    return {'status': 'DD_TWO_OUTPUT_INDEPENDENT_AUDIT_PASS_ENTIRE_CARD_PENDING',
            'runner_status': receipt['status'], 'planned_phases': 6, 'planned_outputs': 6,
            'files': files, 'native_nine_keys_recomputed': KEYS,
            'pipeline_five_keys_recomputed': PIPELINE,
            'quality_acceptance': False, 'clean_E2E_speed_claim': False}


def audit(receipt, directory):
    result = {'runner_status': receipt['status'], 'planned_phases': 6, 'planned_outputs': 6,
              'clean_E2E_speed_claim': False, 'files': []}
    if receipt['status'] != 'COMPLETE_SIX_OUTPUTS_DD_AND_TWO_WC_S_PAIRS_REQUIRES_AUDIT':
        result.update(status='INCOMPLETE_CARD_NOT_ACCEPTED', error=receipt.get('error'),
                      present_outputs=[str(p) for p in directory.glob('**/*.mp4')])
        return result
    result['files'] = audit_dense_control(receipt, directory)['files']
    requests = receipt['comparison']['requests']
    assert [r['sample_name'] for r in requests] == receipt['scope']['sample_names']
    hybrid = []
    for request in requests:
        left, right = request['phases']
        assert request['status'] == 'FULL36_CFG72_CLOSED_LOOP_INTERFACE_PASS_NOT_QUALITY'
        assert left['sampling'] == right['sampling'] and left['conditions'] == right['conditions']
        assert left['named_inputs'][0] == right['named_inputs'][0]
        assert all(left[k] == right[k] for k in ['flags_before', 'flags_after', 'rng_after'])
        prepared = request['prepared_input_calls']
        assert len(prepared) == 2 and prepared[0]['prepared'] == prepared[1]['prepared']
        sample = request['sample_name']
        for phase in request['phases']:
            info = phase_audit(phase, directory / 'comparison' / sample / phase['phase'] / (sample + '.mp4'))
            result['files'].append(info)
        info = result['files'][-1]
        hybrid.append(bool(info['sparse_calls'] and info['cache_hits_with_approximate_reference']))
    assert len(result['files']) == len(list(directory.glob('**/*.mp4'))) == 6
    result.update(status='COMPLETE_SIX_OUTPUT_STRUCTURAL_DD_PROVENANCE_AUDIT_PASS',
                  WC_S_hybrid_observed_per_request=hybrid, quality_acceptance=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path,
                        help='Use an immutable receipt snapshot outside a running output directory')
    parser.add_argument('--control-only', action='store_true',
                        help='Audit completed DD control without accepting the six-output card')
    args = parser.parse_args()
    receipt_path = args.receipt or args.directory / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    result = (audit_dense_control if args.control_only else audit)(receipt, args.directory)
    result['receipt_sha256'] = sha(receipt_path)
    result['audit_code_sha256'] = sha(Path(__file__))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'files': len(result['files']),
                      'quality_acceptance': False}))
