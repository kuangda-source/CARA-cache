"""Single-card host/hidden-supervisor entry; unchanged allocation primitives."""
import argparse,json,os,sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('guardian','supervise'))
    for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
    from wcomr.cara_f19_speed190_execution_r1 import validate_stage,publish_and_allocate
    from wcomr.history104_storage_r2 import storage_for
    validate_stage(a.project,a.stage)
    if a.action=='guardian':
        secret=json.load(sys.stdin)['sudo_password']
        result=publish_and_allocate(a.project,a.stage,secret)
    else:
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
        from wcomr.cara_budget_supervisor_r1 import supervise
        result=supervise(a.project,a.stage,storage_for(a.stage))
    print(json.dumps(result))


if __name__=='__main__':main()
