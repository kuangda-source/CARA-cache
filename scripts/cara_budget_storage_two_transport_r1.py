"""Launch once or capture the fixed two-card storage preparation process."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from cara_two_card_transport_r1 import password

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = 'scripts/provision_cara_budget_two_storage_r1.py'
REMOTE = r'''
import base64,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
control=root/'.sync/cara-budget-storage-provision-two-r1-20261031'
cpu=root/'.sync/cara-budget-two-card-policy-CPU-a6000-r1-20261031'
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(cpu/'registration.json')=='cee04693f585c3089614febe71078d409112b1d73df93d847292a261b2be3181'
reg=json.loads((cpu/'registration.json').read_text())
for name in ('src/wcomr/history104_storage_r2.py','src/wcomr/cara_budget_original_handles_r1.py','src/wcomr/gpu_budget_pool_v2.py'):
 assert sha(cpu/name)==reg['payload_sha256'][name]
sys.path.insert(0,str(cpu/'src'))
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
if p['action']=='launch':
 assert not control.exists() and not control.is_symlink(),'Original preparation exists: capture only'
 raw=base64.b64decode(p['operator']);assert hashlib.sha256(raw).hexdigest()==p['operator_sha256']
 control.mkdir(mode=0o700);operator=control/'operator.py';operator.write_bytes(raw)
 registration=dict(source_revision=p['source_revision'],operator_sha256=p['operator_sha256'],GPU_submissions=0,ledger_written=False)
 (control/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
 with (control/'process.log').open('x') as log:
  child=subprocess.Popen([sys.executable,str(operator)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   launch=dict(status='ORIGINAL_TWO_CARD_STORAGE_PROCESS_LAUNCHED_NO_GPU',control=str(control),identity=bind_original_process(child.pid),source_revision=p['source_revision'],operator_sha256=p['operator_sha256'],started_unix=time.time(),GPU_submissions=0,ledger_written=False)
   (control/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
   child.stdin.write(json.dumps(dict(sudo_password=p['sudo_password'])).encode());child.stdin.flush()
  finally:child.stdin.close()
 print(json.dumps(launch))
else:
 assert p['action']=='capture'
 launch=json.loads((control/'launch.json').read_text());state=control/'state.json'
 print(json.dumps(dict(status='ORIGINAL_TWO_CARD_STORAGE_CAPTURE',launch=launch,observation=observe_original_process(launch['identity']),operator_intact=sha(control/'operator.py')==launch['operator_sha256'],state=json.loads(state.read_text()) if state.exists() else None,log_tail=(control/'process.log').read_text(errors='replace')[-3000:],observed_unix=time.time(),GPU_submissions=0,ledger_written=False)))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['launch', 'capture'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert len(args.source_revision) == 40 and all(c in '0123456789abcdef' for c in args.source_revision)
    private = ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'
    assert private.stat().st_mode & 0o077 == 0
    secret = password()
    payload = dict(action=args.action, source_revision=args.source_revision)
    if args.action == 'launch':
        raw = subprocess.check_output(['git', 'show', args.source_revision+':'+OPERATOR], cwd=ROOT)
        assert raw == (ROOT/OPERATOR).read_bytes()
        payload.update(operator=base64.b64encode(raw).decode(), operator_sha256=hashlib.sha256(raw).hexdigest(),
                       sudo_password=secret)
    command = "sudo -S -p '' -u gaokuangda -g docker python3 -c "+shlex.quote(
        "import sys,json;packet=json.load(sys.stdin);exec(packet['code'])")
    packet = json.dumps(dict(code=REMOTE, arguments=payload))
    started = time.time()
    child = subprocess.Popen(['ssh', '-C', '-F', str(private), '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=30',
        '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', 'two_card_lan', command],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = child.communicate((secret+'\n'+packet).encode(), timeout=100)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGTERM)
        out, err = child.communicate()
    report = dict(action=args.action, source_revision=args.source_revision, started_unix=started,
        observed_unix=time.time(), exit_code=child.returncode,
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        stderr=err.decode(errors='replace').replace(secret, '[REDACTED]'),
        result=json.loads(out) if child.returncode == 0 else None,
        recovery_only_on_unknown=True, GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode, result=report['result'])))


if __name__ == '__main__':
    main()
