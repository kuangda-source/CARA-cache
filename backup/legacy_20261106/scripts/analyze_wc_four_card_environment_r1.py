#!/usr/bin/env python3
"""Accept saved environment evidence offline, without granting GPU admission."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', choices=['prerequisites', 'environment'], required=True)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    envelope = json.loads(args.launch_ref.read_text())
    launch = envelope.get('remote') or envelope.get('launch') or envelope
    capture = json.loads(args.capture.read_text())
    result = capture.get('result', {})
    expected = ('CONTAINER_AND_TORCH_CPU_PREREQUISITES_READY_NOT_PRODUCTION'
                if args.kind == 'prerequisites' else 'CPU_ENVIRONMENT_BASE_READY_NOT_PRODUCTION_OR_GPU')
    checks = {
        'original_launch_matches': capture.get('launch') == launch,
        'original_worker_matches': capture.get('worker_source_sha256') == launch['worker_source_sha256'],
        'original_process_exited': capture.get('original_handle_live') is False,
        'own_CPU_container_exited': capture.get('own_container_running') is False,
        'terminal_result_present': capture.get('result_exists') is True and bool(result),
        'expected_environment_terminal': result.get('status') == expected,
        'all_recorded_commands_exit_zero': bool(result.get('commands')) and all(
            command.get('exit_code') == 0 for command in result.get('commands', [])),
        'no_GPU_submission': result.get('GPU_submissions') == 0 and capture.get('GPU_submissions') == 0,
        'no_ledger_write': result.get('ledger_written') is False and capture.get('ledger_written') is False,
        'not_production_CPU_or_GPU': result.get('production_CPU_accepted') is False
                                   and result.get('GPU_dispatch_ready') is False,
        'recorded_time_order': result.get('ended_unix', 0) >= result.get('started_unix', 1)
                              and result.get('wall_seconds', -1) >= 0,
    }
    if args.kind == 'prerequisites':
        checks.update(
            worker_result_source_matches=result.get('worker_sha256') == launch['worker_source_sha256'],
            Torch_CPU_import_marker=capture.get('CPU_import_marker_present') is True,
            exact_CUDA128_Torch_metadata=capture.get('torch_metadata_versions') == ['2.7.1+cu128'],
            environment_python_exists=capture.get('environment_python_exists') is True)
    else:
        checks.update(
            GitHub_revision_matches=result.get('GitHub_revision_deployed') == launch['source_revision']
                                    == capture.get('actual_GitHub_revision'),
            runtime_critical_sources_match=capture.get('all_runtime_source_SHA_match') is True,
            Cosmos_request_CPU_import=capture.get('Cosmos_CPU_import_marker_present') is True
                                      and result.get('actual_CPU_import_passed') is True,
            extension_wheels_installed=result.get('CUDA_extension_wheels_installed') is True,
            actual_freeze_captured=bool(capture.get('resolved_python_freeze')),
            manifest_matches=capture.get('manifest_sha256') == launch.get('manifest_sha256'))
        checks['data_disk_native_dependencies_match'] = (
            capture.get('native_dependency_archive_SHA_match') is True
            and capture.get('native_library_manifest_sha256') == result.get('native_library_manifest_sha256')
            and result.get('native_libraries_prepared') is True)
    accepted = all(checks.values())
    value = dict(status='ENVIRONMENT_EVIDENCE_ACCEPTED' if accepted else 'ENVIRONMENT_NOT_ACCEPTED_RETAINED',
                 kind=args.kind, checks=checks, accepted=accepted,
                 launch_ref=str(args.launch_ref), capture=str(args.capture),
                 launch_sha256=hashlib.sha256(args.launch_ref.read_bytes()).hexdigest(),
                 capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
                 source_revision=launch['source_revision'], worker_sha256=launch['worker_source_sha256'],
                 environment_base_CPU_accepted=accepted,
                 production_CPU_accepted=False, GPU_dispatch_ready=False,
                 GPU_driver_compatibility_verified=False, model_assets_accepted=False,
                 GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as file:
        json.dump(value, file, indent=2)
        file.write('\n')
    print(json.dumps(value))
    raise SystemExit(0 if accepted else 2)


if __name__ == '__main__':
    main()
