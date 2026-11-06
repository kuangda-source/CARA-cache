"""Immutable four-card CPU S topology check; no GPU or ledger commands."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_owner_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-sq-s-collection-cpu-four-card-r1-20261029'
SCOPE='plans/cara_next_stage_20261028/sq/S_COLLECTION_CPU_R1.json'
FILES=tuple(dict.fromkeys(previous.FILES+('src/wcomr/sq_s_collection_r1.py',
    'tests/check_sq_s_collection_cpu_r1.py','scripts/check_cara_sq_s_collection_cpu_r1.py',SCOPE)))


def launch_source():
    code=previous.launch_source()
    for before,after in (('cara-sq-s-owner-CPU-only-r2.lock','cara-sq-s-collection-CPU-only-r1.lock'),
        ('CARA_SQ_S_OWNER_CPU_R2','CARA_SQ_S_COLLECTION_CPU_R1'),
        ('scripts/check_cara_sq_s_owner_cpu_r1.py','scripts/check_cara_sq_s_collection_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU resource boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S collection CPU receipt')
    if args.command=='launch':
        accepted=json.loads((ROOT/'reports/cara_sq_s_owner_four_card_cpu_accepted_r2_20261029.json').read_text())
        if not accepted['passed'] or accepted['host']!='four_card' or accepted['complete_S_collector_accepted']:
            raise ValueError('First accept the original isolated S owner component on this host')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the immutable S collection CPU source before dispatch')
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        if any(hashlib.sha256(files[name]).hexdigest()!=digest
                for name,digest in accepted['critical_source_sha256'].items()):
            raise ValueError('S owner component differs from its accepted CPU source')
        base=json.loads((ROOT/'reports/cara_sq_q1_control_four_card_cpu_launch_r3_20261028.json').read_text())
        value=four_ssh(launch_source(),dict(stage_name=STAGE,profile='four_card',scope_name=SCOPE,
            manifest_sha256=previous.previous.MANIFEST_SHA,base=base,revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
            runtime_extra_sha256={}))
    elif args.command=='capture':value=four_ssh(CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+STAGE+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_S_COLLECTION_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=four_ssh(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
