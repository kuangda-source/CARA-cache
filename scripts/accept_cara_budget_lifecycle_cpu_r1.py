"""Accept the original Linux CPU delta; mocked GPU metadata stays explicitly scoped."""
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


def accept(path, *, revision="r2"):
    if revision not in ("r1","r2"):raise ValueError("Explicit original CPU revision required")
    capture=json.loads(Path(path).read_text());state=capture['container_state'];proof=capture['CPU_proof'];reg=capture['registration']
    if (state['Status']!='exited' or state['Running'] or state['Pid']!=0 or state['ExitCode']!=0
            or state['OOMKilled'] or proof is None):
        raise ValueError('Original normal terminal and complete CPU proof required')
    if (capture['host_config']!=HOST_CONFIG or reg['expected_host_config']!=HOST_CONFIG
            or not capture['payload_intact'] or not capture['runtime_intact']):
        raise ValueError('Original resource/source contract differs')
    intent=json.loads((ROOT/f'plans/cara_next_stage_20261028/mainline/r2/BUDGET_LIFECYCLE_CPU_FRAGMENT_{revision.upper()}.json').read_text())
    launch=json.loads((ROOT/f'reports/cara_budget_lifecycle_four_card_CPU_launch_{revision}_20261030.json').read_text())
    binding=json.loads((ROOT/f'reports/cara_budget_lifecycle_four_card_CPU_binding_{revision}_20261030.json').read_text())
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
    if (proof['status']!='LIFECYCLE_CAPTURE_LINUX_CPU_CONTROLS_COMPLETE_NOT_GPU'
            or proof['tests_run']!=22 or proof['tests_skipped']!=0
            or proof['lifecycle_controls']!=15 or proof['capture_controls']!=7
            or proof['resource_bound']!=dict(cpus=1,memory_GiB=4,work_seconds=120,exit_seconds=30)
            or proof['Docker_metadata_mocked'] is not True or proof['temporary_fixture_ledger_only'] is not True
            or any(proof[k] for k in ('original_GPU_processes_observed','production_guardian_witness_emitter_implemented',
                'whole_GPU_card_accepted','GPU_submissions','ledger_written'))):
        raise ValueError('Complete explicitly CPU-only lifecycle control matrix required')
    return dict(status='FOUR_CARD_LIFECYCLE_CAPTURE_LINUX_CPU_DELTA_ACCEPTED_NOT_GPU',observed_unix=time.time(),
        capture_ref=str(path),capture_sha256=sha(path),launch=launch,container_state=state,host_config=HOST_CONFIG,
        CPU_proof_sha256=proof_sha,source_sha256=intent['source_sha256'],acceptor_source_sha256=sha(__file__),
        worker_wall_seconds=proof['ended_unix']-proof['started_unix'],tests_run=22,
        actual_GPU_lifecycle_accepted=False,production_guardian_witness_emitter_implemented=False,
        dual_host_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--revision',choices=['r1','r2'],default='r2');args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh acceptance receipt required')
    result=accept(args.capture,revision=args.revision)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],tests_run=result['tests_run'])))


if __name__=='__main__':main()
