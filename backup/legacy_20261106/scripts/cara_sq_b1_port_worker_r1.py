"""One bounded direct CPU B1 port; passwords stay in stdin and memory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);args=p.parse_args()
    stage=args.stage;sys.path[:0]=[str(stage/'src')]
    from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
    from wcomr.sq_b1_port_r1 import ASSETS,MANIFEST_SHA,PROJECT,TOTAL_BYTES,copy_assets,readonly_source,require
    reg=json.loads((stage/'registration.json').read_text());profile=json.loads((stage/reg['profile_path']).read_text())
    require(all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==v for n,v in reg['payload_sha256'].items()),
            'Frozen B1 CPU transfer source differs')
    require(profile['files']==32 and profile['asset_bytes']==TOTAL_BYTES and profile['source_manifest_sha256']==MANIFEST_SHA,
            'Exact old B1 CPU transfer scope required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void',
            'CPU transfer cannot expose GPU devices')
    os.sched_setaffinity(0,set(profile['source_and_destination_CPU_affinity']));os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30))
    resource.setrlimit(resource.RLIMIT_FSIZE,(2*2**30,2*2**30))
    secret=json.load(sys.stdin);password=secret.pop('source_password');secret.clear()
    started,cpu=time.monotonic(),time.process_time()
    status=dict(status='B1_CPU_PORT_CONNECTING',identity=process_identity(os.getpid()),GPU_submissions=0,ledger_writes=0)
    atomic_json(stage/'worker.json',status)
    try:
        remaining=int(reg.get('original_deadline_unix',time.time()+7200)-time.time())
        require(0<remaining<=7200,'Original CPU transfer time envelope exhausted')
        with readonly_source(reg['endpoint'],reg['host_key_pins'],password,wall_seconds=remaining) as (sftp,source):
            password=None;status['source_server']=source;atomic_json(stage/'worker.json',status)
            result=copy_assets(sftp,PROJECT+'/'+ASSETS,Path(PROJECT)/ASSETS,
                minimum_free_bytes=profile['minimum_destination_free_bytes'],
                readv_requests=profile.get('readv_requests',0),
                incoming_name=profile.get('incoming_name','.sq-b1-port-cpu-r1-20261029'),
                save=lambda value:atomic_json(stage/'progress.json',value))
        result.update(source_server=source,CPU_wall_seconds=time.monotonic()-started,
            destination_CPU_seconds=time.process_time()-cpu,source_SSH_daemon_CPU_seconds=None,
            peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            no_GPU_or_model_import='torch' not in sys.modules)
        atomic_json(stage/'result.json',result)
        status.update(status='B1_CPU_PORT_TERMINAL',exit_code=0,result_sha256=hashlib.sha256((stage/'result.json').read_bytes()).hexdigest())
    except BaseException as error:
        status.update(status='B1_CPU_PORT_FAILED',exit_code=1,error_type=type(error).__name__,error=str(error))
        raise
    finally:
        password=None;status.update(ended_unix=time.time(),wall_seconds=time.monotonic()-started,
            destination_CPU_seconds=time.process_time()-cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(stage/'exit.json',status)


if __name__=='__main__':main()
