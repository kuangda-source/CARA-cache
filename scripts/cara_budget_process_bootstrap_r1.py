"""Bind an original host-view child before executing its frozen command."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--role',choices=['runner','container_cli'],required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.cara_budget_search_journal_r1 import create_record,read_record
    from wcomr.gpu_budget_pool_v2 import sha
    launch=read_record(args.stage/'GPU-launch.json');registration=read_record(args.stage/'registration.json')
    if (launch['stage']!=str(args.stage) or sha(args.stage/'registration.json')!=launch['registration_sha256']
            or sha(__file__)!=registration['payload_sha256']['scripts/cara_budget_process_bootstrap_r1.py']):
        raise ValueError('Original bootstrap/source registration required')
    command=launch['commands'][args.role]
    if not isinstance(command,list) or not command or any(not isinstance(arg,str) for arg in command):
        raise ValueError('Frozen argv required')
    identity=bind_original_process(os.getpid())
    create_record(args.stage/(args.role+'-start.json'),dict(identity=identity,launch_id=launch['launch_id'],
        source_revision=launch['source_revision'],started_unix=time.time()))
    grant=args.stage/(args.role+'-dispatch-grant.json');deadline=time.monotonic()+30
    while not grant.exists():
        if time.monotonic()>=deadline:raise TimeoutError('Original child was not granted execution')
        time.sleep(.02)
    accepted=read_record(grant)
    if accepted!={'identity':identity,'launch_sha256':sha(args.stage/'GPU-launch.json')}:
        raise ValueError('Original child identity grant differs')
    environment=dict(os.environ,CUDA_VISIBLE_DEVICES='' if launch['CPU_fixture_only'] or args.role=='container_cli' else launch['gpu_uuid'])
    if launch['CPU_fixture_only']:environment['NVIDIA_VISIBLE_DEVICES']='void'
    os.execvpe(command[0],command,environment)


if __name__=='__main__':main()
