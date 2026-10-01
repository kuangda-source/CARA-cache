"""Derive the original93 hash lock with six audited wheels as local URLs.

No dependency version changes, resolver run, installation or native import.
"""
import argparse
import hashlib
import json
from pathlib import Path
from wcomr.local_wheel_lock import bind_local_wheels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--original-audit', type=Path, required=True)
    parser.add_argument('--transitive-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new derived lock path')
    original = args.original.read_text()
    parent = json.loads(args.original_audit.read_text())
    audit = json.loads(args.transitive_audit.read_text())
    original_sha = hashlib.sha256(original.encode()).hexdigest()
    if original_sha != parent['phase']['requirements_sha256'] or original_sha != audit['source_requirements_sha256']:
        raise ValueError('Original graph attestation differs')
    if audit['status'] != 'ALL6_TRANSITIVE_FRESH_OFFICIAL_SHA_AND_METADATA_PASS_NOT_INSTALLED' or len(audit['files']) != 6:
        raise ValueError('Complete fresh six-wheel audit required')
    expected = {name: row['version'] for name, row in parent['packages'].items()}
    text, changed = bind_local_wheels(original, audit['files'], expected)
    expected_names = {'nvidia-cublas-cu12','nvidia-cudnn-cu12','nvidia-cusolver-cu12','nvidia-cusparse-cu12','nvidia-nccl-cu12','triton'}
    if set(changed) != expected_names:
        raise ValueError('Six-wheel scope differs')
    # Linux/Python3.11 is the frozen target; these wheels' dependency metadata
    # must remain satisfied by the full original graph, including file URLs.
    from packaging.requirements import Requirement
    from packaging.markers import default_environment
    target = default_environment()
    target.update(python_version='3.11',python_full_version='3.11.15',implementation_version='3.11.15',
                  implementation_name='cpython',platform_python_implementation='CPython',
                  os_name='posix',sys_platform='linux',platform_machine='x86_64',platform_system='Linux',extra='')
    checked = []
    for row in audit['files']:
        for raw in row['metadata']['requires_dist']:
            req = Requirement(raw)
            if req.marker and not req.marker.evaluate(target):
                continue
            name = req.name.lower().replace('_','-')
            if name not in expected or not req.specifier.contains(expected[name],prereleases=True):
                raise ValueError('Selected wheel dependency differs from the original graph')
            checked.append(raw)
    args.output.write_text(text)
    receipt = {'status':'DERIVED93_LOCAL6_HASH_LOCK_NOT_INSTALLED',
               'derivation':'Transport-only rewrite of original frozen93 graph; no new resolver run',
               'original_requirements_sha256':original_sha,
               'requirements_sha256':hashlib.sha256(text.encode()).hexdigest(),
               'original_audit_sha256':hashlib.sha256(args.original_audit.read_bytes()).hexdigest(),
               'transitive_audit_sha256':hashlib.sha256(args.transitive_audit.read_bytes()).hexdigest(),
               'package_count':93,'versions':expected,'replacements':changed,
               'wheel_dependency_metadata_satisfied':checked,'gpu_workload_started':False}
    args.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'package_count':93,'replacement_count':len(changed)}))


if __name__ == '__main__':
    main()
