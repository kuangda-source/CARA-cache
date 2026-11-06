#!/usr/bin/env python3
"""Local CPU validation, offline candidate generation and saved-data selection."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_source_coverage_r1 import candidate_pool, select_endpoint


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def cpu(args):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(ROOT/'tests'))
    import test_cara_source_coverage_r1 as controls

    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(controls))
    if not result.wasSuccessful():
        write_new(args.output, dict(status='CPU_FAILED', tests=result.testsRun,
            errors=len(result.errors), failures=len(result.failures), test_log=log.getvalue(),
            GPU_submissions=0, ledger_written=False))
        print(log.getvalue())
        return 1
    manifest = json.loads(Path(args.manifest).read_text())
    profile, sigmas = profile_from(manifest['profile']), manifest['schedule']['sigmas']
    pools = {f'{mode}_{count}': candidate_pool(profile, count, sigmas, mode=mode)
             for mode in ('two', 'single') for count in (19, 22)}
    bundle = dict(schema='CARA_SOURCE_COVERAGE_CPU_CANDIDATES_R1',
        status='CPU_GENERATED_ENDPOINTS_PENDING', pools=pools,
        neutral_ablation={key: [c['candidate_id'] for c in pool['candidates']
            if any(o['tilt'] == 0 for o in c['origins'])] for key, pool in pools.items()},
        original_schedule_ref=args.manifest, original_schedule_sha256=hashlib.sha256(
            Path(args.manifest).read_bytes()).hexdigest(),
        historical_19D_22D_already_exposed=True, GPU_dispatch_ready=False)
    write_new(args.pools_output, bundle)
    refs = [Path(__file__).relative_to(ROOT).as_posix(),
        'src/wcomr/cara_source_coverage_r1.py', 'tests/test_cara_source_coverage_r1.py',
        'src/wcomr/cara_fast_spec_r1.py', 'src/wcomr/policy_generator_r1/interval_grammar.py',
        'src/wcomr/cara_read_write_step_r1.py', 'src/wcomr/cara_read_write_provenance_r1.py',
        'src/wcomr/cara_read_write_transition_r1.py', 'src/wcomr/cara_read_write_state_r1.py',
        'tests/test_cara_read_write_provenance_r1.py', 'tests/test_cara_read_write_transition_r1.py']
    runtime = ROOT/'.sync/read-write-pinned-runtime-r1'
    from wcomr.cfg_paired_probe_forward import RF_PATH, WC_PATH
    pinned = [RF_PATH, WC_PATH, 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py']
    receipt = dict(schema='CARA_SOURCE_COVERAGE_CPU_ACCEPTANCE_R1',
        status='CPU_ACCEPTED_REAL_ENDPOINT_EVALUATION_PENDING', started_UTC=started,
        ended_UTC=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-start,
        tests=result.testsRun, errors=0, failures=0, metrics=controls.METRICS,
        test_log=log.getvalue(), pools_ref=args.pools_output,
        pools_file_sha256=hashlib.sha256(Path(args.pools_output).read_bytes()).hexdigest(),
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in refs},
        pinned_runtime_sha256={str(p): hashlib.sha256((runtime/p).read_bytes()).hexdigest() for p in pinned},
        interpreter=sys.version, executable=sys.executable,
        CPU_device='cpu', CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],
        real_Cosmos_weights=False, real_video_scores=0, endpoint_selection_fixture_only=True,
        old_42_query_ranking_audit='PENDING_ORIGINAL_COMPLETE_QUERY_AND_LABEL_BYTES',
        GPU_submissions=0, ledger_written=False, old_frozen_results_changed=False)
    write_new(args.output, receipt)
    print(json.dumps({k: receipt[k] for k in ('status', 'tests', 'metrics', 'elapsed_seconds')}, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('cpu')
    check.add_argument('--manifest', default=str(ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json'))
    check.add_argument('--output', required=True)
    check.add_argument('--pools-output', required=True)
    generate = commands.add_parser('generate')
    generate.add_argument('--manifest', required=True)
    generate.add_argument('--dense', type=int, required=True)
    generate.add_argument('--mode', choices=('single', 'two'), default='two')
    generate.add_argument('--output', required=True)
    select = commands.add_parser('select')
    select.add_argument('--pool', required=True)
    select.add_argument('--rows', required=True)
    select.add_argument('--fit', nargs='+', required=True)
    select.add_argument('--cost-limit-gpuh', type=float, required=True)
    select.add_argument('--overhead-gpuh', type=float, default=0.)
    select.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'cpu':
        return cpu(args)
    if args.command == 'generate':
        manifest = json.loads(Path(args.manifest).read_text())
        value = candidate_pool(profile_from(manifest['profile']), args.dense,
            manifest['schedule']['sigmas'], mode=args.mode)
    else:
        value = select_endpoint(json.loads(Path(args.pool).read_text()), args.fit,
            json.loads(Path(args.rows).read_text()), cost_limit_GPUh=args.cost_limit_gpuh,
            overhead_GPUh=args.overhead_gpuh)
    write_new(args.output, value)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
