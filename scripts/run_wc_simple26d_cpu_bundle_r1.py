#!/usr/bin/env python3
"""Complete CPU suite in a fresh immutable stage; never load model weights."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();start=time.time();reg=json.loads((a.stage/'registration.json').read_text())
    assert all(hashlib.sha256((a.stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items())
    dest=a.stage/'CPU-bundle-result.json';assert not dest.exists()
    commands=[
        [sys.executable,str(a.stage/'scripts/check_wc_simple26d_cpu_r1.py'),'--stage',str(a.stage),'--runtime',str(a.project/'runtime'),'--output',str(a.stage/'simple26d-sampling-CPU-result.json')],
        [sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p','test_gpu_budget_pool_v2.py','-v'],
        [sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p','test_simple26d_contract_r1.py','-v'],
        [sys.executable,str(a.stage/'scripts/run_wc_simple26d_full36_r1.py'),'--project',str(a.project),'--stage',str(a.stage),'--cpu-check']]
    state=dict(status='SIMPLE26D_COMPLETE_CPU_RUNNING',source_revision=reg['source_revision'],commands=[],GPU_submissions=0,
        shared_runtime_written=False,old_W3_stage_written=False,ledger_written=False,started_unix=start)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=str(a.stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code=subprocess.call(command,cwd=a.project/'runtime',env=env)
            state['commands'].append(dict(command=command,exit_code=code))
            if code:raise RuntimeError('CPU suite exited '+str(code))
        state.update(status='SIMPLE26D_COMPLETE_CPU_ACCEPTED_NOT_GPU',exit_code=0)
    except BaseException as e:
        state.update(status='SIMPLE26D_COMPLETE_CPU_FAILED_NOT_GPU',exit_code=1,error_type=type(e).__name__,error=str(e));raise
    finally:
        state['wall_seconds']=time.time()-start
        dest.write_text(json.dumps(state,indent=2)+'\n')

if __name__=='__main__':main()
