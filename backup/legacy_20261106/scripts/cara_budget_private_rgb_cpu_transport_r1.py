"""One two-card CPU IO probe, bound to the accepted private filesystem."""
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
sys.path.insert(0, str(ROOT/'src'))
from cara_budget_calibration_cpu_hosts_r3 import REMOTE as ORIGINAL
from cara_two_card_transport_r1 import password
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG

STAGE = 'cara-budget-private-RGB-CPU-a6000-r1-20261031'
WORKER = 'scripts/check_cara_budget_private_RGB_io_r1.py'
BASE_REF = 'reports/cara_budget_two_card_policy_CPU_capture_r1_20261031.json'
VOLUME = '/data20t/gaokuangda/worldcache_workspace/outputs/cara-budget-calibration-14gpuh-r1-20261030'
BACKING = '/data20t/gaokuangda/worldcache_workspace/.sync/storage-reservations/budget-calibration-r1'
JOURNAL = '/home/gaokuangda/cara_control/budget-calibration-r1'
MOUNTS = [(VOLUME, 'rw'), (BACKING, 'ro'), (JOURNAL, 'ro')]
PROVISION_SHA = '6f0e02cbc722ed85d312adae957079026fd78ecd6888bca632399e9d4bf60484'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'capture'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    revision = args.source_revision
    assert len(revision) == 40 and all(c in '0123456789abcdef' for c in revision)
    base = json.loads((ROOT/BASE_REF).read_text())['result']
    raw = subprocess.check_output(['git', 'show', revision+':'+WORKER], cwd=ROOT)
    worker_sha = hashlib.sha256(raw).hexdigest()
    hashes = dict(base['registration']['payload_sha256'], **{WORKER: worker_sha})
    remote = ORIGINAL.replace('check_cara_budget_calibration_cpu_r3.py', Path(WORKER).name)
    remote = remote.replace('registration=reg,', 'registration=None,container_mounts=con["Mounts"],')
    needle = ' cmd=bind_cpu_limits(cmd)'
    assert remote.count(needle) == 1
    insert = '\n'.join([
        ' mount_args='+repr([arg for path, mode in MOUNTS for arg in ('-v', path+':'+path+':'+mode)]),
        " position=cmd.index('--entrypoint');cmd[position:position]=mount_args",
        needle])
    remote = remote.replace(needle, insert)
    needle = ' stage.mkdir(mode=0o700)'
    assert remote.count(needle) == 1
    remote = remote.replace(needle,
        ' assert sha('+repr(BACKING+'/provision.json')+')=='+repr(PROVISION_SHA)+'\n'+needle)
    payload = dict(action=args.action, host='two_card', stage_name=STAGE)
    if args.action == 'prepare':
        assert raw == (ROOT/WORKER).read_bytes()
        payload.update(base_stage=base['launch']['stage'],
            base_registration_sha256=base['registration_sha256'], parent_git_revision=revision,
            hashes=hashes, files={WORKER: base64.b64encode(raw).decode()},
            expected_host_config=HOST_CONFIG, minimum_available_memory_GiB=8)
    code = ('import io,sys,json,gzip,base64,hashlib\n'
        'sys.stdin=io.StringIO('+repr(json.dumps(payload))+')\n'
        'saved=sys.stdout;sys.stdout=io.StringIO()\nexec('+repr(remote)+')\n'
        'raw=sys.stdout.getvalue().encode();sys.stdout=saved\n'
        'print(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),raw_sha256=hashlib.sha256(raw).hexdigest())))\n')
    secret = password()
    command = "sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote('import sys;exec(sys.stdin.read())')
    private = ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'
    assert private.stat().st_mode & 0o077 == 0
    started = time.time()
    child = subprocess.Popen(['ssh', '-C', '-F', str(private), '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=35', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
        'two_card_lan', command], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = child.communicate((secret+'\n'+code).encode(), timeout=100)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGTERM)
        out, err = child.communicate()
    result = None
    if child.returncode == 0:
        wrapped = json.loads(out)
        decoded = gzip.decompress(base64.b64decode(wrapped['gzip_base64']))
        assert hashlib.sha256(decoded).hexdigest() == wrapped['raw_sha256']
        result = json.loads(decoded)
        if args.action == 'capture':
            reg = dict(host='two_card', stage=result['launch']['stage'], payload_sha256=hashes,
                runtime_source_sha256=base['registration']['runtime_source_sha256'],
                parent_git_revision=revision, source_identity='EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY',
                expected_host_config=HOST_CONFIG, original_endpoint_stage=base['launch']['stage'],
                base_registration_sha256=base['registration_sha256'])
            assert hashlib.sha256((json.dumps(reg, indent=2)+'\n').encode()).hexdigest() == result['registration_sha256']
            result['registration'] = reg
            result['registration_reconstructed_and_bound_to_remote_SHA'] = True
    report = dict(action=args.action, host='two_card', stage=STAGE, source_revision=revision,
        started_unix=started, observed_unix=time.time(), exit_code=child.returncode, result=result,
        stderr=err.decode(errors='replace').replace(secret, '[REDACTED]'),
        remote_code_sha256=hashlib.sha256(code.encode()).hexdigest(),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        recovery_only_on_unknown=True, work_seconds=180, exit_seconds=30,
        GPU_submissions=0, four_card_contacted=False)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode, state=(result or {}).get('container_state'),
        status=(result or {}).get('status'), log_tail=(result or {}).get('log_tail'))))


if __name__ == '__main__':
    main()
