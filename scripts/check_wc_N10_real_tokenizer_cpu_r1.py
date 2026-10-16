#!/usr/bin/env python3
"""Real BPE/tokenizer CPU parity; explicitly not ViCLIP model or video scoring."""
import argparse
import ast
import copy
from functools import lru_cache
import gzip
import hashlib
import html
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokenizer(path, *, cache, bpe, ftfy, regex):
    """Original pure definitions, with only CACHE_DIR/import globals supplied.

    Full VBench imports need additional metric dependencies. This deliberately
    does not claim that those dependencies, model constructors or weights run.
    """
    tree = ast.parse(path.read_text())
    definitions = [copy.deepcopy(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    assert definitions and any(n.name == 'SimpleTokenizer' for n in definitions)
    namespace = dict(__file__=str(path.resolve()), os=os, subprocess=subprocess, gzip=gzip,
        html=html, lru_cache=lru_cache, ftfy=ftfy, re=regex, CACHE_DIR=str(cache.resolve()))
    with patch.object(subprocess, 'run', side_effect=AssertionError('NO_IMPLICIT_DOWNLOAD_ALLOWED')) as launch:
        exec(compile(ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[])), str(path), 'exec'), namespace)
        result = namespace['SimpleTokenizer'](str(bpe.resolve()))
    launch.assert_not_called()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pack-ref', 'tokenizer-ref', 'CLIP-source-ref', 'dependencies', 'artifacts', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists() and not args.artifacts.exists()
    started = time.time(); pack = json.loads(args.pack_ref.read_text()); asset = json.loads(args.tokenizer_ref.read_text())
    clip = json.loads(args.CLIP_source_ref.read_text()); root = Path(pack['source_root'])
    source = root/'vbench/third_party/ViCLIP/simple_tokenizer.py'
    row = next(r for r in pack['records'] if r['path'] == str(source.relative_to(root)))
    assert sha(source) == row['sha256'] and pack['official_commit'] == 'fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490'
    official = Path(clip['path']); bpe = Path(asset['tokenizer_ref'])
    assert sha(official) == clip['sha256'] and clip['commit'] == asset['tokenizer_commit']
    assert sha(bpe) == asset['tokenizer_sha256'] and bpe.stat().st_size == asset['tokenizer_bytes']
    sys.path.insert(0, str(args.dependencies.resolve()))
    import ftfy
    import regex
    import wcwidth
    assert Path(ftfy.__file__).resolve().is_relative_to(args.dependencies.resolve())
    assert Path(wcwidth.__file__).resolve().is_relative_to(args.dependencies.resolve())
    assert importlib.metadata.version('ftfy') == '6.3.1' and importlib.metadata.version('wcwidth') == '0.2.13'
    args.artifacts.mkdir(parents=True)
    cache = args.artifacts/'verified-cache'; (cache/'ViCLIP').mkdir(parents=True)
    link = cache/'ViCLIP/bpe_simple_vocab_16e6.txt.gz'; link.symlink_to(bpe.resolve())
    assert sha(link) == asset['tokenizer_sha256']
    candidate = tokenizer(source, cache=cache, bpe=bpe, ftfy=ftfy, regex=regex)
    reference = tokenizer(official, cache=cache, bpe=bpe, ftfy=ftfy, regex=regex)
    assert len(candidate.encoder) == len(reference.encoder) == 49408
    texts = ['', 'A robot pushes a blue block.', '  A ROBOT\n pushes\t a blue block.  ',
        'A person turns left, then right!', 'Two objects: red & blue.',
        'Café naïve façade', '实体在桌面上移动。', 'Video motion: ↔️ 👋', '&amp; <test>']
    rows = []
    for index, text in enumerate(texts):
        ids = candidate.encode(text); expected = reference.encode(text)
        assert ids == expected and candidate.decode(ids) == reference.decode(expected)
        rows.append(dict(id='SYNTHETIC_TEXT_'+str(index), text=text, token_ids=ids,
                         decoded=candidate.decode(ids), original_CLIP_equal=True))
    assert 'torch' not in sys.modules
    dependencies = {str(p.relative_to(args.dependencies)): sha(p)
        for p in args.dependencies.rglob('*.py') if p.is_file()}
    result = dict(status='N10_REAL_BPE_TOKENIZER_CPU_PARITY_ACCEPTED_NOT_VICLIP_MODEL',
        vbench_source_ref=str(source), vbench_source_sha256=sha(source),
        official_CLIP_source_ref=str(official), official_CLIP_source_sha256=sha(official),
        official_CLIP_commit=clip['commit'], actual_verified_BPE_sha256=sha(bpe),
        tokenizer_vocab_size=49408, synthetic_text_controls=rows,
        dependencies=dict(ftfy='6.3.1', wcwidth='0.2.13', regex=regex.__version__,
            isolated_target=str(args.dependencies), source_sha256=dependencies),
        original_source_functions_and_classes_AST_only=True,
        whole_upstream_package_imported=False, actual_metric_model_CPU_accepted=False,
        actual_semantic_video_metric_ready=False, real_quality_scores_generated=False,
        model_checkpoint_downloaded=False, model_weights_loaded=0, Torch_imported=False,
        source_and_assets_existed_before_definition=True, implicit_download_requests=0,
        shared_project_or_server_environment_changed=False, original_N05_queried=False,
        CPU_wall_seconds=time.time()-started, SSH_queries=0, GPU_submissions=0, server_ledger_written=False)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('dependencies','synthetic_text_controls')}))


if __name__ == '__main__': main()
