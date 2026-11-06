#!/usr/bin/env python3
"""Read-only CPU postprocessing of every original40 N09 diagnostic position."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(args.stage / 'src'))
    from wcomr.runtime_profile40_production_r1 import CONFIG, RUN, validate
    from wcomr.runtime_profile40_post_r1 import (
        GPU_TERMINAL_STATUS, audit_payload, audit_profile, audit_rows, parity_controls, summarize,
    )
    from wcomr.frozen_shared_post_r1 import inspect_video
    from wcomr.frozen_shared_production_r1 import fingerprint, sha, write
    from wcomr.gpu_budget_pool_v2 import same_live_process
    config, registration, old, _, _, _, bound, _ = validate(args.project, args.stage)
    if not all(sha(args.stage / name) == digest for name, digest in registration['payload_sha256'].items()):
        raise ValueError('Original N09 production payload SHA differs')
    root = (args.project / 'outputs' / RUN).resolve()
    supervisor = json.loads((root / 'supervisor.json').read_text())
    if (supervisor['status'] != GPU_TERMINAL_STATUS or supervisor['run_id'] != RUN
            or supervisor['source_revision'] != registration['source_revision']
            or supervisor['config_sha256'] != sha(args.stage / CONFIG)
            or supervisor['scope_counts'] != bound['scope_counts']
            or supervisor['bound_profile_fingerprint'] != fingerprint(bound)
            or same_live_process(dict(pid=supervisor['pid'], start_ticks=supervisor['start_ticks']))
            or (supervisor.get('child_identity') and same_live_process(supervisor['child_identity']))):
        raise ValueError('Collect only the original terminated full40 supervisor and worker')
    runner_path = root / 'runner.json'
    runner = json.loads(runner_path.read_text()) if runner_path.exists() else {'runs': []}
    if runner_path.exists() and (sha(runner_path) != supervisor['runner_sha256']
            or runner['source_revision'] != registration['source_revision']
            or runner['config_sha256'] != sha(args.stage / CONFIG)
            or runner['scope_counts'] != bound['scope_counts']
            or runner['bound_profile_fingerprint'] != fingerprint(bound)
            or runner['matrix'] != bound['execution_plan'] or runner['bindings'] != bound['bindings']):
        raise ValueError('Original complete mode matrix or runner source differs')
    import torch
    torch.set_num_threads(2)
    def forbidden(*a, **kw):
        raise RuntimeError('N09 CPU audit forbids CUDA execution and downloads')
    if torch.cuda.is_initialized():raise RuntimeError('Start CPU audit without CUDA')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    destination = args.stage / 'N09-CPU-final-results.json'
    if destination.exists():raise FileExistsError('Preserve the original N09 CPU audit receipt')
    started = time.time()
    value = dict(status='N09_FULL40_CPU_AUDIT_RUNNING', source_revision=registration['source_revision'],
        config_sha256=sha(args.stage / CONFIG), bound_profile_fingerprint=fingerprint(bound),
        scope_counts=bound['scope_counts'], GPU_supervisor=supervisor, audit_failures=[],
        resource_boundary_observations=runner.get('resource_observations', []),
        original_model_load_calls=runner.get('model_load_calls'),
        original_model_loads_completed=runner.get('model_loads_completed'),
        original_load_seconds=runner.get('load_seconds'),
        GPU_submissions=0, ledger_written=False, CUDA_initialized=False)
    def save():
        value['CPU_wall_seconds'] = time.time() - started
        write(destination, value)
    def progress(result):
        value.update(result); save()
    save()
    try:
        value.update(audit_rows(runner['runs'], bound,
            lambda row, planned, b: audit_payload(row, planned, b, root,
                expected_shape=old['expected_real_shape']),
            lambda row: inspect_video(root, row),
            lambda row, planned: audit_profile(row, planned, root, expected_device='cuda:0',
                probe_depth=old['historical_wc_settings']['probe_depth']),
            expected_device='cuda:0', save=progress))
        controls, failed = parity_controls(value['rows'], bound)
        value.update(controls); value['audit_failures'].extend(failed)
        value.update(summarize(value, bound, observed_paths=len(runner['runs']),
                               child_exit_code=supervisor['child_exit_code']))
        value['artifact_inventory'] = [dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(root.rglob('*')) if p.is_file()
            and (p.suffix in ('.pt', '.mp4') or p.name == 'profile-scalars.json')]
        if torch.cuda.is_initialized():raise RuntimeError('CPU postprocessing unexpectedly initialized CUDA')
        save()
        if value['audit_failures']:
            raise RuntimeError('Original N09 tensor/video/profile/memory failures retained; no full acceptance')
    except BaseException as error:
        value.update(CPU_terminal_error_type=type(error).__name__, CPU_terminal_error=str(error))
        if value['status'] == 'N09_FULL40_CPU_AUDIT_RUNNING':
            value['status'] = 'N09_FULL40_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        save(); raise


if __name__ == '__main__':main()
