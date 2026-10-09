#!/usr/bin/env python3
"""Recheck preserved R1 native evidence without rerunning the experiment.

The original capture and its KeyError remain unchanged. A failed final writer
does not reach the success-only eval/parameter fields; all its executed steps,
failure receipt, and full-state restoration are still checked.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import time


PREFIX = 'reports/wc_ra_baseline_sampling_cpu_r1_terminal_20261010_'


def main():
    original = Path(PREFIX+'capture_and_independent_audit.json')
    proof = json.loads(original.read_bytes())
    assert proof['independent_check_failure'] == {'type': 'KeyError', 'error': "'all_modules_eval'"}
    objects = {}
    for name, item in proof['files'].items():
        packed = Path(item['local_path']).read_bytes()
        raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == item['compressed_sha256']
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        if name.endswith('.json'):
            objects[name] = json.loads(raw)
    r, core, reg = (objects[n] for n in ('receipt.json', 'result.json', 'ra-baseline-sampling-preregistration.json'))
    assert r['exit_code'] == r['child_exit_code'] == 0
    assert r['status'] == core['status'] == 'RA_BASELINE_SAMPLING_CPU_NOT_REAL_MODEL'
    assert core['planned_scope'] == reg['CPU_scope'] == r['planned_scope'] == proof['planned_scope']
    assert core['payload_sha256'] == reg['payload_sha256'] == r['payload_after_sha256']
    assert r['result_sha256'] == proof['files']['result.json']['sha256']
    assert not core['CUDA_initialized'] and core['GPU_submissions'] == 0
    assert not r['ledger_written_by_this_driver'] and proof['CPU_never_writes_ledger']
    assert (core['solver_updates'], core['net_calls'], core['actual_guided_tensors_reloaded'], core['actual_final_latents_reloaded']) == (864, 1728, 432, 12)
    assert len(core['checks']) == 4
    assert {(x['flow'], x['scenario']) for x in core['checks']} == {(f, s) for f in (False, True) for s in ('complete', 'last_vector_writer_failure')}
    actual = {x['path']: x for x in proof['actual_tensor_files']}
    recorded = set()
    assert len(actual) == 22
    old = json.loads(gzip.decompress(Path(reg['calibration_batch_CPU_result_ref']).read_bytes()))
    completed = failed = paths = 0
    for check in core['checks']:
        state = check['receipt']
        assert state['planned_paths'] == state['planned_videos'] == 6 and state['teacher_calls'] == 0
        assert state['initial_state_restored'] and len(state['requests']) == 2
        for request in state['requests']:
            rows = request['paths']
            assert len(rows) == 3 and [x['method'] for x in rows] == ['WC', 'JOINT_NATIVE', 'RA']
            for row in rows:
                paths += 1
                assert len(row['guided_sha256']) == len(row['solver_returns']) == 36
                assert row['counters'] == list(range(0, 70, 2))+[0]
                assert row['actions'][:7] == ['DD']*7 and row['actions'][-1] == 'DD'
                assert len(row['actions']) == len(row['block_visits']) == 36
                assert row['conditions_before'] == row['conditions_after'] == rows[0]['conditions_before']
                assert row['first_velocity_input_sha256'] == rows[0]['first_velocity_input_sha256']
                assert row['rng_after'] == rows[0]['rng_after']
                assert [x['step'] for x in row['checkpoints']] == [13, 21, 33, 35, 36]
                assert all(len(x['components']) == 50 for x in row['checkpoints'])
                if row['status'] == 'COMPLETE_PATH':
                    assert row['all_modules_eval'] and row['parameter_versions_unchanged']
                    completed += 1
                else:
                    assert check['scenario'] == 'last_vector_writer_failure'
                    assert row is state['requests'][-1]['paths'][-1]
                    assert row['status'] == 'METHOD_FAILED_COMPLETE_SCOPE_RETAINED'
                    assert row['error'] == 'Injected last complete RA method vector writer failure'
                    assert 'vector_artifact' not in row
                    # These success-only fields are set after the injected write.
                    assert 'all_modules_eval' not in row and 'parameter_versions_unchanged' not in row
                    failed += 1
                for action, visits in zip(row['actions'], row['block_visits']):
                    assert visits == [[1, 1]+[int(a == 'D')]*(row['layers']-2) for a in action]
                if row['method'] == 'WC':
                    assert not row['policy_history'] and not row['prefix_decisions']
                else:
                    assert [h['step'] for h in row['policy_history']] == list(range(1, 37))
                    assert [h['action'] for h in row['policy_history']] == row['actions']
                    assert [d['step'] for d in row['prefix_decisions']] == list(range(8, 36))
                    for d in row['prefix_decisions']:
                        t = d['step']; packets = d['paid_probes']
                        assert d['prefix_visits_before_deep'] == [[1, 1]+[0]*(row['layers']-2)]*2
                        assert [(p['slot'], p['counter']) for p in packets] == [(0, 2*(t-1)), (1, 2*(t-1)+1)]
                        assert d['action'] == row['actions'][t-1]
                        if row['method'] == 'JOINT_NATIVE':
                            assert d['action'] == ('CC' if all(p['native_cache'] for p in packets) else 'DD')
                    if row['method'] == 'RA':
                        assert row['RA_threshold'] == state['RA_threshold'] and row['calibration_fingerprint'] == state['calibration_fingerprint']
                if 'vector_artifact' in row:
                    art = row['vector_artifact']; raw = actual[art['path']]
                    assert raw['bytes'] == art['bytes'] and raw['sha256'] == art['sha256']
                    recorded.add(art['path'])
        if check['scenario'] == 'complete':
            assert check['status'] == 'PASS' and len(check['semantic_mutation_refusals']) == 6
            audit = check['actual_tensor_audit']
            assert audit['actual_guided_tensors_reloaded'] == 216 and audit['actual_final_latents_reloaded'] == 6
            assert audit['actual_initial_7_DD_guided_direct_equal'] and len(audit['files']) == 6
            assert check['actual_final_method_truncation_refused']
            initialized = check['threshold_initialization']
            assert initialized['rule'] == 'MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS'
            prior = next(x for x in old['checks'] if x['status'] == 'PASS' and x['flow'] == check['flow'])
            table = prior['actual_tensor_audit']['table']
            assert table['toy_only_not_Cosmos_calibration']
            assert initialized['calibration_fingerprint'] == table['fingerprint'] == state['calibration_fingerprint']
            totals = []
            for request in prior['receipt']['requests']:
                history = request['paths'][0]['own_history']
                for anchor, stop in ((7, 13), (13, 19), (19, 25), (25, 31)):
                    total = 0.
                    for t in range(anchor+1, stop+1):
                        a, b = [p['delta_y'] for p in history[t-1]['paid_probes']]
                        total += math.sqrt((8*a-7*b)**2+112*a*b*(1-table['rho_prior']))*table['gains'][str(t)]
                    totals.append(total)
            assert len(initialized['observed_intervals']) == 8
            assert math.isclose(median(totals), state['RA_threshold'], rel_tol=1e-12)
            assert not initialized['endpoint_quality_used_to_choose_threshold']
            assert not initialized['matches_actual_RA_time_or_dense_count']
        else:
            assert check['status'] == 'EXPECTED_FAILURE' and check['complete_scope_retained']
            assert check['initial_full_state_restored']
    assert (paths, completed, failed) == (24, 22, 2) and recorded == set(actual)
    result = {
        'status': 'RA_BASELINE_R1_RETAINED_COMPLETE_CPU_NATIVE_AUDIT_PASSED',
        'original_capture_failure_preserved': str(original),
        'original_capture_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
        'source_revision': proof['source_revision'], 'original_pids_absent': proof['original_pids_absent'],
        'CPU_wall_seconds': proof['CPU_wall_seconds'], 'core_CPU_wall_seconds': core['CPU_wall_seconds'],
        'complete_executed_paths': paths, 'successful_fixture_paths': 12,
        'completed_paths_including_expected_failure_scenarios': completed,
        'last_writer_failure_controls': failed, 'solver_updates': 864, 'net_calls': 1728,
        'actual_guided_reloaded': 432, 'actual_latents_reloaded': 12,
        'semantic_mutation_refusals': 12, 'actual_last_method_truncation_refusals': 2,
        'actual_retained_Toy_tensor_file_size_and_hash_bindings': 22,
        'independently_reconstructed_eight_interval_initial_thresholds': 2,
        'native_bytes_preserved_and_verified': True, 'GPU_submissions': 0,
        'CPU_or_GPU_experiment_reruns': 0, 'ledger_writes': 0,
        'real_model_or_video_or_quality_or_speed_claim': False, 'observed_unix': time.time(),
    }
    target = Path(PREFIX+'retained_independent_audit.json')
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
