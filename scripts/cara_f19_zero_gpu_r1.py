#!/usr/bin/env python3
"""CPU-only F19 timing/layout exploration and optional saved B1 analysis."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--b1-assets', type=Path)
    parser.add_argument('--b1-manifest-sha256', default='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import torch
    from wcomr.cara_f19_zero_gpu_r1 import analyze_saved_B1, candidate_layouts, timing_audit

    def forbid(*a, **kw):
        raise RuntimeError('This exploration forbids CUDA initialization')
    torch.cuda._lazy_init = forbid
    torch.set_num_threads(2)
    args.output_directory.mkdir(parents=True, exist_ok=False)
    paths = dict(
        manifest='plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
        analysis='reports/cara_fast_B36_complete_analysis_r1_20261029.json',
        historical_profile='reports/wc_paper_N09_full40_complete_results_analysis_20261018.json')
    data = {k: json.loads((ROOT/p).read_text()) for k, p in paths.items()}
    timing = timing_audit(data['analysis'], data['manifest'], data['historical_profile'])
    layouts = candidate_layouts(data['manifest'], timing)
    b1 = analyze_saved_B1(args.b1_assets, args.b1_manifest_sha256) if args.b1_assets else dict(
        status='REAL_B1_TENSORS_UNAVAILABLE_REMOTE_TRANSPORT_FAILED',
        requested_update_lags=[1, 2], available_state_updates=[22, 23, 25, 33, 34, 35],
        expected_pairs_per_input=[[22,23,1],[23,25,2],[33,34,1],[33,35,2],[34,35,1]],
        expected_comparisons=10, real_tensor_comparisons=0, held_guided_MSE=None,
        single_branch_cache_trajectory_validated=False, GPU_screen_ready=False)
    payloads = {'timing.json': timing, 'candidate_layouts.json': layouts, 'B1_delta_hold.json': b1}
    receipt = dict(schema='CARA_F19_ZERO_GPU_EXPLORATION_R1',
        input_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths.values()},
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
            'src/wcomr/cara_f19_zero_gpu_r1.py', 'src/wcomr/cara_f19_profile_r1.py',
            'scripts/cara_f19_zero_gpu_r1.py')},
        GPU_submissions=0, ledger_accessed=False, CUDA_initialized=torch.cuda.is_initialized(),
        old_frozen_results_changed=False, protected_inputs_accessed=False,
        endpoint_inference_or_rescoring=0, real_candidate_LPIPS=None,
        real_candidate_speedup=None, GPU_dispatch_ready=False,
        B1_status=b1['status'])
    payloads['receipt.json'] = receipt
    for name, value in payloads.items():
        with (args.output_directory/name).open('x') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(args.output_directory), GPU_submissions=0,
        B1_status=b1['status'], candidates=len(layouts['candidates']))))


if __name__ == '__main__':
    main()
