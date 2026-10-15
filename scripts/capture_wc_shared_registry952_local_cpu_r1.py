#!/usr/bin/env python3
"""One local original-handle collection after ETA, with no SSH or relaunch."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    launch = json.loads(args.launch_ref.read_text())
    now = time.time()
    if now < launch['first_collection_not_before_unix']:
        raise ValueError('Before original complete952 CPU ETA; do not inspect partial artifacts')
    process = subprocess.run(['ps', '-p', str(launch['pid']), '-o', 'pid=,lstart=,stat=,command='],
                             capture_output=True, text=True, timeout=10)
    alive = bool(process.stdout.strip())
    same = None
    if alive:
        date = r'\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4}'
        before = re.match(r'^\d+\s+(' + date + r')\s+(.*)$', launch['process_at_admission'])
        actual = re.match(r'^\s*\d+\s+(' + date + r')\s+(\S+)\s+(.*)$', process.stdout.strip())
        assert before and actual
        same = (' '.join(before[1].split()) == ' '.join(actual[1].split()) and before[2] == actual[3])
        alive = bool(same and actual[2][0] not in ('Z', 'X'))
    source = ROOT / launch['test_source_ref']
    files = {}
    for ref in (launch['result_ref'], launch['exit_ref'],
                str(Path(launch['result_ref']).with_suffix('.failure.json'))):
        path = ROOT / ref
        data, error = None, None
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except ValueError as problem:
                error = str(problem)
        files[ref] = dict(exists=path.exists(), sha256=sha(path) if path.exists() else None,
                          data=data, parse_error=error)
    outputs = []
    for path in sorted((ROOT / launch['artifacts_ref']).rglob('*.mp4')):
        try:
            data, error = json.loads(path.read_text()), None
        except (ValueError, UnicodeError) as problem:
            data, error = None, str(problem)
        outputs.append(dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                            sha256=sha(path), data=data, error=error))
    log = ROOT / launch['log_ref']
    result = dict(status='SHARED_REGISTRY952_ORIGINAL_LOCAL_CPU_ONCE_CAPTURE',
        at_unix=now, launch=launch, launch_ref=str(args.launch_ref), launch_sha256=sha(args.launch_ref),
        original_handle_confirmed_live_now=alive, PID_identity_matches=same, process_stdout=process.stdout,
        payload_verified={name: (source / name).is_file() and sha(source / name) == digest
                          for name, digest in launch['payload_sha256'].items()},
        registration_sha256=sha(ROOT / launch['registration_ref']), files=files,
        mock_outputs=outputs, log_tail=log.read_text(errors='replace')[-18000:] if log.exists() else None,
        GPU_submissions=0, SSH_queries=0, ledger_written=False)
    args.output.write_bytes(gzip.compress(json.dumps(result, indent=2).encode(), mtime=0))
    print(json.dumps(dict(status=result['status'], original_handle_confirmed_live_now=alive,
        result_exists=files[launch['result_ref']]['exists'], exit_exists=files[launch['exit_ref']]['exists'],
        mock_outputs=len(outputs))))


if __name__ == '__main__':
    main()
