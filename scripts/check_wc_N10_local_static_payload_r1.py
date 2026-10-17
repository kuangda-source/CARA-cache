#!/usr/bin/env python3
"""Materialize/check existing local N10 code and tokenizer, without models or SSH."""
import argparse
import ast
import concurrent.futures
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PACK = 'reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json'
LAUNCHER = 'scripts/launch_wc_N10_models_cpu_r1.py'
PROBE = 'scripts/evaluate_wc_N10_metric_model_cpu_r1.py'
TOKENIZER = '.sync/wc-N10-official-tokenizer-pinned-r1-20261016/bpe_simple_vocab_16e6.txt.gz'
RESOURCE_AUDIT = 'reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json'


def constant(path, name):
    nodes = ast.parse(path.read_text()).body
    matches = [n.value for n in nodes if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    assert len(matches) == 1
    return ast.literal_eval(matches[0])


def metadata(path):
    s = path.stat()
    ghost = bool(getattr(s, 'st_flags', 0) & 0x40000000
                 or s.st_size > 0 and getattr(s, 'st_blocks', 1) == 0)
    return dict(bytes=s.st_size, blocks=getattr(s, 'st_blocks', None),
                flags=getattr(s, 'st_flags', None), placeholder=ghost)


def safe(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Bound static resource path must remain relative')
    path = root / str(p)
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Bound static resource path escaped its root')
    return path


def run(materialize):
    start = time.time()
    pack_raw = (ROOT / PACK).read_bytes()
    pack = json.loads(pack_raw)
    assert pack['official_commit'] == 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
    assert pack['registered_files'] == pack['verified_files'] == len(pack['records']) == 216
    assert pack['failure_count'] == 0
    git_files = constant(ROOT / LAUNCHER, 'GIT_FILES')
    roles = constant(ROOT / PROBE, 'ROLES')
    bpe_sha = constant(ROOT / PROBE, 'BPE_SHA')
    weights = constant(ROOT / PROBE, 'WEIGHTS')
    assert set(roles) == set(weights) == {'DINO', 'AMT_S', 'RAFT_THINGS', 'ViCLIP', 'MUSIQ_SPAQ'}
    source_root = safe(ROOT, pack['source_root'])
    selected = [(name, safe(ROOT, name), None) for name in git_files]
    selected += [('upstream/' + r['path'], safe(source_root, r['path']), r) for r in pack['records']]
    selected.append(('cache/ViCLIP/bpe_simple_vocab_16e6.txt.gz', ROOT / TOKENIZER, None))
    assert len({name for name, _, _ in selected}) == len(selected)
    before = {name: metadata(path) for name, path, _ in selected}
    ghosts = [(name, path) for name, path, _ in selected if before[name]['placeholder']]
    hydration = []
    if materialize:
        def request(pair):
            name, path = pair
            c = subprocess.run(['brctl', 'download', str(path)], capture_output=True, timeout=10)
            return dict(name=name, exit_code=c.returncode, stderr=c.stderr.decode(errors='replace'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            hydration = list(pool.map(request, ghosts))
        if any(r['exit_code'] != 0 for r in hydration):
            raise ValueError('Local materialization request failed; no file content was replaced')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    queries = ''.join(revision + ':' + name + '\n' for name in git_files)
    import io
    blobs = io.BytesIO(subprocess.check_output(['git', 'cat-file', '--batch'], input=queries.encode(), cwd=ROOT))
    committed = {}
    for name in git_files:
        header = blobs.readline().decode().split()
        assert len(header) == 3 and header[1] == 'blob'
        b = blobs.read(int(header[2])); assert blobs.read(1) == b'\n'
        committed[name] = b
    records = []
    for name, path, expected in selected:
        b = path.read_bytes(); sha = hashlib.sha256(b).hexdigest()
        if name in committed:
            assert committed[name] == b, 'Uncommitted production source: ' + name
        elif expected is not None:
            assert len(b) == expected['bytes'] == expected['expected_bytes']
            assert sha == expected['sha256']
            assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == expected['expected_git_blob_sha1']
        else:
            assert len(b) == 1356917 and sha == bpe_sha
        after = metadata(path)
        assert not after['placeholder'], 'Read resource still unavailable locally: ' + name
        records.append(dict(name=name, local_path=str(path.relative_to(ROOT)), bytes=len(b),
            sha256=sha, before=before[name], after=after))
    audit_raw = (ROOT / RESOURCE_AUDIT).read_bytes()
    audit = json.loads(audit_raw)['observation']
    assert len(audit['resources']) == 4
    for r in audit['resources']:
        assert (r['bytes'], r['sha256']) == weights[r['role']]
    return dict(status='N10_LOCAL_STATIC_CODE_TOKENIZER_MATERIALIZED_NOT_MODEL_RUNTIME', accepted=True,
        source_revision=revision, official_VBench_commit=pack['official_commit'],
        source_pack_ref=PACK, source_pack_sha256=hashlib.sha256(pack_raw).hexdigest(),
        existing_server_resource_audit_ref=RESOURCE_AUDIT,
        existing_server_resource_audit_sha256=hashlib.sha256(audit_raw).hexdigest(),
        project_Git_source_files=len(git_files), official_code_files=216, tokenizer_files=1,
        local_static_files=len(records), verified_bytes=sum(r['bytes'] for r in records),
        initially_placeholder_files=len(ghosts), local_materialization_requests=hydration,
        materialization_acceptance_uses_actual_bytes_and_hashes_not_request_exit_only=True,
        records=records, roles=list(roles), declared_weight_bytes_and_SHA=weights,
        server_DINO_cached_sources_still_require_fresh_check=len(audit['DINO_cached_python_sources']),
        server_resource_relay_complete=False, five_model_CPU_accepted=False,
        complete_transport_payload_selected=False, model_resource_paths_synthesized=False,
        upstream_code_executed=False, model_weights_loaded=0, real_quality_scores=0,
        neural_framework_imported=False, GPU_submissions=0, SSH_queries=0, ledger_written=False,
        wall_seconds=time.time() - start)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--materialize-icloud', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError('Preserve the original static preparation receipt')
    value = run(a.materialize_icloud)
    a.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in value.items() if k not in ('records', 'local_materialization_requests')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
