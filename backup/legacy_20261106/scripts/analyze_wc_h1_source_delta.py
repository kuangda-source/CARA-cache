#!/usr/bin/env python3
"""CPU-only descriptive source perturbations from sealed H1 raw receipts.

This performs no model inference and changes neither the frozen card nor its
acceptance criteria. D, MF and S refer to held reference sources, not trajectories.
"""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def decomposition(candidate, dense, truth):
    """Exact output-space MSE identity; no linearity assumption about predictor."""
    assert candidate.shape == dense.shape == truth.shape
    totals = np.zeros(5, dtype=np.float64)
    candidate, dense, truth = [x.reshape(-1) for x in (candidate, dense, truth)]
    for start in range(0, truth.numel(), 1 << 20):
        c, d, t = [x[start:start + (1 << 20)].float().numpy().astype(np.float64)
                   for x in (candidate, dense, truth)]
        assert all(np.isfinite(x).all() for x in (c, d, t))
        drift, perturbation = d - t, c - d
        totals += [np.dot(drift, drift), np.dot(perturbation, perturbation),
                   np.dot(drift, perturbation), np.dot(c - t, c - t), np.dot(t, t)]
    common, perturbation, cross, total, energy = totals / truth.numel()
    assert energy > 0
    assert math.isclose(total, common + perturbation + 2 * cross,
                        rel_tol=1e-10, abs_tol=1e-12)
    cosine = cross / math.sqrt(common * perturbation) if common * perturbation > 0 else None
    return {'common_dense_mse': common, 'source_delta_mse': perturbation,
            'cross_term_mse': 2 * cross, 'candidate_mse': total,
            'reference_mean_square': energy,
            'source_delta_relative_rmse': math.sqrt(perturbation / energy),
            'signed_excess_relative_mse': (perturbation + 2 * cross) / energy,
            'delta_alignment_with_dense_error': cosine}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    begin = time.perf_counter()
    assert not torch.cuda.is_initialized()
    def forbidden(*unused_args, **unused_kwargs):
        raise RuntimeError('CUDA initialization forbidden in raw H1 analysis')
    torch.cuda._lazy_init = forbidden
    runner, audit = [json.loads(path.read_text()) for path in (args.runner, args.audit)]
    assert audit['status'] == 'H1_SOURCE_RAW_ERRORS_NINE_GATES_COST_RELEASE_AUDIT_PASS'
    assert runner['status'] == 'H1_SOURCE6_LOCAL18_FULL42_NINE_GATE_PASS_REQUIRES_AUDIT'
    indexed = {row['path']: row['sha256'] for row in audit['raw_checks']['checked']}
    loaded = {}
    def load(snapshot):
        path = snapshot['path']
        if path not in loaded:
            assert indexed[path] == snapshot['sha256'] == sha(path)
            value = torch.load(path, map_location='cpu', weights_only=True)
            assert set(value) == {'postwarp_residual', 'velocity'}
            for field, tensor in value.items():
                meta = snapshot['tensors'][field]
                assert list(tensor.shape) == meta['shape'] and str(tensor.dtype) == meta['dtype']
                raw = memoryview(tensor.contiguous().reshape(-1).view(torch.uint8).numpy())
                assert hashlib.sha256(raw).hexdigest() == meta['raw_sha256']
            loaded[path] = value
        return loaded[path]
    source_mse, source_rows, future_rows = {}, [], []
    for record in runner['h1_source_records']:
        arms = {row['arm']: row for row in record['arms']}
        dense = load(arms['dense']['raw_snapshot'])
        for kind in ('matched_full', 'sparse'):
            candidate = load(arms[kind]['raw_snapshot'])
            fields = {}
            for field in dense:
                metrics = decomposition(candidate[field], dense[field], dense[field])
                assert math.isclose(metrics['candidate_mse'], arms[kind][field]['mse'],
                                    rel_tol=2e-6, abs_tol=1e-9)
                source_mse[(record['cfg_slot'], kind, field)] = metrics['source_delta_mse']
                fields[field] = metrics
            source_rows.append({'call': record['call'], 'cfg_slot': record['cfg_slot'],
                                'source': kind, 'fields': fields})
        loaded.clear()
        del dense, candidate
    for record in runner['h1_records']:
        arms = {row['arm']: row for row in record['completed_arms']}
        dense, truth = [load(snapshot) for snapshot in
                        (arms['dense']['raw_snapshot'], record['truth_raw_snapshot'])]
        for kind in ('matched_full', 'sparse'):
            candidate = load(arms[kind]['raw_snapshot'])
            fields = {}
            for field in dense:
                metrics = decomposition(candidate[field], dense[field], truth[field])
                assert math.isclose(metrics['candidate_mse'], arms[kind][field]['mse'],
                                    rel_tol=2e-6, abs_tol=1e-9)
                assert math.isclose(metrics['common_dense_mse'], arms['dense'][field]['mse'],
                                    rel_tol=2e-6, abs_tol=1e-9)
                initial = source_mse[(record['cfg_slot'], kind, field)]
                metrics['absolute_delta_norm_ratio_to_source'] = (
                    math.sqrt(metrics['source_delta_mse'] / initial) if initial > 0 else None)
                fields[field] = metrics
            future_rows.append({'call': record['call'], 'cfg_slot': record['cfg_slot'],
                                'age': record['age'], 'source': kind, 'fields': fields})
        loaded.clear()
        del dense, truth, candidate
    assert len(source_rows) == 4 and len(future_rows) == 12
    assert not torch.cuda.is_initialized()
    result = {'status': 'H1_CPU_SOURCE_DELTA_DECOMPOSITION_DESCRIPTIVE_ONLY',
              'frozen_gpu_source': audit['source_revision'],
              'script_sha256': sha(__file__),
              'input_receipts_sha256': {str(p): sha(p) for p in (args.runner, args.audit)},
              'cpu_wall_seconds': time.perf_counter() - begin,
              'cuda_initialized': False, 'source_rows': source_rows, 'future_rows': future_rows,
              'identity': '||S-T||^2 = ||D-T||^2 + ||S-D||^2 + 2<D-T,S-D>; also MF',
              'limits': 'One exposed CAL/two correlated CFG. Fixed-trajectory output-space '
                        'identity, not causal rollout, learned router, safe lifetime or video quality. '
                        'Post hoc descriptive analysis changes no frozen screen.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'cpu_wall_seconds': result['cpu_wall_seconds'],
                      'source_rows': len(source_rows), 'future_rows': len(future_rows)}))


if __name__ == '__main__':
    main()
