"""One GPU-hidden four-card S component run; preserve all existing jobs/stages."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_q1_control_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh

ROOT=Path(__file__).resolve().parents[1]
STAGES={'r1':'cara-sq-s-owner-cpu-four-card-r1-20261028',
        'r2':'cara-sq-s-owner-cpu-four-card-r2-20261029'}
SCOPE='plans/cara_next_stage_20261028/sq/S_OWNER_ROUNDTRIP_CPU_R1.json'
FILES=('src/wcomr/sq_s_owner_roundtrip_r1.py','src/wcomr/sq_s_sources_r1.py','src/wcomr/sq_risk_r1.py',
    'tests/check_sq_s_owner_roundtrip_cpu_r1.py','tests/check_cara_pg_production_sampling_cpu_r1.py',
    'tests/check_partial_mlp_guided_sampling_cpu_r1.py','tests/check_full_sampling.py',
    'tests/check_rv0_video_actions_cpu.py','tests/check_rv0_restore_cpu.py',
    'scripts/check_cara_sq_s_owner_cpu_r1.py',SCOPE)


def launch_source():
    code=previous.launch_source()
    for before,after in (('cara-sq-q1-control-CPU-only-r3.lock','cara-sq-s-owner-CPU-only-r2.lock'),
        ('CARA_SQ_Q1_CONTROL_CPU_R3','CARA_SQ_S_OWNER_CPU_R2'),
        ('scripts/check_cara_sq_q1_control_cpu_r1.py','scripts/check_cara_sq_s_owner_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU resource boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--attempt',choices=tuple(STAGES),default='r2')
    p.add_argument('--source-revision',help='Published immutable S component source')
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    stage=STAGES[args.attempt]
    if args.output.exists():raise FileExistsError('Preserve original S CPU controller output')
    if args.command=='launch':
        if args.attempt!='r2':raise ValueError('R1 is immutable; recover its original failure')
        failed=json.loads((ROOT/'reports/cara_sq_s_owner_four_card_cpu_failed_terminal_r1_20261029.json').read_text())
        if (failed['launch']['stage'].split('/')[-1]!=STAGES['r1']
                or failed['container_state']['Running'] or failed['container_state']['ExitCode']!=1
                or failed['result'] is not None):
            raise ValueError('Recover the original terminal R1 before preparing a new CPU stage')
        revision=args.source_revision or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish exact S CPU component source before dispatch')
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        base=json.loads((ROOT/'reports/cara_sq_q1_control_four_card_cpu_launch_r3_20261028.json').read_text())
        value=four_ssh(launch_source(),dict(stage_name=stage,profile='four_card',scope_name=SCOPE,
            manifest_sha256=previous.MANIFEST_SHA,base=base,revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
            runtime_extra_sha256={}))
    elif args.command=='capture':value=four_ssh(CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_S_OWNER_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=four_ssh(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
