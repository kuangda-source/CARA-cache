"""Verify downloaded public assets against pinned official HF tree metadata.

LFS objects use SHA256; ordinary Git blobs include the Git length/type prefix.
No model loading, network requests, or GPU use.
"""
import argparse
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath

PATTERNS = ['*.json', '*.safetensors', '*.txt', '*.model', '*.tiktoken']


def verify(root, entry):
    relative = PurePosixPath(entry['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe metadata path')
    path = root / str(relative)
    result = {'path': str(relative), 'status': 'MISSING'}
    if not path.is_file(): return result
    size = path.stat().st_size
    result['bytes'] = size
    if size != entry['size']:
        result['status'] = 'SIZE_MISMATCH'; return result
    lfs = entry.get('lfs')
    digest = hashlib.sha256() if lfs else hashlib.sha1()
    if not lfs: digest.update(f'blob {size}\0'.encode())
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b''): digest.update(chunk)
    actual = digest.hexdigest()
    expected = lfs['oid'] if lfs else entry['git_blob_oid']
    result.update(digest=actual, algorithm='sha256' if lfs else 'git-blob-sha1',
                  status='PASS' if actual == expected else 'HASH_MISMATCH')
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--repo', required=True)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    lock = json.loads(a.manifest.read_text())[a.repo]
    root = a.cache / ('models--' + a.repo.replace('/', '--')) / 'snapshots' / lock['revision']
    entries = [x for x in lock['files'] if any(fnmatch.fnmatch(x['path'], pat) for pat in PATTERNS)]
    if not entries: raise ValueError('No expected inference assets in manifest')
    files = [verify(root, item) for item in entries]
    state = {'repo_id': a.repo, 'revision': lock['revision'], 'metadata_source': lock['source'],
             'status': 'HASH_VERIFIED_NOT_LOAD_TESTED' if all(x['status'] == 'PASS' for x in files) else 'INCOMPLETE_OR_CORRUPT',
             'files': files, 'gpu_workload_started': False}
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps(state, indent=2)+'\n')
    print(json.dumps({'repo_id': a.repo, 'status': state['status'], 'files': len(files)}))
    return 0 if state['status'] == 'HASH_VERIFIED_NOT_LOAD_TESTED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
