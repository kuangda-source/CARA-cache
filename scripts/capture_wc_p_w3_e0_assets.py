"""Collect existing28 tensors on CPU once via SSH stdin; remote filesystem read-only."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
READER = "scripts/audit_wc_p_w3_e0_remote_cpu.py"
CAPTURES = (
    ("SOURCE_PHASE16", "reports/wc_source_phase16_live_or_terminal_capture_20261012.json", 16),
    ("N1_INVENTORY_ONLY", "reports/wc_math_n1_live_or_terminal_capture_20261012.json", 12),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet():
    groups = []; inputs = {}
    for kind, name, count in CAPTURES:
        path = ROOT / name
        capture = json.loads(path.read_text())
        points = capture['final']['points']
        if len(points) != count or len({p['raw_artifact']['path'] for p in points}) != count:
            raise ValueError('All original unique raw files required')
        if not capture['payload_verified'] or capture['post_exit']['exit_code'] != 0:
            raise ValueError('Accepted original CPU/source receipt required')
        groups.append({'kind': kind, 'stage': capture['stage'], 'output': capture['output'],
                       'source_revision': capture['runner']['source_revision'],
                       'runner_sha256': capture['runner_sha256'], 'final_sha256': capture['final_sha256'],
                       'points': points})
        inputs[name] = sha(path)
    spec = {'root': '/home/gaokuangda/data/gkd/worldcache_omr', 'groups': groups,
            'CPU_only': True, 'new_teacher_calls': 0, 'remote_writes': 0}
    return spec, inputs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--read-existing-assets', action='store_true')
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('New receipt path required; never overwrite prior captures')
    spec, inputs = packet()
    if not args.read_existing_assets:
        print(json.dumps({'status': 'PACKET_ONLY_NO_SSH', 'files': 28,
                          'raw_bytes': sum(p['raw_artifact']['bytes'] for g in spec['groups'] for p in g['points']),
                          'inputs': inputs, 'GPU_submissions': 0}))
        return
    code = (ROOT / READER).read_text()
    encoded = base64.b64encode(json.dumps(spec, allow_nan=False).encode()).decode()
    invocation = code + '\nimport base64\nraise SystemExit(main(json.loads(base64.b64decode(' + repr(encoded) + '))))\n'
    cmd = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes', 'gkd_minchen',
           '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python', '-']
    started = time.time()
    proc = subprocess.run(cmd, input=invocation, text=True, capture_output=True, timeout=600)
    result = {'started_unix': started, 'ended_unix': time.time(), 'exit_code': proc.returncode,
              'input_sha256': {**inputs, READER: sha(ROOT / READER)}, 'stderr': proc.stderr,
              'transport': 'SSH_STDIN_NO_REMOTE_FILE_WRITE', 'estimated_CPU_seconds': [60, 180]}
    try:
        result['remote'] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result['unparsed_stdout'] = proc.stdout
    with args.output.open('xb') as f:
        f.write(gzip.compress(json.dumps(result, ensure_ascii=False, allow_nan=False).encode(), mtime=0))
    remote = result.get('remote', {})
    print(json.dumps({'receipt': str(args.output), 'exit_code': proc.returncode, 'status': remote.get('status'),
                      'error': remote.get('error'), 'CPU_wall_seconds': remote.get('CPU_wall_seconds'),
                      'groups': [{'kind': g['kind'], 'points': len(g['points'])} for g in remote.get('groups', [])]}))
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
