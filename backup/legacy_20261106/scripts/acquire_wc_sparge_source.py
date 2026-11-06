#!/usr/bin/env python3
"""Acquire a fixed complete upstream tree, validating every Git blob, without executing it."""
import argparse
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath


def fetch(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'worldcache-source-acquisition'})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('download limit exceeded')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-lock', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    if any(p.exists() for p in [args.destination, args.manifest, args.archive]):
        raise ValueError('preserve existing acquisition; inspect it instead of restarting')
    selected = json.loads(args.selected_lock.read_text())
    commit = selected['commit']
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('invalid fixed commit')
    base = 'https://api.github.com/repos/thu-ml/SpargeAttn/git/trees/'
    tree = json.loads(fetch(base + commit + '?recursive=1', 2 * 1024 * 1024))
    if tree.get('truncated') or any(x['type'] not in ['blob', 'tree'] for x in tree['tree']):
        raise ValueError('incomplete tree or submodule')
    blobs = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
    if any(x['mode'] not in ['100644', '100755'] for x in blobs.values()):
        raise ValueError('symlink or unsupported source mode')
    archive_url = 'https://codeload.github.com/thu-ml/SpargeAttn/tar.gz/' + commit
    archive = fetch(archive_url, 64 * 1024 * 1024)
    payloads = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        total = 0
        for member in tar:
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError('archive contains nonregular member')
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or len(path.parts) < 2:
                raise ValueError('unsafe archive path')
            name = str(PurePosixPath(*path.parts[1:]))
            if name not in blobs or name in payloads or member.size != blobs[name]['size']:
                raise ValueError('unexpected, duplicate or wrong-sized member: ' + name)
            total += member.size
            if total > 80 * 1024 * 1024:
                raise ValueError('expanded source limit exceeded')
            data = tar.extractfile(member).read()
            git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if git_sha != blobs[name]['sha']:
                raise ValueError('Git blob mismatch: ' + name)
            payloads[name] = data
    if set(payloads) != set(blobs):
        raise ValueError('archive does not cover complete Git tree')
    for name, entry in selected['files'].items():
        if hashlib.sha256(payloads[name]).hexdigest() != entry['sha256']:
            raise ValueError('selected source identity differs: ' + name)
    args.destination.mkdir(parents=True)
    for name, data in payloads.items():
        path = args.destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    args.archive.write_bytes(archive)
    receipt = {
        'repository': selected['repository'], 'commit': commit,
        'git_tree_sha': tree['sha'], 'archive_url': archive_url,
        'archive_sha256': hashlib.sha256(archive).hexdigest(), 'archive_bytes': len(archive),
        'file_count': len(payloads), 'source_bytes': sum(map(len, payloads.values())),
        'selected_sources_match': True,
        'status': 'COMPLETE_GIT_BLOB_AND_SHA_SOURCE_PASS_NOT_BUILD_OR_INSTALL',
        'files': {name: {'git_blob_sha': blobs[name]['sha'], 'mode': blobs[name]['mode'],
                         'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                  for name, data in sorted(payloads.items())},
    }
    args.manifest.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['status', 'commit', 'file_count', 'source_bytes', 'archive_bytes']}))


if __name__ == '__main__':
    main()
