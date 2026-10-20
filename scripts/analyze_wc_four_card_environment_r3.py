#!/usr/bin/env python3
"""Combine immutable successful installation evidence with remaining CPU probes."""
import argparse
import hashlib
import json
from pathlib import Path
from repair_wc_four_card_environment_r2 import VERSIONS


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ('launch-ref', 'upstream-capture', 'capture', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    launch = json.loads(a.launch_ref.read_text())['launch']
    u = json.loads(a.upstream_capture.read_text())
    c = json.loads(a.capture.read_text())
    r = c.get('result') or {}
    m = c.get('manifest') or {}
    prefix = (u.get('result') or {}).get('commands', [])[:6]
    checks = dict(
        original_launch_matches=c.get('launch') == launch,
        worker_source_matches=c.get('worker_sha256') == r.get('worker_sha256') == launch['worker_sha256'],
        manifest_matches=c.get('manifest_sha256') == r.get('manifest_sha256') == launch['manifest_sha256'],
        published_source_matches=r.get('source_revision') == launch['source_revision'],
        original_PID_exited=c.get('original_handle_live') is False,
        own_container_exited=c.get('own_container_running') is False,
        expected_terminal=r.get('status') == 'COSMOS_CPU_ENVIRONMENT_COMPLETION_READY_NOT_PRODUCTION_OR_GPU',
        three_remaining_commands_zero=len(r.get('commands', [])) == 3 and all(x['exit_code'] == 0 for x in r.get('commands', [])),
        actual_upstream_result_preserved=c.get('upstream_result_sha256') == r.get('upstream_result_sha256') == u.get('result_sha256') == m.get('upstream_result_sha256'),
        upstream_six_valid_commands=len(prefix) == 6 and all(x['exit_code'] == 0 for x in prefix)
            and [x['phase'] for x in prefix] == ['copy-existing-base-to-independent-environment',
                'install-verified-local-cuda-wheels', 'install-matching-official-cosmos-cuda-package',
                'install-runtime-packaging-dependency-alignment', 'installed-dependency-check',
                'actual-Cosmos-request-import-CPU-only'],
        successful_prefix_reused_exactly=r.get('upstream_successful_commands') == prefix,
        upstream_request_import=u.get('request_import_marker') is True
            and r.get('reused_request_probe') == u.get('request_probe'),
        exact_versions=(r.get('reused_request_probe') or {}).get('versions') == VERSIONS,
        no_CUDA_initialization=(r.get('reused_request_probe') or {}).get('CUDA_initialized') is False
            and r.get('CUDA_initialized') is False,
        environment_metadata_unchanged=r.get('environment_metadata_unchanged') is True
            and r.get('environment_metadata_before') == r.get('environment_metadata_after'),
        old_base_environment_preserved=(u.get('result') or {}).get('source_environment_unchanged') is True,
        runtime_critical_sources_match=c.get('runtime_critical_sources_match') is r.get('runtime_critical_sources_unchanged') is True,
        original_project_preserved=c.get('original_project_revision') == u.get('original_project_revision'),
        original_R1_result_preserved=c.get('original_R1_result_sha256') == u.get('original_result_sha256'),
        official_wheel_hashes=u.get('all_wheel_SHA_match') is c.get('all_wheel_SHA_match') is True,
        native_archive_hashes=u.get('native_archives_SHA_match') is c.get('native_archives_SHA_match') is True,
        decoder_payload_preserved=r.get('decord_payload_unchanged') is True,
        actual_CPU_video_decode=c.get('decord_decode_marker') is True,
        guarded_inference_import=c.get('guarded_inference_marker') is True,
        actual_resolved_freeze=bool(c.get('resolved_python_freeze')),
        no_environment_reinstall=r.get('environment_modified') is False,
        no_model_loading=r.get('model_weights_loaded') == 0,
        no_GPU_submission=r.get('GPU_submissions') == c.get('GPU_submissions') == 0,
        no_ledger_write=r.get('ledger_written') is c.get('ledger_written') is False,
        no_shared_driver_or_daemon_change=r.get('driver_or_daemon_config_changed') is False,
        not_production_or_GPU=r.get('production_CPU_accepted') is r.get('GPU_dispatch_ready') is False,
    )
    accepted = all(checks.values())
    value = dict(status='COSMOS_CPU_ENVIRONMENT_COMPLETION_ACCEPTED' if accepted else 'CPU_ENVIRONMENT_COMPLETION_NOT_ACCEPTED_RETAINED',
                 accepted=accepted, checks=checks, launch_ref=str(a.launch_ref),
                 capture_ref=str(a.capture), upstream_capture_ref=str(a.upstream_capture),
                 launch_sha256=digest(a.launch_ref), capture_sha256=digest(a.capture),
                 upstream_capture_sha256=digest(a.upstream_capture),
                 environment_CPU_accepted=accepted, production_CPU_accepted=False,
                 GPU_dispatch_ready=False, model_assets_accepted=False,
                 GPU_driver_compatibility_verified=False, GPU_submissions=0, ledger_written=False)
    with a.output.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')
    print(json.dumps(value))
    raise SystemExit(0 if accepted else 2)


if __name__ == '__main__':
    main()
