#!/usr/bin/env python3
"""Read only six original warm artifacts in a separate CPU analysis stage."""
import argparse
import ast
import gc
import gzip
import hashlib
import importlib.util
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage', type=Path, required=True)
    a = p.parse_args()
    start = time.time()
    stage = a.stage.resolve()
    registration = json.loads((stage / 'registration.json').read_text())
    for name, digest in registration['payload_sha256'].items():
        assert sha(stage / name) == digest, name
    plan = json.loads((stage / 'manifests/wc_drop1_saved_warm_step21_CPU_plan_20261017.json').read_text())
    assert sha(stage / plan['plan_ref']) == plan['plan_sha256']
    capture_path = stage / 'reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz'
    capture = json.loads(gzip.decompress(capture_path.read_bytes()))
    accepted = json.loads((stage / 'reports/wc_drop1_full18_independent_acceptance_20261018.json').read_text())
    assert accepted['accepted'] and not accepted['errors'] and accepted['capture_sha256'] == sha(capture_path)
    launch = capture['launch']
    original = Path(launch['stage']).resolve()
    project = original.parents[1]
    assert stage.parent == project / '.sync' and stage != original
    assert launch['source_revision'] == plan['original_source_revision']
    assert launch['run_id'] == plan['original_run_id'] and launch['config_sha256'] == plan['original_config_sha256']
    assert all(q['state'] in (None, 'Z', 'X') for q in capture['original_processes'].values())
    output = project / 'outputs' / launch['run_id']
    originals = {
        original / 'registration.json': capture['registration_sha256'],
        output / 'runner.json': capture['runner_sha256'],
        output / 'supervisor.json': capture['supervisor_sha256'],
        output / 'billing.json': capture['billing_sha256'],
        original / 'post-CPU-exit.json': capture['post_exit_sha256'],
        original / 'production-CPU-result.json': capture['production_CPU_sha256'],
        original / 'configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json': launch['config_sha256'],
    }
    for path, digest in originals.items():
        assert sha(path) == digest, str(path)
    old_reg = json.loads((original / 'registration.json').read_text())
    assert old_reg == capture['registration'] and old_reg['source_revision'] == plan['original_source_revision']
    for name in ('scripts/run_wc_drop1_full18_r1.py', 'src/wcomr/drop1_full18_r1.py', 'src/wcomr/mid_coverage.py'):
        assert sha(original / name) == old_reg['payload_sha256'][name]
    sup = json.loads((output / 'supervisor.json').read_text())
    assert sup['child_exit_code'] == 0 and capture['post_exit']['exit_code'] == 0
    assert capture['billing']['status'] == 'DROP1_ACTUAL_GPU_BILL'
    assert accepted['actual_GPUh'] == capture['billing']['actual_GPUh']
    ledger = project / 'reports/gpu-budget-v2.json'
    ledger_before = sha(ledger)
    pool = json.loads(ledger.read_text())
    assert not any(q['status'] == 'RESERVED_OR_RUNNING' for q in pool['jobs'].values()), 'Defer CPU analysis while GPU work is registered'
    config = json.loads((original / 'configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json').read_text())
    request = config['requests'][0]
    assert request['name'] == plan['scene'] and request['seed'] == plan['seed'] == 0
    assert capture['runner']['config_sha256'] == launch['config_sha256']
    assert capture['production_CPU']['source_revision'] == plan['original_source_revision']
    assert capture['production_CPU']['config_sha256'] == launch['config_sha256']
    assert len(capture['final']['rows']) == 18
    os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    assert not torch.cuda.is_initialized()
    def forbidden(*args, **kwargs):
        raise RuntimeError('Saved-tensor CPU analysis prohibits CUDA and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    spec = importlib.util.spec_from_file_location('saved_warm_math', stage / 'src/wcomr/drop1_warm21_analysis_r1.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tiny = json.loads((stage / 'reports/wc_drop1_saved_warm21_math_local_CPU_preparation_20261017.json').read_text())
    assert tiny['accepted'] and tiny['actual_tests'] == 5 and not tiny['real_saved_warm_tensors_read']
    assert tiny['source_sha256']['src/wcomr/drop1_warm21_analysis_r1.py'] == sha(stage / 'src/wcomr/drop1_warm21_analysis_r1.py')
    # Execute only the original hash function, not the generator imports/module.
    tree_source = (original / 'src/wcomr/mid_coverage.py').read_text()
    tree_node = next(n for n in ast.parse(tree_source).body if isinstance(n, ast.FunctionDef) and n.name == 'tree_digest')
    namespace = dict(hashlib=hashlib, torch=torch, np=np, Mapping=Mapping)
    exec(compile(ast.Module(body=[tree_node], type_ignores=[]), '<original-bound-tree-digest>', 'exec'), namespace)
    tree_digest = namespace['tree_digest']
    rows = {r['id']: r for r in capture['final']['rows']}
    positions, rounds, errors = [], [], []
    for repeat in (1, 2):
        predictions, group = {}, {}
        for method in module.METHODS:
            key = f'warm_{repeat}_{method}'
            slot = dict(id=key, method=method, round=repeat, status='UNAVAILABLE_RETAINED', local_error=None)
            positions.append(slot)
            try:
                row = rows[key]
                assert row['section'] == 'WARMUP' and row['scene'] == plan['scene'] and row['round'] == repeat and row['method'] == method
                assert row['status'] == 'COMPLETE' and row['solver_steps'] == row['guided_pairs'] == 36
                assert row['semantic_plan'] == config['plans'][method]
                artifact = row['warm_guided_artifact']
                path = Path(artifact['path']).resolve()
                assert path == output / key / 'warm-guided.pt'
                assert path.stat().st_size == artifact['bytes'] and sha(path) == artifact['sha256']
                payload = torch.load(path, map_location='cpu', weights_only=True)
                assert set(payload) == {'guided'}
                guides = payload['guided']
                digest = tree_digest(guides)
                assert digest == row['warm_guided_tree_sha256']
                predictions[method] = guides
                group[method] = row
                slot.update(status='ORIGINAL_FILE_SHA_TREE_AND_METADATA_VERIFIED', artifact=artifact,
                            tree_sha256=digest, original_status=row['status'], outputs=len(guides))
            except Exception as e:
                slot['local_error'] = type(e).__name__ + ': ' + str(e)
                errors.append(dict(id=key, error=slot['local_error']))
        if len(predictions) == 3:
            comparison = module.compare_round(predictions, group, expected_shape=plan['expected_guided_shape'],
                                              validated_same_input=True, torch=torch)
            rounds.append(dict(round=repeat, **comparison))
            if not comparison['same_state_verified']:
                errors.append(dict(round=repeat, reasons=comparison['reasons']))
        else:
            rounds.append(dict(round=repeat, status='MISSING_OR_FAILED_ORIGINAL_POSITION_RETAINED',
                               absolute_guided_MSE_C=None, absolute_guided_MSE_A=None))
        del predictions, group
        if 'payload' in locals(): del payload
        if 'guides' in locals(): del guides
        gc.collect()
    repeat_trees = {method: len({p['tree_sha256'] for p in positions if p['method'] == method and 'tree_sha256' in p}) == 1
                    and sum(p['method'] == method and 'tree_sha256' in p for p in positions) == 2
                    for method in module.METHODS}
    if not all(repeat_trees.values()):
        errors.append(dict(original_all36_repeat_trees_equal=repeat_trees))
    unchanged = all(sha(path) == digest for path, digest in originals.items())
    assert unchanged and not torch.cuda.is_initialized()
    result = dict(status='SAVED_WARM6_UPDATE21_REAL_CPU_COMPLETE' if not errors else 'SAVED_WARM6_CPU_FAILURES_OR_GAPS_RETAINED',
        accepted=not errors, errors=errors, source_revision=registration['source_revision'],
        original_source_revision=plan['original_source_revision'], original_run=plan['original_run_id'],
        original_capture_sha256=sha(capture_path), original_config_sha256=launch['config_sha256'],
        analysis_registration_sha256=sha(stage / 'registration.json'),
        original_metadata_unchanged=unchanged, positions=positions, rounds=rounds,
        original_all36_repeat_trees_equal=repeat_trees,
        original_positions_denominator=6, guided_per_position=36, independent_inputs=1,
        same_input_basis='ORIGINAL_SOURCE_BOUND_SEEDED_REQUEST_COMPLETESTATE_RESTORE_PLUS_BIT_EQUAL_GUIDED_PREFIX',
        direct_latent_input_snapshot_saved=False, actual_solver_update=21,
        CFG_or_propagation_gain_applied_again=False, new_teacher_calls=0, new_generator_runs=0,
        model_weights_loaded=0, GPU_submissions=0, new_GPUh=0, CUDA_initialized=False,
        ledger_written=False, ledger_sha256_before=ledger_before, ledger_sha256_after=sha(ledger),
        CPU_wall_seconds=time.time() - start, main_card_acceptance_changed=False,
        local_MSE_is_endpoint_LPIPS=False, original_warm_timing_used_as_speed_result=False)
    destination = stage / 'result.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, allow_nan=False))
    raise SystemExit(0 if result['accepted'] else 1)


if __name__ == '__main__':
    main()
