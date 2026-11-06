#!/usr/bin/env python3
"""Compare pure sampling/parser helpers with pinned author source, no models."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.automatic_quality_r1 import DIMENSIONS, VBENCH_COMMIT, sampling_spec, vbench_metadata


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def author_function(path, name, *, class_name=None):
    tree = ast.parse(path.read_text())
    if class_name:
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
        assert len(classes) == 1
        tree = classes[0]
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1 and not nodes[0].decorator_list
    namespace = dict(np=np, random=random, json=json)
    # Only the selected pure helper is executed; no upstream imports/model constructors.
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(nodes[0])],
                                                      type_ignores=[])), str(path), 'exec'), namespace)
    return namespace[name], namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.artifacts.exists() and not args.output.exists()
    args.artifacts.mkdir(parents=True)
    started = time.time()
    inventory = ROOT / 'reports/wc_paper_N10_source_and_resource_readiness_inventory_20261016.json'
    source = json.loads(inventory.read_text())
    assert source['official_commit'] == VBENCH_COMMIT
    identities = {}
    for item in source['official_source_files']:
        path = args.source_root / item['path']
        assert sha(path) == item['sha256']
        identities[item['path']] = sha(path)
    util = args.source_root / 'vbench/utils.py'
    get_indices, _ = author_function(util, 'get_frame_indices')
    middle = [int(i) for i in get_indices(8, 93, sample='middle', input_fps=16)]
    assert middle == sampling_spec('overall_consistency')['frame_indices']
    extract_dynamic, _ = author_function(args.source_root / 'vbench/dynamic_degree.py',
                                         'extract_frame', class_name='DynamicDegree')
    dynamic = extract_dynamic(None, list(range(93)), interval=max(1, round(16 / 8)))
    assert dynamic == sampling_spec('dynamic_degree')['frame_indices']
    extract_amt, _ = author_function(args.source_root / 'vbench/motion_smoothness.py',
                                     'extract_frame', class_name='FrameProcess')
    assert extract_amt(None, list(range(93)), start_from=0) == sampling_spec('motion_smoothness')['frame_indices']
    assert extract_amt(None, list(range(93)), start_from=1) == sampling_spec('motion_smoothness')['target_indices']
    fixture_path = ROOT / 'tests/test_automatic_quality_r1.py'
    spec = importlib.util.spec_from_file_location('synthetic_quality_CPU_only', fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    cases, methods, generation, evaluator, bundle, _ = fixture.fixture()
    loader, globals_ = author_function(util, 'load_dimension_info')
    load_json, _ = author_function(util, 'load_json')
    globals_['load_json'] = load_json
    metadata_checks = []
    for dimension in DIMENSIONS:
        if dimension == 'MUSIQ_LONGER512':
            continue  # Project full93 scorer, not an upstream VBench dimension alias.
        metadata = vbench_metadata(bundle, dimension)
        path = args.artifacts / (dimension + '.json')
        path.write_text(json.dumps(metadata, indent=2) + '\n')
        videos, prompts = loader(str(path), dimension, 'en')
        expected = [r for r in bundle['rows'] if r['dimension'] == dimension and r['input_status'] == 'READY_TO_SCORE']
        assert len(videos) == len(set(videos)) == len(expected)
        assert set(videos) == {r['video_path'] for r in expected}
        assert {p['prompt'] for p in prompts} == {r['prompt'] for r in expected}
        metadata_checks.append(dict(dimension=dimension, explicit_prompt_groups=len(prompts),
            explicit_video_positions=len(videos), filename_text_inference=False,
            upstream_parser_exact_prompt_and_paths_equal=True, metadata_ref=str(path), metadata_sha256=sha(path)))
    assert 'torch' not in sys.modules
    result = dict(status='N10_PINNED_PURE_SAMPLING_AND_PROMPT_METADATA_CPU_PASS_NOT_METRIC_MODEL',
        official_commit=VBENCH_COMMIT, verified_source_files=identities,
        source_inventory_ref=str(inventory.relative_to(ROOT)), source_inventory_sha256=sha(inventory),
        source_sampling_checks=dict(overall_middle8=middle, dynamic47=dynamic,
            AMT_even_input_frames=47, AMT_odd_comparison_frames=46),
        metadata_checks=metadata_checks, synthetic_generation_positions=len(generation),
        synthetic_metric_positions=len(bundle['rows']), final_inputs_selected=False,
        pure_helper_AST_only=True, whole_VBench_imported=False, Torch_imported=False,
        metric_model_CPU_accepted=False, weights_loaded=0, scoring_card_selected=False,
        new_real_videos_generated=0, real_quality_results_generated=0,
        GPU_submissions=0, SSH_queries=0, ledger_written=False,
        CPU_wall_seconds=time.time() - started,
        implementation_sha256={str(p.relative_to(ROOT)): sha(p) for p in (
            ROOT/'src/wcomr/automatic_quality_r1.py', fixture_path, Path(__file__).resolve())})
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in (
        'verified_source_files', 'implementation_sha256', 'metadata_checks', 'source_sampling_checks')}))


if __name__ == '__main__':
    main()
