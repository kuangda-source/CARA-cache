"""Run only through the registered four-card central operator stage."""
import argparse
import json
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['snapshot','reserve','settle'])
    for key in ('project','operator-stage'):parser.add_argument('--'+key,type=Path,required=True)
    for key in ('admission','observations','capture'):parser.add_argument('--'+key,type=Path)
    parser.add_argument('--expected-launch-sha256')
    args=parser.parse_args();sys.path[:0]=[str(args.operator_stage/'src'),str(args.operator_stage/'scripts')]
    from wcomr.cara_budget_central_r1 import reserve,settle,Pool,SOURCE
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.gpu_budget_pool_v2 import sha
    reg=read_record(args.operator_stage/'registration.json')
    if (reg['host']!='four_card' or reg['payload_sha256']['scripts/cara_budget_central_r1.py']!=sha(__file__)
            or reg['payload_sha256'][SOURCE]!=sha(args.operator_stage/SOURCE)):
        raise ValueError('Original four-card central operator source required')
    if args.action=='snapshot':
        result=dict(central_ledger_host='four_card',ledger=Pool(args.project).read(),observed_unix=time.time())
    elif args.action=='reserve':
        if args.admission is None or args.observations is None:raise ValueError('Complete admission and both original handles required')
        result=reserve(args.project,read_record(args.admission),read_record(args.observations))
    else:
        if args.capture is None or not args.expected_launch_sha256:raise ValueError('Original capture and dispatch-bound SHA required')
        result=settle(args.project,read_record(args.capture),args.expected_launch_sha256)
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
