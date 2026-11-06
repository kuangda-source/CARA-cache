#!/usr/bin/env python3
"""Accept repaired dependency components while retaining blocked full inference."""
import argparse
import hashlib
import json
from pathlib import Path
from repair_wc_four_card_environment_r2 import VERSIONS


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def normalized(name):
    return name.lower().replace('_', '-')


def main():
    p = argparse.ArgumentParser()
    for name in ('upstream-capture', 'capture', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    u = json.loads(a.upstream_capture.read_text())
    c = json.loads(a.capture.read_text())
    r = c.get('result') or {}
    ur = u.get('result') or {}
    prefix = ur.get('commands', [])[:6]
    commands = r.get('commands', [])
    errors = json.dumps(c.get('errors', []))
    distributions = {normalized(x['name']): x['version']
                     for x in c.get('installed_distribution_metadata', [])}
    checks = dict(
        R2_real_terminal_present=u.get('result_exists') is True,
        R2_valid_install_request_prefix=len(prefix) == 6 and all(x['exit_code'] == 0 for x in prefix)
            and [x['phase'] for x in prefix] == ['copy-existing-base-to-independent-environment',
                'install-verified-local-cuda-wheels', 'install-matching-official-cosmos-cuda-package',
                'install-runtime-packaging-dependency-alignment', 'installed-dependency-check',
                'actual-Cosmos-request-import-CPU-only'],
        R3_real_terminal_present=c.get('result_exists') is True,
        R3_actual_CPU_decode=len(commands) == 2 and commands[0]['phase'] == 'corrected-synthetic-CPU-video-decode'
            and commands[0]['exit_code'] == 0 and c.get('decord_decode_marker') is True,
        R3_full_import_refusal_retained=len(commands) == 2 and commands[1]['phase'] == 'frozen-production-guarded-inference-import'
            and commands[1]['exit_code'] == 1 and c.get('guarded_inference_marker') is False,
        specific_model_asset_blocker='LocalEntryNotFoundError' in errors and 'nvidia/Cosmos-Guardrail1/revision/d6d4bfa899a71454a700907664f3e88f503950cf' in errors,
        worker_and_manifest_match=c.get('worker_sha256') == r.get('worker_sha256') == c['launch']['worker_sha256']
            and c.get('manifest_sha256') == r.get('manifest_sha256') == c['launch']['manifest_sha256'],
        actual_upstream_result_matches=c.get('upstream_result_sha256') == r.get('upstream_result_sha256') == u.get('result_sha256'),
        valid_prefix_reused_exactly=r.get('upstream_successful_commands') == prefix,
        same_frozen_helper_source=c.get('support_source_sha256') == u.get('worker_sha256'),
        ordinary_Cosmos_request_passed=u.get('request_import_marker') is True
            and r.get('reused_request_probe') == u.get('request_probe'),
        request_exact_versions=(r.get('reused_request_probe') or {}).get('versions') == VERSIONS,
        actual_installed_exact_versions=all(distributions.get(normalized(k)) == v for k, v in VERSIONS.items()),
        installed_dependency_metadata_captured=len(distributions) > 100,
        official_four_wheel_hashes=c.get('all_wheel_SHA_match') is u.get('all_wheel_SHA_match') is True,
        native_archive_hashes=c.get('native_archives_SHA_match') is u.get('native_archives_SHA_match') is True,
        original_environment_preserved=ur.get('source_environment_unchanged') is True,
        installed_environment_metadata_preserved=r.get('environment_metadata_unchanged') is True
            and r.get('environment_metadata_before') == r.get('environment_metadata_after'),
        decoder_payload_preserved=r.get('decord_payload_unchanged') is True,
        runtime_sources_preserved=c.get('runtime_critical_sources_match') is r.get('runtime_critical_sources_unchanged') is True,
        original_project_preserved=c.get('original_project_revision') == u.get('original_project_revision'),
        original_R1_failure_preserved=c.get('original_R1_result_sha256') == u.get('original_result_sha256'),
        original_R2_failure_preserved=ur.get('status') == 'ISOLATED_ENVIRONMENT_REPAIR_FAILED_RETAINED',
        original_R3_failure_preserved=r.get('status') == 'CPU_VALIDATION_COMPLETION_FAILED_RETAINED',
        R2_and_R3_processes_exited=c.get('original_handle_live') is u.get('original_handle_live') is False,
        own_containers_exited=c.get('own_container_running') is u.get('own_container_running') is False,
        no_CUDA_initialized=(r.get('reused_request_probe') or {}).get('CUDA_initialized') is r.get('CUDA_initialized') is False,
        no_weight_or_GPU_submission=r.get('model_weights_loaded') == r.get('GPU_submissions') == c.get('GPU_submissions') == 0,
        no_ledger_or_host_change=r.get('ledger_written') is c.get('ledger_written') is r.get('driver_or_daemon_config_changed') is False,
    )
    accepted = all(checks.values())
    out = dict(status='CORE_DEPENDENCY_REPAIR_ACCEPTED_FULL_INFERENCE_ASSETS_PENDING' if accepted else 'CORE_DEPENDENCY_REPAIR_NOT_ACCEPTED',
               core_dependency_repair_accepted=accepted, checks=checks,
               accepted_scope=['official_extension_installation', 'matching_cosmos_cuda',
                               'installed_dependency_consistency', 'ordinary_Cosmos_CPU_request_import',
                               'actual_synthetic_CPU_video_encode_decode'],
               full_environment_accepted=False, full_inference_import_accepted=False,
               production_CPU_accepted=False, model_assets_accepted=False,
               GPU_dispatch_ready=False, GPU_driver_compatibility_verified=False,
               missing_model_repo='nvidia/Cosmos-Guardrail1',
               missing_model_revision='d6d4bfa899a71454a700907664f3e88f503950cf',
               upstream_capture_ref=str(a.upstream_capture), upstream_capture_sha256=sha(a.upstream_capture),
               capture_ref=str(a.capture), capture_sha256=sha(a.capture),
               installed_distribution_count=len(distributions), GPU_submissions=0, ledger_written=False)
    with a.output.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(json.dumps(out))
    raise SystemExit(0 if accepted else 2)


if __name__ == '__main__':
    main()
