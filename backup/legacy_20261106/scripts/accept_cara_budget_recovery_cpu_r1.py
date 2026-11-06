"""Accept the original CPU recovery component, never a GPU search run."""
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
    intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_RECOVERY_CPU_FRAGMENT_R1.json').read_text())
    host=capture['launch']['host']
    if (host not in intent['hosts_enabled'] or host!=proof['host'] or host!=reg['host']
            or Path(capture['launch']['stage']).name!=intent['stages'][host]
            or capture['launch']['stage']!=reg['stage']):
        raise ValueError('Original registered host/stage required')
    for name,expected in intent['source_sha256'].items():
        if sha(ROOT/name)!=expected or (name in reg['payload_sha256'] and reg['payload_sha256'][name]!=expected):
            raise ValueError('Registered recovery source changed: '+name)
    original_path=ROOT/'reports/cara_budget_endpoint_four_card_CPU_terminal_capture_r2_20261030.json'
    original=json.loads(original_path.read_text())
    if (reg['base_registration_sha256']!=original['registration_sha256']
            or reg['original_endpoint_stage']!=original['launch']['stage']
            or proof['original_CPU_proof_sha256']!=original['CPU_proof_sha256']):
        raise ValueError('Original completed endpoint evidence differs')
    if (proof['status']!='CPU_ORIGINAL_ENDPOINT_RECOVERY_COMPONENT_COMPLETE_NOT_GPU'
            or proof['local_controls']!=9 or proof['skipped_tests']!=0
            or proof['recovered_complete_two_FIT_objectives']!=4 or len(proof['original_production_copies'])!=4
            or not proof['originals_unchanged'] or any(proof[k] for k in (
                'new_generation_calls','GPU_process_terminal_reader_accepted','whole_GPU_card_accepted',
                'GPU_submissions','ledger_written'))):
        raise ValueError('Complete CPU-only recovery matrix required')
    for item in proof['original_production_copies']:
        r=item['recovered']
        if (not item['second_call_no_write'] or r['status']!='ORIGINAL_COMPLETE_CPU_CALLBACK_RECOVERED'
                or not r['new_return_written'] or r['new_generation_calls'] or r['GPU_dispatch_ready']
                or len(r['recovery']['original_artifacts'])!=4 or r['recovery']['GPU_process_terminal_verified']):
            raise ValueError('Complete original cohort recovery with no generation required')
    return dict(status='FOUR_CARD_ORIGINAL_ENDPOINT_RECOVERY_CPU_COMPONENT_ACCEPTED_NOT_GPU',
        observed_unix=time.time(),capture_ref=str(path),capture_sha256=sha(path),
        container_state=state,host_config=HOST_CONFIG,launch=capture['launch'],CPU_proof_sha256=proof_sha,
        local_and_Linux_controls=9,actual_original_copies=4,new_generation_calls=0,
        originals_unchanged=True,worker_wall_seconds=proof['ended_unix']-proof['started_unix'],
        source_sha256=intent['source_sha256'],acceptor_source_sha256=sha(__file__),
        dual_host_endpoint_CPU_accepted=False,GPU_process_terminal_reader_accepted=False,
        whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh acceptance receipt required')
    result=accept(args.capture)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','actual_original_copies','new_generation_calls']}))


if __name__=='__main__':main()
