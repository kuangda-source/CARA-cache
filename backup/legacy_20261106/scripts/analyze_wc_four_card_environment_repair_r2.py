#!/usr/bin/env python3
"""Offline acceptance of an isolated CPU environment repair, never GPU admission."""
import argparse
import hashlib
import json
from pathlib import Path
from repair_wc_four_card_environment_r2 import VERSIONS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    launch=json.loads(a.launch_ref.read_text())['launch']
    c=json.loads(a.capture.read_text());r=c.get('result') or {};m=c.get('manifest') or {};probe=c.get('request_probe') or {}
    checks={
        'original_repair_launch_matches':c.get('launch')==launch,
        'worker_source_matches':c.get('worker_sha256')==r.get('worker_sha256')==launch['worker_sha256'],
        'manifest_matches':c.get('manifest_sha256')==r.get('manifest_sha256')==launch['manifest_sha256'],
        'published_repair_source_matches':r.get('repair_source_revision')==launch['source_revision'],
        'original_project_revision_preserved':c.get('original_project_revision')==m.get('original_project_revision')==r.get('original_project_revision'),
        'original_failed_result_preserved':c.get('original_result_sha256')==m.get('original_result_sha256'),
        'original_repair_PID_exited':c.get('original_handle_live') is False,
        'own_CPU_container_exited':c.get('own_container_running') is False,
        'expected_terminal':r.get('status')=='ISOLATED_COSMOS_CPU_ENVIRONMENT_REPAIR_READY_NOT_PRODUCTION_OR_GPU',
        'all_commands_exit_zero':len(r.get('commands',[]))>=9 and all(x['exit_code']==0 for x in r.get('commands',[])),
        'source_environment_unchanged':r.get('source_environment_unchanged') is True,
        'copied_base_metadata_matches':r.get('copied_environment_metadata_matches') is True,
        'runtime_critical_sources_unchanged':r.get('runtime_critical_sources_unchanged') is True,
        'actual_runtime_critical_sources_match':c.get('runtime_critical_sources_match') is True,
        'data_disk_native_archives_match':c.get('native_archives_SHA_match') is True,
        'runtime_overlay_critical_sources_identical':r.get('runtime_overlay_critical_sources_identical') is True,
        'decord_payload_unchanged':r.get('decord_retag_preserves_all_payload_SHA') is True,
        'decord_actual_CPU_decode':c.get('decord_decode_marker') is True,
        'ordinary_Cosmos_CPU_request_import':c.get('request_import_marker') is True and r.get('actual_CPU_request_import_passed') is True,
        'guarded_production_inference_import':c.get('guarded_inference_marker') is True and r.get('guarded_production_import_passed') is True,
        'installed_dependency_check_passed':r.get('dependency_check_passed') is True,
        'exact_versions_observed':probe.get('versions')==r.get('exact_versions')==VERSIONS,
        'official_wheel_SHA_match':c.get('all_wheel_SHA_match') is True and r.get('verified_wheels')==m.get('wheels'),
        'actual_freeze_captured':bool(c.get('resolved_python_freeze')),
        'no_CUDA_initialized':probe.get('CUDA_initialized') is False,
        'no_weights_loaded':r.get('model_weights_loaded')==0,
        'no_GPU_submission':r.get('GPU_submissions')==c.get('GPU_submissions')==0,
        'no_ledger_write':r.get('ledger_written') is c.get('ledger_written') is False,
        'no_shared_driver_or_daemon_change':r.get('driver_or_daemon_config_changed') is False,
        'not_production_CPU_or_GPU':r.get('production_CPU_accepted') is r.get('GPU_dispatch_ready') is False,
        'time_order_valid':r.get('ended_unix',0)>=r.get('started_unix',1) and r.get('wall_seconds',-1)>=0,
    }
    accepted=all(checks.values())
    out=dict(status='ISOLATED_COSMOS_CPU_ENVIRONMENT_REPAIR_ACCEPTED' if accepted else 'REPAIR_NOT_ACCEPTED_RETAINED',
             accepted=accepted,checks=checks,launch_ref=str(a.launch_ref),capture_ref=str(a.capture),
             launch_sha256=sha(a.launch_ref),capture_sha256=sha(a.capture),
             source_revision=launch['source_revision'],worker_sha256=launch['worker_sha256'],
             environment_CPU_accepted=accepted,production_CPU_accepted=False,GPU_dispatch_ready=False,
             GPU_driver_compatibility_verified=False,model_assets_accepted=False,
             GPU_submissions=0,ledger_written=False)
    with a.output.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out))
    raise SystemExit(0 if accepted else 2)


if __name__=='__main__':main()
