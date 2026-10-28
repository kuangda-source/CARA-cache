"""Stage one immutable GPU-hidden S resource inventory per registered host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_s_physical_cpu_r1 as previous
import cara_sq_q1_control_cpu_r1 as boundary
from cara_sq_two_card_cpu_r1 import CAPTURE
from cara_two_card_transport_r1 import four_ssh,ssh

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_RESOURCES_CPU_R1.json'
SCOPE_R2='plans/cara_next_stage_20261028/sq/S_RESOURCES_CPU_R2.json'
SCOPE_R3='plans/cara_next_stage_20261028/sq/S_RESOURCES_CPU_R3.json'
SCOPE_R4='plans/cara_next_stage_20261028/sq/S_RESOURCES_CPU_R4.json'
FILES=tuple(dict.fromkeys(previous.FILES+('src/wcomr/sq_s_resources_r1.py',
    'tests/test_sq_s_resources_r1.py','tests/check_sq_s_resources_cpu_r1.py',
    'scripts/check_cara_sq_s_resources_cpu_r1.py','src/wcomr/runtime_config.py',
    'src/wcomr/h0_mode.py','manifests/wc_h0_eval_mode_contract_20261003.json',SCOPE)))
RUNTIME_EXTRA=('cosmos_predict2/_src/predict2/configs/video2world/defaults/net.py',
    'cosmos_predict2/_src/predict2/configs/video2world/config.py',
    'cosmos_predict2/_src/imaginaire/lazy_config/__init__.py',
    'cosmos_predict2/_src/imaginaire/lazy_config/instantiate.py',
    'cosmos_predict2/_src/imaginaire/utils/config_helper.py')


def launch_source(attempt='r4'):
    code=boundary.launch_source()
    for before,after in (('cara-sq-q1-control-CPU-only-r6.lock','cara-sq-s-resources-CPU-only-'+attempt+'.lock'),
        ('CARA_SQ_Q1_CONTROL_CPU_R6','CARA_SQ_S_RESOURCES_CPU_'+attempt.upper()),
        ('scripts/check_cara_sq_q1_control_cpu_r1.py','scripts/check_cara_sq_s_resources_cpu_r1.py')):
        if code.count(before)!=1:raise ValueError('Accepted CPU resource boundary changed: '+before)
        code=code.replace(before,after)
    if "runtime_hashes.update(p['runtime_extra_sha256'])" not in code:
        before='assert runtime_hashes and all('
        if code.count(before)!=1:raise ValueError('Accepted runtime binding changed')
        code=code.replace(before,"runtime_hashes.update(p['runtime_extra_sha256'])\n assert runtime_hashes and all(")
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','launch','capture'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--attempt',choices=('r1','r2','r3','r4'),default='r4')
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain original resource CPU receipt')
    stage='cara-sq-s-resources-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261029'
    def remote(code,data=None):
        return ssh(code,data,docker_group=True) if args.host=='two_card' else four_ssh(code,data)
    if args.command=='launch':
        if args.attempt!='r4':raise ValueError('Earlier resource stages are immutable; recover their original handles')
        failed=json.loads((ROOT/f'reports/cara_sq_s_resources_{args.host}_cpu_failed_r1_20261029.json').read_text())
        if not failed['failure_terminal_verified'] or failed['container_state']['ExitCode']!=1 or failed['original_CLI_live'] is not False:
            raise ValueError('Recover original same-host R1 failure before the corrected metadata stage')
        if args.host=='two_card':
            failed2=json.loads((ROOT/'reports/cara_sq_s_resources_two_card_cpu_failed_r2_20261029.json').read_text())
            if not failed2['failure_terminal_verified'] or failed2['original_CLI_live'] is not False:
                raise ValueError('Recover original R2 refusal before the corrected metadata stage')
        failed3=json.loads((ROOT/f'reports/cara_sq_s_resources_{args.host}_cpu_failed_r3_20261029.json').read_text())
        if not failed3['failure_terminal_verified'] or failed3['original_CLI_live'] is not False:
            raise ValueError('Recover original same-host R3 reset refusal before R4 metadata dispatch')
        version='r2' if args.host=='two_card' else 'r1'
        accepted=json.loads((ROOT/f'reports/cara_sq_s_physical_{args.host}_cpu_accepted_{version}_20261029.json').read_text())
        base=json.loads((ROOT/f'reports/cara_sq_s_physical_{args.host}_cpu_launch_{version}_20261029.json').read_text())
        original=ROOT/accepted['capture_ref'];captured=json.loads(original.read_text())
        if (not accepted['passed'] or captured['container_state']['Running'] or captured['container_state']['ExitCode']!=0
                or hashlib.sha256(original.read_bytes()).hexdigest()!=accepted['capture_sha256']):
            raise ValueError('Recover original accepted physical CPU stage before resource preparation')
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the exact resource CPU source before dispatch')
        files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES+(SCOPE_R2,SCOPE_R3,SCOPE_R4)}
        value=remote(launch_source(args.attempt),dict(stage_name=stage,profile=args.host,scope_name=SCOPE_R4,
            manifest_sha256=previous.previous.MANIFEST_SHA,base=base,revision=revision,
            files={n:base64.b64encode(raw).decode() for n,raw in files.items()},
            hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()},
            runtime_extra_sha256={n:hashlib.sha256((ROOT/'cache/runtime'/n).read_bytes()).hexdigest() for n in RUNTIME_EXTRA}))
    elif args.command=='capture':
        original=json.loads(args.launch_ref.read_text())
        if not original['stage'].endswith('/'+stage):raise ValueError('Capture the exact original resource stage')
        code=CAPTURE.replace("print(json.dumps(dict(status='SQ_CPU_PREPARATION_CAPTURE'",
            "sys.path.insert(0,str(s/'src'))\nfrom wcomr.gpu_budget_pool_v2 import same_live_process\nprint(json.dumps(dict(original_CLI_live=same_live_process(L['identity']),status='SQ_CPU_PREPARATION_CAPTURE'")
        value=remote(code,original)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps(dict(status='NO_S_RESOURCES_CPU_LAUNCH',stage_exists=p.parent.exists())))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
