"""Prepare/capture one bounded CPU-only endpoint stage on each registered host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from cara_two_card_transport_r1 import password
from wc_dual_host_paper_timing_cpu_r1 import REMOTE as PARENT_REMOTE

ROOT=Path(__file__).resolve().parents[1]
STAGES={'four_card':'cara-budget-endpoint-CPU-ada-r1-20261030',
        'two_card':'cara-budget-endpoint-CPU-a6000-r1-20261030'}
PARENTS={'four_card':'reports/cara_fast_binding_four_card_CPU_capture3_r6_20261028.json',
         'two_card':'reports/cara_fast_binding_two_card_CPU_capture_r8_20261028.json'}
NEW_FILES=(
    'src/wcomr/cara_budget_search_r1.py','src/wcomr/cara_budget_search_journal_r1.py',
    'src/wcomr/cara_budget_rgb_objective_r1.py','src/wcomr/cara_budget_endpoint_requests_r1.py',
    'tests/test_cara_budget_search_r1.py','tests/test_cara_budget_search_journal_r1.py',
    'tests/test_cara_budget_rgb_objective_r1.py','tests/check_cara_budget_endpoint_routes_r1.py',
    'scripts/check_cara_budget_endpoint_cpu_r1.py')
REMOTE=PARENT_REMOTE.replace('check_cara_paper_timing_cpu_r1.py','check_cara_budget_endpoint_cpu_r1.py').replace(
    "('NanoCpus','Memory','DeviceRequests','NetworkMode','ReadonlyRootfs')",
    "('NanoCpus','Memory','MemorySwap','CpusetCpus','DeviceRequests','NetworkMode','ReadonlyRootfs')")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','capture'])
    parser.add_argument('--host',choices=list(STAGES),required=True)
    parser.add_argument('--ssh-config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Fresh local CPU receipt required')
    if args.ssh_config.stat().st_mode & 0o077: raise ValueError('Private SSH configuration must remain0600')
    payload=dict(action=args.action,host=args.host,stage_name=STAGES[args.host])
    if args.action=='prepare':
        intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_ENDPOINT_CPU_FRAGMENT_R1.json').read_text())
        if intent['stages'] != STAGES: raise ValueError('Registered CPU stages differ')
        for name,expected in intent['source_sha256'].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('Registered CPU source changed: '+name)
        base=json.loads((ROOT/PARENTS[args.host]).read_text())
        paths=set(base['registration']['payload_sha256']) | set(NEW_FILES)
        files={n:(ROOT/n).read_bytes() for n in sorted(paths)}
        payload.update(base_stage=base['launch']['stage'],base_registration_sha256=base['registration_sha256'],
            parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            files={n:base64.b64encode(b).decode() for n,b in files.items()},
            hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
    interpreter=('/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        if args.host=='two_card' else 'python3')
    command=shlex.quote(interpreter)+' -c '+shlex.quote(REMOTE)
    data=json.dumps(payload)
    secret=None
    if args.host=='two_card':
        secret=password()
        command="sudo -S -p '' -u gaokuangda -g docker "+command
        data=secret+'\n'+data
    result=subprocess.run(['/usr/bin/ssh','-F',str(args.ssh_config),'-o','BatchMode=yes',
        '-o','ConnectTimeout=15',args.host+'_lan',command],input=data,text=True,capture_output=True,timeout=180)
    if result.returncode:
        error=result.stderr.replace(secret,'[REDACTED]') if secret else result.stderr
        raise RuntimeError('CPU transport/operation failed; recover original stage before any retry: '+error[-1800:])
    receipt=json.loads(result.stdout)
    with args.output.open('x') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:receipt.get(k) for k in ('status','host','stage','container_state','log_tail')}))


if __name__=='__main__': main()
