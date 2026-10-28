"""One bounded native CPU SHA scan, never imports torch or touches GPU mode."""
import argparse
import os
from pathlib import Path
import resource
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.sq_q1_execution_r1 import read,require
    from wcomr.sq_q1_spec_r1 import PROFILE
    from wcomr.sq_q1_stage_r1 import verify_assets
    from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void',
        'GPU-free CPU asset scan required')
    registration=read(args.stage/'registration.json');profile=read(args.stage/PROFILE)
    cpus=set(map(int,profile['hosts'][registration['host']]['cpuset_cpus'].split(',')))
    require(cpus<=os.sched_getaffinity(0),'Registered CPU affinity unavailable')
    os.sched_setaffinity(0,cpus);os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*2**20,64*2**20))
    started,cpu=time.monotonic(),time.process_time()
    state=dict(status='Q1_ASSET_CPU_RUNNING',identity=process_identity(os.getpid()),GPU_submissions=0)
    atomic_json(args.stage/'asset-CPU-worker.json',state)
    try:
        result=verify_assets(args.project,args.stage)
        state.update(status='Q1_ASSET_CPU_TERMINAL',exit_code=0,verification_status=result['status'])
    except BaseException as error:
        state.update(status='Q1_ASSET_CPU_FAILED',exit_code=1,error_type=type(error).__name__,error=str(error));raise
    finally:
        state.update(wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
            peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,ended_unix=time.time())
        atomic_json(args.stage/'asset-CPU-exit.json',state)


if __name__=='__main__':main()
