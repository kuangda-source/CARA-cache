"""Accept only the exited, source-bound native S CPU container."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def require(value, message):
    if not value: raise ValueError(message)


def accept(capture, scope, host, revision):
    state = capture['container_state']; config = capture['host_config']; registration = capture['registration']
    limits = scope['resources']
    require(capture['original_CLI_live'] is False and not state['Running']
        and state['Status'] == 'exited' and state['ExitCode'] == 0, 'Recover original terminal native S CPU container')
    require(capture['source_hashes_equal'] and capture['runtime_hashes_equal']
        and registration['source_revision'] == revision and registration['GPU_submissions'] == 0,
        'Original native S CPU source/runtime differs')
    require(not config.get('DeviceRequests') and config['NetworkMode'] == 'none'
        and config['Memory'] == config['MemorySwap'] == limits['RAM_bytes']
        and config['NanoCpus'] == limits['CPUs']*10**9 and config['CpusetCpus'] == limits['cpuset'],
        'Original native S CPU isolation differs')
    result = capture['result']
    digest = hashlib.sha256((json.dumps(result, indent=2, allow_nan=False)+'\n').encode()).hexdigest()
    require(capture['result_sha256'] == digest, 'Original native S CPU result bytes differ')
    require(result['status'] == 'S_NATIVE_IMPORTS_CLI_MATRIX_AND_LINUX_LIFECYCLE_CPU_PASS'
        and result['profile'] == host and result['scope'] == scope
        and result['actual_platform']['system'] == 'Linux' and result['torch_version'] == '2.7.1+cu128',
        'Actual same-host Linux S CPU result required')
    units = result['unit_controls']
    require(units['tests'] == scope['unit_controls'] and units['skipped'] == units['errors'] == units['failures'] == 0,
        'All affected S CPU controls must pass without skips')
    require(result['critical_source_sha256'] == scope['critical_source_sha256']
        and all(registration['payload_sha256'].get(name) == value for name, value in result['critical_source_sha256'].items()),
        'Complete production-critical source binding required')
    require(all(result[key] is True for key in ('actual_full_inference_module_import',
        'actual_full_WC_RF_module_imports', 'actual_native_parser', 'CPU_import_probes_restored',
        'model_loads_are_declared_tiny_CPU_standins', 'weight_loads_forbidden',
        'downloads_and_socket_outbound_blocked')), 'Actual native imports/parser boundaries required')
    require(result['pinned_config_source_sha256'] == scope['native_parser_source_sha256']
        and result['checkpoint_lookup_is_metadata_sentinel'] is False
        and len(result['checkpoint_cache_lookups']) == 1
        and result['checkpoint_cache_lookups'][0]['bytes'] == scope['diffusion_checkpoint_bytes'],
        'Original cached checkpoint metadata resolution required')
    require(len(result['rows']) == 2 and {row['flow'] for row in result['rows']} == {False, True}
        and result['tiny_tensor_load_calls'] == 80 and result['unique_tiny_tensor_files_loaded'] == 64,
        'Two complete flows and exact tensor-reload denominator required')
    for row in result['rows']:
        require(row['host'] == host and row['status'] == 'CPU_CLI_MODEL_MATRIX_PASS'
            and row['full_native_WC_RF_module_namespaces'] is True
            and row['new_tiny_paths'] == 10 and row['reused_OFF_roles'] == 0
            and row['model_load_standins'] == row['environment_cleanup_standins'] == 1
            and row['observed_head_calls'] == 936 and row['observed_deep_calls'] == 552
            and row['resource_checks'] == row['same_state_rows'] == 108
            and row['raw_states'] == 8 and row['unique_anchors'] == 24
            and row['original_cli_replay_refused'] and row['actual_pinned_config_parser']
            and row['reload_audit']['files_SHA_and_bytes_reloaded'] == 140,
            'Full native S CLI/model/matrix/streaming cohort required')
    controls = result['supervisor_controls']
    require([row['scenario'] for row in controls] == scope['supervisor_scenarios']
        and [row['flow'] for row in controls] == scope['supervisor_flows']
        and all(row['passed'] and row['host'] == host and row['real_Linux_PID_start_ticks_and_inherited_lease']
            and row['original_child_exited'] and row['original_lease_released'] and row['replay_refused']
            and row['technical_accepted'] is (row['scenario'] == 'complete')
            and row['diagnostic_bill_chargeable'] is False for row in controls),
        'Complete Linux S supervisor child/lease/failure controls required')
    require(all(result[key] is False for key in ('actual_weights_loaded', 'real_generated_video',
        'CUDA_initialized', 'actual_GPU_entry_accepted', 'full_S_entry_CPU_accepted'))
        and result['real_S_labels'] == result['GPU_submissions'] == result['new_GPUh'] == result['real_central_ledger_writes'] == 0,
        'CPU proof cannot add GPU/scientific/financial acceptance')
    instant = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    wall = (instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0 < result['CPU_wall_seconds'] <= wall <= limits['wall_seconds']+10
        and 0 < result['peak_RSS_KiB'] < limits['RAM_bytes']/1024, 'Native S CPU cost/limit differs')
    return dict(status='S_COMPLETE_NATIVE_PRODUCTION_ENTRY_CPU_ACCEPTED_NOT_GPU_CARD', passed=True,
        host=host, source_revision=revision, actual_platform=result['actual_platform'], skipped=0,
        full_S_entry_CPU_accepted=True, native_parser_accepted=True,
        payload_sha256=registration['payload_sha256'], critical_source_sha256=result['critical_source_sha256'],
        unit_controls=units['tests'], complete_tiny_paths=20, Linux_supervisor_controls=len(controls),
        resources=dict(container_wall_seconds=wall, worker_wall_seconds=result['CPU_wall_seconds'],
            worker_CPU_seconds=result['CPU_seconds'], parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20),
        original_container_terminal_accepted=True, actual_weights_loaded=False, actual_S_labels=0,
        actual_GPU_entry_accepted=False, whole_S_quote_frozen=False, GPU_submissions=0, ledger_writes=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--host', choices=('two_card', 'four_card'), required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError('Preserve original native S CPU acceptance')
    from cara_sq_s_production_entry_cpu_r6 import FILES, SCOPE
    revision = subprocess.check_output(['git', 'rev-parse', args.source_revision+'^{commit}'], cwd=ROOT, text=True).strip()
    frozen = lambda name: subprocess.check_output(['git', 'show', revision+':'+name], cwd=ROOT)
    capture = json.loads(args.capture.read_text())
    for name in FILES:
        require(capture['registration']['payload_sha256'].get(name) == hashlib.sha256(frozen(name)).hexdigest(),
            'Exact published S CPU overlay differs: '+name)
    result = accept(capture, json.loads(frozen(SCOPE)), args.host, revision)
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        auditor_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.output.open('x') as stream: json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({key: result[key] for key in ('status', 'host', 'resources')}))


if __name__ == '__main__': main()
