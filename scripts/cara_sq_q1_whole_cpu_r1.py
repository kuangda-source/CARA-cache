"""Reuse the accepted immutable dual-host CPU staging and resource boundary."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_readout_cut_cpu_r1 as previous

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'plans/cara_next_stage_20261028/sq/Q1_WHOLE_SCOPE_R1.json'
FILES = previous.FILES + ('src/wcomr/sq_q1_collection_r1.py','tests/test_sq_q1_collection_r1.py',
    'scripts/check_cara_sq_q1_whole_cpu_r1.py',SCOPE)


def launch_source():
    code = previous.launch_source()
    for before,after in (
        ('cara-sq-readout-cut-CPU-only-r1.lock','cara-sq-q1-whole-CPU-only-r1.lock'),
        ('CARA_SQ_READOUT_CUT_CPU_R1','CARA_SQ_Q1_WHOLE_CPU_R1'),
        ('scripts/check_cara_sq_readout_cut_cpu_r1.py','scripts/check_cara_sq_q1_whole_cpu_r1.py')):
        if code.count(before) != 1:raise ValueError('Accepted CPU launch boundary changed: '+before)
        code = code.replace(before,after)
    return code


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original CPU controller receipt')
    stage = 'cara-sq-q1-whole-cpu-'+args.host.replace('_','-')+'-r1-20261028'
    transport = previous.prior.transport
    def remote(code,data=None):
        return transport.ssh(code,data,docker_group=True) if args.host=='two_card' else transport.four_ssh(code,data)
    if args.command=='launch':
        revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0] != revision:
            raise ValueError('Publish the exact Q1 entry before CPU dispatch')
        files = {name:(ROOT/name).read_bytes() for name in FILES}
        if any(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) != raw for name,raw in files.items()):
            raise ValueError('Unpublished Q1 CPU source')
        base_name = {'two_card':'cara_IG_grouped_two_card_CPU_finished_r1_20261027.json',
                     'four_card':'cara_IG_four_card_CPU_terminal_r3_20261027.json'}[args.host]
        base = json.loads((ROOT/'reports'/base_name).read_text())['launch']
        value = remote(launch_source(),dict(stage_name=stage,profile=args.host,scope_name=SCOPE,
            manifest_sha256=previous.prior.previous.MANIFEST,base=base,revision=revision,
            files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}))
    elif args.command=='capture':
        value = remote(previous.prior.previous.CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code = "import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_Q1_WHOLE_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value = remote(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
