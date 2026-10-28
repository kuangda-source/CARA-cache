"""Q1's sole allocation clock, from host admission through original release."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def container_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid):
    from cara_fast_host_guardian_r2 import container_arguments as base_arguments
    command=base_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid,memory_GiB=16)
    old=str(stage/'scripts/cara_fast_worker_r2.py')
    command[command.index(old)]=str(stage/'scripts/cara_sq_q1_worker_r1.py')
    at=command.index('--entrypoint')
    command[at:at]=['--ulimit','fsize=67108864:67108864']
    return command


def pending_release(stage,storage):
    """Join original host release with optional supervisor diagnostics, never bill twice."""
    from wcomr.sq_q1_execution_r1 import read
    from wcomr.gpu_budget_pool_v2 import atomic_json,sha
    allocation=storage.output/'Q1-allocation-release.json'
    if not allocation.exists():return
    release=dict(read(allocation),allocation_release_sha256=sha(allocation),
        GPU_released=False,original_process_exited=False,technical_accepted=False,
        collection_classification=None,collection_sha256=None,final_snapshot=None,
        supervisor_release_sha256=None,supervisor_billing_sha256=None)
    release['GPU_released']=release['original_process_exited']=release['allocation_release_accepted']
    diagnostic=storage.output/'Q1-supervisor-release-diagnostic.json'
    bill=storage.output/'Q1-supervisor-billing-diagnostic.json'
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
            release['technical_accepted']=False
            release['supervisor_diagnostic_invalid']=True
    if bill.exists():release['supervisor_billing_sha256']=sha(bill)
    storage.persist('pending_release',storage.output/'Q1-release-pending-central.json',release,atomic_json)


def run(args,password,*,ops=None,clock=time):
    from wcomr.sq_q1_execution_r1 import validate,read,require
    from wcomr.sq_q1_spec_r1 import PROFILE
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_control_storage_r1 import storage_for
    from wcomr.sq_gpu_allocation_r1 import run_allocation
    _,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage);profile=read(args.stage/PROFILE)
    require(not (args.stage/'pg-host-guardian.json').exists()
            and not (storage.output/'Q1-release-pending-central.json').exists(),
            'Original Q1 allocation exists; recover only')
    cpuset=profile['hosts'][authority['host']]['cpuset_cpus']
    require(set(map(int,cpuset.split(',')))<=os.sched_getaffinity(0),'Registered Q1 CPU set unavailable')
    command=lambda:container_arguments(args.project,args.stage,storage,sha(args.stage/'registration.json'),
        cpuset,os.getuid(),os.getgid(),authority['gpu_uuid'])
    try:
        return run_allocation(args.project,args.stage,authority,registration,storage,profile,'Q1',
            command,password,ops=ops,clock=clock)
    finally:
        pending_release(args.stage,storage)


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.sq_q1_stage_r1 import publish_launch
    # The child records its own identity before credentials can be lost.
    publish_launch(args.project,args.stage)
    try:
        incoming=json.load(sys.stdin)
        password=incoming.get('sudo_password') if isinstance(incoming,dict) and set(incoming)=={'sudo_password'} else None
        if not isinstance(password,str) or not password:password=None
    except (ValueError,KeyError,TypeError):password=None
    run(args,password)


if __name__=='__main__':main()
