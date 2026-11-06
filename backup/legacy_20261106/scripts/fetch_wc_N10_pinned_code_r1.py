#!/usr/bin/env python3
"""Acquire the pinned VBench code/config tree; never import it or fetch weights."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
import urllib.request

COMMIT = 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
PREFIX = 'https://raw.githubusercontent.com/Vchitect/VBench/' + COMMIT + '/'
EXTENSIONS = ('.py', '.yaml', '.yml', '.txt', '.txt.gz', '.json')


def selected(row):
    return row['type'] == 'blob' and (
        (row['path'].startswith('vbench/') and row['path'].endswith(EXTENSIONS))
        or row['path'] in ('README.md', 'requirements.txt', 'LICENSE'))


def fetch(root, row):
    name = PurePosixPath(row['path'])
    if name.is_absolute() or '..' in name.parts or str(name) != row['path']:
        raise ValueError('Only original normalized code-tree paths allowed')
    url = PREFIX + str(name)
    record = dict(path=str(name), url=url, expected_git_blob_sha1=row['sha'], expected_bytes=row['size'])
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'WorldCache-fixed-source-audit'})
        with urllib.request.urlopen(request, timeout=30) as reply:
            data = reply.read()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != row['sha'] or len(data) != row['size']:
            raise ValueError('Original Git blob bytes differ from pinned tree')
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle: handle.write(data)
        record.update(status='VERIFIED_CODE_BYTES_ONLY', bytes=len(data), git_blob_sha1=actual,
                      sha256=hashlib.sha256(data).hexdigest())
    except BaseException as error:
        record.update(status='ACQUISITION_FAILED_RETAINED', error_type=type(error).__name__, error=str(error))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree-ref', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.source_root.exists() and not args.output.exists()
    raw = args.tree_ref.read_bytes(); tree = json.loads(raw)
    assert tree['sha'] == COMMIT and not tree.get('truncated') and tree['tree']
    entries = [r for r in tree['tree'] if selected(r)]
    assert len(entries) == len({r['path'] for r in entries}) and entries
    args.source_root.mkdir(parents=True)
    started = time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda row: fetch(args.source_root, row), entries))
    failed = [r for r in records if r['status'] != 'VERIFIED_CODE_BYTES_ONLY']
    result = dict(status='N10_PINNED_CODE_RESOURCE_PACK_VERIFIED_NOT_RUNTIME' if not failed else
        'N10_PINNED_CODE_RESOURCE_PACK_INCOMPLETE_ORIGINAL_FAILURES_RETAINED',
        official_repo='https://github.com/Vchitect/VBench', official_commit=COMMIT,
        tree_ref=str(args.tree_ref), tree_sha256=hashlib.sha256(raw).hexdigest(),
        source_root=str(args.source_root), registered_files=len(entries), verified_files=len(records)-len(failed),
        records=records, failure_count=len(failed), wall_seconds=time.time()-started,
        scope='All pinned vbench Python/config/text metadata plus root README/requirements/license; not the full repository or benchmark.',
        upstream_code_imported_or_executed=False, metric_models_loaded=False,
        model_weights_downloaded=False, real_quality_scores_generated=False,
        server_environment_changed=False, original_N05_queried=False, SSH_queries=0,
        GPU_submissions=0, server_ledger_written=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}))
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__': main()
