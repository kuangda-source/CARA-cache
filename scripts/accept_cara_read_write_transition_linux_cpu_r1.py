"""Accept the original GPU-hidden transition CPU terminal, without replay."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from cara_read_write_transition_linux_cpu_r1 import OVERLAY, STAGE
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS


def original_capture(launch_path, capture_path, *, stage, overlay_names, expected_tests=5):
    encoded = lambda value: hashlib.sha256((json.dumps(value, indent=2)+'\n').encode()).hexdigest()
    launch, capture = [json.loads(Path(p).read_text()) for p in (launch_path, capture_path)]
    assert launch['exit_code'] == capture['exit_code'] == 0
    cap = capture['result'];reg = cap['registration'];proof = cap['CPU_proof'];state = cap['container_state']
    assert cap['launch'] == launch['result'] and cap['host_config'] == reg['expected_host_config'] == LIMITS
    assert state['Status'] == 'exited' and state['ExitCode'] == 0 and state['Pid'] == 0 and not state['OOMKilled']
    assert cap['launch']['container'] == stage+'-cpu' and Path(reg['stage']).name == stage
    assert reg['host'] == 'two_card' and reg['parent_git_revision'] == launch['source_revision'] == capture['source_revision']
    assert cap['registration_sha256'] == encoded(reg) == proof['registration_sha256'] == cap['launch']['registration_sha256']
    assert cap['CPU_proof_sha256'] == encoded(proof) and cap['payload_intact'] and cap['runtime_intact']
    base_bytes = (ROOT/BASE_CAPTURE).read_bytes();base = json.loads(base_bytes)['result']
    base_accept = json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert base_accept['capture_sha256'] == hashlib.sha256(base_bytes).hexdigest() and base_accept['total_controls_passed'] == 113
    revision = subprocess.check_output(['git', 'rev-parse', launch['source_revision']], cwd=ROOT, text=True).strip()
    overlay = {p:hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+p], cwd=ROOT)).hexdigest() for p in overlay_names}
    assert reg['payload_sha256'] == proof['payload_sha256'] == {**base['registration']['payload_sha256'], **overlay}
    assert reg['runtime_source_sha256'] == proof['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert proof['tests_run'] == expected_tests
    assert proof['actual_WC_RF_imports_and_globals_accepted'] and proof['actual_CPU_affinity'] == [26]
    assert proof['CPU_import_adapters_used'] and proof['tiny_model_weights']
    assert all(proof[k] is False for k in ('CUDA_initialized', 'actual_Cosmos_weights', 'actual_Cosmos_model_VJP',
        'terminal_LPIPS_VJP', 'complete_augmented_adjoint', 'ledger_written'))
    assert proof['GPU_submissions'] == 0 and proof['work_seconds'] == 600 and proof['exit_seconds'] == 60
    assert cap['launch']['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= proof['started_unix']+600
    assert cap['launch']['MemAvailable_before'] >= 8*2**30
    return cap, revision, overlay


def accept(launch_path, capture_path):
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    cap, revision, overlay = original_capture(launch_path, capture_path, stage=STAGE, overlay_names=OVERLAY)
    proof, state = cap['CPU_proof'], cap['container_state']
    assert proof['status'] == 'READ_WRITE_TRANSITION_ACTUAL_LINUX_CPU_PASS_NOT_COSMOS_VJP'
    metrics = proof['metrics']
    expected = dict(exact_outputs=True, exact_complete_WC_state=True, exact_buffers=True,
        caller_and_each_input_state_unchanged=True, original70_call_cycle_reset_covered=True, total_branches=72)
    assert all(metrics['flow_'+str(flow)+'_full36'] == expected for flow in (False, True))
    assert metrics['C_working_state_is_nonidentity_and_differentiable'] is True
    derivatives = metrics['actual_C_cache_and_flow_RF_tiny_VJP']
    assert [row['group'] for row in derivatives] == ['current_input', 'cached_residual']
    whole = metrics['full36_pinned_WC_RF_UniPC_tiny_graph']
    assert whole['actual_Cosmos_weights'] is False and whole['terminal_loss'] == 'declared_synthetic_latent_MSE'
    for row in [*derivatives, whole]:
        assert row['epsilon'] == .01 and row['tolerance'] == 4e-6
        assert all(math.isfinite(row[k]) for k in ('predicted', 'central_FD', 'absolute_error'))
        assert abs(row['predicted']-row['central_FD']) <= 4e-6
        assert math.isclose(row['absolute_error'], abs(row['predicted']-row['central_FD']), rel_tol=1e-9, abs_tol=1e-15)
        assert abs(row['predicted']) > 1e-5
    return dict(status='ORIGINAL_READ_WRITE_TRANSITION_LINUX_CPU_ACCEPTED_NOT_REAL_COSMOS_VJP',
        source_revision=revision, launch_ref=str(launch_path), launch_sha256=sha(launch_path),
        capture_ref=str(capture_path), capture_sha256=sha(capture_path), launch=cap['launch'], container_state=state,
        registration_sha256=cap['registration_sha256'], CPU_proof_sha256=cap['CPU_proof_sha256'],
        affected_source_sha256=overlay, actual_Linux_imports=True, actual_WC_RF_globals=True,
        tests_run=5, torch_version=proof['torch_version'], metrics=metrics,
        wall_seconds=proof['ended_unix']-proof['started_unix'], actual_Cosmos_weights=False,
        actual_Cosmos_model_VJP=False, terminal_LPIPS_VJP=False, complete_augmented_adjoint=False,
        GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('launch', 'capture', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    receipt = accept(args.launch, args.capture)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], wall_seconds=receipt['wall_seconds'])))


if __name__ == '__main__':
    main()
