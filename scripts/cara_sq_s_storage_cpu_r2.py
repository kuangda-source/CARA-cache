"""New immutable CPU storage composition after the original S topology accepted."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_collection_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-sq-s-storage-cpu-four-card-r2-20261029'
SCOPE='plans/cara_next_stage_20261028/sq/S_COLLECTION_STORAGE_CPU_R2.json'
FILES=tuple(dict.fromkeys(previous.FILES+('src/wcomr/sq_s_storage_r1.py',
    'src/wcomr/scout_parent_v22.py','tests/test_sq_s_storage_r1.py',
    'tests/check_sq_s_collection_storage_cpu_r2.py',SCOPE)))


def launch_source():
    code=previous.launch_source()
    for before,after in (('cara-sq-s-collection-CPU-only-r1.lock','cara-sq-s-storage-CPU-only-r2.lock'),
        ('CARA_SQ_S_COLLECTION_CPU_R1','CARA_SQ_S_STORAGE_CPU_R2')):
        if code.count(before)!=1:raise ValueError('Accepted CPU resource boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S CPU storage receipt')
    if args.command=='launch':
        accepted=json.loads((ROOT/'reports/cara_sq_s_collection_four_card_cpu_accepted_r1_20261029.json').read_text())
        if not accepted['passed'] or accepted['host']!='four_card' or accepted['complete_S_card_accepted']:
            raise ValueError('First accept the original complete S CPU topology on this host')
        original=json.loads((ROOT/accepted['capture_ref']).read_text())
        if hashlib.sha256((ROOT/accepted['capture_ref']).read_bytes()).hexdigest()!=accepted['capture_sha256']:
            raise ValueError('Original accepted S CPU terminal changed')
        if original['container_state']['Running'] or original['container_state']['ExitCode']!=0:
            raise ValueError('Recover the original S CPU terminal before a new stage')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish immutable S CPU storage source before dispatch')
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        owner=json.loads((ROOT/'reports/cara_sq_s_owner_four_card_cpu_accepted_r2_20261029.json').read_text())
        if any(hashlib.sha256(files[name]).hexdigest()!=digest for name,digest in owner['critical_source_sha256'].items()):
            raise ValueError('S owner component changed from its original accepted source')
        base=json.loads((ROOT/'reports/cara_sq_q1_control_four_card_cpu_launch_r3_20261028.json').read_text())
        value=four_ssh(launch_source(),dict(stage_name=STAGE,profile='four_card',scope_name=SCOPE,
            manifest_sha256=previous.previous.previous.MANIFEST_SHA,base=base,revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},runtime_extra_sha256={}))
    elif args.command=='capture':value=four_ssh(CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+STAGE+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_S_STORAGE_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=four_ssh(code)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:value.get(key) for key in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
