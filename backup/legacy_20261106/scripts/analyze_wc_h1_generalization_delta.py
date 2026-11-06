#!/usr/bin/env python3
"""CPU-only source perturbation decomposition for an audited two-CAL H1 batch.

Keeps the sealed H1 single-window analyzer and frozen GPU payload unchanged.
Every source lookup includes request, region and CFG. This is descriptive
analysis of fixed-trajectory raw outputs, not an intervention or new screen.
"""
import argparse
import json
import math
import time
from pathlib import Path

import torch

from analyze_wc_h1_source_delta import decomposition, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    begin = time.perf_counter()
    assert not torch.cuda.is_initialized()

    def forbidden(*unused_args, **unused_kwargs):
        raise RuntimeError('CUDA forbidden in H1 generalization raw analysis')

    torch.cuda._lazy_init = forbidden
    runner, audit = [json.loads(p.read_text()) for p in (args.runner, args.audit)]
    assert audit['status'] == 'H1_GENERALIZATION_SOURCE_RAW_ERRORS_NINE_GATES_COST_RELEASE_AUDIT_PASS'
    assert runner['status'] == 'H1_REQUESTS2_SOURCE24_LOCAL72_FULL66_NINE_GATE_PASS_REQUIRES_AUDIT'
    assert audit['raw_output_files_checked'] == 120 and len(runner['requests']) == 2
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
                assert sha_bytes(raw) == meta['raw_sha256']
            loaded[path] = value
        return loaded[path]

    source_mse, provenance, source_rows, future_rows = {}, {}, [], []
    for req in runner['requests']:
        request = req['reference_context'][0]
        sample = req['sample_name']
        assert request.endswith(':' + sample)
        for record in req['h1_source_records']:
            region, branch = record['region'], record['cfg_slot']
            arms = {row['arm']: row for row in record['arms']}
            dense = load(arms['dense']['raw_snapshot'])
            for kind in ('matched_full', 'sparse'):
                candidate = load(arms[kind]['raw_snapshot'])
                key = (request, region, branch, kind)
                assert key not in provenance
                provenance[key] = arms[kind]['provenance']
                assert provenance[key]['identity']['request'] == request
                fields = {}
                for field in dense:
                    metrics = decomposition(candidate[field], dense[field], dense[field])
                    assert math.isclose(metrics['candidate_mse'], arms[kind][field]['mse'],
                                        rel_tol=2e-6, abs_tol=1e-9)
                    source_mse[key + (field,)] = metrics['source_delta_mse']
                    fields[field] = metrics
                source_rows.append({'sample': sample, 'request': request, 'region': region,
                    'call': record['call'], 'cfg_slot': branch, 'source': kind, 'fields': fields})
            loaded.clear()
            del dense, candidate
        for record in req['h1_records']:
            region, branch = record['region'], record['cfg_slot']
            arms = {row['arm']: row for row in record['completed_arms']}
            dense, truth = [load(snapshot) for snapshot in
                           (arms['dense']['raw_snapshot'], record['truth_raw_snapshot'])]
            for kind in ('matched_full', 'sparse'):
                candidate = load(arms[kind]['raw_snapshot'])
                key = (request, region, branch, kind)
                assert arms[kind]['provenance'] == provenance[key]
                assert record['source_call'] == provenance[key]['identity']['source_call']
                fields = {}
                for field in dense:
                    metrics = decomposition(candidate[field], dense[field], truth[field])
                    assert math.isclose(metrics['candidate_mse'], arms[kind][field]['mse'],
                                        rel_tol=2e-6, abs_tol=1e-9)
                    assert math.isclose(metrics['common_dense_mse'], arms['dense'][field]['mse'],
                                        rel_tol=2e-6, abs_tol=1e-9)
                    initial = source_mse[key + (field,)]
                    metrics['absolute_delta_norm_ratio_to_source'] = (
                        math.sqrt(metrics['source_delta_mse'] / initial) if initial > 0 else None)
                    fields[field] = metrics
                future_rows.append({'sample': sample, 'request': request, 'region': region,
                    'call': record['call'], 'source_call': record['source_call'],
                    'cfg_slot': branch, 'age': record['age'], 'source': kind, 'fields': fields})
            loaded.clear()
            del dense, truth, candidate
    assert len(source_rows) == 16 and len(future_rows) == 48
    assert len(provenance) == 16 and not torch.cuda.is_initialized()
    result = {'status': 'H1_GENERALIZATION_CPU_SOURCE_DELTA_DESCRIPTIVE_ONLY',
        'frozen_gpu_source': audit['source_revision'],
        'analysis_code_sha256': {str(p): sha(p) for p in
            (Path(__file__), Path(__file__).with_name('analyze_wc_h1_source_delta.py'))},
        'input_receipts_sha256': {str(p): sha(p) for p in (args.runner, args.audit)},
        'cpu_wall_seconds': time.perf_counter() - begin, 'cuda_initialized': False,
        'source_rows': source_rows, 'future_rows': future_rows,
        'identity': '||S-T||^2 = ||D-T||^2 + ||S-D||^2 + 2<D-T,S-D>; also MF',
        'limits': 'Two exposed CAL; correlated CFG/windows/ages. Output-space identity '
                  'on the fixed official trajectory, no causal rollout, independent '
                  'confirmation, safe lifetime or video quality. Frozen screen unchanged.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'cpu_wall_seconds', 'cuda_initialized')}
                     | {'source_rows': 16, 'future_rows': 48}))


def sha_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    main()
