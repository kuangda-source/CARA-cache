#!/usr/bin/env python3
"""Collect the original local CPU once after ETA, then accept the stored capture."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.frozen_shared_execution_r1 import AVAILABLE_METHODS, point


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=sha(raw), value=json.loads(raw))


def collect(launch):
    if time.time() < launch['first_collection_not_before_unix']:
        raise ValueError('Wait until the single estimated collection time; do not poll partial progress')
    process = subprocess.run(['ps', '-p', str(launch['pid']), '-o', 'pid=,lstart=,command='],
                             text=True, capture_output=True, timeout=10)
    state = process.stdout.strip()
    capture = dict(captured_unix=time.time(), launch=launch, process_at_collection=state,
                   process_returncode=process.returncode, SSH_queries=0, GPU_submissions=0)
    if state:
        capture['status'] = 'ORIGINAL_CPU_HANDLE_STILL_PRESENT_NO_PARTIAL_READ'
        return capture
    capture['status'] = 'ORIGINAL_CPU_TERMINAL_CAPTURE'
    capture['registration'] = read(ROOT / launch['registration_ref'])
    source = ROOT / launch['test_source_ref']
    capture['payload_actual_sha256'] = {
        n: sha((source / n).read_bytes()) for n in launch['payload_sha256']}
    capture['exit'] = read(ROOT / launch['exit_ref'])
    result = ROOT / launch['result_ref']
    if not result.exists():
        failure = result.with_suffix('.failure.json')
        capture['failure'] = read(failure) if failure.exists() else None
        return capture
    capture['result'] = read(result)
    runtime = ROOT / launch['runtime_ref']
    capture['runtime_actual_sha256'] = {
        str(p.relative_to(runtime)): sha(p.read_bytes()) for p in runtime.rglob('*.py')}
    profiles, mocks = {}, {}
    for flow in capture['result']['value']['checks']:
        for profile in flow['profiles']:
            profiles[profile['ref']] = read(profile['ref'])
        for check in flow['checks']:
            for mock in check['mock_paths']:
                mocks[mock] = read(mock)
    capture.update(profiles=profiles, mocks=mocks)
    return capture


def accept(capture):
    assert capture['status'] == 'ORIGINAL_CPU_TERMINAL_CAPTURE'
    assert capture['process_at_collection'] == '' and capture['process_returncode'] == 1
    launch = capture['launch']
    assert capture['captured_unix'] >= launch['first_collection_not_before_unix']
    assert launch['expected_CPU_paths'] == 102 and launch['expected_pairs'] == 3516
    registration, terminal = capture['registration']['value'], capture['exit']['value']
    assert capture['registration']['sha256'] == launch['registration_sha256']
    assert capture['payload_actual_sha256'] == registration['payload_sha256'] == launch['payload_sha256']
    assert terminal['exit_code'] == 0 and terminal['pid'] == launch['pid']
    result = capture['result']['value']
    assert terminal['source_revision'] == result['source_revision'] == launch['source_revision']
    assert terminal['result_sha256'] == capture['result']['sha256']
    assert result['source_sha256'] == launch['payload_sha256']
    assert result['runtime_source_sha256'] == capture['runtime_actual_sha256']
    assert not result['CUDA_initialized'] and result['actual_CPU_paths'] == 102
    assert {row['flow'] for row in result['checks']} == {False, True}
    expected = {(flow, method) for flow in (False, True) for method in AVAILABLE_METHODS}
    indexed = {(group['flow'], check['method']): check
               for group in result['checks'] for check in group['checks']}
    assert set(indexed) == expected and len(indexed) == 34
    pairs = 0
    for (flow, method), check in indexed.items():
        updates = point(method)['actual_updates']
        assert check['flow'] is flow and check['seed'] == 17 and check['actual_updates'] == updates
        assert check['original_guided_sha256'] == check['profile_guided_sha256']
        assert len(check['original_guided_sha256']) == updates
        assert check['all_components_released']
        assert len(check['mock_paths']) == 3 and len(set(check['mock_paths'])) == 3
        for path in check['mock_paths']:
            assert capture['mocks'][path]['sha256'] == check['mock_sha256']
        pairs += 3 * updates
    assert pairs == 3516 and len(capture['mocks']) == 102
    profiled = {(row['flow'], row['method'], row['mode']): row
                for group in result['checks'] for row in group['profiles']}
    assert set(profiled) == {(f, m, mode) for f, m in expected for mode in ('profile_audit', 'profile_lean')}
    assert len(capture['profiles']) == len(profiled) == 68
    intervals = 0
    for (flow, method, mode), row in profiled.items():
        observed = capture['profiles'][row['ref']]
        assert observed['sha256'] == row['sha256']
        profile = observed['value']
        assert profile['status'] == 'PROFILE_COMPLETE' and profile['device'] == 'cpu'
        assert not profile['peak_reset_before_request']
        for memory in ('memory_before', 'memory_after'):
            assert profile[memory] == dict(available=False, allocated_bytes=None, reserved_bytes=None,
                peak_allocated_bytes=None, peak_reserved_bytes=None)
        assert len(profile['intervals']) == row['intervals']
        counts = Counter()
        sums = Counter()
        for index, span in enumerate(profile['intervals']):
            assert span['id'] == index and (span['parent'] is None or 0 <= span['parent'] < index)
            assert span['outcome'] == 'RETURNED' and span['CUDA_elapsed_ms'] is None
            assert math.isfinite(span['CPU_seconds']) and span['CPU_seconds'] >= 0
            counts[span['component']] += 1
            sums[span['component']] += span['CPU_seconds']
        assert set(counts) == set(profile['components'])
        assert profile['components'] == row['components']
        for component, count in counts.items():
            cell = profile['components'][component]
            assert cell['calls'] == count and cell['inclusive_CPU_seconds'] == sums[component]
            assert cell['inclusive_CUDA_ms'] is None and cell['exceptions'] == 0
        updates = point(method)['actual_updates']
        assert counts['shallow_block'] == 4 * updates  # Declared two-block Toy probe boundary.
        assert counts['solver_update'] == updates and counts['VAE_decode'] == counts['video_write'] == 1
        assert counts['output_head'] >= 2 * updates and counts['method_install_inclusive'] == 1
        intervals += len(profile['intervals'])
    assert all(result[k] == 0 for k in ('weights_loaded', 'GPU_submissions', 'SSH_queries'))
    assert not result['ledger_written'] and not result['CUDA_profile_or_memory_measured']
    return dict(status='DEPLOYMENT_PROFILE_FULL102_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU_PROFILE',
        source_revision=launch['source_revision'], actual_CPU_paths=102,
        ordinary_pairs=pairs, CFG_calls=2 * pairs, profiled_paths=68,
        full_guided_parities=34, profile_audit_lean_parities=34,
        mock_files=102, scalar_profile_intervals=intervals,
        CPU_wall_seconds=result['CPU_wall_seconds'], all_original_components_released=True,
        actual_GPU_peak_or_component_cost_measured=False, final_N09_GPU_card_selected=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.launch_ref:
        assert not args.capture.exists()
        capture = collect(json.loads(args.launch_ref.read_text()))
        args.capture.write_bytes(gzip.compress((json.dumps(capture, indent=2) + '\n').encode(), mtime=0))
    else:
        capture = json.loads(gzip.decompress(args.capture.read_bytes()))
    if capture['status'] != 'ORIGINAL_CPU_TERMINAL_CAPTURE' or 'result' not in capture:
        failure = (capture.get('failure') or {}).get('value', {})
        print(json.dumps(dict(status='FULL102_NOT_ACCEPTED', original_state=capture.get('status'),
                              failure_type=failure.get('error_type'), failure=failure.get('error'))))
        raise SystemExit(2 if capture['status'] == 'ORIGINAL_CPU_TERMINAL_CAPTURE' else 3)
    accepted = accept(capture)
    accepted.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture.read_bytes()))
    args.output.write_text(json.dumps(accepted, indent=2) + '\n')
    print(json.dumps(accepted))


if __name__ == '__main__':
    main()
