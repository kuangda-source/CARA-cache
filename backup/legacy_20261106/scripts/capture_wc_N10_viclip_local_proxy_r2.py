#!/usr/bin/env python3
"""One ETA-gated local resource collection; no model, SSH or budget writes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def worker_identity(stage,launch,reg):
    name=launch.get('worker_file','fetch_wc_N10_viclip_resource_r1.py')
    assert name in ('fetch_wc_N10_viclip_resource_r1.py','fetch_wc_N10_viclip_ranges_r1.py',
                    'fetch_wc_N10_viclip_direct_r2.py')
    assert sha(stage/name)==launch['worker_sha256']==reg['worker_sha256']
    if name=='fetch_wc_N10_viclip_direct_r2.py':
        expected='abed3996e5552680aefb1c63f179c3c394ea4b2abb4fb0e0a1812c3be611dee4'
        assert sha(stage/'fetch_wc_N10_viclip_ranges_r1.py')==reg['original_range_worker_sha256']==expected
        assert reg['transport_policy']==launch['transport_policy']=='DIRECT_HTTPS_NO_ENV_PROXY'
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    launch = json.loads(args.launch_ref.read_text())
    now = time.time()
    if now < launch['first_collection_not_before_unix']:
        raise SystemExit('Before original local resource ETA; do not query its PID or files')
    stage = Path(launch['stage'])
    assert stage.resolve().parent == ROOT / '.sync' and not stage.is_symlink()
    registration = stage / 'registration.json'
    assert sha(registration) == launch['registration_sha256']
    reg = json.loads(registration.read_text())
    assert reg['source_revision'] == launch['source_revision']
    assert reg['expected_weight'] == launch['expected_weight']
    worker_name = worker_identity(stage,launch,reg)
    process = subprocess.run(['ps', '-p', str(launch['pid']), '-o', 'pid=,lstart=,stat=,command='],
                             capture_output=True, text=True, timeout=10)
    same, alive = None, False
    if process.stdout.strip():
        date = r'\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4}'
        before = re.match(r'^\d+\s+(' + date + r')\s+(.*)$', launch['process_at_admission'])
        actual = re.match(r'^\s*\d+\s+(' + date + r')\s+(\S+)\s+(.*)$', process.stdout.strip())
        assert before and actual
        marker = str(stage/worker_name)
        same = (' '.join(before[1].split()) == ' '.join(actual[1].split())
                and marker in before[2] and marker in actual[3]
                and before[2].split(marker, 1)[1] == actual[3].split(marker, 1)[1])
        alive = bool(same and actual[2][0] not in ('Z', 'X'))
    result_path = stage / 'resource-result.json'
    data, parse_error = None, None
    if result_path.is_file():
        try:
            data = json.loads(result_path.read_text())
        except (ValueError, UnicodeError) as error:
            parse_error = str(error)
    progress_path = stage/'range-progress.json'
    progress = json.loads(progress_path.read_text()) if progress_path.is_file() else None
    expected = launch['expected_weight']
    target = stage / expected['name']
    partial = stage / (expected['name'] + '.part')
    assert not target.is_symlink() and not partial.is_symlink()
    digest = sha(target) if not alive and target.is_file() else None
    count = target.stat().st_size if target.is_file() else None
    accepted = bool(not alive and data and not parse_error
        and data.get('source_revision') == launch['source_revision']
        and data.get('status') == 'N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME'
        and data.get('exit_code') == 0 and data.get('target') == str(target)
        and data.get('actual_bytes') == count == expected['bytes']
        and data.get('actual_sha256') == digest == expected['sha256'])
    value = dict(status='N10_LOCAL_PROXY_RESOURCE_ORIGINAL_ONCE_CAPTURE', observed_unix=now,
        launch=launch, launch_ref=str(args.launch_ref), launch_sha256=sha(args.launch_ref),
        original_process_alive=alive, PID_identity_matches=same, process_stdout=process.stdout,
        registration_sha256=sha(registration), result=data, result_parse_error=parse_error,
        result_sha256=sha(result_path) if result_path.is_file() else None,
        range_progress=progress,
        local_resource_bytes_independently_accepted=accepted,
        target_exists=target.is_file(), independent_target_bytes=count,
        independent_target_sha256=digest, partial_bytes=partial.stat().st_size if partial.is_file() else None,
        log_tail=(stage/'resource.log').read_text(errors='replace')[-6000:] if (stage/'resource.log').is_file() else None,
        server_resource_transferred=False, GPU_submissions=0, models_imported=False,
        weights_loaded=0, ledger_written=False, SSH_queries=0)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: value[k] for k in ('status', 'original_process_alive',
        'local_resource_bytes_independently_accepted', 'independent_target_bytes', 'partial_bytes')}))


if __name__ == '__main__':
    main()
