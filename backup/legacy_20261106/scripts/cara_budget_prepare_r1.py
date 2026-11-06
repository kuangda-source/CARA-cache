"""Explicit CPU source preparation/admission; no GPU submission actions."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['package','observe','prepare','bind-authority','admit','bind-reservation'])
    for key in ('project','source-root','stage','base','plan','archive','observations','authorization',
                'proof','quote','envelope','central-snapshot','base-registration','output'):
        parser.add_argument('--'+key,type=Path)
    parser.add_argument('--host',choices=['four_card','two_card']);parser.add_argument('--revision')
    args=parser.parse_args()
    root=args.source_root or Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(root/'src'),str(root/'scripts')]
    from wcomr.cara_budget_prepare_r1 import source_plan,observe_original,prepare,bind_authority,admit,bind_reservation
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.cara_fast_b36_dispatch_r2 import create
    from wcomr.immutable_stage_payload_r1 import git_archive
    from wcomr.gpu_budget_pool_v2 import sha
    def needed(*names):
        for name in names:
            if getattr(args,name) is None:raise ValueError('Required argument: --'+name.replace('_','-'))
    if args.action=='package':
        needed('base_registration','revision','plan','archive')
        base=read_record(args.base_registration)
        field='source_revision' if 'source_revision' in base else 'parent_git_revision'
        value=source_plan(root,sha(args.base_registration),base[field],field)
        raw=git_archive(root,value,args.revision)
        create(args.plan,value)
        with args.archive.open('xb') as stream:stream.write(raw)
        result=dict(status='PUBLISHED_SOURCE_PACKAGE_ONLY',source_revision=args.revision,
            plan_sha256=sha(args.plan),archive_sha256=sha(args.archive),overlay_files=len(value['overlay_sha256']),GPU_submissions=0)
    else:
        needed('project')
        if args.action=='observe':needed('host');result=observe_original(args.project,args.host)
        elif args.action=='prepare':
            needed('host','base','archive','plan','revision','observations')
            result=prepare(args.project,args.host,args.base,args.archive.read_bytes(),read_record(args.plan),
                args.revision,read_record(args.observations))
        elif args.action=='bind-authority':
            needed('stage','authorization','proof','quote')
            result=bind_authority(args.project,args.stage,read_record(args.authorization),read_record(args.proof),read_record(args.quote))
        elif args.action=='admit':needed('stage');result=admit(args.project,args.stage)
        else:
            needed('stage','envelope','central_snapshot')
            result=bind_reservation(args.project,args.stage,read_record(args.envelope),read_record(args.central_snapshot))
    if args.output:create(args.output,result)
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
