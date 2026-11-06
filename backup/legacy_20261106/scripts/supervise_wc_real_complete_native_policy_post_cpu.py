#!/usr/bin/env python3
"""Wait for the original supervised GPU handle, then audit every raw pair on CPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','post'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--supervisor-pid',type=int,required=True);args=p.parse_args()
    c=json.loads((args.stage/'native-policy-config.json').read_text());out=args.project/'outputs'/c['execution_run_id']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    receipt=args.post/'receipt.json';assert not receipt.exists()
    r={'status':'WAITING_ORIGINAL_PAIRED_GPU_NOT_NEW_SUBMISSION','pid':os.getpid(),'supervisor_pid':args.supervisor_pid,
        'source_revision':args.source_revision,'run_id':c['execution_run_id'],'config_sha256':sha(args.stage/'native-policy-config.json'),
        'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.perf_counter()
    try:
        while Path('/proc/'+str(args.supervisor_pid)).exists():time.sleep(3)
        supervisor=json.loads((out/'supervisor.json').read_text())
        assert supervisor['pid']==args.supervisor_pid and supervisor['source_revision']==args.source_revision
        assert supervisor['status']=='EXITED_REQUIRES_RESULT_AUDIT' and supervisor['exit_code']==0
        assert not Path('/proc/'+str(supervisor['child_pid'])).exists() and not supervisor['release']['pids']
        r.update(status='PAIRED_RAW_CPU_AUDIT_RUNNING_NOT_GPU',GPU_exit_code=supervisor['exit_code'],
                 original_GPU_PIDs_absent=[supervisor['pid'],supervisor['child_pid']],budget_before_sha256=sha(args.project/'reports/budget.json'));save()
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2')
        python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        with (args.post/'CPU-audit.log').open('x') as log:
            child=subprocess.Popen([python,str(args.stage/'scripts/audit_wc_real_complete_native_policy_cpu.py'),
                '--project',str(args.project),'--stage',str(args.stage),'--output',str(args.post/'result.json')],stdout=log,stderr=subprocess.STDOUT,env=env)
            r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()
        assert r['child_exit_code']==0
        result=json.loads((args.post/'result.json').read_text())
        assert result['status']=='REAL_COMPLETE_NATIVE_POLICY_RAW_CPU_AUDIT_NOT_NEW_POLICY_OR_QUALITY'
        assert result['actual_tensor_audit']['actual_guided_tensors_reloaded']==576 and result['actual_tensor_audit']['actual_final_latents_reloaded']==16
        assert result['all_16_full93_videos_and_actual_raw_tensors_verified'] and not result['CUDA_initialized']
        r.update(status='REAL_COMPLETE_NATIVE_POLICY_COMPLETE_CPU_AUDIT_NOT_NEW_POLICY',exit_code=0,result_sha256=sha(args.post/'result.json'))
    except BaseException as error:
        r.update(status='REAL_COMPLETE_NATIVE_POLICY_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(total_driver_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(args.project/'reports/budget.json'),
            payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']})
        save()
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
