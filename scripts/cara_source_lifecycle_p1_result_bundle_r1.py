"""Export complete P1 receipts on the host; render their original bytes locally."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]

from wcomr import cara_source_lifecycle_p1_result_bundle_r1 as bundle


if __name__=='__main__':
    parser=argparse.ArgumentParser();commands=parser.add_subparsers(dest='action',required=True)
    export=commands.add_parser('export');export.add_argument('--stage',type=Path,required=True)
    export.add_argument('--cpu-validation',action='store_true');export.add_argument('--fixture-summary',type=Path)
    render=commands.add_parser('render');render.add_argument('--bundle',type=Path,required=True)
    render.add_argument('--expected-sha256',required=True);render.add_argument('--output',type=Path,required=True)
    render.add_argument('--cpu-validation',action='store_true')
    args=parser.parse_args()
    if args.action=='export':result=bundle.export(args.stage,cpu_validation=args.cpu_validation,fixture_summary=args.fixture_summary)
    else:result=bundle.render(args.bundle,args.expected_sha256,args.output,cpu_validation=args.cpu_validation)
    print(json.dumps(result,allow_nan=False))
