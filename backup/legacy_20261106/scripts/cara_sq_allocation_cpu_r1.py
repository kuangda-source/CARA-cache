"""Publish/recover one isolated no-GPU host-allocation CPU stage per host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_physical_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh,ssh

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/ALLOCATION_CPU_R1.json'
SCOPE_R2='plans/cara_next_stage_20261028/sq/ALLOCATION_CPU_R2.json'
FILES=('src/wcomr/sq_gpu_allocation_r1.py','tests/test_sq_gpu_allocation_r1.py',
    'scripts/check_cara_sq_allocation_cpu_r1.py','scripts/cara_sq_q1_control_r1.py',SCOPE)


def launch_source(attempt='r2'):
    code=previous.launch_source('r1')
    for before,after in (('cara-sq-s-physical-CPU-only-r1.lock','cara-sq-allocation-CPU-only-'+attempt+'.lock'),
        ('CARA_SQ_S_PHYSICAL_CPU_R1','CARA_SQ_ALLOCATION_CPU_'+attempt.upper()),
        ('scripts/check_cara_sq_s_physical_cpu_r1.py','scripts/check_cara_sq_allocation_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU sandbox boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r1','r2'),default='r2')
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original full-allocation CPU receipt')
    stage='cara-sq-allocation-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261029'
    scope_name=SCOPE_R2 if args.attempt=='r2' else SCOPE
    file_names=FILES+((SCOPE_R2,) if args.attempt=='r2' else ())
    def remote(code,data=None):
        return ssh(code,data,docker_group=True) if args.host=='two_card' else four_ssh(code,data)
    if args.command=='launch':
        if args.attempt!='r2':raise ValueError('R1 is immutable; recover the original failed CPU checks')
        failed=json.loads((ROOT/f'reports/cara_sq_allocation_{args.host}_cpu_terminal_r1_20261029.json').read_text())
        if (failed['container_state']['Running'] or failed['container_state']['ExitCode']!=1
                or failed['result'] is not None):raise ValueError('First recover the original same-host R1 terminal')
        attempt='r2' if args.host=='two_card' else 'r1'
        proof=json.loads((ROOT/f'reports/cara_sq_s_physical_{args.host}_cpu_accepted_{attempt}_20261029.json').read_text())
        base=json.loads((ROOT/f'reports/cara_sq_s_physical_{args.host}_cpu_launch_{attempt}_20261029.json').read_text())
        capture=json.loads((ROOT/proof['capture_ref']).read_text())
        if (not proof['passed'] or proof['host']!=args.host or proof['source_revision']!=base['source_revision']
                or capture['launch']!=base or capture['container_state']['Running'] or capture['container_state']['ExitCode']!=0
                or hashlib.sha256((ROOT/proof['capture_ref']).read_bytes()).hexdigest()!=proof['capture_sha256']):
            raise ValueError('Recover and accept original physical CPU stage before another component')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the exact allocation CPU component first')
        files={n:subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT) for n in file_names}
        value=remote(launch_source(args.attempt),dict(stage_name=stage,profile=args.host,scope_name=scope_name,
            manifest_sha256=previous.previous.MANIFEST_SHA,base=base,revision=revision,
            files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},runtime_extra_sha256={}))
    elif args.command=='capture':
        launch=json.loads(args.launch_ref.read_text())
        if not launch['stage'].endswith('/'+stage):raise ValueError('Capture the exact original allocation CPU stage')
        value=remote(CAPTURE,launch)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_ALLOCATION_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
