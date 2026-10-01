"""Bind attested local wheels into an existing version/hash-frozen graph."""
import re
from pathlib import Path
from packaging.requirements import Requirement


def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def blocks(text):
    result, pending = [], ''
    for line in text.splitlines(keepends=True):
        pending += line
        if not line.rstrip().endswith('\\'):
            result.append(pending)
            pending = ''
    if pending:
        raise ValueError('Incomplete requirements continuation')
    return result


def parse(block):
    parts = block.replace('\\\n', '').split('--hash=sha256:')
    requirement = Requirement(parts[0].strip())
    hashes = [part.strip() for part in parts[1:]]
    if not hashes or any(not re.fullmatch('[0-9a-f]{64}', h) for h in hashes):
        raise ValueError('Every dependency must retain valid hashes')
    return requirement, hashes


def bind_local_wheels(text, rows, expected_versions, expected_count=93):
    """Leave every non-replaced block byte-identical; retain package versions.

    Callers must separately verify the actual wheel bytes and audit identity.
    This function changes transport references, and does not run a resolver.
    """
    if len(expected_versions) != expected_count:
        raise ValueError('Frozen graph population differs')
    replacements = {canonical(r['package']): r for r in rows}
    if len(replacements) != len(rows):
        raise ValueError('Duplicate local binary identity')
    seen, changed, output = set(), {}, []
    for block in blocks(text):
        if not block.strip():
            output.append(block)
            continue
        req, hashes = parse(block)
        name = canonical(req.name)
        if name in seen or name not in expected_versions:
            raise ValueError('Dependency coverage differs')
        seen.add(name)
        if not req.url and str(req.specifier) != '==' + expected_versions[name]:
            raise ValueError('Frozen graph version mapping differs')
        if name not in replacements:
            output.append(block)
            continue
        row = replacements[name]
        version = expected_versions[name]
        if req.url or str(req.specifier) != '==' + version or row['version'] != version:
            raise ValueError('Local binding changes a frozen version')
        if canonical(row['metadata']['package']) != name or row['metadata']['version'] != version:
            raise ValueError('Actual wheel metadata differs')
        digest = row['official_sha256']
        if row['actual_sha256'] != digest or digest not in hashes:
            raise ValueError('Local binary digest is outside the original hash lock')
        path = Path(row['path'])
        if not path.is_absolute() or path.name != row['filename'] or not path.name.endswith('.whl'):
            raise ValueError('Invalid attested local wheel path')
        output.append(name + ' @ ' + path.as_uri() + ' \\\n    --hash=sha256:' + digest + '\n')
        changed[name] = {'version': version, 'official_sha256': digest, 'local_url': path.as_uri()}
    if seen != set(expected_versions) or set(changed) != set(replacements):
        raise ValueError('Frozen graph coverage or replacement scope differs')
    return ''.join(output), changed
