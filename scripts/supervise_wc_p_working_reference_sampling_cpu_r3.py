"""One isolated complete P-reference CPU check; never access a GPU or ledger writer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    project=Path('/home/gaokuangda/data/gkd/worldcache_omr')
    stage=args.stage.resolve()
    reg=json.loads((stage/'registration.json').read_text())
    assert stage==(project/'.sync'/reg['stage_name']).resolve()
    payload=dict(reg['inherited_payload_sha256'],**reg['new_payload_sha256'])
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert {n:sha(stage/n) for n in payload}==payload
    budget_before=sha(project/'reports/budget.json')
    receipt={'status':'P_REFERENCE_COMPLETE10_CPU_RUNNING','source_revision':args.revision,
        'pid':os.getpid(),'payload_files':len(payload),'registered_paths':10,
        'budget_before_sha256':budget_before,'GPU_submissions':0,'ledger_written':False,
        'started_unix':time.time()}
    def save():
        tmp=stage/'receipt.tmp';tmp.write_text(json.dumps(receipt,indent=2)+'\n');tmp.replace(stage/'receipt.json')
    save();started=time.monotonic()
    py='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=[py,str(stage/'scripts/check_wc_p_working_reference_sampling_cpu_r2.py'),
        '--stage',str(stage),'--runtime',str(project/'runtime'),'--output',str(stage/'result.json')]
    with (stage/'CPU.log').open('x') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
                     HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
        receipt['child_pid']=child.pid;receipt['original_command']=command;save()
        exit_code=child.wait()
    after={n:sha(stage/n) for n in payload}
    assert after==payload
    receipt.update(exit_code=exit_code,CPU_wall_seconds=time.monotonic()-started,
        payload_after_sha256=after,budget_after_sha256=sha(project/'reports/budget.json'),
        status='P_REFERENCE_COMPLETE10_CPU_PASS_PENDING_INDEPENDENT_CAPTURE' if exit_code==0
            else 'P_REFERENCE_COMPLETE10_CPU_FAILED_SCOPE_RETAINED',finished_unix=time.time())
    if exit_code==0:receipt['result_sha256']=sha(stage/'result.json')
    save()


if __name__=='__main__':main()
