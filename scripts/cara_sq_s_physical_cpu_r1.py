"""One immutable CPU physical-matrix check on each registered host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_batch_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh, ssh

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_PHYSICAL_CPU_R1.json'
FILES=tuple(dict.fromkeys(previous.FILES+('src/wcomr/sq_s_physical_r1.py','src/wcomr/sq_s_reuse_r1.py',
    'src/wcomr/rv0_video_reader.py','tests/test_sq_s_physical_r1.py','tests/check_sq_s_physical_cpu_r1.py',
    'scripts/check_cara_sq_s_physical_cpu_r1.py',SCOPE,
    'plans/cara_next_stage_20261028/sq/S_EXECUTION_IDENTITY_R1.json',
    'plans/cara_next_stage_20261028/sq/S_RETAINED_OFF_WITNESS_R1.json',
    'plans/cara_next_stage_20261028/sq/S_PHYSICAL_TWO_CARD_R1.json',
    'plans/cara_next_stage_20261028/sq/S_PHYSICAL_FOUR_CARD_R1.json',
    'plans/cara_next_stage_20261028/sq/S_SUPPORT_RECONCILIATION_R2.json',
    'reports/cara_sq_s_retained_CPU_OFF_fixture_r1_20261029.json')))


def launch_source():
    code=previous.launch_source()
    for before,after in (('cara-sq-s-batch-CPU-only-r1.lock','cara-sq-s-physical-CPU-only-r1.lock'),
        ('CARA_SQ_S_BATCH_CPU_R1','CARA_SQ_S_PHYSICAL_CPU_R1'),
        ('scripts/check_cara_sq_s_batch_cpu_r1.py','scripts/check_cara_sq_s_physical_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU resource boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original physical S CPU receipt')
    stage='cara-sq-s-physical-cpu-'+args.host.replace('_','-')+'-r1-20261029'
    def remote(code,data=None):
        return ssh(code,data,docker_group=True) if args.host=='two_card' else four_ssh(code,data)
    if args.command=='launch':
        proof=json.loads((ROOT/('reports/cara_sq_s_batch_'+args.host+'_cpu_accepted_r1_20261029.json')).read_text())
        base=json.loads((ROOT/('reports/cara_sq_s_batch_'+args.host+'_cpu_launch_r1_20261029.json')).read_text())
        capture=json.loads((ROOT/proof['capture_ref']).read_text())
        if (not proof['passed'] or capture['container_state']['Running'] or capture['container_state']['ExitCode']!=0
                or hashlib.sha256((ROOT/proof['capture_ref']).read_bytes()).hexdigest()!=proof['capture_sha256']):
            raise ValueError('First recover and accept the original whole S CPU matrix on this host')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the exact new physical-composition CPU source first')
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        if any(hashlib.sha256(files[name]).hexdigest()!=digest for name,digest in proof['critical_source_sha256'].items()):
            raise ValueError('Original accepted S composition source changed')
        value=remote(launch_source(),dict(stage_name=stage,profile=args.host,scope_name=SCOPE,
            manifest_sha256=previous.MANIFEST_SHA,base=base,revision=revision,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
            hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},runtime_extra_sha256={}))
    elif args.command=='capture':
        launch=json.loads(args.launch_ref.read_text())
        if not launch['stage'].endswith('/'+stage):raise ValueError('Recover the original host-bound physical CPU stage')
        value=remote(CAPTURE,launch)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_S_PHYSICAL_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
