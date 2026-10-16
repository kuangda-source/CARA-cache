#!/usr/bin/env python3
"""Score the original complete160/six-dimension960 cohort inside its admitted job.

This entrypoint cannot reserve a GPU or launch a supervisor. CPU-check validates
the actual complete input and original-model proof without importing Torch.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-revision'); parser.add_argument('--gpu-uuid')
    parser.add_argument('--cpu-check', action='store_true')
    args = parser.parse_args(); stage = args.stage.resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(stage / 'src'))
    from wcomr.automatic_quality_production_r1 import (
        CONFIG, CPU_STATUS, admitted_job, load, read, score_complete, validate_authority,
    )
    from wcomr.automatic_quality_models_r1 import OriginalMetricFactory, sha
    from wcomr.gpu_budget_pool_v2 import BudgetPool, atomic_json, process_identity
    config, registration, bundle, accepted, CPU_registration, resources = load(stage)
    if args.cpu_check:
        if 'torch' in sys.modules: raise ValueError('Contract CPU must not import the neural framework')
        path = stage / 'CPU-scoring-entry-result.json'
        if path.exists(): raise FileExistsError(path)
        with path.open('x') as handle:
            json.dump(dict(status=CPU_STATUS, exit_code=0,
                source_revision=registration['source_revision'], config_sha256=sha(stage / CONFIG),
                registration_sha256=sha(stage / 'registration.json'),
                input_bundle_fingerprint=bundle['fingerprint'], scope_counts=config['scope_counts'],
                runner_source_sha256=sha(Path(__file__)),
                metric_positions=960, neural_framework_imported=False, GPU_submissions=0,
                ledger_written=False), handle, indent=2, allow_nan=False)
        return
    if args.source_revision != registration['source_revision']:
        raise ValueError('Use the immutable source registration, separate from the hashed scoring config')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Use exactly the supervisor-admitted GPU UUID')
    if os.environ.get('WC_SUPERVISOR_PID') != str(os.getppid()):
        raise ValueError('Original supervising parent required')
    descriptor = int(os.environ['WC_LOCK_FD'])
    lease = (args.project / '.sync/gpu-locks' / (args.gpu_uuid + '.lock')).resolve()
    if Path('/proc/self/fd/' + str(descriptor)).resolve() != lease:
        raise ValueError('Original inherited UUID lease required')
    os.fstat(descriptor)
    authority = read(stage / 'N10-launch-authorization.json')
    proof_path = stage / 'CPU-scoring-entry-result.json'
    validate_authority(config, registration, bundle, read(proof_path), authority,
        revision=args.source_revision, gpu_uuid=args.gpu_uuid, config_sha256=sha(stage / CONFIG),
        registration_sha256=sha(stage / 'registration.json'), proof_sha256=sha(proof_path),
        worker_sha256=sha(Path(__file__)))
    observed = admitted_job(config, pool=BudgetPool(args.project).read(),
        source_revision=args.source_revision, config_sha256=sha(stage / CONFIG),
        gpu_uuid=args.gpu_uuid, authority=authority, parent=process_identity(os.getppid()))
    output = (args.project / 'outputs' / config['run_id']).resolve()
    if not output.is_dir() or (output / 'runner.json').exists():
        raise ValueError('Use one original empty supervisor-created run; never resume unknown scoring')
    state = dict(status='N10_FULL960_INITIALIZING_ORIGINAL_MODELS', pid=os.getpid(),
        source_revision=args.source_revision, config_sha256=sha(stage / CONFIG),
        input_bundle_fingerprint=bundle['fingerprint'], scope_counts=config['scope_counts'],
        original_admission=observed, started_unix=time.time(), generation_latency_claim=False)
    atomic_json(output / 'runner.json', state)
    try:
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        import torch
        if torch.cuda.device_count() != 1 or torch.cuda.get_device_capability() != (8, 6):
            raise ValueError('One original A6000 device required')
        factory = OriginalMetricFactory(stage=stage, resources=resources['resources'], CPU_acceptance=accepted,
            CPU_registration=CPU_registration, scorer_fingerprint=bundle['scorer_fingerprint'],
            torch=torch, device='cuda')
        result = score_complete(bundle, config['comparisons'], factory, output)
        state.update(status='N10_FULL960_FINISHED_FAILURES_RETAINED',
            metric_status_counts=result['metric_status_counts'],
            all_ready_positions_scored=result['all_ready_positions_scored'],
            original_journal_sha256=result['original_journal_sha256'])
    except BaseException as error:
        state.update(status='N10_FULL960_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',
            error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        state['ended_unix'] = time.time(); atomic_json(output / 'runner.json', state)


if __name__ == '__main__': main()
