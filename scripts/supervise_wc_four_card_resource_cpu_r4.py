#!/usr/bin/env python3
"""Bounded supervisor for one owned, GPU-hidden resource container."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    job=a.manifest.parent;m=json.loads(a.manifest.read_text());root=Path(m['workspace']);digest=sha(a.manifest)
    lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(__file__)==m['supervisor_sha256']
    env=root/'envs/wc-cosmos-py310-cu128-r3'
    variables=dict(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1',
        HOME='/tmp',TMPDIR='/tmp',HF_HOME=str(root/'cache/huggingface'),HF_HUB_CACHE=str(root/'cache/huggingface/hub'),
        TORCH_HOME=str(root/'cache/torch'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',
        LD_LIBRARY_PATH=str(root/'system-libs-r1/usr/lib/x86_64-linux-gnu')+':'+str(root/'system-libs-r1/lib/x86_64-linux-gnu'),
        PATH=str(root/'system-libs-r1/usr/bin')+':/usr/local/bin:/usr/bin:/bin')
    if m.get('resume_completed_resolver'):
        site=env/'lib/python3.10/site-packages'
        variables.update(CUDA_HOME=str(site/'nvidia/cuda_nvrtc'),CUDA_PATH=str(site/'nvidia/cuda_nvrtc'))
        libraries=[site/'nvidia'/name/'lib' for name in ['cuda_nvrtc','cuda_runtime','cudnn','nvjitlink','cublas']]+[site/'torch/lib']
        variables['LD_LIBRARY_PATH']+=':'+':'.join(map(str,libraries))
        variables['PATH']+=':/usr/sbin:/sbin'
    args=['docker','run','--rm','--read-only','--network','none' if m.get('offline_only') else 'host','--name',m['run_id'],'--label','wcomr.manifest='+digest,
        '--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--memory','16g','--pids-limit','256',
        '--tmpfs','/tmp:rw,size=1g','-v',str(root)+':'+str(root)+':ro','-v',str(job)+':'+str(job)+':rw',
        '-v',str(root/'cache/torch')+':'+str(root/'cache/torch')+(':'+('ro' if m.get('torch_cache_readonly') else 'rw')),'-w',str(job)]
    for k,v in variables.items():args+=['-e',k+'='+v]
    args+=['--entrypoint',str(env/'bin/python'),m['container_image_id'],str(job/'worker.py'),'--manifest',str(a.manifest)]
    with (job/'container-command.json').open('x') as command:
        json.dump(args,command,indent=2);command.write('\n')
    begin=time.time();result=dict(started_unix=begin,manifest_sha256=digest,container=m['run_id'],GPU_submissions=0,ledger_written=False)
    with (job/'container.log').open('xb') as log:
        try:
            proc=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            result['docker_client_pid']=proc.pid
            try:result['exit_code']=proc.wait(timeout=m['maximum_wall_seconds'])
            except subprocess.TimeoutExpired:
                result['exit_code']=124
                owned=subprocess.run(['docker','inspect',m['run_id'],'--format','{{index .Config.Labels "wcomr.manifest"}}'],capture_output=True,text=True,timeout=15)
                if owned.returncode==0 and owned.stdout.strip()==digest:
                    subprocess.run(['docker','stop','--time','20',m['run_id']],stdout=log,stderr=subprocess.STDOUT,timeout=45)
                try:proc.wait(timeout=30)
                except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=15)
        except BaseException as error:
            result.update(exit_code=result.get('exit_code',125),error_type=type(error).__name__)
        finally:
            result.update(ended_unix=time.time(),wall_seconds=time.time()-begin)
            temporary=job/'supervisor-result.json.tmp';temporary.write_text(json.dumps(result,indent=2)+'\n');temporary.replace(job/'supervisor-result.json')


if __name__=='__main__':main()
