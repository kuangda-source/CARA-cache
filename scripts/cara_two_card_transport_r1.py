"""Scoped, key-authenticated two-card transport through the working four-card hop.

Optional Docker group applies to this process only. No account/group, SSH config,
or GPU mode is modified. The password stays in ignored storage and stdin.
"""
import json
from pathlib import Path
import shlex
import subprocess

REPO = Path(__file__).resolve().parents[1]
SECRET = REPO / '.sync/two-card-cal66-migration-20261025/credential.private.json'


def password():
    if SECRET.stat().st_mode & 0o077:
        raise ValueError('Private credential permissions must be 0600')
    return json.loads(SECRET.read_text())['sudo_password']


def ssh(code, data=None, *, docker_group=False, timeout=180):
    args = ['ssh', '-o', 'ProxyJump=four_card', '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3', 'two_card_lan']
    # The host default can be Python3.8; registered validation uses pathlib3.9+.
    interpreter = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command = shlex.quote(interpreter) + ' -c ' + shlex.quote(code)
    payload = json.dumps(data) if data is not None else ''
    if docker_group:
        command = "sudo -S -p '' -u gaokuangda -g docker " + command
        payload = password() + '\n' + payload
    result = subprocess.run(args + [command], input=payload, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        message = result.stderr
        if SECRET.exists():
            message = message.replace(password(), '[REDACTED]')
        raise RuntimeError('Two-card read/operation failed: ' + message[-1800:])
    return json.loads(result.stdout)
