"""Accept saved original P1 R2 CPU bytes; never execute a collector or scorer."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]

from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS
from cara_source_lifecycle_p1_linux_cpu_r2 import OVERLAY, STAGE
from wcomr.cara_fast_spec_r1 import policy_from_mask, profile_from
from wcomr.cara_source_lifecycle_estimation_r1 import FAMILIES


def accept(launch_file, capture_file):
    read = lambda p: json.loads(Path(p).read_bytes())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    encode = lambda value: (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    launch, capture = read(launch_file), read(capture_file)
    assert launch['exit_code'] == capture['exit_code'] == 0
    cap, launched = capture['result'], launch['result']
    assert cap['launch'] == launched and Path(launched['stage']).name == STAGE
    reg, state, proof = cap['registration'], cap['container_state'], cap['CPU_proof']
    assert proof is not None, 'Preserve original failed/unknown CPU; no implicit rerun'
    assert reg['host'] == 'two_card' and cap['host_config'] == reg['expected_host_config'] == LIMITS
    assert state['Status'] == 'exited' and state['ExitCode'] == state['Pid'] == 0
    assert not any(state[k] for k in ('Running', 'Paused', 'Restarting', 'OOMKilled', 'Dead'))
    assert cap['payload_intact'] and cap['runtime_intact']
    assert reg['parent_git_revision'] == launch['source_revision'] == capture['source_revision'] == proof['source_revision']
    assert cap['registration_sha256'] == hashlib.sha256(encode(reg)).hexdigest() == proof['registration_sha256']
    raw = encode(proof)
    assert hashlib.sha256(raw).hexdigest() == cap['CPU_proof_sha256'], 'Recover original CPU proof bytes'
    base, accepted = read(ROOT/BASE_CAPTURE)['result'], read(ROOT/BASE_ACCEPTED)
    assert accepted['capture_sha256'] == sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed'] == 113
    revision = subprocess.check_output(['git', 'rev-parse', proof['source_revision']], cwd=ROOT, text=True).strip()
    overlay = {n: hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+n], cwd=ROOT)).hexdigest() for n in OVERLAY}
    assert reg['payload_sha256'] == proof['payload_sha256'] == {**base['registration']['payload_sha256'], **overlay}
    assert reg['runtime_source_sha256'] == proof['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert proof['status'] == 'P1_LOADED_ALGORITHM_INTERNAL_FIT_LINUX_CPU_PASS_NOT_WHOLE_GPU_ENTRY'
    assert proof['tests_run'] == 33 and proof['complete_semantic_positions'] == 292 and proof['same_state_scalar_rows'] == 128
    assert proof['actual_CPU_affinity'] == [26] and proof['work_seconds'] == 1800 and proof['exit_seconds'] == 60
    assert launched['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= launched['started_unix']+1800
    assert all(proof[k] for k in ('actual_WC_RF_imports_and_globals_accepted', 'actual_Cosmos_arguments',
        'CPU_import_adapters_used', 'synthetic_cost_ticks_not_GPU_quote'))
    assert all(proof[k] is False for k in ('actual_Cosmos_weights', 'real_V1_labels', 'real_video_efficacy',
        'whole_GPU_entry_accepted', 'P1_GPU_authorized', 'CUDA_initialized', 'ledger_written'))
    assert proof['GPU_submissions'] == 0
    checks = proof['loaded']['checks']
    assert sorted(c['flow'] for c in checks) == [False, True]
    profile = profile_from(read(ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json')['profile'])
    selections = {family+'-K'+str(k) for family in FAMILIES for k in (19, 22)}
    for row in checks:
        assert row['status'] == 'P1_ACTUAL_LOADED_TINY_ALGORITHM_AND_INTERNAL_CPU_SCORES_PASS'
        assert row['source_scalar_rows'] == 64 and row['semantic_positions'] == 146
        assert 46 <= row['actual_complete_tiny_requests'] <= 142
        assert row['shared_state_and_parameters_restored'] and row['recovery_new_physical_and_score_callbacks'] == 0
        assert row['actual_Cosmos_arguments'] and row['real_Alex_weights_on_synthetic_media']
        assert row['cost_clock'] == 'SYNTHETIC_OPERATION_SECONDS_NOT_GPU_QUOTE'
        assert not any(row[k] for k in ('actual_Cosmos_weights', 'whole_GPU_entry_accepted', 'scientific_method_efficacy', 'ledger_written'))
        assert row['GPU_submissions'] == 0
        cohorts = row['accepted_internal_FIT_cohorts']
        assert 6 <= len(cohorts) <= 42 and row['actual93_frame_metric_pairs'] == 2*len(cohorts)
        assert len({c['packet_sha256'] for c in cohorts}) == len(cohorts) and all(c['pairs'] == 2 for c in cohorts)
        assert set(row['FIT_selected']) == selections
        for key, plan in row['FIT_selected'].items():
            budget = int(key.rsplit('K', 1)[1])
            assert len(plan['dense_steps']) == budget and policy_from_mask(profile, plan['dense_steps']) == plan['policy']
    assert sum(c['actual_complete_tiny_requests'] for c in checks) == proof['actual_complete_loaded_tiny_requests']
    assert sum(c['actual93_frame_metric_pairs'] for c in checks) == proof['real93_frame_synthetic_metric_pairs']
    return dict(status='ORIGINAL_P1_R2_LOADED_ALGORITHM_INTERNAL_SCORE_LINUX_CPU_ACCEPTED_NOT_GPU_ENTRY',
        source_revision=revision, launch_ref=str(launch_file), launch_sha256=sha(launch_file),
        capture_ref=str(capture_file), capture_sha256=sha(capture_file), CPU_proof_sha256=cap['CPU_proof_sha256'],
        original_launch=launched, original_container_state=state, original_CPU_ended=True,
        registration_sha256=cap['registration_sha256'], payload_sha256=proof['payload_sha256'],
        tests_run=33, complete_semantic_positions=292, same_state_scalar_rows=128,
        actual_complete_loaded_tiny_requests=proof['actual_complete_loaded_tiny_requests'],
        real93_frame_synthetic_metric_pairs=proof['real93_frame_synthetic_metric_pairs'],
        recovery_new_physical_and_score_callbacks=0, actual_original_WC_RF_globals_and_Cosmos_arguments=True,
        real_Alex_weights_on_explicit_synthetic_media=True, synthetic_cost_ticks_not_GPU_quote=True,
        prior_R1_failure_ref='reports/cara_v1_P1_algorithm_Linux_CPU_original_failure_r1_20261102.json',
        whole_GPU_entry_accepted=False, host_score_broker_accepted=False, real_V1_labels=False,
        scientific_method_efficacy=False, P1_GPU_authorized=False, GPU_submissions=0, ledger_written=False), raw


def main():
    parser = argparse.ArgumentParser()
    for name in ('launch', 'capture', 'output', 'proof-output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.proof_output.exists()
    accepted, raw = accept(args.launch, args.capture)
    args.proof_output.write_bytes(raw)
    accepted['original_proof_ref'] = str(args.proof_output)
    with args.output.open('x') as stream:
        json.dump(accepted, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: accepted[k] for k in ('status', 'tests_run', 'actual_complete_loaded_tiny_requests',
                                             'real93_frame_synthetic_metric_pairs', 'P1_GPU_authorized')}))


if __name__ == '__main__':
    main()
