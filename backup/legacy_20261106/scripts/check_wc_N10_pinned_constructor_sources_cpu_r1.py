#!/usr/bin/env python3
"""Verify acquired metric source and definition-time resource side effects only."""
import argparse
import ast
import copy
from contextlib import redirect_stdout
import gzip
import hashlib
import html
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

import yaml

COMMIT = 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nodes(path, names):
    tree = ast.parse(path.read_text())
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    assert sorted(n.name for n in selected) == sorted(names)
    return ast.fix_missing_locations(ast.Module(body=copy.deepcopy(selected), type_ignores=[]))


def tokenizer_definition_probe(source):
    """Execute exact author function/class definitions, not model/tokenizer init."""
    selected = nodes(source, ['default_bpe', 'SimpleTokenizer'])
    observations = []
    with tempfile.TemporaryDirectory() as directory:
        cache = Path(directory); target = cache / 'ViCLIP/bpe_simple_vocab_16e6.txt.gz'
        for present in (False, True):
            if present:
                target.parent.mkdir(); target.write_bytes(b'SYNTHETIC_EXISTENCE_ONLY_NOT_VALID_VOCAB')
            calls = []
            def block(command, *args, **kwargs):
                calls.append(command)
                raise RuntimeError('SYNTHETIC_BLOCKED_DOWNLOAD_NO_PROCESS_CREATED')
            namespace = dict(os=os, subprocess=subprocess, CACHE_DIR=str(cache), gzip=gzip, html=html)
            with patch.object(subprocess, 'run', side_effect=block), redirect_stdout(io.StringIO()):
                if not present:
                    try: exec(compile(selected, str(source), 'exec'), namespace)
                    except RuntimeError as error:
                        assert str(error) == 'SYNTHETIC_BLOCKED_DOWNLOAD_NO_PROCESS_CREATED'
                    else: raise AssertionError('Expected the original default expression to request wget')
                    assert len(calls) == 1 and calls[0][0] == 'wget'
                    assert calls[0][1] == 'https://raw.githubusercontent.com/openai/CLIP/main/clip/bpe_simple_vocab_16e6.txt.gz'
                    assert not target.exists()
                else:
                    exec(compile(selected, str(source), 'exec'), namespace)
                    assert calls == []
                    assert namespace['SimpleTokenizer'].__init__.__defaults__[0] == str(target)
            observations.append(dict(synthetic_existence_fixture=present,
                definition_time_download_requests=len(calls), request_executed=False,
                tokenizer_instance_constructed=False, actual_vocabulary_validated=False))
    return dict(source_definition_nodes=['default_bpe', 'SimpleTokenizer'],
        observations=observations, full_upstream_module_imported=False,
        conclusion='The original constructor default calls default_bpe while defining the class; preload and verify resources before importing this module, not only before scoring.')


def amt_dynamic_builder_probe(root):
    """Use the original parser/builder; stand-in constructor never loads weights."""
    config_path = root / 'vbench/third_party/amt/cfgs/AMT-S.yaml'
    builder = root / 'vbench/third_party/amt/utils/build_utils.py'
    config = yaml.safe_load(config_path.read_text())['network']
    module_name, class_name = config['name'].rsplit('.', 1)
    actual_source = root / 'vbench/third_party/amt' / (module_name.replace('.', '/') + '.py')
    assert actual_source.is_file() and class_name == 'Model'
    calls = []; sentinel = object()
    def constructor(**params):
        calls.append(params); return sentinel
    namespace = dict(importlib=importlib)
    exec(compile(nodes(builder, ['base_build_fn', 'build_from_cfg']), str(builder), 'exec'), namespace)
    with patch.object(importlib, 'import_module', return_value=SimpleNamespace(Model=constructor)) as imported:
        assert namespace['build_from_cfg'](config) is sentinel
    imported.assert_called_once_with(module_name, package=None)
    assert calls == [config['params']]
    return dict(network_name=config['name'], config_ref=str(config_path), config_sha256=sha(config_path),
        builder_ref=str(builder), builder_sha256=sha(builder), resolved_source_ref=str(actual_source),
        resolved_source_sha256=sha(actual_source), original_import_request=module_name,
        actual_model_constructed=False, declared_constructor_stand_in=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    started = time.time(); pack = json.loads(args.pack_ref.read_text()); root = Path(pack['source_root'])
    assert pack['status'] == 'N10_PINNED_CODE_RESOURCE_PACK_VERIFIED_NOT_RUNTIME'
    assert pack['official_commit'] == COMMIT and pack['failure_count'] == 0
    assert len(pack['records']) == pack['registered_files'] == pack['verified_files'] == 216
    verified = {}
    for row in pack['records']:
        path = root / row['path']; raw = path.read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['expected_git_blob_sha1']
        verified[row['path']] = row['sha256']
        if path.suffix == '.py': compile(raw, str(path), 'exec')  # Parse only; no upstream imports.
    old = json.loads((ROOT / 'reports/wc_paper_N10_source_and_resource_readiness_inventory_20261016.json').read_text())
    assert all(verified[row['path']] == row['sha256'] for row in old['official_source_files'])
    tokenizer = tokenizer_definition_probe(root / 'vbench/third_party/ViCLIP/simple_tokenizer.py')
    amt = amt_dynamic_builder_probe(root)
    assert 'torch' not in sys.modules
    result = dict(status='N10_PINNED_SOURCE_AND_CONSTRUCTOR_BOUNDARY_CPU_ACCEPTED_NOT_MODEL_RUNTIME',
        official_commit=COMMIT, pack_ref=str(args.pack_ref), pack_sha256=sha(args.pack_ref),
        pinned_code_files_verified=len(verified), original_nine_source_identities_preserved=True,
        compiled_python_sources=sum(n.endswith('.py') for n in verified),
        tokenizer_definition_probe=tokenizer, AMT_dynamic_builder_probe=amt,
        actual_server_cached_resource_SHA_verified=False, actual_metric_model_CPU_accepted=False,
        upstream_full_package_imported=False, real_quality_scores_generated=False,
        source_pack_suffices_for_all_external_runtime_dependencies=False,
        Torch_imported=False, weights_loaded=0, weights_downloaded=0, real_download_subprocesses=0,
        implementation_sha256={str(Path(__file__).relative_to(ROOT)): sha(Path(__file__).resolve())},
        CPU_wall_seconds=time.time()-started, original_N05_queried=False,
        SSH_queries=0, GPU_submissions=0, server_environment_changed=False, server_ledger_written=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tokenizer_definition_probe','AMT_dynamic_builder_probe','implementation_sha256')}))


if __name__ == '__main__': main()
