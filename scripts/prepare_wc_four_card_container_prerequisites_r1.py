#!/usr/bin/env python3
"""Prepare the isolated CPU container and Torch while source transfer proceeds."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--job',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--environment-name',default='wc-cosmos-py310-cu128-r2')
    args=parser.parse_args();job=args.job;workspace=args.workspace.resolve()
    assert str(workspace).startswith('/data20t/gaokuangda/') and job.is_dir()
    assert '/' not in args.environment_name and args.environment_name.startswith('wc-cosmos-')
    assert not (job/'result.json').exists()
    value=dict(status='CONTAINER_AND_TORCH_CPU_PREPARATION_RUNNING',commands=[],started_unix=time.time(),
               worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               GPU_submissions=0,model_weights_loaded=0,ledger_written=False,
               production_CPU_accepted=False,GPU_dispatch_ready=False)
    def save(name='health.json'):
        temporary=job/(name+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');os.replace(temporary,job/name)
    def run(phase,argv,timeout):
        free=os.statvfs(str(workspace));assert free.f_bavail*free.f_frsize>=128*1024**3
        value['phase']=phase;save();began=time.time()
        with (job/(phase+'.log')).open('xb') as log:
            p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,
                             env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
        value['commands'].append(dict(phase=phase,exit_code=p.returncode,wall_seconds=time.time()-began));save()
        if p.returncode:raise RuntimeError('Original prerequisite phase failed: '+phase)
    try:
        root=os.statvfs('/');assert root.f_bavail*root.f_frsize>=4*1024**3
        tag='python:3.10.19-slim-bookworm'
        cached=subprocess.run(['docker','image','inspect',tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
        if not cached:run('base-image-pull',['docker','pull',tag],900)
        image=subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()
        value['resolved_image_id']=image;save()
        for name in ['user-home','envs','cache/pip','tmp']:(workspace/name).mkdir(parents=True,exist_ok=True)
        env=workspace/'envs'/args.environment_name;assert not env.exists();py=str(env/'bin/python')
        value['base_environment_path']=str(env);save()
        check=('import torch,sys; assert sys.version_info[:2]==(3,10); '
               'assert torch.__version__=="2.7.1+cu128"; assert not torch.cuda.is_initialized(); '
               'print(sys.version,torch.__version__,torch.version.cuda,"CPU_ONLY_NO_CUDA_INIT")')
        code=('import subprocess; subprocess.run('+repr(['python','-m','venv',str(env)])+',check=True); '
              'subprocess.run('+repr([py,'-m','pip','install','--disable-pip-version-check','pip==25.2',
                                      '--index-url','https://pypi.org/simple'])+',check=True); '
              'subprocess.run('+repr([py,'-m','pip','install','--disable-pip-version-check','--only-binary=:all:',
                                      'torch==2.7.1+cu128','torchvision==0.22.1+cu128',
                                      '--index-url','https://download.pytorch.org/whl/cu128',
                                      '--extra-index-url','https://pypi.org/simple'])+',check=True); '
              'subprocess.run('+repr([py,'-c',check])+',check=True)')
        cmd=['docker','run','--rm','--read-only','--name',job.name,
             '--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--memory','16g',
             '--tmpfs','/tmp:rw,size=512m','-v',str(workspace)+':'+str(workspace),'-w',str(workspace)]
        for k,v in dict(NVIDIA_VISIBLE_DEVICES='void',CUDA_VISIBLE_DEVICES='',HOME=str(workspace/'user-home'),
                        TMPDIR=str(workspace/'tmp'),PIP_CACHE_DIR=str(workspace/'cache/pip'),
                        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1').items():
            cmd+=['-e',k+'='+v]
        cmd+=['--entrypoint','/usr/local/bin/python',image,'-c',code]
        run('python-and-pinned-torch',cmd,3600)
        value.update(status='CONTAINER_AND_TORCH_CPU_PREREQUISITES_READY_NOT_PRODUCTION',
                     base_environment_path=str(env),GPU_driver_compatibility_verified=False)
    except BaseException as exc:value.update(status='CONTAINER_OR_TORCH_CPU_PREREQUISITES_FAILED_RETAINED',error_type=type(exc).__name__,error=str(exc))
    finally:
        value.update(ended_unix=time.time(),wall_seconds=time.time()-value['started_unix']);save();save('result.json');print(json.dumps(value))


if __name__=='__main__':main()
