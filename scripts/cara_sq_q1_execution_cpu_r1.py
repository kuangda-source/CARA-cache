"""Immutable dual-host Q1 execution CPU staging; no GPU/budget mutation."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import cara_sq_q1_whole_cpu_r1 as previous

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL,RUNTIME_REQUIRED,PROFILE,QUOTES

FILES=tuple(dict.fromkeys(previous.FILES+EXECUTION_CRITICAL+tuple(QUOTES.values())+(PROFILE,
    'src/wcomr/policy_price_terminal_r1.py','src/wcomr/policy_asset_price_review_r1.py',
    'src/wcomr/policy_price_refresh_contract_r1.py','src/wcomr/policy_interval_assets_r1.py',
    'tests/test_sq_q1_execution_r1.py','tests/test_sq_q1_terminal_r1.py','tests/test_sq_q1_assets_r1.py',
    'tests/test_sq_gpu_allocation_r1.py','tests/test_sq_q1_allocation_r2.py',
    'scripts/check_cara_sq_q1_execution_cpu_r1.py')))


def launch_source():
    code=previous.launch_source()
    changes=(('cara-sq-q1-whole-CPU-only-r1.lock','cara-sq-q1-execution-CPU-only-r1.lock'),
        ('CARA_SQ_Q1_WHOLE_CPU_R1','CARA_SQ_Q1_EXECUTION_CPU_R1'),
        ('scripts/check_cara_sq_q1_whole_cpu_r1.py','scripts/check_cara_sq_q1_execution_cpu_r1.py'),
        ('assert runtime_hashes and all(',
         "runtime_hashes.update(p['runtime_extra_sha256'])\n assert runtime_hashes and all("))
    for before,after in changes:
        if code.count(before)!=1:raise ValueError('Accepted CPU boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original CPU controller receipt')
    stage='cara-sq-q1-execution-cpu-'+args.host.replace('_','-')+'-r1-20261028'
    transport=previous.previous.prior.transport
    def remote(code,data=None):
        return transport.ssh(code,data,docker_group=True) if args.host=='two_card' else transport.four_ssh(code,data)
    if args.command=='launch':
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]!=revision:
            raise ValueError('Publish exact Q1 execution entry before CPU dispatch')
        files={name:(ROOT/name).read_bytes() for name in FILES}
        if any(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)!=raw for name,raw in files.items()):
            raise ValueError('Unpublished Q1 execution CPU source')
        base_name={'two_card':'cara_IG_grouped_two_card_CPU_finished_r1_20261027.json',
            'four_card':'cara_IG_four_card_CPU_terminal_r3_20261027.json'}[args.host]
        base=json.loads((ROOT/'reports'/base_name).read_text())['launch']
        value=remote(launch_source(),dict(stage_name=stage,profile=args.host,scope_name=previous.SCOPE,
            manifest_sha256=previous.previous.prior.previous.MANIFEST,base=base,revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
            runtime_extra_sha256={name:hashlib.sha256((ROOT/'cache/runtime'/name).read_bytes()).hexdigest()
                for name in RUNTIME_REQUIRED}))
    elif args.command=='capture':
        value=remote(previous.previous.prior.previous.CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_Q1_EXECUTION_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=remote(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
