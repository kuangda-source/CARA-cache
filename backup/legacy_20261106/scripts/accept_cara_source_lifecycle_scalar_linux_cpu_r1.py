"""Accept original scalar R3 CPU terminal bytes; never execute its tests again."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]

from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS
from cara_source_lifecycle_scalar_linux_cpu_r3 import STAGE, OVERLAY
from fit_cara_source_lifecycle_v1_r1 import frozen_weights
from wcomr.cara_source_lifecycle_estimation_r1 import complete_samples


def accept(launch_file, capture_file):
    read = lambda p: json.loads(Path(p).read_text())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    encode = lambda value: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    launched, captured = read(launch_file), read(capture_file)
    assert captured['exit_code'] == 0
    cap = captured['result']
    reg, proof, state = cap['registration'], cap['CPU_proof'], cap['container_state']
    assert proof is not None, 'Original CPU proof absent: recover terminal failure, never rerun'
    assert cap['launch'] == launched['result'] and launched['exit_code'] == 0
    assert Path(cap['launch']['stage']).name == STAGE and reg['host'] == 'two_card'
    assert cap['host_config'] == reg['expected_host_config'] == LIMITS
    assert state['Status'] == 'exited' and state['ExitCode'] == state['Pid'] == 0
    assert not any(state[k] for k in ('Running', 'Paused', 'Restarting', 'OOMKilled', 'Dead'))
    assert cap['payload_intact'] and cap['runtime_intact']
    assert reg['parent_git_revision'] == launched['source_revision'] == captured['source_revision'] == proof['source_revision']
    assert cap['registration_sha256'] == hashlib.sha256(encode(reg)).hexdigest() == proof['registration_sha256']
    raw = encode(proof)
    assert hashlib.sha256(raw).hexdigest() == cap['CPU_proof_sha256'], 'Recover original bytes if serialization differs'
    revision = subprocess.check_output(['git', 'rev-parse', proof['source_revision']], cwd=ROOT, text=True).strip()
    base = read(ROOT/BASE_CAPTURE)['result']
    base_accepted = read(ROOT/BASE_ACCEPTED)
    assert base_accepted['capture_sha256'] == sha(ROOT/BASE_CAPTURE) and base_accepted['total_controls_passed'] == 113
    overlay = {n: hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+n], cwd=ROOT)).hexdigest() for n in OVERLAY}
    assert reg['payload_sha256'] == proof['payload_sha256'] == {**base['registration']['payload_sha256'], **overlay}
    assert reg['runtime_source_sha256'] == proof['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert proof['status'] == 'SOURCE_SCALAR_ACTUAL_LINUX_CPU_PASS_NOT_REAL_MODEL_METHOD'
    assert proof['tests_run'] == 13 and proof['fixed_estimation_tests'] == 11 and proof['original_CFG_pair_tests'] == 2
    assert proof['complete_tiny_requests'] == 32 and proof['synthetic_scalar_rows'] == 128
    assert proof['actual_CPU_affinity'] == [26] and proof['actual_WC_RF_imports_and_globals_accepted']
    assert proof['CPU_import_adapters_used']
    assert all(proof[k] is False for k in ('actual_Cosmos_weights', 'real_source_labels_fitted',
        'real_generated_plan_efficacy', 'CUDA_initialized', 'ledger_written'))
    assert proof['GPU_submissions'] == 0
    assert cap['launch']['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= proof['started_unix']+600
    collection = proof['collection']
    assert collection['status'] == 'PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE'
    assert sorted(row['flow'] for row in collection['checks']) == [False, True]
    manifest = read(ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    design = read(ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json')
    contract = read(ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json')
    expected = {(m, p['id']) for m in design['FIT'] for p in design['parents']}
    for row in collection['checks']:
        assert row['complete_requests'] == 16 and row['complete_scalar_requests'] == row['complete_independent_ordinary_requests'] == 8
        assert row['scalar_rows'] == 64 and row['scalar_physical_pairs'] == 352 and row['independent_control_pairs'] == 288
        assert row['caller_restored'] and not row['actual_Cosmos_weights'] and not row['real_video_efficacy']
        assert len(row['controls']) == 8 and {(c['member'], c['parent']) for c in row['controls']} == expected
        assert all(c['complete_scalar_pairs'] == 44 and c['ordinary_pairs'] == 36
                   and c['final_latent_and_mock_RGB_bitwise_equal'] for c in row['controls'])
        assert all(p['complete_requests'] == 8 and p['prepared_replay_identical'] for p in row['prepared'])
        assert len(complete_samples(row['packet'], design, manifest['schedule'])) == 64
        frozen_weights(row['original_UniPC_scale'], manifest['schedule'], contract, False)
        candidate = row['candidates']
        assert candidate['CPU_fixture_only'] and candidate['samples'] == 64 and len(candidate['families']) == 3
        assert not candidate['endpoint_selection_performed'] and not candidate['GPU_dispatch_ready']
        assert all(len(c['plans']) == 3 for family in candidate['families'] for c in family['candidates'].values())
    return dict(status='ORIGINAL_SCALAR_R3_CPU_COMPLETE_ENTRY_ACCEPTED_NOT_GPU',
                source_revision=revision, recorded_source_revision=proof['source_revision'],
                launch_ref=str(launch_file), launch_sha256=sha(launch_file),
                capture_ref=str(capture_file), capture_sha256=sha(capture_file),
                launch=cap['launch'], registration_sha256=cap['registration_sha256'],
                CPU_proof_sha256=cap['CPU_proof_sha256'], container_state=state,
                payload_sha256=proof['payload_sha256'], tests_run=13,
                complete_loaded_tiny_requests=32, same_state_scalar_rows=128,
                actual_original_UniPC_scales_exported=True, complete_scalar_to_candidate_CLI=True,
                both_flows_all_parent_endpoints_match_independent_ordinary=True,
                actual_Linux_imports=True, CPU_import_adapters_used=True,
                wall_seconds=proof['ended_unix']-proof['started_unix'],
                prior_failure_refs=['reports/cara_v1_scalar_Linux_CPU_original_failure_r1_20261102.json',
                                    'reports/cara_v1_scalar_Linux_CPU_original_failure_r2_20261102.json'],
                actual_Cosmos_weights=False, real_labels_fitted=False, real_video_efficacy=False,
                whole_P1_GPU_entry_accepted=False, P1_GPU_authorized=False,
                GPU_submissions=0, ledger_written=False), raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--proof-output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.proof_output.exists()
    result, raw = accept(args.launch, args.capture)
    args.proof_output.write_bytes(raw)
    result['original_proof_ref'] = str(args.proof_output)
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], tests=13, complete_tiny_requests=32,
                          original_CPU_ended=True, source_revision=result['source_revision'])))


if __name__ == '__main__':
    main()
