"""Accept the two completed affected-path CPU captures, never an F18 GPU card."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
NEW_SOURCES = ('scripts/check_cara_fast_f18_cpu_r1.py', 'tests/check_cara_fast_f18_routes_r1.py')
ROLES = ('F18_C', 'F18_A1', 'UNIFORM18_C')


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(paths):
    if len(paths) != 2:
        raise ValueError('Two original host captures required')
    receipts, scopes, source_maps = [], [], []
    for host, path in zip(('four_card', 'two_card'), paths):
        value = json.loads(path.read_bytes())
        state, proof, registration = (value[k] for k in ('container_state', 'CPU_proof', 'registration'))
        if (state['Status'] != 'exited' or state['Running'] or state['Pid'] != 0
                or state['ExitCode'] != 0 or state['OOMKilled'] or proof is None):
            raise ValueError('Original F18 CPU must exit normally with a complete proof: '+host)
        proof_sha = hashlib.sha256((json.dumps(proof, indent=2, allow_nan=False)+'\n').encode()).hexdigest()
        registration_sha = hashlib.sha256((json.dumps(registration, indent=2)+'\n').encode()).hexdigest()
        if (proof_sha != value['CPU_proof_sha256'] or registration_sha != value['registration_sha256']
                or proof['payload_sha256'] != registration['payload_sha256']
                or proof['runtime_source_sha256'] != registration['runtime_source_sha256']):
            raise ValueError('Original CPU proof or registration bytes differ')
        expected = dict(NanoCpus=10**9, Memory=4*2**30, MemorySwap=4*2**30, CpusetCpus='26',
            DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)
        if (value['host_config'] != expected or not value['payload_intact'] or not value['runtime_intact']
                or proof['host'] != host or value['launch']['host'] != host
                or proof['registration_sha256'] != value['registration_sha256']
                or proof['CUDA_initialized'] or proof['Cosmos_model_weights_loaded']
                or proof['GPU_submissions'] != 0 or proof['ledger_written']
                or proof['whole_GPU_card_accepted'] or proof['actual_compile_threads'] != 1
                or proof['compile_pools'] != []):
            raise ValueError('Bound GPU-hidden resource/source CPU evidence required: '+host)
        parent_name = {'four_card':'reports/cara_fast_binding_four_card_CPU_capture3_r6_20261028.json',
                       'two_card':'reports/cara_fast_binding_two_card_CPU_capture_r8_20261028.json'}[host]
        parent = json.loads((ROOT/parent_name).read_bytes())
        if registration['base_registration_sha256'] != parent['registration_sha256']:
            raise ValueError('Original accepted parent CPU source differs')
        for name in NEW_SOURCES:
            if registration['payload_sha256'][name] != file_sha(ROOT/name):
                raise ValueError('Affected F18 source changed: '+name)
        checks = proof['numeric']['checks']
        if [row['flow'] for row in checks] != [False, True]:
            raise ValueError('Both original flow modes required')
        failures = {role+':'+fault for role in ROLES for fault in ('refusal','decode','writer')}
        for row in checks:
            if (row['validation'] != 'F18_AFFECTED_PRODUCTION_CPU_FRAGMENT'
                    or row['parent_scope_sha256'] != proof['scope_sha256']
                    or row['registered_CPU_positions'] != 27 or row['successful_tiny_paths'] != 18
                    or row['formal_CHECK_positions'] != 6 or tuple(row['roles']) != ROLES
                    or len(row['failures']) != 9 or set(row['failures']) != failures
                    or row['whole_GPU_card_accepted'] or row['Cosmos_weights_loaded']
                    or row['real_video_quality_or_speed_result'] or not all(row[key] for key in (
                        'full36_and_exact_actions','F18_A1_step9_C_from_D7_preserved',
                        'ON_OFF_and_clean_audit_latent_RGB_RNG_exact',
                        'clean_research_counters_zero','cleanup_no_replay_and_context_guards'))):
                raise ValueError('Complete F18 affected-path matrix required: '+host)
            scopes.append(row['CPU_fragment_scope_sha256'])
        source_maps.append(registration['payload_sha256'])
        receipts.append(dict(host=host, path=str(path.relative_to(ROOT)), sha256=file_sha(path),
            launch=value['launch'], container_state=state, host_config=value['host_config'],
            CPU_proof_sha256=value['CPU_proof_sha256'], parent_acceptance_ref=parent_name,
            CPU_process_seconds=proof['CPU_process_seconds'],
            worker_wall_seconds=proof['ended_unix']-proof['started_unix']))
    if len(set(scopes)) != 1:
        raise ValueError('The same CPU fragment must be exercised on both hosts')
    preserved = {}
    for name, count in [('reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json',52),
                        ('reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json',4),
                        ('reports/cara_fast_B36_figures_CPU_acceptance_r2_20261029.json',6)]:
        sources = json.loads((ROOT/name).read_bytes())['critical_source_sha256']
        if len(sources) != count or any(file_sha(ROOT/path) != sha for path, sha in sources.items()):
            raise ValueError('Original B36 critical sources changed')
        preserved.update(sources)
    inherited = {name: sha for name, sha in preserved.items() if all(name in m for m in source_maps)}
    if any(m[name] != sha for m in source_maps for name, sha in inherited.items()):
        raise ValueError('Inherited critical production components differ from current accepted source')
    return dict(status='F18_AFFECTED_PRODUCTION_CPU_DUAL_HOST_ACCEPTED_NOT_GPU', observed_unix=time.time(),
        receipts=receipts, CPU_fragment_scope_sha256=scopes[0], CHECK_positions=6,
        roles=list(ROLES), successful_tiny_paths_per_host=36, declared_failure_attempts_per_host=18,
        acceptor_source_sha256=file_sha(Path(__file__)),
        flow_modes=[False,True], source_sha256={n:file_sha(ROOT/n) for n in NEW_SOURCES},
        inherited_critical_component_sha256=inherited, original_62_sources_unchanged=True,
        full_F18_physical_GPU_scope_frozen=False, whole_quote_frozen=False, GPU_dispatch_ready=False,
        Cosmos_weights_loaded=False, real_video_quality_or_speed_result=False,
        GPU_submissions=0, new_reserved_GPUh=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--four-card', type=Path, required=True)
    parser.add_argument('--two-card', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh F18 CPU acceptance receipt required')
    result = accept([args.four_card.resolve(), args.two_card.resolve()])
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], hosts=2, GPU_submissions=0)))


if __name__ == '__main__':
    main()
