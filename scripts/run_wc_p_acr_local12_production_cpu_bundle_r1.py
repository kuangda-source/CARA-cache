"""One independent full H1 diagnostic CPU bundle; never submit/charge a GPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    for name in ('stage','project','runtime'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();reg=json.loads((a.stage/'registration.json').read_text())
    before=sha(a.project/'reports/budget.json');start=time.time()
    result={'status':'CPU_BUNDLE_RUNNING','pid':os.getpid(),'started_unix':start,'source_revision':reg['source_revision'],
        'budget_before_sha256':before,'GPU_submissions':0,'real_models_loaded':0,'jobs':[]}
    output=a.stage/'CPU-bundle-result.json';assert not output.exists()
    def save():output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    save()
    try:
        assert all(sha(a.stage/name)==h for name,h in reg['payload_sha256'].items())
        assert all(sha(a.runtime/name)==h for name,h in reg['runtime_source_sha256'].items())
        env={**os.environ,'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','OMP_NUM_THREADS':'2'}
        jobs=[('PRODUCTION','run_wc_p_acr_local12_profile528_r1.py','production-CPU-result.json')]
        for name,script,filename in jobs:
            command=[sys.executable,str(a.stage/'scripts'/script),'--stage',str(a.stage),'--project',str(a.project),'--cpu-check']
            started=time.time()
            with (a.stage/(name+'.log')).open('x') as log:
                p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env)
            row={'name':name,'exit_code':p.returncode,'wall_seconds':time.time()-started,'command':command}
            if (a.stage/filename).exists():row.update(result_sha256=sha(a.stage/filename),result=json.loads((a.stage/filename).read_text()))
            result['jobs'].append(row);save()
        result.update(status='PA_LOCAL12_PRODUCTION_ENTRY_CPU_ACCEPTED_NOT_GPU_LAUNCH_READY' if all(r['exit_code']==0 for r in result['jobs']) else 'PA_LOCAL12_PRODUCTION_ENTRY_CPU_FAILED_FULL_SCOPE_RETAINED',
            ended_unix=time.time(),wall_seconds=time.time()-start,budget_after_sha256=sha(a.project/'reports/budget.json'))
        if result['budget_after_sha256']!=before:raise ValueError('CPU bundle ledger changed')
        save()
    except BaseException as e:
        result.update(status='CPU_BUNDLE_TECHNICAL_FAILURE',error_type=type(e).__name__,error=str(e),ended_unix=time.time(),budget_after_sha256=sha(a.project/'reports/budget.json'));save();raise
    if result['status']!='PA_LOCAL12_PRODUCTION_ENTRY_CPU_ACCEPTED_NOT_GPU_LAUNCH_READY':raise SystemExit(1)


if __name__=='__main__':main()
