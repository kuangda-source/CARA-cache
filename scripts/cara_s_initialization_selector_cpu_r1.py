"""Prepare/capture one isolated selector CPU stage; never access GPU outputs."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from cara_budget_calibration_cpu_hosts_r3 import REMOTE as BASE_REMOTE
from cara_two_card_transport_r1 import password
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG

STAGE = 'cara-S-init-selector-CPU-a6000-r1-20261031'
CONTRACT = 'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_SELECTOR_CPU_R1_20261031.json'
OVERLAY = ('src/wcomr/cara_s_initialization_audit_r1.py',
           'scripts/check_cara_s_initialization_selector_cpu_r1.py', CONTRACT)
BASE_CAPTURE = 'reports/cara_budget_successor_CPU_capture_r4_20261031.json'
BASE_ACCEPTED = 'reports/cara_budget_successor_CPU_accepted_r2_20261031.json'
LIMITS = dict(HOST_CONFIG, CpusetCpus='26')
assert BASE_REMOTE.count('cmd=bind_cpu_limits(cmd)') == 1
REMOTE = BASE_REMOTE.replace('check_cara_budget_calibration_cpu_r3.py',
    'check_cara_s_initialization_selector_cpu_r1.py').replace('cmd=bind_cpu_limits(cmd)',
    "cmd=bind_cpu_limits(cmd);cmd[2:2]=['--cpuset-cpus','26']")


def main(*, stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
         work_seconds=180, exit_seconds=30):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare','capture'])
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    p = dict(action=args.action, host='two_card', stage_name=stage)
    if args.action == 'prepare':
        raw_base = (ROOT/BASE_CAPTURE).read_bytes()
        accepted = json.loads((ROOT/BASE_ACCEPTED).read_text())
        assert accepted['capture_sha256'] == hashlib.sha256(raw_base).hexdigest()
        assert accepted['total_controls_passed'] == 113
        base = json.loads(raw_base)['result']
        raw = {n:subprocess.check_output(['git','show',args.source_revision+':'+n],cwd=ROOT) for n in overlay}
        assert all((ROOT/n).read_bytes() == b for n,b in raw.items())
        hashes = {**base['registration']['payload_sha256'], **{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
        p.update(base_stage=base['launch']['stage'],base_registration_sha256=base['registration_sha256'],
                 parent_git_revision=args.source_revision,expected_host_config=LIMITS,minimum_available_memory_GiB=8,
                 files={n:base64.b64encode(b).decode() for n,b in raw.items()},
                 overlay_sha256={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()},
                 full_mapping_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    wrapper = """import json,sys,hashlib,io
from pathlib import Path
p=json.load(sys.stdin)
if p['action']=='prepare':
 b=Path(p['base_stage'])/'registration.json';assert hashlib.sha256(b.read_bytes()).hexdigest()==p['base_registration_sha256']
 p['hashes']={**json.loads(b.read_text())['payload_sha256'],**p.pop('overlay_sha256')}
 assert hashlib.sha256(json.dumps(p['hashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==p.pop('full_mapping_sha256')
sys.stdin=io.StringIO(json.dumps(p))
"""
    remote = wrapper+'\nexec('+repr(remote_code)+')\n'
    remote = "import io,sys,gzip,base64,json,hashlib\nsaved=sys.stdout;sys.stdout=io.StringIO()\nexec("+repr(remote)+")\nraw=sys.stdout.getvalue().encode();sys.stdout=saved\nprint(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),sha256=hashlib.sha256(raw).hexdigest())))\n"
    secret = password()
    command = "sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote("import sys,json,io,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));sys.stdin=io.StringIO(json.dumps(packet['payload']));exec(packet['code'])")
    encoded = base64.b64encode(gzip.compress(json.dumps(dict(code=remote,payload=p)).encode())).decode()
    binding = dict(action=args.action,host='two_card',stage_name=stage,source_revision=args.source_revision,
        started_unix=time.time(),expected_host_config=LIMITS,work_seconds=work_seconds,exit_seconds=exit_seconds,
        remote_code_sha256=hashlib.sha256(remote.encode()).hexdigest(),transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        payload_sha256=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest(),GPU_submissions=0,ledger_written=False)
    with args.output.with_name(args.output.stem+'_binding.json').open('x') as stream:
        json.dump(binding,stream,indent=2);stream.write('\n')
    child = subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),
        '-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err = child.communicate((secret+'\n'+encoded).encode(),timeout=110)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    result = None
    if child.returncode == 0:
        wrapped=json.loads(out);body=gzip.decompress(base64.b64decode(wrapped['gzip_base64']))
        assert hashlib.sha256(body).hexdigest()==wrapped['sha256'];result=json.loads(body)
    report=dict(binding,observed_unix=time.time(),exit_code=child.returncode,result=result,
                stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),unknown_requires_original_capture=True)
    with args.output.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,status=(result or {}).get('status'),
        container_state=(result or {}).get('container_state'),stderr=report['stderr'][-1000:])))


if __name__ == '__main__':
    main()
