"""Offline acceptance of the complete14 original Linux CPU terminal, no replay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from cara_read_write_collection_linux_cpu_r1 import OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE, BASE_ACCEPTED, LIMITS


def accept(launch_path, capture_path):
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    encoded = lambda value: hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()
    launch, capture = [json.loads(Path(p).read_text()) for p in (launch_path,capture_path)]
    assert launch['exit_code'] == capture['exit_code'] == 0
    cap = capture['result'];reg = cap['registration'];proof = cap['CPU_proof'];state = cap['container_state']
    assert cap['launch'] == launch['result'] and cap['host_config'] == reg['expected_host_config'] == LIMITS
    assert state['Status'] == 'exited' and state['ExitCode'] == 0 and state['Pid'] == 0 and not state['OOMKilled']
    assert reg['host'] == 'two_card' and reg['parent_git_revision'] == launch['source_revision'] == capture['source_revision']
    assert cap['registration_sha256'] == encoded(reg) == proof['registration_sha256'] == cap['launch']['registration_sha256']
    assert cap['CPU_proof_sha256'] == encoded(proof) and cap['payload_intact'] and cap['runtime_intact']
    base_bytes = (ROOT/BASE_CAPTURE).read_bytes();base = json.loads(base_bytes)['result']
    base_accept = json.loads((ROOT/BASE_ACCEPTED).read_text())
    assert base_accept['capture_sha256'] == hashlib.sha256(base_bytes).hexdigest() and base_accept['total_controls_passed'] == 113
    revision = subprocess.check_output(['git','rev-parse',launch['source_revision']],cwd=ROOT,text=True).strip()
    overlay = {p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    assert reg['payload_sha256'] == proof['payload_sha256'] == {**base['registration']['payload_sha256'],**overlay}
    assert reg['runtime_source_sha256'] == proof['runtime_source_sha256'] == base['registration']['runtime_source_sha256']
    assert proof['status'] == 'READ_WRITE_FULL14_ACTUAL_LINUX_CPU_PASS_NOT_GPU'
    assert proof['complete_guarded_tiny_requests'] == 28 and proof['actual_Cosmos_argument_class']
    assert proof['per_matrix'] == dict(requests=14,scientific_outputs=8,logical_solver_updates=504,physical_model_pairs=512,physical_CFG_calls=1024)
    assert proof['actual_WC_RF_imports_and_globals_accepted'] and proof['actual_CPU_affinity'] == [26]
    assert all(proof[k] is False for k in ('CUDA_initialized','actual_Cosmos_weights','real_encoded_video','actual_model_VJP','ledger_written','whole_GPU_card_accepted'))
    assert proof['GPU_submissions'] == 0
    assert cap['launch']['started_unix'] <= proof['started_unix'] < proof['ended_unix'] <= proof['started_unix']+600
    assert len(proof['collection']['checks']) == 2
    assert sum(r['complete_paths'] for r in proof['collection']['checks']) == 28
    assert all(r['physical_model_pairs']==512 and r['actual_Cosmos_argument_class']
               and r['caller_reset_and_duplicate_refusal'] for r in proof['collection']['checks'])
    return dict(status='ORIGINAL_READ_WRITE_FULL14_LINUX_CPU_ACCEPTED_GPU_ORCHESTRATION_PENDING',
        source_revision=revision, launch_ref=str(launch_path),launch_sha256=sha(launch_path),
        capture_ref=str(capture_path),capture_sha256=sha(capture_path),launch=cap['launch'],container_state=state,
        registration_sha256=cap['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],
        affected_source_sha256=overlay,actual_Linux_imports=True,actual_Cosmos_argument_class=True,complete_tiny_requests=28,requests_per_matrix=14,physical_model_pairs_per_matrix=512,
        wall_seconds=proof['ended_unix']-proof['started_unix'],actual_Cosmos_weights=False,
        real_encoded_video=False,real_model_VJP=False,whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)


def main():
    p = argparse.ArgumentParser()
    for name in ('launch','capture','output'):p.add_argument('--'+name,type=Path,required=True)
    args = p.parse_args();assert not args.output.exists()
    value = accept(args.launch,args.capture)
    with args.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=value['status'],wall_seconds=value['wall_seconds'])))


if __name__ == '__main__':main()
