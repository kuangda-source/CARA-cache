"""Lifecycle capture CPU validation; no GPU execution or mutation."""
import argparse
import inspect
import sys
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess

from cara_budget_endpoint_cpu_hosts_r1 import ROOT, PARENTS, NEW_FILES, REMOTE
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_budget_cpu_resources_r2 import bind_cpu_limits, HOST_CONFIG

STAGES={'four_card':'cara-budget-lifecycle-CPU-ada-r2-20261030',
        'two_card':'cara-budget-lifecycle-CPU-a6000-r2-20261030'}
from cara_two_card_transport_r1 import password
PARENTS={'four_card':'reports/cara_budget_endpoint_four_card_CPU_terminal_capture_r2_20261030.json'}
NEW_FILES=NEW_FILES+('src/wcomr/cara_budget_original_handles_r1.py',
    'src/wcomr/cara_budget_lifecycle_r1.py','src/wcomr/cara_budget_lifecycle_capture_r1.py',
    'tests/test_cara_budget_lifecycle_r1.py','tests/test_cara_budget_lifecycle_capture_r1.py',
    'scripts/check_cara_budget_lifecycle_cpu_r1.py')

NEW_FILES=NEW_FILES+('src/wcomr/__init__.py', 'src/wcomr/cara_budget_cpu_resources_r2.py', 'src/wcomr/cara_fast_b36_capture_r1.py', 'src/wcomr/cara_fast_b36_execution_r1.py', 'src/wcomr/cara_fast_b36_r1.py', 'src/wcomr/cara_fast_b36_terminal_r1.py', 'src/wcomr/cara_fast_binding_r2.py', 'src/wcomr/cara_fast_capture_r2.py', 'src/wcomr/cara_fast_collection_r2.py', 'src/wcomr/cara_fast_execution_r2.py', 'src/wcomr/cara_fast_post_r2.py', 'src/wcomr/cara_fast_scoring_manifest_r2.py', 'src/wcomr/cara_fast_spec_r1.py', 'src/wcomr/cara_fast_terminal_r2.py', 'src/wcomr/gpu_budget_pool_v2.py', 'src/wcomr/policy_asset_price_review_r1.py', 'src/wcomr/policy_generator_r1/__init__.py', 'src/wcomr/policy_generator_r1/interval_grammar.py', 'src/wcomr/policy_interval_assets_r1.py', 'src/wcomr/policy_price_refresh_contract_r1.py', 'src/wcomr/policy_price_terminal_r1.py', 'src/wcomr/wc73_exclusive_r1.py', 'src/wcomr/wc73_execution_r1.py')

OLD=""" for n,encoded in p['files'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
"""
NEW=""" for n,expected in p['hashes'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(p['files'][n]) if n in p['files'] else (base/n).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==expected,'Original inherited or uploaded CPU source differs: '+n
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
"""
if REMOTE.count(OLD)!=1:
    raise ValueError('Original bounded CPU source-copy block changed')
DELTA_REMOTE=REMOTE.replace(OLD,NEW).replace('check_cara_budget_endpoint_cpu_r1.py','check_cara_budget_lifecycle_cpu_r1.py')
ANCHOR=" assert '--gpus' not in cmd and 'CUDA_VISIBLE_DEVICES=' in cmd"
assert DELTA_REMOTE.count(ANCHOR)==1
DELTA_REMOTE=inspect.getsource(bind_cpu_limits)+'\n'+DELTA_REMOTE.replace(
    ANCHOR, " cmd=bind_cpu_limits(cmd)\n"+ANCHOR)
DELTA_REMOTE=DELTA_REMOTE.replace('assert mem>=8*2**30',
    "assert mem>=p['minimum_available_memory_GiB']*2**30")
DELTA_REMOTE=DELTA_REMOTE.replace("source_identity='EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY',",
    "source_identity='EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY',expected_host_config=p['expected_host_config'],original_endpoint_stage=str(base),")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','capture'])
    parser.add_argument('--host',choices=['four_card'],required=True)
    parser.add_argument('--ssh-config',type=Path,required=True)
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.binding.exists(): raise ValueError('Fresh control binding and launch receipt required')
    if args.ssh_config.stat().st_mode&0o077: raise ValueError('Private SSH configuration must remain0600')
    intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_LIFECYCLE_CPU_FRAGMENT_R2.json').read_text())
    if intent['stages']!=STAGES: raise ValueError('Original CPU stages differ')
    for name,expected in intent['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Original frozen CPU source changed: '+name)
    parent=json.loads((ROOT/PARENTS[args.host]).read_text())
    original=parent['registration']['payload_sha256']
    paths=sorted(set(original)|set(NEW_FILES))
    raw={name:(ROOT/name).read_bytes() for name in paths}
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in raw.items()}
    upload={name:base64.b64encode(data).decode() for name,data in raw.items() if hashes[name]!=original.get(name)}
    binding=dict(status='LIFECYCLE_CPU_RESOURCE_AND_SOURCE_BOUND_BEFORE_REMOTE_CALL',host=args.host,
        stage_name=STAGES[args.host],action=args.action,expected_host_config=HOST_CONFIG,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(DELTA_REMOTE.encode()).hexdigest(),full_payload_sha256=hashes,
        uploaded_files=len(upload),reused_parent_files=len(paths)-len(upload),
        uploaded_raw_bytes=sum(len(raw[n]) for n in upload),full_raw_bytes=sum(map(len,raw.values())),
        base_registration_sha256=parent['registration_sha256'],GPU_submissions=0)
    with args.binding.open('x') as stream:json.dump(binding,stream,indent=2);stream.write('\n')
    payload=dict(action=args.action,host=args.host,stage_name=STAGES[args.host],
        expected_host_config=HOST_CONFIG,minimum_available_memory_GiB=56 if args.host=='two_card' else 8,
        base_stage=parent['launch']['stage'],base_registration_sha256=parent['registration_sha256'],
        parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        files=upload,hashes=hashes)
    interpreter='python3' if args.host=='four_card' else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote(DELTA_REMOTE)
    data=json.dumps(payload);secret=None
    if args.host=='two_card':
        secret=password();command="sudo -S -p '' -u gaokuangda -g docker "+command;data=secret+'\n'+data
    target='four_card' if args.host=='four_card' else 'two_card_lan'
    child=subprocess.Popen(['/usr/bin/ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=15',
        target,command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err=child.communicate(data.encode(),timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGTERM);child.communicate()
        raise RuntimeError('CPU preparation transport unknown; recover this original stage before any new prepare') from None
    if child.returncode:
        message=err.decode(errors='replace');message=message.replace(secret,'[REDACTED]') if secret else message
        raise RuntimeError('CPU preparation failed; recover original stage: '+message[-1600:])
    receipt=json.loads(out)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(receipt))


if __name__=='__main__': main()
