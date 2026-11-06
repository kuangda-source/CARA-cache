#!/usr/bin/env python3
"""Materialize pinned Guardrail NLTK bytes without weakening NLTK path checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

MANIFEST_SHA = 'd43349c4e6b5e31d4f34d600f21c8d49d94cf35b63bd9bb50b05341a37a07571'
RESOURCE_REL = 'runtime-resources/nltk-guardrail-d6d4bfa8-r1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root, manifest, physical):
    root = Path(root)
    if physical and (root.is_symlink() or root.resolve() != root.absolute()):
        raise ValueError('NLTK data root must be a physical directory')
    expected = manifest['files']
    paths = [p for p in root.rglob('*') if p.is_file()]
    actual = {p.relative_to(root).as_posix() for p in paths}
    if actual != set(expected):
        raise ValueError('NLTK resource inventory differs')
    if physical and any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('NLTK data cannot contain symbolic links')
    for name, spec in expected.items():
        p = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe resource path')
        if p.stat().st_size != spec['bytes'] or sha(p) != spec['sha256']:
            raise ValueError('NLTK resource bytes differ: ' + name)
    return len(paths)


def materialize(project, manifest_path):
    project = Path(project).resolve()
    manifest_path = Path(manifest_path)
    if sha(manifest_path) != MANIFEST_SHA:
        raise ValueError('Only the frozen Guardrail NLTK manifest is accepted')
    manifest = json.loads(manifest_path.read_text())
    hub = project / 'cache/huggingface/hub/models--nvidia--Cosmos-Guardrail1'
    source = hub / 'snapshots' / manifest['revision'] / manifest['subdirectory']
    inventory(source, manifest, physical=False)
    for name in manifest['files']:
        if os.path.commonpath([str((source / name).resolve()), str(hub.resolve())]) != str(hub.resolve()):
            raise ValueError('Source escaped the pinned model cache')
    destination = project / RESOURCE_REL
    receipt = destination.with_suffix('.manifest.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        inventory(destination, manifest, physical=True)
        if not receipt.is_file() or receipt.is_symlink() or sha(receipt) != MANIFEST_SHA:
            raise ValueError('Existing materialization has no matching physical receipt')
        return {'status': 'EXISTING_EXACT_NLTK_MATERIALIZATION', 'root': str(destination)}
    with tempfile.TemporaryDirectory(prefix='.nltk-materialize-', dir=destination.parent) as temp:
        staged = Path(temp) / 'data'
        shutil.copytree(source, staged, symlinks=False)
        inventory(staged, manifest, physical=True)
        for p in staged.rglob('*'):
            if p.is_file():
                p.chmod(0o444)
        staged.rename(destination)
    with receipt.open('xb') as stream:
        stream.write(manifest_path.read_bytes())
    receipt.chmod(0o444)
    return {'status': 'PINNED_NLTK_MATERIALIZED', 'root': str(destination),
            'manifest_sha256': MANIFEST_SHA, 'files': len(manifest['files']),
            'bytes': sum(v['bytes'] for v in manifest['files'].values()),
            'source_modified': False, 'guardrail_disabled': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(materialize(args.project, args.manifest)))
