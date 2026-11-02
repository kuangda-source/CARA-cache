"""Restore lost original ledger-only cache bytes; never prepare or dispatch a card."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import base64,fcntl,hashlib,json,os,pathlib,time
p=packet;root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
run='cara-source-lifecycle-V1-P1-full146-r1-20261102'
source=pathlib.Path('/tmp/source-lifecycle-P1-central-operator-a2b1dcf993774897902a5f0cc0858220')
sha=lambda body:hashlib.sha256(body).hexdigest()
ledger_path=root/'reports/gpu-budget-v2.json'
assert ledger_path.is_file() and not ledger_path.is_symlink()
before=sha(ledger_path.read_bytes());ledger=json.loads(ledger_path.read_bytes())
reservation=json.loads((root/'reports'/(run+'.central-reservation.json')).read_bytes())
assert reservation==p['original_envelope'],'Original reservation differs'
assert all(ledger['jobs'][run][k]==reservation['job'][k] for k in p['identity_keys'])
assert ledger['jobs'][run]['status'] in ('RESERVED_OR_RUNNING','SETTLED')
assert ledger['cap_gpu_hours']>=250 and len(p['expected'])==len(p['files_base64'])==115
with source.with_name(source.name+'.restore.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if not source.exists():
  staging=source.with_name(source.name+'.original-restore')
  staging.mkdir(mode=0o700,exist_ok=True);assert not staging.is_symlink()
  for name,h in p['expected'].items():
   relative=pathlib.Path(name)
   assert not relative.is_absolute() and '..' not in relative.parts and relative.suffix=='.py'
   body=base64.b64decode(p['files_base64'][name],validate=True);assert sha(body)==h
   target=staging/name;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():assert not target.is_symlink() and target.read_bytes()==body
   else:
    with target.open('xb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
  assert {str(f.relative_to(staging)) for f in staging.rglob('*') if f.is_file()}==set(p['expected'])
  os.rename(staging,source)
 assert source.is_dir() and not source.is_symlink()
 assert all(not (source/n).is_symlink() and sha((source/n).read_bytes())==h for n,h in p['expected'].items())
 assert sha(ledger_path.read_bytes())==before,'Concurrent ledger change: recover original transaction'
 result=dict(status='ORIGINAL_LEDGER_OPERATOR_CACHE_EXACT_BYTES_RESTORED',source=str(source),
  original_operator_ref=p['original_operator_ref'],original_operator_sha256=p['original_operator_sha256'],
  original_launch_id=reservation['job']['launch_id'],source_files=115,source_sha256=p['expected'],
  ledger_before_sha256=before,ledger_after_sha256=sha(ledger_path.read_bytes()),
  ledger_written=False,GPU_submissions=0,new_operator_or_card_prepared=False,restored_unix=time.time())
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    sys.path.insert(0, str(ROOT/'src'))
    from wcomr.immutable_stage_payload_r1 import local_python_closure
    from wcomr.cara_source_lifecycle_p1_central_r1 import validate_authority
    from wcomr.cara_s_endpoint_lifecycle_r1 import JOB_IDENTITY
    load = lambda name: json.loads((ROOT/name).read_bytes())
    auth = load('plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json')
    validate_authority(auth, Path('/data20t/gaokuangda/worldcache_workspace'))
    diagnosis = load('reports/cara_v1_P1_quarter_central_cache_readonly_r1_20261102.json')
    assert diagnosis['exit_code'] == 0 and diagnosis['result']['exists'] is False
    proof = load('reports/cara_v1_P1_whole_CPU_memory50_accepted_r2_20261102.json')
    expected = local_python_closure(ROOT, ['src/wcomr/cara_source_lifecycle_p1_central_r1.py'])
    assert len(expected) == 115 and all(proof['payload_sha256'][n] == h for n,h in expected.items())
    original_ref = 'reports/cara_v1_P1_central_operator_ready_r1_20261102.json'
    original = load(original_ref)
    assert original['exit_code'] == 0 and original['result']['operator_source_files'] == 115
    payload = dict(expected=expected,files_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in expected},
        original_envelope=load('reports/cara_v1_P1_memory50_central_reservation_r1_20261102.json')['result']['envelope'],
        identity_keys=list(JOB_IDENTITY),original_operator_ref=original_ref,
        original_operator_sha256=hashlib.sha256((ROOT/original_ref).read_bytes()).hexdigest())
    private = ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'
    assert private.stat().st_mode & 0o077 == 0
    code = "import json,sys;packet=json.load(sys.stdin);exec("+repr(REMOTE)+")"
    started = time.time()
    try:
        child = subprocess.run(['ssh','-C','-F',str(private),'-o','BatchMode=yes','-o','ConnectTimeout=30',
            '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','four_card_lan',
            'python3 -c '+shlex.quote(code)],input=json.dumps(payload),text=True,capture_output=True,timeout=100)
        receipt = dict(exit_code=child.returncode,result=json.loads(child.stdout) if child.returncode==0 else None,
            stderr=child.stderr,started_unix=started,observed_unix=time.time())
    except subprocess.TimeoutExpired:
        receipt = dict(exit_code=None,result=None,status='ORIGINAL_CACHE_RESTORE_UNKNOWN_RECOVER_SAME_PATH',
            started_unix=started,observed_unix=time.time())
    receipt.update(operator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest())
    with args.output.open('x') as stream:
        json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=receipt['exit_code'],status=(receipt['result'] or {}).get('status'),
        stderr=receipt.get('stderr','')[-1500:])))


if __name__ == '__main__':
    main()
