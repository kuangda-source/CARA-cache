"""Host-side original dispatch/recovery; accepts no CPU bypass or new authority."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['launch','status'])
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--central-snapshot',type=Path)
    args=parser.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_s_endpoint_gpu_dispatch_r1 import dispatch,recover,CLI
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.gpu_budget_pool_v2 import sha
    if read_record(args.stage/'registration.json')['payload_sha256'][CLI]!=sha(__file__):
        raise ValueError('Original dispatch entry source differs')
    result=recover(args.stage)
    if result is None and args.action=='launch':
        if args.central_snapshot is None:raise ValueError('Fresh central snapshot required')
        incoming=json.load(sys.stdin)
        if set(incoming)!={'sudo_password'}:raise ValueError('Only the private credential is accepted on stdin')
        result=dispatch(args.project,args.stage,read_record(args.central_snapshot),incoming['sudo_password'])
    print(json.dumps(result or dict(status='NO_ORIGINAL_DISPATCH_RECORD',GPU_submissions=0),allow_nan=False))


if __name__=='__main__':main()
