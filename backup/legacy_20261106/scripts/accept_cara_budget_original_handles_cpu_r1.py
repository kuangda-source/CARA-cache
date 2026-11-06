"""Accept the original process identity CPU component, never a GPU search run."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(path):
    capture=json.loads(Path(path).read_text());state=capture['container_state'];proof=capture['CPU_proof'];reg=capture['registration']
    if (state['Status']!='exited' or state['Running'] or state['Pid']!=0 or state['ExitCode']!=0
            or state['OOMKilled'] or proof is None):
        raise ValueError('Original complete exited CPU proof required')
    if (capture['host_config']!=HOST_CONFIG or reg['expected_host_config']!=HOST_CONFIG
            or not capture['payload_intact'] or not capture['runtime_intact']):
        raise ValueError('Exact registered CPU resource and source limits required')
    registration_sha=hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()
    proof_sha=hashlib.sha256((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    if (registration_sha!=capture['registration_sha256'] or registration_sha!=proof['registration_sha256']
            or registration_sha!=capture['launch']['registration_sha256'] or proof_sha!=capture['CPU_proof_sha256']
            or reg['payload_sha256']!=proof['source_sha256']):
        raise ValueError('Original registration/proof digest differs')
    intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_ORIGINAL_HANDLES_CPU_FRAGMENT_R1.json').read_text())
    host=capture['launch']['host']
    if (host not in intent['hosts_enabled'] or host!=proof['host'] or host!=reg['host']
            or Path(capture['launch']['stage']).name!=intent['stages'][host]
            or capture['launch']['stage']!=reg['stage']):
        raise ValueError('Original registered host/stage required')
    for name,expected in intent['source_sha256'].items():
        if sha(ROOT/name)!=expected or (name in reg['payload_sha256'] and reg['payload_sha256'][name]!=expected):
            raise ValueError('Registered process identity source changed: '+name)
    original_launch=json.loads((ROOT/'reports/cara_budget_original_handles_four_card_CPU_launch_r1_20261030.json').read_text())
    binding=json.loads((ROOT/'reports/cara_budget_original_handles_four_card_CPU_binding_r1_20261030.json').read_text())
    if capture['launch']!=original_launch or reg['payload_sha256']!=binding['full_payload_sha256']:
        raise ValueError('Original launch or pre-call source binding differs')
    if (proof['status']!='ORIGINAL_PROCESS_VIEW_CPU_CONTROLS_COMPLETE_NOT_GPU'
            or proof['tests_run']!=7 or proof['tests_skipped']!=0 or proof['real_children']!=4
            or not proof['all_own_children_exited_zero'] or not proof['ended_process_bind_refused']
            or not proof['simulated_PID_reuse'] or any(proof[k] for k in (
                'actual_OS_PID_reuse_forced','actual_GPU_handle_observed',
                'complete_GPU_terminal_reader_accepted','GPU_submissions','ledger_written'))):
        raise ValueError('Complete CPU-only identity matrix required')
    roles={'guardian','container_cli','supervisor','runner'}
    handles=proof['original_handles'];obs=proof['observations']
    if set(handles)!=roles or len({(h['pid'],h['start_ticks']) for h in handles.values()})!=4:
        raise ValueError('Four distinct original child bindings required')
    for label in ('all_live','runner_ended_others_live','all_ended'):
        group=obs[label]
        if set(group['handles'])!=roles or group['unresolved_handles']:
            raise ValueError('Complete original role observations required')
        expected={r:label=='all_live' or (label=='runner_ended_others_live' and r!='runner') for r in roles}
        if (group['any_original_handle_live']!=any(expected.values())
                or group['all_original_handles_not_live']!=(not any(expected.values()))):
            raise ValueError('Partial exit must not become a complete terminal')
        for role,row in group['handles'].items():
            h=handles[role]
            if (row['original_live'] is not expected[role] or row['original_pid']!=h['pid']
                    or row['original_start_ticks']!=h['start_ticks'] or row['observed_host_view']!=h['host_view']):
                raise ValueError('Original child identity or liveness differs')
        for row in [group,*group['handles'].values()]:
            if any(row[k] for k in ('dispatch_allowed','financial_settlement_allowed','scientific_read_allowed')):
                raise ValueError('Process evidence must grant no execution or acceptance authority')
    for label in ('different_boot_id','different_pid_namespace_inode'):
        row=obs[label]
        if (row['original_live'] is not None or row['status']!='UNKNOWN'
                or row['reason']!='ORIGINAL_BOOT_OR_PID_NAMESPACE_UNAVAILABLE' or 'observed_process' in row):
            raise ValueError('Wrong host view must remain UNKNOWN without reading a PID')
    reused=obs['simulated_reused_identity_against_real_live_PID']
    if reused['original_live'] is not False or reused['reason']!='PID_REUSED_ORIGINAL_PROCESS_EXITED':
        raise ValueError('Simulated start-tick mismatch evidence required')
    return dict(status='FOUR_CARD_ORIGINAL_PROCESS_IDENTITY_CPU_COMPONENT_ACCEPTED_NOT_GPU',
        observed_unix=time.time(),capture_ref=str(path),capture_sha256=sha(path),
        container_state=state,host_config=HOST_CONFIG,launch=capture['launch'],CPU_proof_sha256=proof_sha,
        local_and_Linux_controls=7,actual_CPU_children=4,simulated_PID_reuse=True,actual_OS_PID_reuse_forced=False,
        worker_wall_seconds=proof['ended_unix']-proof['started_unix'],
        source_sha256=intent['source_sha256'],acceptor_source_sha256=sha(__file__),
        dual_host_endpoint_CPU_accepted=False,GPU_process_terminal_reader_accepted=False,
        whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh acceptance receipt required')
    result=accept(args.capture)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','actual_CPU_children','worker_wall_seconds']}))


if __name__=='__main__':main()
