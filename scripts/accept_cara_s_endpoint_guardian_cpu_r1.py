"""Accept the original exited bounded CPU guardian proof; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from cara_s_endpoint_guardian_cpu_r1 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from test_cara_s_endpoint_host_guardian_r1 import SCENARIOS
from wcomr.policy_price_terminal_r1 import require


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_sha(value):return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured,launched):
    require(captured['exit_code']==launched['exit_code']==0,'Original launch and capture required')
    c,l=captured['result'],launched['result']
    reg,proof,state=c['registration'],c['CPU_proof'],c['container_state']
    require(c['launch']==l and l['host']=='two_card' and Path(l['stage']).name==STAGE
            and l['container']==STAGE+'-cpu','Original endpoint CPU identity differs')
    require(state['Status']=='exited' and state['Running'] is False and state['Pid']==0
            and state['ExitCode']==0 and state['OOMKilled'] is False and proof is not None,
            'Original exited zero proof required')
    require(c['registration_sha256']==encoded_sha(reg)==l['registration_sha256']==proof['registration_sha256']
            and c['CPU_proof_sha256']==encoded_sha(proof),'Original proof bytes differ')
    base=json.loads((ROOT/BASE_CAPTURE).read_text())['result']
    accepted=json.loads((ROOT/BASE_ACCEPTED).read_text())
    require(accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed']==113,
            'Accepted source base differs')
    revision=launched['source_revision']
    overlay={p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    require(reg['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}==proof['payload_sha256']
            and reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']==proof['runtime_source_sha256']
            and reg['base_registration_sha256']==base['registration_sha256']
            and reg['parent_git_revision']==proof['source_revision']==captured['source_revision']==revision
            and c['payload_intact'] is True and c['runtime_intact'] is True,'Original source/runtime differs')
    require(c['host_config']==reg['expected_host_config']==LIMITS and proof['actual_CPU_affinity']==[26],
            'Original CPU resource limits differ')
    require(proof['status']=='ENDPOINT_GUARDIAN_LINUX_CPU_COMPLETE_NOT_WHOLE_CARD'
            and proof['host']=='two_card' and proof['total_controls_passed']==19
            and proof['actual_process_scenarios']==14,'Complete CPU denominator differs')
    results=proof['control_results']
    require(len(results)==2 and [(r['module'],r['tests_run']) for r in results]==[
        ('test_cara_s_endpoint_guardian_binding_r1',4),('test_cara_s_endpoint_host_guardian_r1',15)]
        and all(r['failures']==r['errors']==r['skipped']==0 for r in results),'All Linux controls must pass')
    rows=results[1]['observations']
    require(len(rows)==len(SCENARIOS) and {r['scenario'] for r in rows}==set(SCENARIOS),
            'Every original process scenario required')
    for row in rows:
        unknown=row['scenario'] in ('unknown','wrong_container')
        require(all(row[k] is True for k in ('original_processes_ended','foreign_CPU_sentinel_preserved',
                    'own_lease_released','no_replay'))
                and row['original_wall_interval_complete'] is (not unknown)
                and row['temporary_settlement_events']==(0 if unknown else 1)
                and row['execution_success'] is (row['scenario']=='complete')
                and row['operational_status']==('ORIGINAL_ENDPOINT_LIVE_OR_UNKNOWN' if unknown else
                    'ORIGINAL_ENDPOINT_LIFECYCLE_CAPTURE'),'Original closure/no-replay/settlement boundary differs')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=900
            and proof['work_seconds']==900 and proof['exit_seconds']==60
            and proof['synthetic_GPU_and_Docker'] is True and proof['temporary_ledger_only'] is True
            and all(proof[k] is False for k in ('whole_GPU_card_accepted','active_experiment_outputs_read','ledger_written'))
            and proof['GPU_submissions']==0,'CPU-only or bounded runtime differs')
    return dict(status='ENDPOINT_GUARDIAN_LINUX_CPU_ACCEPTED_NOT_WHOLE_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        total_controls_passed=19,actual_process_scenarios=14,CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        original_handles_only=True,foreign_CPU_sentinel_preserved=True,thermal_stop_90C_checked=True,
        hard_deadline_checked=True,temporary_ledger_only=True,whole_GPU_card_accepted=False,
        active_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','launch','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Preserve original acceptance')
    result=accept(json.loads(args.capture.read_text()),json.loads(args.launch.read_text()))
    result.update(capture_ref=str(args.capture),capture_sha256=sha(args.capture),launch_ref=str(args.launch),
                  launch_sha256=sha(args.launch),acceptor_sha256=sha(__file__))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','total_controls_passed','CPU_wall_seconds')}))


if __name__=='__main__':main()
