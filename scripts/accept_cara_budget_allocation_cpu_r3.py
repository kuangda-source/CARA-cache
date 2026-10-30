"""Accept the original host allocation CPU chain."""
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


def accept(path, *, revision="r3"):
    if revision!="r3":raise ValueError("Explicit original CPU revision required")
    capture=json.loads(Path(path).read_text());state=capture['container_state'];proof=capture['CPU_proof'];reg=capture['registration']
    if (state['Status']!='exited' or state['Running'] or state['Pid']!=0 or state['ExitCode']!=0
            or state['OOMKilled'] or proof is None):
        raise ValueError('Original normal terminal and complete CPU proof required')
    if (capture['host_config']!=HOST_CONFIG or reg['expected_host_config']!=HOST_CONFIG
            or not capture['payload_intact'] or not capture['runtime_intact']):
        raise ValueError('Original resource/source contract differs')
    intent=json.loads((ROOT/f'plans/cara_next_stage_20261028/mainline/r2/BUDGET_ALLOCATION_CPU_FRAGMENT_{revision.upper()}.json').read_text())
    launch=json.loads((ROOT/f'reports/cara_budget_allocation_four_card_CPU_launch_{revision}_20261030.json').read_text())
    binding=json.loads((ROOT/f'reports/cara_budget_allocation_four_card_CPU_binding_{revision}_20261030.json').read_text())
    reg_sha=hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()
    proof_sha=hashlib.sha256((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    if (capture['launch']!=launch or reg['stage']!=launch['stage'] or reg['host']!='four_card'
            or proof['host']!='four_card' or Path(reg['stage']).name!=intent['stages']['four_card']
            or reg_sha!=capture['registration_sha256'] or reg_sha!=launch['registration_sha256']
            or proof['registration_sha256']!=reg_sha or capture['CPU_proof_sha256']!=proof_sha
            or reg['payload_sha256']!=proof['source_sha256'] or reg['payload_sha256']!=binding['full_payload_sha256']):
        raise ValueError('Original launch/registration/payload/proof identity differs')
    for name,expected in intent['source_sha256'].items():
        if sha(ROOT/name)!=expected or (name in reg['payload_sha256'] and reg['payload_sha256'][name]!=expected):
            raise ValueError('Registered lifecycle delta source changed: '+name)
    if (proof['status']!='ALLOCATION_LINUX_CHAIN_CPU_CONTROLS_COMPLETE_NOT_GPU'
            or proof['tests_run']!=13 or proof['tests_skipped']!=0
            or proof['resource_bound']!=dict(cpus=1,memory_GiB=4,work_seconds=120,exit_seconds=30)
            or proof['Docker_metadata_mocked'] is not True or proof['temporary_fixture_ledger_only'] is not True
            or proof['original_guardian_CLI_supervisor_runner_CPU_processes'] is not True
            or any(proof[k] for k in ('original_GPU_processes_observed','production_GPU_dispatch_bound',
                'whole_GPU_card_accepted','GPU_submissions','ledger_written'))):
        raise ValueError('Complete explicitly CPU-only lifecycle control matrix required')
    expected={'complete','runner_failure','missing_credential','busy','mode_failure','no_container',
        'init_failure','hard_limit','unknown','wrong_container','restore_busy','bootstrap_failure'}
    rows=proof['scenario_observations']
    if len(rows)!=12 or {r['scenario'] for r in rows}!=expected:
        raise ValueError('All twelve original allocation scenarios required')
    reasons={'runner_failure':'Original container CLI failed','missing_credential':'credential delivery failed',
        'busy':'Selected GPU is busy','mode_failure':'mode command failed','no_container':'Original container CLI failed',
        'init_failure':'Original container CLI failed','hard_limit':'release margin','unknown':'observation unknown',
        'wrong_container':'original Docker creation ID','bootstrap_failure':'Original container CLI failed'}
    for row in rows:
        scenario=row['scenario'];unknown=scenario in ('unknown','wrong_container')
        roles=['guardian']
        if scenario not in ('missing_credential','busy','mode_failure'):roles.append('container_cli')
        if scenario in ('complete','runner_failure','hard_limit','unknown','wrong_container','restore_busy','bootstrap_failure'):
            roles+=['supervisor','runner']
        if (row['actual_bound_process_roles']!=roles
                or not all(row[k] for k in ('original_processes_ended','foreign_CPU_sentinel_preserved','own_lease_released','no_replay'))
                or row['original_wall_interval_complete'] is unknown
                or row['temporary_settlement_events']!=(0 if unknown else 1)
                or row['execution_success'] is not (scenario=='complete')
                or row['mode_restored'] is not (scenario!='restore_busy')
                or row['operational_status']!=('ORIGINAL_CALIBRATION_LIVE_OR_UNKNOWN' if unknown else 'ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE')
                or (scenario in reasons and (not row['error_type'] or reasons[scenario] not in row['stop_reason']))
                or (scenario not in reasons and row['error_type'] is not None)):
            raise ValueError('Original chain, unique charge, unknown or release boundary differs')
    return dict(status='FOUR_CARD_ALLOCATION_LINUX_CPU_CHAIN_ACCEPTED_NOT_GPU',observed_unix=time.time(),
        capture_ref=str(path),capture_sha256=sha(path),launch=launch,container_state=state,host_config=HOST_CONFIG,
        CPU_proof_sha256=proof_sha,source_sha256=intent['source_sha256'],acceptor_source_sha256=sha(__file__),
        worker_wall_seconds=proof['ended_unix']-proof['started_unix'],tests_run=13,operational_scenarios=12,actual_runner_CPU_children=7,actual_guardian_CPU_children=12,
        actual_GPU_lifecycle_accepted=False,production_GPU_dispatch_bound=False,actual_GPU_monitor_verified=False,
        dual_host_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--revision',choices=['r3'],default='r3');args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh acceptance receipt required')
    result=accept(args.capture,revision=args.revision)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],tests_run=result['tests_run'])))


if __name__=='__main__':main()
