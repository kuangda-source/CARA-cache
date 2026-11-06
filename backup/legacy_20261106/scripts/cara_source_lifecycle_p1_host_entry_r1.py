"""The original P1 guardian starts the sole FIT service inside its own bill."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_source_lifecycle_p1_dispatch_r1 import publish_launch,GUARDIAN,ENVIRONMENT
    from wcomr.cara_source_lifecycle_p1_service_r1 import HeldFITService
    from wcomr.cara_s_endpoint_host_guardian_r1 import allocate
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.gpu_budget_pool_v2 import sha
    if read_record(args.stage/'registration.json')['payload_sha256'][GUARDIAN]!=sha(__file__):
        raise ValueError('Original P1 guardian entry source differs')
    incoming=json.load(sys.stdin)
    if set(incoming)!={'sudo_password'} or not isinstance(incoming['sudo_password'],str) or not incoming['sudo_password']:
        raise ValueError('Only the original private credential may enter the P1 guardian')
    password=incoming.pop('sudo_password')
    try:
        _,storage=publish_launch(args.project,args.stage)
        service=HeldFITService(args.project,args.stage,read_record(args.stage/ENVIRONMENT))
        allocate(args.project,args.stage,storage,password,fit_service=service)
    finally:password=None


if __name__=='__main__':main()
