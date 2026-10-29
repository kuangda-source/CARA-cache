"""One immutable complete S runner CPU composition per registered host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_resource_guard_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh,ssh

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_RUNNER_CPU_R1.json'
FILES=previous.FILES+('src/wcomr/sq_s_runner_r1.py','tests/test_sq_s_runner_r1.py',
    'tests/check_sq_s_runner_cpu_r1.py','scripts/check_cara_sq_s_runner_cpu_r1.py',SCOPE)


def launch_source():
    code=previous.launch_source()
    for old,new in (('cara-sq-s-resource-guard-CPU-only-r1.lock','cara-sq-s-runner-CPU-only-r1.lock'),
        ('CARA_SQ_S_RESOURCE_GUARD_CPU_R1','CARA_SQ_S_RUNNER_CPU_R1'),
        ('scripts/check_cara_sq_s_resource_guard_cpu_r1.py','scripts/check_cara_sq_s_runner_cpu_r1.py')):
        if code.count(old)!=1:raise ValueError('Accepted accepted CPU boundary changed: '+old)
        code=code.replace(old,new)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original S runner CPU receipt')
    stage='cara-sq-s-runner-cpu-'+args.host.replace('_','-')+'-r1-20261029'
    def remote(code,data=None):return ssh(code,data,docker_group=True) if args.host=='two_card' else four_ssh(code,data)
    if args.command=='launch':
        proof=json.loads((ROOT/f'reports/cara_sq_s_resource_guard_{args.host}_cpu_accepted_r1_20261029.json').read_text())
        capture_path=ROOT/proof['capture_ref'];capture=json.loads(capture_path.read_text())
        if (not proof['passed'] or capture['original_CLI_live'] is not False
                or capture['container_state']['Status']!='exited' or capture['container_state']['ExitCode']!=0
                or hashlib.sha256(capture_path.read_bytes()).hexdigest()!=proof['capture_sha256']):
            raise ValueError('Prior same-host affected CPU card must be accepted and terminal')
        base=json.loads((ROOT/f'reports/cara_sq_s_resource_guard_{args.host}_cpu_launch_r1_20261029.json').read_text())
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:raise ValueError('Publish exact S runner CPU source')
        files={n:subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT) for n in FILES}
        if any(hashlib.sha256(files[n]).hexdigest()!=digest for n,digest in proof['critical_source_sha256'].items()):
            raise ValueError('Original affected S component changed')
        parent=previous.previous
        value=remote(launch_source(),dict(stage_name=stage,profile=args.host,scope_name=SCOPE,
            manifest_sha256=parent.previous.previous.MANIFEST_SHA,base=base,revision=revision,
            files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},
            runtime_extra_sha256={n:hashlib.sha256((ROOT/'cache/runtime'/n).read_bytes()).hexdigest() for n in parent.RUNTIME_EXTRA}))
    elif args.command=='capture':
        original=json.loads(args.launch_ref.read_text())
        if not original['stage'].endswith('/'+stage):raise ValueError('Recover exact original S runner stage')
        code=CAPTURE.replace("print(json.dumps(dict(status='SQ_CPU_PREPARATION_CAPTURE'",
            "sys.path.insert(0,str(s/'src'))\nfrom wcomr.gpu_budget_pool_v2 import same_live_process\nprint(json.dumps(dict(original_CLI_live=same_live_process(L['identity']),status='SQ_CPU_PREPARATION_CAPTURE'")
        value=remote(code,original)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_S_RUNNER_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
