"""Bounded32 transport continuation inside the original CPU time envelope."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

import cara_sq_b1_port_cpu_r1 as original
from cara_two_card_transport_r1 import four_ssh,password

ROOT=Path(__file__).resolve().parents[1]
STAGE='/home/user/cara_sq_b1_port_cpu_r2_20261029'
PROFILE='plans/cara_next_stage_20261028/sq/B1_PORT_CPU_PROFILE_R2.json'
FILES=tuple(dict.fromkeys(original.FILES+(PROFILE,)))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','start','capture'))
    p.add_argument('--source-revision');p.add_argument('--previous-launch',type=Path)
    p.add_argument('--source-release',type=Path);p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original CPU port R2 evidence')
    if args.command=='start':
        previous=json.loads(args.previous_launch.read_text());released=json.loads(args.source_release.read_text())
        if previous['stage']!=original.STAGE or released['original_source_live'] is not False:
            raise ValueError('Recover and release exactly the original R1 CPU transfer first')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the new bounded32 CPU transport before starting')
        endpoint,pins=original.source_endpoint()
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        data=dict(stage=STAGE,profile_path=PROFILE,revision=revision,endpoint=endpoint,pins=pins,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            previous_launch=previous,source_release=released,source_password=password())
        try:value=four_ssh(original.START,data)
        finally:data.pop('source_password',None)
    else:
        launch=json.loads(args.launch_ref.read_text()) if args.launch_ref else None
        value=four_ssh(original.CAPTURE,dict(stage=STAGE,launch=launch))
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','original_handle_live','original_deadline_unix')}))


if __name__=='__main__':main()
