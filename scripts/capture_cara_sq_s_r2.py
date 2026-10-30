"""One original-handle S observation; never dispatches, retries or settles."""
import argparse
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--launch-sha256',required=True);args=p.parse_args()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.sq_s_capture_r2 import capture
    if args.output.exists():raise FileExistsError('Preserve original S observation')
    value=capture(args.project,args.stage,args.launch_sha256)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=value['status'],GPU_submissions=0,ledger_writes=0)))


if __name__=='__main__':main()
