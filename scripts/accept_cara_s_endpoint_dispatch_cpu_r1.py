"""Accept the original exited bounded CPU recovery proof; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from cara_s_endpoint_dispatch_cpu_r1 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.policy_price_terminal_r1 import require


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_sha(value):return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured,launched):
    require(captured['exit_code']==0,'Original capture required')
    c=captured['result'];recovered=launched['exit_code']!=0
    require(launched['action']=='prepare' and launched['host']=='two_card' and launched['stage_name']==STAGE,
            'Original prepare binding required')
    if recovered:
        require(launched['result'] is None and launched['unknown_requires_original_capture'] is True,
                'Unknown transport must retain its original prepare binding')
        l=c['launch']
        require(l['started_unix']>=launched['started_unix'],'Recovered launch predates original prepare')
    else:l=launched['result']
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
    require(proof['status']=='ENDPOINT_SCORE_ONCE_DISPATCH_CPU_COMPLETE_NOT_WHOLE_CARD'
            and proof['host']=='two_card' and proof['total_controls_passed']==21
            and proof['metadata_controls']==dict(tests_run=13,failures=0,errors=0,skipped=0),
            'Complete original once-dispatch CPU denominator required')
    actual=proof['actual'];cases=actual['cases']
    scenarios=('complete','worker_failure','preworker_failure','timeout','unknown_capture','wrong_container','bootstrap_failure')
    require(actual['status']=='ACTUAL_LINUX_ONCE_SCORE_DISPATCH_CPU_PASS' and actual['scenarios']==7
            and [c['scenario'] for c in cases]==list(scenarios),'Every original process scenario required')
    def original_ended(identity,observation):
        require(observation['original_live'] is False and observation['status']=='ORIGINAL_NOT_LIVE'
                and observation['original_pid']==identity['pid'] and observation['original_start_ticks']==identity['start_ticks']
                and observation['observed_host_view']==identity['host_view'],'Original process is not proved ended')
    for case in cases:
        scenario=case['scenario'];terminal=case['supervisor_terminal']
        expected='ORIGINAL_COMPLETE24_SCORE_ACCEPTED' if scenario in ('complete','unknown_capture') else (
            'FOREIGN_CONTAINER_REFUSED' if scenario=='wrong_container' else (
                'ORIGINAL_SCORE_DISPATCH_UNKNOWN' if scenario=='bootstrap_failure' else 'ORIGINAL_SCORE_FAILED'))
        require(case['status']==expected and (case['exit_code']==0)==(scenario in ('complete','unknown_capture'))
                and case['one_supervisor_spawn'] is True and case['repeated_dispatch_spawned'] is False
                and case['foreign_process_preserved'] is True,'Original once-dispatch/recovery boundary differs')
        original_ended(terminal['identity'],case['supervisor_observation'])
        roles=set(case['original_handles'])
        require(roles==(set() if scenario=='bootstrap_failure' else ({'cli'} if scenario=='preworker_failure' else {'cli','worker'})),
                'Original process roles differ')
        for handle in case['original_handles'].values():original_ended(handle['identity'],handle['observation'])
        if scenario in ('complete','unknown_capture'):
            require(terminal['exit_code']==0 and terminal['error'] is None and terminal['cleanup_error'] is None,
                    'Complete supervisor must be clean')
        if scenario in ('timeout','wrong_container'):
            require(terminal['error']['type']=='TimeoutExpired','Original shortened CPU deadline must fire')
        if scenario=='wrong_container':require(terminal['cleanup_error'] is not None,'Foreign container must not be stopped')
    environment=proof['actual_readonly_CPU_environment']
    require(environment['available_memory_bytes']>=12*1024**3 and environment['free_disk_bytes']>=2*1024**3
            and environment['CPU_affinity']==[26] and environment['actual_Alex_checkpoint_SHA_checked'] is True
            and environment['actual_PIQ_site_checked'] is True and environment['future_dispatch_admission'] is False
            and environment['production_two_core_affinity_checked'] is False
            and proof['started_unix']<=environment['observed_unix']<=proof['ended_unix'],
            'Actual readonly CPU environment proof differs')
    require(actual['full24_acceptances']==2 and actual['new_pairs_per_acceptance']==12
            and actual['Docker_simulated'] is True and actual['score_values_synthetic'] is True
            and actual['metric_computations']==actual['GPU_submissions']==0 and actual['ledger_written'] is False
            and actual['original_experiment_outputs_read'] is False,'Synthetic scope must remain explicit')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=300 and proof['work_seconds']==300 and proof['exit_seconds']==30
            and proof['Docker_observations_simulated'] is True and proof['score_rows_synthetic'] is True
            and proof['metric_computations']==proof['GPU_submissions']==0 and proof['ledger_written'] is False
            and proof['whole_GPU_card_accepted'] is False and proof['active_experiment_outputs_read'] is False,
            'Original bounded CPU-only scope differs')
    return dict(status='ENDPOINT_SCORE_ONCE_DISPATCH_CPU_ACCEPTED_NOT_WHOLE_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,launch_recovered_from_original_capture=recovered,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],total_controls_passed=21,
        metadata_controls_passed=13,actual_process_scenarios=7,actual_readonly_environment_checks=1,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],actual_original_Linux_processes=True,
        Docker_observations_simulated=True,score_rows_synthetic=True,metric_computations=0,
        whole_GPU_card_accepted=False,active_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)


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
