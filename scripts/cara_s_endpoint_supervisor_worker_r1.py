"""Container supervisor entry for an already admitted original endpoint."""
import argparse
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from cara_s_endpoint_container_r1 import container_arguments,PROFILE,WORKER
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.cara_s_endpoint_supervisor_r1 import supervise
    from wcomr.cara_budget_original_handles_r1 import observe_original_process
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.policy_price_terminal_r1 import require
    launch=read_record(args.stage/'GPU-launch.json');registration=read_record(args.stage/'registration.json')
    authority=read_record(args.stage/'GPU-authorization.json');profile=read_record(args.stage/PROFILE)
    require(launch['CPU_fixture_only'] is False and authority['CPU_fixture_only'] is False
            and authority['execution_authorized'] is True and authority['authorizes_replay'] is False
            and launch['authorization_sha256']==sha(args.stage/'GPU-authorization.json')
            and launch['registration_sha256']==sha(args.stage/'registration.json')
            and launch['billed_limit_GPUh']==profile['hard_GPUh']
            and registration['payload_sha256'][WORKER]==sha(__file__)
            and registration['payload_sha256'][PROFILE]==sha(args.stage/PROFILE)
            and registration['payload_sha256']['scripts/cara_s_endpoint_container_r1.py']==sha(args.stage/'scripts/cara_s_endpoint_container_r1.py'),
            'Original approved production worker/profile/source binding required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')==''
            and os.environ.get('NVIDIA_VISIBLE_DEVICES')==launch['gpu_uuid'],
            'Only the original runner may expose CUDA')
    require(observe_original_process(launch['guardian_identity'])['original_live'] is True,
            'Original host guardian must still be live before starting its worker')
    storage=storage_for(args.stage);storage.check()
    expected=container_arguments(project=args.project,stage=args.stage,storage=storage,
        registration_sha=launch['registration_sha256'],profile=profile,host=launch['host'],
        run_id=launch['run_id'],uuid=launch['gpu_uuid'],uid=os.getuid(),gid=os.getgid())
    require(launch['commands']['container_cli']==expected,'Original frozen container command differs')
    supervise(args.project,args.stage,storage)


if __name__=='__main__':main()
