"""One immutable full Q1/real-journal CPU correction per registered host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import cara_sq_q1_control_cpu_r1 as previous
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh,ssh
from wcomr.sq_q1_spec_r1 import SCOPE,MANIFEST_SHA,RUNTIME_REQUIRED

CONTROL_SCOPE='plans/cara_next_stage_20261028/sq/Q1_CONTROL_JOURNAL_CPU_R1.json'
FILES=tuple(dict.fromkeys(previous.FILES+('src/wcomr/sq_control_storage_r1.py',
    'tests/test_sq_control_storage_r1.py','tests/test_sq_journal_allocation_r1.py',
    'scripts/check_cara_sq_control_journal_cpu_r1.py',CONTROL_SCOPE)))
UNCHANGED_SCIENCE=('src/wcomr/sq_q1_collection_r1.py','src/wcomr/sq_q1_readout_r1.py',
    'src/wcomr/sq_readout_subgraph_r1.py','src/wcomr/sq_codec_r1.py','src/wcomr/sq_q1_assets_r1.py')


def launch_source(attempt='r2'):
    if attempt!='r2':raise ValueError('Preserve the original R1 CPU failure; recover its original handles')
    code=previous.launch_source()
    for old,new in (('cara-sq-q1-control-CPU-only-r6.lock','cara-sq-control-journal-CPU-only-r2.lock'),
        ('CARA_SQ_Q1_CONTROL_CPU_R6','CARA_SQ_CONTROL_JOURNAL_CPU_R2'),
        ('scripts/check_cara_sq_q1_control_cpu_r1.py','scripts/check_cara_sq_control_journal_cpu_r1.py')):
        if code.count(old)!=1:raise ValueError('Accepted CPU boundary changed: '+old)
        code=code.replace(old,new)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r1','r2'),default='r2')
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original journal correction CPU receipt')
    stage='cara-sq-control-journal-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261029'
    def remote(code,data=None):return ssh(code,data,docker_group=True) if args.host=='two_card' else four_ssh(code,data)
    if args.command=='launch':
        if args.attempt!='r2':raise ValueError('Original R1 CPU attempt is immutable; recover only')
        failed=json.loads((ROOT/f'reports/cara_sq_control_journal_{args.host}_cpu_check_r1_20261029.json').read_text())
        if (failed['launch']['source_revision']!='c26de98365f8d6b57d4c29b25219a94e9ca2ab70'
                or not failed['launch']['stage'].endswith('/'+stage.replace('-r2-','-r1-'))
                or failed['container_state']['Status']!='exited' or failed['container_state']['ExitCode']!=1
                or failed['original_CLI_live'] is not False):raise ValueError('Recover original same-host R1 CPU failure first')
        proof=json.loads((ROOT/f'reports/cara_sq_q1_control_{args.host}_cpu_accepted_r6_20261029.json').read_text())
        path=ROOT/proof['capture_ref'];old=json.loads(path.read_text())
        if (not proof['passed'] or hashlib.sha256(path.read_bytes()).hexdigest()!=proof['capture_sha256']
                or old['container_state']['Status']!='exited' or old['container_state']['ExitCode']!=0
                or old['original_CLI_live'] is not False):raise ValueError('Recover original terminal Q1 R6 CPU first')
        base=old['launch']
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:raise ValueError('Publish exact journal correction source')
        files={n:subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT) for n in FILES}
        for n in UNCHANGED_SCIENCE:
            if hashlib.sha256(files[n]).hexdigest()!=proof['critical_source_sha256'][n]:
                raise ValueError('Frozen Q1 numerical source changed: '+n)
        value=remote(launch_source(args.attempt),dict(stage_name=stage,profile=args.host,scope_name=SCOPE,
            manifest_sha256=MANIFEST_SHA,base=base,revision=revision,
            files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},
            runtime_extra_sha256={n:hashlib.sha256((ROOT/'cache/runtime'/n).read_bytes()).hexdigest() for n in RUNTIME_REQUIRED}))
    elif args.command=='capture':
        original=json.loads(args.launch_ref.read_text())
        if not original['stage'].endswith('/'+stage):raise ValueError('Recover exact original journal CPU stage')
        code=CAPTURE.replace("print(json.dumps(dict(status='SQ_CPU_PREPARATION_CAPTURE'",
            "sys.path.insert(0,str(s/'src'))\nfrom wcomr.gpu_budget_pool_v2 import same_live_process\nprint(json.dumps(dict(original_CLI_live=same_live_process(L['identity']),status='SQ_CPU_PREPARATION_CAPTURE'")
        value=remote(code,original)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_SQ_CONTROL_JOURNAL_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
