"""Bounded dual-host CPU controller; original B1 data is read only on A6000."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_q1_cpu_r1 as prior

ROOT = Path(__file__).resolve().parents[1]
FILES = prior.FILES + ('src/wcomr/sq_readout_subgraph_r1.py', 'tests/test_sq_readout_subgraph_r1.py',
    'scripts/check_cara_sq_readout_cut_cpu_r1.py',
    'plans/cara_next_stage_20261028/sq/Q1_READOUT_CONTROL_CPU_R3.json',
    'plans/cara_next_stage_20261028/sq/Q1_READOUT_CONTROL_CPU_R4.json')


def launch_source():
    code = prior.launch_source()
    for before, after in (
        ('cara-sq-q1-CPU-only-r1.lock', 'cara-sq-readout-cut-CPU-only-r1.lock'),
        ('CARA_SQ_Q1_CPU_PREPARATION_R1', 'CARA_SQ_READOUT_CUT_CPU_R1'),
        ('scripts/check_cara_sq_q1_cpu_r1.py', 'scripts/check_cara_sq_readout_cut_cpu_r1.py'),
        ("'--profile',p['profile'],'--output'", "'--profile',p['profile'],'--scope',p['scope_name'],'--output'")):
        if code.count(before) != 1:
            raise ValueError('Accepted CPU resource boundary changed: '+before)
        code = code.replace(before, after)
    return code


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=('launch','capture','recover'))
    p.add_argument('--host', choices=('two_card','four_card'), required=True)
    p.add_argument('--attempt', choices=('r1','r2'), default='r2')
    p.add_argument('--launch-ref', type=Path); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError('Keep original CPU controller receipt')
    stage = 'cara-sq-readout-cut-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261028'
    def remote(code, data=None):
        return prior.transport.ssh(code, data, docker_group=True) if args.host == 'two_card' else prior.transport.four_ssh(code, data)
    if args.command == 'launch':
        if args.attempt != 'r2':
            raise ValueError('R1 is an immutable historical attempt; use recover/capture')
        revision = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
        if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'], cwd=ROOT, text=True).split()[0] != revision:
            raise ValueError('Publish exact source before CPU dispatch')
        files = {name:(ROOT/name).read_bytes() for name in FILES}
        if any(subprocess.check_output(['git','show',revision+':'+name], cwd=ROOT) != raw for name, raw in files.items()):
            raise ValueError('Unpublished readout CPU source')
        name = {'two_card':'cara_IG_grouped_two_card_CPU_finished_r1_20261027.json',
                'four_card':'cara_IG_four_card_CPU_terminal_r3_20261027.json'}[args.host]
        base = json.loads((ROOT/'reports'/name).read_text())['launch']
        value = remote(launch_source(), dict(stage_name=stage, profile=args.host,
            scope_name='plans/cara_next_stage_20261028/sq/Q1_READOUT_CONTROL_CPU_R4.json',
            manifest_sha256=prior.previous.MANIFEST,
            base=base, revision=revision, files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}))
    elif args.command == 'capture':
        value = remote(prior.previous.CAPTURE, json.loads(args.launch_ref.read_text()))
    else:
        code = "import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_READOUT_CUT_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value = remote(code)
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__ == '__main__': main()
