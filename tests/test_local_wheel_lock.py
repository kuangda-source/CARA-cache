"""Test transport rewrites against the actual frozen93 graph, using fake paths.

These fixtures are not downloaded payload or environment compatibility proof.
"""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from wcomr.local_wheel_lock import bind_local_wheels, blocks, canonical, parse

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    text = (ROOT / 'manifests/l0_native_environment_resolved_requirements_20261001.txt').read_text()
    parent = json.loads((ROOT / 'reports/l0_native_env_resolve_r2_terminal_audit_20261001.json').read_text())
    manifest = json.loads((ROOT / 'manifests/l0_native_transitive_binary_sources_20261001.json').read_text())
    versions = {n:r['version'] for n,r in parent['packages'].items()}
    rows = []
    for row in manifest['files']:
        rows.append(dict(row, path='/synthetic/' + row['filename'],actual_sha256=row['official_sha256'],
                         metadata={'package':row['package'],'version':row['version']}))
    return text, rows, versions


def test_actual93_graph_only_six_transport_blocks_change():
    original, rows, versions = inputs()
    output, changed = bind_local_wheels(original, rows, versions)
    before = {canonical(parse(b)[0].name):b for b in blocks(original) if b.strip()}
    after = {canonical(parse(b)[0].name):b for b in blocks(output) if b.strip()}
    assert len(before) == len(after) == 93 and before.keys() == after.keys()
    assert {n for n in before if before[n] != after[n]} == set(changed) == {r['package'] for r in rows}
    assert all(before[n] == after[n] for n in before.keys() - changed.keys())
    for row in rows:
        req, hashes = parse(after[row['package']])
        assert req.url.startswith('file:///synthetic/') and hashes == [row['official_sha256']]


@pytest.mark.parametrize('mutation', ['wheel_version','digest','nonreplaced_version_map'])
def test_inconsistent_graph_or_local_identity_rejected(mutation):
    original, rows, versions = inputs()
    rows, versions = deepcopy(rows), deepcopy(versions)
    if mutation == 'wheel_version':rows[0]['version'] = '999.0'
    elif mutation == 'digest':rows[0]['actual_sha256'] = rows[0]['official_sha256'] = '0' * 64
    else:versions['numpy'] = '2.0.0'
    with pytest.raises(ValueError):bind_local_wheels(original, rows, versions)
