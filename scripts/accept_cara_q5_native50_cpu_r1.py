"""Accept the original two-host Native50 CPU component, without accepting Q5."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
INTENT = 'plans/cara_next_stage_20261028/mainline/r2/Q5_NATIVE50_CPU_FRAGMENT_R1.json'
ROLES = ('NATIVE50', 'ALLD50')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(paths):
    if len(paths) != 2:
        raise ValueError('Two original host captures required')
    intent = json.loads((ROOT/INTENT).read_bytes())
    sources = intent['source_sha256']
    if any(sha(ROOT/name) != value for name, value in sources.items()):
        raise ValueError('Registered Q5 Native50 component source changed')
    parent_ref = 'reports/cara_fast_F18_affected_production_CPU_acceptance_r1_20261030.json'
    parent = json.loads((ROOT/parent_ref).read_bytes())
    if parent['status'] != 'F18_AFFECTED_PRODUCTION_CPU_DUAL_HOST_ACCEPTED_NOT_GPU':
        raise ValueError('Accepted original F18 CPU parents required')
    receipts, scopes, schedules, source_maps = [], [], [], []
    for host, path, accepted_parent in zip(('four_card', 'two_card'), paths, parent['receipts']):
        value = json.loads(path.read_bytes())
        state, proof, reg = (value[k] for k in ('container_state', 'CPU_proof', 'registration'))
        if (state['Status'] != 'exited' or state['Running'] or state['Pid'] != 0
                or state['ExitCode'] != 0 or state['OOMKilled'] or proof is None):
            raise ValueError('Original Q5 CPU must exit normally with a complete proof: '+host)
        proof_sha = hashlib.sha256((json.dumps(proof, indent=2, allow_nan=False)+'\n').encode()).hexdigest()
        reg_sha = hashlib.sha256((json.dumps(reg, indent=2)+'\n').encode()).hexdigest()
        if (proof_sha != value['CPU_proof_sha256'] or reg_sha != value['registration_sha256']
                or proof['payload_sha256'] != reg['payload_sha256']
                or proof['runtime_source_sha256'] != reg['runtime_source_sha256']):
            raise ValueError('Original CPU proof or registration bytes differ')
        launch_ref = f'reports/cara_Q5_Native50_{host}_CPU_launch_r1_20261030.json'
        launch = json.loads((ROOT/launch_ref).read_bytes())
        if (value['launch'] != launch or reg['host'] != host or proof['host'] != host
                or reg['stage'] != launch['stage']
                or launch['container'] != intent['stages'][host]+'-cpu'
                or launch['registration_sha256'] != reg_sha or proof['registration_sha256'] != reg_sha):
            raise ValueError('Original Q5 CPU launch identity differs: '+host)
        if (accepted_parent['host'] != host or sha(ROOT/accepted_parent['path']) != accepted_parent['sha256']):
            raise ValueError('Accepted parent capture changed')
        base = json.loads((ROOT/accepted_parent['path']).read_bytes())
        if (reg['base_registration_sha256'] != base['registration_sha256']
                or reg['runtime_source_sha256'] != base['registration']['runtime_source_sha256']
                or reg['payload_sha256'] != {**base['registration']['payload_sha256'], **sources}):
            raise ValueError('Original parent CPU payload or runtime differs')
        resources = dict(NanoCpus=10**9, Memory=4*2**30, MemorySwap=4*2**30, CpusetCpus='26',
            DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)
        if (value['host_config'] != resources or not value['payload_intact'] or not value['runtime_intact']
                or proof['CUDA_initialized'] or proof['numeric']['cuda_initialized']
                or proof['Cosmos_model_weights_loaded'] or proof['GPU_submissions'] != 0
                or proof['ledger_written'] or proof['whole_GPU_card_accepted']
                or proof['actual_compile_threads'] != 1 or proof['compile_pools'] != []
                or proof['resource_bound'] != dict(cpus=1, memory_GiB=4, work_seconds=600, exit_seconds=60)):
            raise ValueError('Bound GPU-hidden CPU resource/source evidence required')
        checks = proof['numeric']['checks']
        if [row['flow'] for row in checks] != [False, True]:
            raise ValueError('Both original flow modes required')
        failures = {role+':'+fault for role in ROLES for fault in ('refusal', 'decode', 'writer')}
        for row in checks:
            grid = row['schedule']
            if (grid['requested_steps'] != 50 or grid['actual_updates'] != 51
                    or len(grid['timesteps']) != 51 or len(grid['sigmas']) != 52
                    or grid['sigmas'][-1] != 0
                    or not all(math.isfinite(v) for v in grid['sigmas']+grid['timesteps'])
                    or not all(a > b for a, b in zip(grid['sigmas'], grid['sigmas'][1:]))):
                raise ValueError('Actual requested50 / 51-update / 52-sigma grid required')
            derivation = row['derivation']
            if (row['validation'] != 'Q5_NATIVE50_ACTUAL_GRID_CPU_COMPONENT'
                    or row['registered_CPU_positions'] != 30 or row['successful_tiny_paths'] != 24
                    or row['Native_reference_members'] != 4 or row['allD_control_members'] != 4
                    or tuple(row['roles']) != ROLES or len(row['failures']) != 6
                    or set(row['failures']) != failures or row['Cosmos_weights_loaded']
                    or row['real_model_quality_or_speed_result'] or row['whole_Q5_GPU_card_accepted']
                    or derivation['sparse_policy_support_extended'] or not all(derivation[key] for key in (
                        'original_request_bytecode_identical', 'Native_range_and_message_only',
                        'full_request_bounds_35_to_50_36_to_51', 'original_module_globals_unchanged'))
                    or not all(row[key] for key in ('actual51_CFG102_and_full_block_witness',
                        'Native_allD_ON_OFF_audit_latent_RGB_RNG_exact', 'all51_audited_guided_outputs_equal',
                        'clean_research_counters_zero', 'cleanup_and_no_replay',
                        'old_Native_range_unchanged', 'sparse36_adapter_still_rejects51'))):
                raise ValueError('Complete Native50 component matrix and unchanged sparse boundary required')
            scopes.append(row['CPU_fragment_scope_sha256'])
            schedules.append(grid)
        source_maps.append(reg['payload_sha256'])
        receipts.append(dict(host=host, path=str(path.relative_to(ROOT)), sha256=sha(path),
            launch_ref=launch_ref, launch_sha256=sha(ROOT/launch_ref), launch=launch,
            container_state=state, host_config=resources, CPU_proof_sha256=proof_sha,
            CPU_process_seconds=proof['CPU_process_seconds'],
            worker_wall_seconds=proof['ended_unix']-proof['started_unix']))
    if len(set(scopes)) != 1 or any(grid != schedules[0] for grid in schedules):
        raise ValueError('Identical component scope and actual grid required on both hosts')
    preserved = {}
    for name, count in [('reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json', 52),
                        ('reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json', 4),
                        ('reports/cara_fast_B36_figures_CPU_acceptance_r2_20261029.json', 6)]:
        original = json.loads((ROOT/name).read_bytes())['critical_source_sha256']
        if len(original) != count or any(sha(ROOT/path) != value for path, value in original.items()):
            raise ValueError('Original B36 critical sources changed')
        preserved.update(original)
    inherited = {n: v for n, v in preserved.items() if all(n in m for m in source_maps)}
    if any(m[n] != v for m in source_maps for n, v in inherited.items()):
        raise ValueError('Inherited critical production components differ')
    freeze_ref = 'plans/cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json'
    if sha(ROOT/freeze_ref) != '56e1eb84fed0a459ae8fdeb6598680009226dced9529052cabc57cf11cef2be8':
        raise ValueError('Original A32 freeze changed')
    return dict(status='Q5_NATIVE50_CPU_COMPONENT_DUAL_HOST_ACCEPTED_NOT_GPU', observed_unix=time.time(),
        receipts=receipts, CPU_fragment_scope_sha256=scopes[0], schedule=schedules[0],
        expected_CFG_model_calls=102, successful_tiny_paths_per_host=48, declared_failures_per_host=12,
        flow_modes=[False, True], roles=list(ROLES), Native_reference_members=4, allD_control_members=4,
        CPU_intent_ref=INTENT, CPU_intent_sha256=sha(ROOT/INTENT), source_sha256=sources,
        acceptor_source_sha256=sha(Path(__file__)), parent_acceptance_ref=parent_ref,
        parent_acceptance_sha256=sha(ROOT/parent_ref), inherited_critical_component_sha256=inherited,
        original_62_sources_unchanged=True, original_A32_freeze_unchanged=True,
        sparse_profile_mapping_frozen=False, S_rule_frozen=False, whole_Q5_GPU_scope_frozen=False,
        whole_quote_frozen=False, GPU_dispatch_ready=False, real_model_quality_or_speed_result=False,
        GPU_submissions=0, new_reserved_GPUh=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--four-card', type=Path, required=True)
    parser.add_argument('--two-card', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh Native50 CPU acceptance receipt required')
    result = accept([args.four_card.resolve(), args.two_card.resolve()])
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], hosts=2, GPU_submissions=0)))


if __name__ == '__main__':
    main()
