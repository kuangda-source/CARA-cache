#!/usr/bin/env python3
"""Unique CPU-only child; keeps original failed card and all accounting intact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-revision',required=True);a=p.parse_args()
    target=a.stage/'receipt.json'
    if target.exists():raise ValueError('No duplicate CPU task identity')
    reg=json.loads((a.stage/'preregistration.json').read_text())
    if any(Path('/proc/'+str(pid)).exists() for pid in reg['original_PIDs']):
        raise ValueError('Original failed-card handles must be terminal before per-path CPU')
    before=sha(a.project/'reports/budget.json');started=time.perf_counter()
    record={'status':'E0_PARTIAL_RECOVERY_CPU_RUNNING','pid':os.getpid(),'source_revision':a.source_revision,
        'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,
        'registration_sha256':sha(a.stage/'preregistration.json'),'budget_before_sha256':before}
    def save():
        tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(target)
    save()
    try:
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
            str(a.stage/'scripts/run_wc_full64_partial_recovery_cpu.py'),'--project',str(a.project),
            '--stage',str(a.stage),'--source-revision',a.source_revision]
        with (a.stage/'CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                    PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
            record.update(child_pid=child.pid,command=command);save();record['child_exit_code']=child.wait()
        if record['child_exit_code']!=0:raise RuntimeError('Per-path CPU child failed; retain original64 and partial receipts')
        result=json.loads((a.stage/'result.json').read_text())
        if (result['status']!='E0_PARTIAL_PATH_RECOVERY_CPU_COMPLETE_ORIGINAL_FULL64_STILL_FAILED_TECH'
            or len(result['all64_slots'])!=64 or result['CUDA_initialized'] or result['GPU_submissions']
            or result['budget_before_sha256']!=result['budget_after_sha256'] or result['budget_after_sha256']!=before):
            raise ValueError('E0 full64 denominator or CPU source/budget contract differs')
        record.update(status='E0_PARTIAL_RECOVERY_CPU_EXIT0_NOT_FULL64_ACCEPTANCE',exit_code=0,
            result_sha256=sha(a.stage/'result.json'))
    except BaseException as error:
        record.update(status='E0_CPU_FAILED_ORIGINAL_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        record.update(CPU_wall_seconds=time.perf_counter()-started,ended_unix=time.time(),budget_after_sha256=sha(a.project/'reports/budget.json'),
            payload_after_sha256={n:sha(a.stage/n) for n in reg['payload_sha256']});save()
    raise SystemExit(record['exit_code'])


if __name__=='__main__':main()
