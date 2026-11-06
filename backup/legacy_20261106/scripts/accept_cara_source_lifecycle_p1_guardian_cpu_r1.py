"""Only accept the saved original affected guardian CPU; never replay its flows."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS
from cara_source_lifecycle_p1_guardian_cpu_r1 import STAGE, OVERLAY


def accept(launch_file,capture_file,*,expected_stage=STAGE,overlay=OVERLAY):
    read=lambda path:json.loads(Path(path).read_bytes())
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    launch,capture=read(launch_file),read(capture_file)
    assert launch['exit_code']==capture['exit_code']==0
    cap,launched=capture['result'],launch['result']
    assert cap['launch']==launched and Path(launched['stage']).name==expected_stage
    reg,state,proof=cap['registration'],cap['container_state'],cap['CPU_proof']
    assert proof is not None and state['Status']=='exited' and state['Pid']==state['ExitCode']==0
    assert not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
    assert cap['host_config']==reg['expected_host_config']==LIMITS
    assert cap['payload_intact'] and cap['runtime_intact']
    revision=launch['source_revision']
    assert revision==capture['source_revision']==reg['parent_git_revision']==proof['source_revision']
    assert subprocess.check_output(['git','rev-parse',revision],cwd=ROOT,text=True).strip()==revision
    encode=lambda value:(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert hashlib.sha256(encode(reg)).hexdigest()==cap['registration_sha256']==proof['registration_sha256']
    raw=encode(proof)
    assert hashlib.sha256(raw).hexdigest()==cap['CPU_proof_sha256']
    base=read(ROOT/BASE_CAPTURE)['result'];accepted=read(ROOT/BASE_ACCEPTED)
    assert accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed']==113
    expected={**base['registration']['payload_sha256'],**{
        n:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in overlay}}
    assert proof['payload_sha256']==reg['payload_sha256']==expected
    assert proof['runtime_source_sha256']==reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']
    assert proof['status']=='P1_ORIGINAL_GUARDIAN_FIT_SERVICE_LINUX_CPU_COMPONENT_PASS'
    assert proof['tests_run']==34 and proof['actual_CPU_affinity']==[26]
    assert proof['work_seconds']==600 and proof['exit_seconds']==60
    assert launched['started_unix']<=proof['started_unix']<proof['ended_unix']<=launched['started_unix']+600
    rows=proof['original_process_scenarios']
    assert {r['scenario'] for r in rows}=={'success','start_failure','service_failure','GPU_failure','cleanup_unknown'}
    for row in rows:
        assert all(row[k] is True for k in ('original_GPU_bill_unique','GPU_and_CPU_originals_ended',
            'mode_restored','foreign_sentinel_preserved','no_replay'))
        assert (row['guardian_exit_code']==0)==(row['scenario']=='success')
        assert row['CPU_cleanup_unknown_retained']==(row['scenario']=='cleanup_unknown')
        assert row['GPU_submissions']==0 and row['ledger_written'] is False
    assert proof['actual_original_Linux_processes'] and proof['internal_GPU_and_Docker_simulated']
    assert all(proof[k] is False for k in ('prior_algorithm_or_metric_work_repeated','actual_Cosmos_weights',
        'actual_central_ledger_accessed','whole_GPU_entry_accepted','P1_GPU_authorized','ledger_written'))
    assert proof['GPU_submissions']==0
    return dict(status='ORIGINAL_P1_GUARDIAN_FIT_LINUX_CPU_COMPONENT_ACCEPTED_NOT_WHOLE_GPU_ENTRY',
        source_revision=revision,CPU_stage=expected_stage,launch_ref=str(launch_file),launch_sha256=sha(launch_file),
        capture_ref=str(capture_file),capture_sha256=sha(capture_file),original_proof_sha256=cap['CPU_proof_sha256'],
        registration_sha256=cap['registration_sha256'],original_CPU_ended=True,original_container_state=state,
        tests_run=34,original_process_scenarios=rows,actual_original_Linux_processes=True,
        internal_GPU_and_Docker_simulated=True,prior_algorithm_or_metric_work_repeated=False,
        whole_GPU_entry_accepted=False,P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False),raw


def main(*,expected_stage=STAGE,overlay=OVERLAY):
    parser=argparse.ArgumentParser()
    for key in ('launch','capture','output','proof-output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and not args.proof_output.exists()
    accepted,raw=accept(args.launch,args.capture,expected_stage=expected_stage,overlay=overlay)
    with args.proof_output.open('xb') as stream:stream.write(raw)
    accepted['original_proof_ref']=str(args.proof_output)
    with args.output.open('x') as stream:json.dump(accepted,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=accepted['status'],tests_run=accepted['tests_run'],P1_GPU_authorized=False)))


if __name__=='__main__':main()
