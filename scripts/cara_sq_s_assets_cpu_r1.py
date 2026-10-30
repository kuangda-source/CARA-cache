"""One bounded, content-only verification of the complete frozen S assets."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.stage / 'src'), str(args.stage / 'scripts')]
    from wcomr.gpu_budget_pool_v2 import atomic_json, process_identity, sha
    from wcomr.sq_s_execution_r2 import assets_current, require, validate_source
    from wcomr.sq_s_spec_r2 import ASSETS
    from wcomr.sq_s_stage_r2 import create

    require(sys.platform == 'linux' and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        and os.environ.get('NVIDIA_VISIBLE_DEVICES') == 'void', 'Native GPU-hidden CPU scan required')
    require(sha(args.stage / 'registration.json') == args.registration_sha256
        and sha(__file__) == args.worker_sha256, 'Original source stage and CPU worker required')
    _, registration = validate_source(args.project, args.stage)
    require(not any((args.stage / name).exists() for name in
        ('S-asset-CPU-consumed.json', 'S-asset-CPU-exit.json', 'S-asset-verification.json')),
        'Original S asset scan exists; recover its original handle')
    cpus = {4, 5}
    require(cpus <= os.sched_getaffinity(0), 'Original preparation CPU cores required')
    os.sched_setaffinity(0, cpus)
    os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 2**30, 2 * 2**30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 2**20, 64 * 2**20))
    resource.setrlimit(resource.RLIMIT_CPU, (1800, 1800))
    def timed_out(signum, frame):
        raise TimeoutError('Original asset CPU scan reached its 1800 second wall limit')
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(1800)
    started, cpu_started = time.monotonic(), time.process_time()
    state = dict(status='S_ASSET_CPU_RUNNING', identity=process_identity(os.getpid()),
        started_unix=time.time(), host=registration['host'], stage=str(args.stage),
        registration_sha256=args.registration_sha256, worker_sha256=args.worker_sha256,
        source_revision=registration['source_revision'], GPU_submissions=0, ledger_writes=0,
        authorizes_retry=False, resources=dict(cpus=sorted(cpus), address_space_GiB=2,
            maximum_file_MiB=64, wall_seconds=1800, CPU_seconds=1800, nice=10, GPU='hidden'))
    create(args.stage / 'S-asset-CPU-consumed.json', state)
    try:
        # Reuse the unchanged, accepted streaming verifier. Never deserialize weights.
        module_path = args.stage / 'src/wcomr/cara_fast_b36_dispatch_r2.py'
        require(sha(module_path) == registration['payload_sha256']['src/wcomr/cara_fast_b36_dispatch_r2.py'],
            'Original accepted asset verifier changed')
        from wcomr.cara_fast_b36_dispatch_r2 import assets_check, assets_unchanged
        specification = json.loads((args.stage / ASSETS).read_text())
        require(len(specification['files']) == 20, 'Complete twenty file S membership required')
        files = []
        for descriptor in specification['files']:
            files += assets_check(args.project, dict(files=[descriptor], snapshot_links=[]))
            atomic_json(args.stage / 'S-asset-CPU-progress.json', dict(checked=len(files), total=20,
                bytes_checked=sum(row['stamp'][2] for row in files), observed_unix=time.time(),
                scientific_scores_returned=False, GPU_submissions=0))
        assets_unchanged(args.project, specification, files)
        require('torch' not in sys.modules, 'Asset verification must not import the model runtime')
        proof = dict(status='S_MODEL_AND_AUXILIARY_ASSETS_SHA_VERIFIED_CPU_ONLY', host=registration['host'],
            asset_contract_sha256=sha(args.stage / ASSETS), files=files,
            bytes_read=sum(row['stamp'][2] for row in files), all_snapshot_links_verified=True,
            registration_sha256=args.registration_sha256, worker_sha256=args.worker_sha256,
            verifier_module_sha256=sha(module_path), started_unix=state['started_unix'], ended_unix=time.time(),
            model_weights_deserialized=False, torch_imported=False, GPU_submissions=0, ledger_writes=0)
        create(args.stage / 'S-asset-verification.json', proof)
        assets_current(args.project, args.stage)
        state.update(status='S_ASSET_CPU_TERMINAL', exit_code=0,
            verification_sha256=sha(args.stage / 'S-asset-verification.json'))
    except BaseException as error:
        state.update(status='S_ASSET_CPU_FAILED', exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
    finally:
        state.update(wall_seconds=time.monotonic() - started, CPU_seconds=time.process_time() - cpu_started,
            peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, ended_unix=time.time())
        create(args.stage / 'S-asset-CPU-exit.json', state)


if __name__ == '__main__':
    main()
