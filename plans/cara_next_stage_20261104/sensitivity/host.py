"""Phase2 admitted launcher; reuses the existing thermal/budget shutdown guards."""
import argparse
import json
from pathlib import Path
import sys


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('guardian','supervise'))
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.history104_storage_r2 import storage_for
    storage=storage_for(args.stage)
    if args.action=='guardian':
        from wcomr.cara_budget_host_guardian_r1 import allocate
        result=allocate(args.project,args.stage,storage,json.load(sys.stdin)['sudo_password'])
    else:
        from wcomr.cara_budget_supervisor_r1 import supervise
        result=supervise(args.project,args.stage,storage)
    print(json.dumps(result))
