"""Accept only the original two-card child CPU component, never GPU authority."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from accept_cara_budget_calibration_cpu_r3 import encoded_sha, require
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-budget-two-card-policy-CPU-a6000-r1-20261031'
OVERLAY = ('src/wcomr/cara_budget_host_policy_r1.py', 'src/wcomr/cara_budget_dispatch_r1.py', 'src/wcomr/cara_budget_prepare_r1.py', 'src/wcomr/cara_budget_central_r1.py', 'tests/test_cara_budget_dispatch_r1.py', 'tests/test_cara_budget_prepare_r1.py', 'tests/test_cara_budget_central_r1.py', 'tests/check_cara_budget_dispatch_child_fixture_r1.py', 'tests/test_cara_budget_dispatch_child_r1.py', 'scripts/check_cara_budget_two_card_policy_cpu_r1.py', 'plans/cara_next_stage_20261028/mainline/r2/TWO_CARD_ONLY_HARDWARE_MAINTENANCE_20261031.json')
BASE_REF = 'reports/cara_budget_current_CPU_two_R4_capture_r4_20261031.json'
BASE_ACCEPTED = 'reports/cara_budget_current_CPU_two_R4_accepted_r1_20261031.json'


def main():
    parser = argparse.ArgumentParser()
    for name in ('capture', 'launch', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Recover an existing acceptance, never overwrite')
    captured = json.loads(args.capture.read_text())
    launched = json.loads(args.launch.read_text())
    require(captured['exit_code'] == launched['exit_code'] == 0, 'Successful original transport required')
    c, launch = captured['result'], launched['result']
    reg, proof, state = c['registration'], c['CPU_proof'], c['container_state']
    require(c['launch'] == launch and launch['host'] == 'two_card'
            and Path(launch['stage']).name == STAGE and launch['container'] == STAGE+'-cpu',
            'Only the original two-card child component is admissible')
    require(state['Status'] == 'exited' and state['Running'] is False and state['Pid'] == 0
            and state['ExitCode'] == 0 and not state['OOMKilled'] and proof is not None,
            'Original CPU must exit normally with a complete proof')
    require(c['registration_sha256'] == encoded_sha(reg) == launch['registration_sha256']
            == proof['registration_sha256'] and c['CPU_proof_sha256'] == encoded_sha(proof),
            'Original registration and proof bytes must match')
    base = json.loads((ROOT/BASE_REF).read_text())['result']
    accepted = json.loads((ROOT/BASE_ACCEPTED).read_text())
    require(accepted['capture_sha256'] == hashlib.sha256((ROOT/BASE_REF).read_bytes()).hexdigest()
            and accepted['status'] == 'CURRENT_R4_CPU_MATRIX_ACCEPTED_NOT_GPU_DISPATCH',
            'Accepted original R4 base required')
    revision = launched['source_revision']
    overlay = {n: hashlib.sha256(subprocess.check_output(['git', 'show', revision+':'+n], cwd=ROOT)).hexdigest()
               for n in OVERLAY}
    require(reg['payload_sha256'] == {**base['registration']['payload_sha256'], **overlay}
            and reg['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
            and reg['base_registration_sha256'] == base['registration_sha256']
            and reg['parent_git_revision'] == proof['source_revision'] == captured['source_revision'] == revision
            and c['payload_intact'] is True and c['runtime_intact'] is True,
            'Published child delta, original full R4 payload and runtime must remain exact')
    require(c['host_config'] == reg['expected_host_config'] == HOST_CONFIG,
            'Original 1CPU/4GiB/no extra swap/no GPU resource boundary differs')
    require(proof['status'] == 'TWO_CARD_HOST_POLICY_AND_ACTUAL_CHILD_CPU_COMPONENT_COMPLETE_NOT_GPU'
            and proof['host'] == 'two_card' and proof['tests_run'] == 43
            and len(proof['observations']) == 1
            and launch['started_unix'] <= proof['started_unix'] <= proof['ended_unix']
            and proof['ended_unix']-proof['started_unix'] <= 180,
            'Complete actual Linux child control within the original time bound required')
    expected_controls = {'test_cara_budget_dispatch_r1': 15, 'test_cara_budget_prepare_r1': 9,
        'test_cara_budget_central_r1': 11, 'test_cara_budget_runner_binding_r1': 7,
        'test_cara_budget_dispatch_child_r1': 1}
    rows = {r['module']: r for r in proof['controls']}
    require(len(proof['controls']) == len(rows) == len(expected_controls)
            and set(rows) == set(expected_controls)
            and all(rows[n]['tests_run'] == count and not any(rows[n][k] for k in ('errors','failures','skipped'))
                    for n,count in expected_controls.items()), 'All affected host-policy controls must pass on Linux')
    row = proof['observations'][0]
    require(row['child_exit_code'] == 1 and all(row[k] is True for k in (
        'exact_guardian_entry', 'real_Popen_and_private_pipe', 'guardian_launch_identity_equal',
        'original_child_ended', 'original_failure_journal_and_bill_complete',
        'no_allocation_attempted', 'no_replay', 'sources_unchanged', 'synthetic_metadata_only'))
        and row['actual_GPU_resources_exercised'] is False and row['actual_GPUh'] == 0
        and row['ledger_written'] is False, 'The original synthetic failure and no-allocation boundary differ')
    identity = row['original_identity']
    require(identity['pid'] > 0 and identity['start_ticks'] > 0
            and identity['host_view']['pid_namespace_inode'] > 0
            and len(identity['original_command_sha256']) == 64, 'Original Linux process witness required')
    require(not any(proof[k] for k in ('GPU_submissions', 'ledger_written', 'whole_GPU_card_accepted',
            'real_Docker_GPU_lifecycle_exercised', 'actual_64GiB_storage_exercised')),
            'CPU component cannot claim GPU or storage acceptance')
    report = dict(status='TWO_CARD_POLICY_AND_ACTUAL_CHILD_CPU_COMPONENT_ACCEPTED_NOT_GPU', observed_unix=time.time(),
        host='two_card', launch=launch, source_revision=revision, overlay_sha256=overlay,
        full_source_files=len(reg['payload_sha256']), original_R4_sources_unchanged=False, affected_controls=proof['controls'],
        original_R4_numeric_sources_reused_unchanged=True,
        original_R4_acceptance_ref=BASE_ACCEPTED, container_state=state, host_config=HOST_CONFIG,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'], observations=proof['observations'],
        capture_ref=str(args.capture), capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        launch_ref=str(args.launch), launch_sha256=hashlib.sha256(args.launch.read_bytes()).hexdigest(),
        CPU_proof_sha256=c['CPU_proof_sha256'], registration_sha256=c['registration_sha256'],
        acceptor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        whole_card_CPU_accepted=False, real_Docker_GPU_lifecycle_exercised=False,
        actual_64GiB_storage_exercised=False, GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(report['status'])


if __name__ == '__main__':
    main()
