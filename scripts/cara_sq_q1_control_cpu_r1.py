"""Use the unchanged GPU-hidden CPU resource/transport boundary for wrappers."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_q1_execution_cpu_r1 as previous
import cara_two_card_transport_r1 as transport
from cara_sq_two_card_cpu_r1 import CAPTURE
from wcomr.sq_q1_spec_r1 import SCOPE,MANIFEST_SHA,RUNTIME_REQUIRED

ROOT=Path(__file__).resolve().parents[1]
FILES=tuple(dict.fromkeys(previous.FILES+('tests/test_sq_q1_control_r1.py',
    'scripts/check_cara_sq_q1_control_cpu_r1.py')))


def launch_source():
    code=previous.launch_source()
    for before,after in (('cara-sq-q1-execution-CPU-only-r1.lock','cara-sq-q1-control-CPU-only-r1.lock'),
        ('CARA_SQ_Q1_EXECUTION_CPU_R1','CARA_SQ_Q1_CONTROL_CPU_R1'),
        ('scripts/check_cara_sq_q1_execution_cpu_r1.py','scripts/check_cara_sq_q1_control_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU boundary changed: '+before)
        code=code.replace(before,after)
    for before,after in (
        ('cara-sq-q1-control-CPU-only-r1.lock','cara-sq-q1-control-CPU-only-r3.lock'),
        ('CARA_SQ_Q1_CONTROL_CPU_R1','CARA_SQ_Q1_CONTROL_CPU_R3')):
        if code.count(before)!=1:raise ValueError('Affected CPU entry changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r1','r2','r3'),default='r3')
    p.add_argument('--source-revision',help='Explicit already published immutable source; permits later unrelated repository commits')
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original wrapper CPU receipt')
    stage='cara-sq-q1-control-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261028'
    def remote(code,data=None):
        return transport.ssh(code,data,docker_group=True) if args.host=='two_card' else transport.four_ssh(code,data)
    if args.command=='launch':
        if args.attempt!='r3':raise ValueError('Earlier attempts are immutable; recover/capture their original handles')
        revision=args.source_revision or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Chosen immutable CPU source is not on published main')
        # Load the declared Git tree, keeping an accepted card independent of
        # simultaneous edits in another chat's shared checkout.
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        ref={'two_card':'cara_IG_grouped_two_card_CPU_finished_r1_20261027.json',
            'four_card':'cara_IG_four_card_CPU_terminal_r3_20261027.json'}[args.host]
        value=remote(launch_source(),dict(stage_name=stage,profile=args.host,
            scope_name=SCOPE,manifest_sha256=MANIFEST_SHA,
            base=json.loads((ROOT/'reports'/ref).read_text())['launch'],revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
            runtime_extra_sha256={name:hashlib.sha256((ROOT/'cache/runtime'/name).read_bytes()).hexdigest()
                for name in RUNTIME_REQUIRED}))
    elif args.command=='capture':
        value=remote(CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_Q1_CONTROL_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=remote(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
