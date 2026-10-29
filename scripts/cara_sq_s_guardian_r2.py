"""S wrapper around the original shared host allocation clock and journal."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def available_memory_bytes():
    return int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
        if line.startswith('MemAvailable:')))*1024


def container_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid):
    from cara_fast_host_guardian_r2 import container_arguments as base_arguments
    command=base_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid,memory_GiB=40)
    command[command.index(str(stage/'scripts/cara_fast_worker_r2.py'))]=str(stage/'scripts/cara_sq_s_worker_r2.py')
    index=command.index('--entrypoint')
    command[index:index]=['--ulimit','fsize=2147483648:2147483648']
    return command


def pending_release(stage,storage):
    from wcomr.sq_s_execution_r2 import read
    from wcomr.gpu_budget_pool_v2 import atomic_json,sha
    allocation=storage.output/'S-allocation-release.json'
    if not allocation.exists():return
    release=dict(read(allocation),allocation_release_sha256=sha(allocation),
        GPU_released=False,original_process_exited=False,technical_accepted=False,
        collection_classification=None,collection_sha256=None,final_snapshot=None,
        supervisor_release_sha256=None,supervisor_billing_sha256=None)
    release['GPU_released']=release['original_process_exited']=release['allocation_release_accepted']
    diagnostic=storage.output/'S-supervisor-release-diagnostic.json'
    if diagnostic.exists():
        release['supervisor_release_sha256']=sha(diagnostic)
        try:
            inner=read(diagnostic)
            keys=('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')
            if all(inner[key]==release[key] for key in keys) and inner['diagnostic_only'] is True:
                for key in ('technical_accepted','collection_classification','collection_sha256','final_snapshot'):
                    release[key]=inner.get(key)
                release['technical_accepted']=bool(release['allocation_release_accepted']
                    and release['technical_accepted'] and inner['GPU_released'] and inner['original_process_exited'])
        except (ValueError,KeyError,TypeError):
            release.update(technical_accepted=False,supervisor_diagnostic_invalid=True)
    bill=storage.output/'S-supervisor-billing-diagnostic.json'
    if bill.exists():release['supervisor_billing_sha256']=sha(bill)
    storage.persist('pending_release',storage.output/'S-release-pending-central.json',release,atomic_json)


def run(args,password,*,ops=None,clock=time):
    from wcomr.sq_s_execution_r2 import validate,require
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_control_storage_r1 import storage_for
    from wcomr.sq_gpu_allocation_r1 import run_allocation
    bundle,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage);profile=bundle['execution_profile']
    require(not (args.stage/'pg-host-guardian.json').exists()
        and not (storage.output/'S-release-pending-central.json').exists(),'Original S allocation exists; recover only')
    cpuset=profile['hosts'][authority['host']]['cpuset_cpus']
    def command():
        # Recheck mutable resources before the container, inside the original
        # admission-through-release clock. Refusal is a retained failed bill.
        require(set(map(int,cpuset.split(',')))<=os.sched_getaffinity(0),'Registered S CPU set unavailable')
        require(available_memory_bytes()>=profile['minimum_host_MemAvailable_GiB']*2**30,
            'S host RAM is below its registered margin')
        storage.check()
        return container_arguments(args.project,args.stage,storage,sha(args.stage/'registration.json'),
            cpuset,os.getuid(),os.getgid(),authority['gpu_uuid'])
    try:
        return run_allocation(args.project,args.stage,authority,registration,storage,profile,'S',
            command,password,ops=ops,clock=clock)
    finally:pending_release(args.stage,storage)


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.sq_s_stage_r2 import publish_launch
    publish_launch(args.project,args.stage)
    try:
        incoming=json.load(sys.stdin)
        password=incoming.get('sudo_password') if isinstance(incoming,dict) and set(incoming)=={'sudo_password'} else None
        if not isinstance(password,str) or not password:password=None
    except (ValueError,KeyError,TypeError):password=None
    run(args,password)


if __name__=='__main__':main()
