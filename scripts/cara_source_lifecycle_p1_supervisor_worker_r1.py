"""Original P1 supervisor only; the admitted host guardian starts the FIT service."""
import argparse
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from cara_source_lifecycle_p1_container_r1 import container_arguments,SOURCE,WORKER
    from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import validate_inputs,PROFILE,IDENTITY
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.cara_budget_original_handles_r1 import observe_original_process
    from wcomr.cara_s_endpoint_supervisor_r1 import supervise
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.gpu_budget_pool_v2 import sha
    card,registration,authority,profile,quote=validate_inputs(args.project,args.stage)
    launch=read_record(args.stage/'GPU-launch.json')
    if (launch['CPU_fixture_only'] is not False or any(launch[k]!=authority[k] for k in IDENTITY)
            or launch['authorization_sha256']!=sha(args.stage/'GPU-authorization.json')
            or launch['registration_sha256']!=sha(args.stage/'registration.json')
            or registration['payload_sha256'][WORKER]!=sha(__file__)
            or registration['payload_sha256'][SOURCE]!=sha(args.stage/SOURCE)
            or registration['payload_sha256'][PROFILE]!=sha(args.stage/PROFILE)
            or os.environ.get('CUDA_VISIBLE_DEVICES')!=''
            or os.environ.get('NVIDIA_VISIBLE_DEVICES')!=launch['gpu_uuid']):
        raise ValueError('Original P1 source-bound GPU-hidden supervisor required')
    if observe_original_process(launch['guardian_identity'])['original_live'] is not True:
        raise ValueError('Original host guardian must remain live; UNKNOWN is recovery only')
    storage=storage_for(args.stage);storage.check()
    expected=container_arguments(project=args.project,stage=args.stage,storage=storage,
        registration_sha=launch['registration_sha256'],profile=profile,host=launch['host'],
        run_id=launch['run_id'],uuid=launch['gpu_uuid'],uid=os.getuid(),gid=os.getgid())
    if launch['commands']['container_cli']!=expected:
        raise ValueError('Original P1 frozen container command changed')
    # This unchanged accepted supervisor owns the device lease/sole runner and
    # thermal/hard-stop policy. It does not create another FIT service or bill.
    supervise(args.project,args.stage,storage)


if __name__=='__main__':main()
