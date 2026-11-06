#!/usr/bin/env python3
"""Independent original-receipt/video audit for the ten-output light card.

No Torch import, generation, budget change or quality acceptance. Diagnostic
control timings never enter the eight deployment measurements.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

KEYS = ['input_hashes', 'output_hashes', 'trace', 'block_counts',
        'state_fingerprints', 'sampling', 'named_inputs', 'conditions', 'field_signatures']
PIPELINE = ['prepared', 'pipeline_witnesses', 'artifacts', 'flags_before', 'flags_after', 'rng_after']
STEPS = [13, 21, 33, 35, 36]
STAGES = ['sample_return', 'decode_input', 'decode_output',
          'guardrail_input', 'guardrail_output', 'save_input']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def state_digest(fields):
    """Hash an observed mapping of component SHA strings, not tensor contents."""
    h = hashlib.sha256()
    for key in sorted(fields):
        assert isinstance(key, str) and isinstance(fields[key], str) and len(fields[key]) == 64
        int(fields[key], 16)
        h.update(key.encode())
        h.update(repr(fields[key]).encode())
    return h.hexdigest()


def provenance_audit(phase, context, *, sparse_allowed):
    report = phase['refresh_provenance']
    assert report['context'] == context and report['group'] == [2, 28] and report['epoch'] == 1
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
            assert e['sparse_layers'] == [v for v in range(2, 28) if v not in (6, 23, 27)]
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
    assert all(ref['kind'] == 'dense' for w in report['true_dense_history'] for ref in w)
    assert true_history == report['true_dense_history']
    return {'status': 'SOURCE_CFG_GROUP_EPOCH_WARM_FALLBACK_TRUE_DENSE_ISOLATION_PASS',
            'sparse_CFG_calls': sparse, 'sparse_attention_operators': operators,
            'cache_calls_reading_approximate': hits}


def phase_audit(phase, path, *, context, sparse_allowed, provenance_validator=None):
    assert phase['status'] == 'COMPLETE36_CFG72_ORDINARY_RETURN_NO_QUALITY_ACCEPTANCE'
    assert phase['solver_steps'] == 36 and phase['CFG_calls'] == 72 and phase['prepare_calls'] == 1
    assert len(phase['trace']) == 72
    assert [p['cache_counter_before'] for p in phase['trace']] == list(range(70)) + [0, 1]
    assert all(p['deep_executed'] for p in phase['trace'][-2:])
    sampling = phase['sampling']
    assert sampling['requested_steps'] == 35 and sampling['actual_schedule_steps'] == 36
    assert len(sampling['timesteps']) == 36 and sampling['worldcache_horizon'] == 70
    assert sampling['use_kerras_sigma'] is True and phase['substage_cuda_isolated'] is False
    assert phase['pipeline_wall_seconds'] > 0 and math.isfinite(phase['pipeline_wall_seconds'])
    assert set(phase['substage_host_wall']) == {'prepare', 'sample', 'decode', 'video_guardrail', 'write'}
    assert all(v['calls'] == 1 and v['seconds'] > 0 and math.isfinite(v['seconds'])
               for v in phase['substage_host_wall'].values())
    events = phase['pipeline_events']
    assert [v['stage'] for v in events] == STAGES
    assert events[2]['value']['shape'] == [1, 3, 93, 432, 768]
    assert events[3]['value']['shape'] == events[4]['value']['shape'] == [93, 432, 768, 3]
    assert events[5]['value']['shape'] == [3, 93, 432, 768]
    artifact, = phase['artifacts']
    assert path.name == artifact['name'] and path.stat().st_size == artifact['bytes']
    assert sha(path) == artifact['sha256']
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
        '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_read_frames',
        '-of', 'json', str(path)], text=True, timeout=90))['streams'][0]
    assert probe['width'] == 768 and probe['height'] == 432 and int(probe['nb_read_frames']) == 93
    numerator, denominator = map(int, probe['r_frame_rate'].split('/'))
    assert numerator / denominator == 16
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(path),
        '-map', '0:v:0', '-f', 'null', '-'], capture_output=True, text=True, timeout=90)
    assert decoded.returncode == 0 and not decoded.stderr.strip(), decoded.stderr
    info = {'path': str(path), 'sha256': artifact['sha256'], 'bytes': artifact['bytes'],
        'ffprobe': probe, 'full93_decode': True, 'index': phase['index'], 'kind': phase['kind'],
        'pipeline_wall_seconds': phase['pipeline_wall_seconds'],
        'deep_CFG_calls': sum(v['deep_executed'] for v in phase['trace'])}
    if phase['kind'] == 'candidate':
        validator = provenance_validator or provenance_audit
        info['provenance'] = validator(phase, context, sparse_allowed=sparse_allowed)
    return info


def dense_control(receipt, directory):
    d = receipt['dense_control']
    assert d['status'] == 'FRESH_PREPARE_LIGHT_DD_NINE_AND_FINAL_PIPELINE_PASS'
    assert d['diagnostic_observers'] and not d['performance_sample']
    assert d['fresh_prepare_per_phase'] and not d['checkpoint_restore']
    assert d['planned_phases'] == d['planned_outputs'] == 2
    assert d['sequence'] == ['official', 'candidate'] == [p['kind'] for p in d['phases']]
    a, b = d['observers']
    nine = {key: a[key] == b[key] for key in KEYS}
    pipeline = {key: a[key] == b[key] for key in PIPELINE}
    assert all(nine.values()) and all(pipeline.values())
    assert nine == d['nine_checks'] and pipeline == d['pipeline_checks']
    for row, phase in zip((a, b), d['phases']):
        assert all(row[key] == phase[key] for key in
            ('trace', 'block_counts', 'sampling', 'artifacts', 'flags_before', 'flags_after', 'rng_after'))
    for row in (a, b):
        assert row['steps'] == 36
        assert len(row['input_hashes']) == len(row['output_hashes']) == len(row['named_inputs']) == len(row['conditions']) == 72
        assert [f['solver_step'] for f in row['field_signatures']] == STEPS
        assert len(row['state_fingerprints']) == 5
        for fields, digest in zip(row['field_signatures'], row['state_fingerprints']):
            components = fields['components']
            assert len(components) >= 36 and 'refresh.provenance' not in components
            assert 'output' in components and 'explicit_generators' in components and 'cuda_rng' in components
            assert state_digest(components) == digest
            false_digest = hashlib.sha256(repr(False).encode()).hexdigest()
            assert all(value == false_digest for key, value in components.items() if key.startswith('mode.'))
        assert [v['stage'] for v in row['pipeline_witnesses']] == STAGES
        assert all(v['value']['finite'] for v in row['pipeline_witnesses'])
    sample = receipt['scope']['sample_names'][0]
    files = [phase_audit(p, directory / 'dense-control' / (str(p['index']).zfill(3) + '_' + p['kind']) /
        (sample + '.mp4'), context=d['context'], sparse_allowed=False) for p in d['phases']]
    assert len(files) == 2 and files[0]['sha256'] == files[1]['sha256']
    return {'status': 'LIGHT_DD_TWO_OUTPUT_INDEPENDENT_AUDIT_PASS_TEN_CARD_PENDING',
        'planned_phases': 10, 'planned_outputs': 10, 'files': files,
        'nine_checks_recomputed': nine, 'pipeline_checks_recomputed': pipeline,
        'state_components_per_checkpoint': [len(f['components']) for f in a['field_signatures']],
        'CPU_only': True, 'quality_acceptance': False, 'deployment_speed_claim': False}


def audit(receipt, directory):
    if receipt['status'] != 'TEN_OUTPUT_LIGHT_PIPELINE_COMPLETE_REQUIRES_INDEPENDENT_AUDIT':
        return {'status':'INCOMPLETE_TEN_CARD_NOT_ACCEPTED', 'planned_outputs':10,
            'runner_status':receipt['status'], 'error':receipt.get('error'),
            'present_files':[str(p) for p in directory.rglob('*.mp4')], 'files':[], 'quality_acceptance':False}
    assert receipt['planned_total_phases'] == receipt['planned_output_files'] == 10
    result = dense_control(receipt, directory)
    requests = receipt['measurements']['requests']
    assert [q['sample_name'] for q in requests] == receipt['scope']['sample_names']
    groups, first_sparse_seen = [], False
    for q, context, sequence in zip(requests, receipt['reference_contexts'], receipt['scope']['measurement_sequences']):
        assert q['status'] == 'BALANCED_FOUR_COMPLETE_OUTPUTS_REQUIRES_METRICS'
        assert not q['diagnostic_observers'] and q['performance_sample'] and q['fresh_prepare_per_phase']
        assert not q['checkpoint_restore'] and not q['per_forward_tensor_diagnostic_hashes']
        assert q['refresh_condition_content_hashes_retained'] and q['refresh_ledger_and_kernel_checks_counted_in_wall']
        assert q['planned_phases'] == q['planned_outputs'] == len(q['phases']) == 4
        assert q['sequence'] == sequence == [p['kind'] for p in q['phases']]
        assert q['context'] == context
        assert all(p['sampling'] == q['phases'][0]['sampling'] for p in q['phases'])
        assert q['phases'][0]['sampling'] == receipt['dense_control']['phases'][0]['sampling']
        files = []
        for index, p in enumerate(q['phases']):
            assert p['index'] == index and 'observers' not in p
            path = directory / 'measurement' / q['sample_name'] / (str(index).zfill(3) + '_' + p['kind']) / (q['sample_name'] + '.mp4')
            f = phase_audit(p, path, context=context, sparse_allowed=True)
            f['performance_sample'] = True
            sparse = p['kind'] == 'candidate' and bool(f['provenance']['sparse_CFG_calls'])
            f['first_sparse_pipeline_in_card'] = sparse and not first_sparse_seen
            first_sparse_seen = first_sparse_seen or sparse
            files.append(f)
        means = {kind: statistics.mean(f['pipeline_wall_seconds'] for f in files if f['kind'] == kind)
                 for kind in ('official', 'candidate')}
        groups.append({'sample_name':q['sample_name'], 'sequence':sequence, 'files':files,
            'all_runs_included':True, 'official_mean_seconds':means['official'],
            'candidate_mean_seconds':means['candidate'],
            'official_over_candidate_mean_wall':means['official']/means['candidate'],
            'repeat_artifact_SHA_equal':{kind:len({f['sha256'] for f in files if f['kind']==kind})==1
                                       for kind in ('official','candidate')}})
        result['files'].extend(files)
    assert len(result['files']) == len(list(directory.rglob('*.mp4'))) == 10
    result.update(status='TEN_LIGHT_OUTPUT_STRUCTURAL_DD_PROVENANCE_AND_TIMING_AUDIT_PASS_NOT_QUALITY',
        measurement_groups=groups, measurement_outputs=8, first_sparse_use_preserved=first_sparse_seen,
        deployment_speed_claim=False,
        limits=['D/D observer timing excluded; all eight deployment runs included.',
            'Two repeats on exposed CAL inputs are descriptive, not independent confirmation.',
            'No full tensor condition/input hashes in light measurements; D/D alone has strict nine-field comparisons.',
            'Video fidelity to official WC is not native full-compute, semantic or physics acceptance.',
            'Host substage wall is not isolated CUDA latency.'])
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--control-only', action='store_true')
    args = p.parse_args()
    r = json.loads(args.receipt.read_text())
    result = (dense_control if args.control_only else audit)(r, args.directory)
    result.update(receipt_sha256=sha(args.receipt), audit_code_sha256=sha(Path(__file__)))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status':result['status'], 'files':len(result['files']), 'quality_acceptance':False}))
