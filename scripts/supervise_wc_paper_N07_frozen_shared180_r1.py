#!/usr/bin/env python3
"""One complete frozen final card; original v2 pool and per-UUID ownership."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def observe(uuid):
    raw = subprocess.check_output(['nvidia-smi', '-i', uuid,
        '--query-gpu=uuid,name,memory.used,compute_cap', '--format=csv,noheader,nounits'],
        text=True, timeout=10).strip().split(',')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True, timeout=10)
    return dict(unix=time.time(), uuid=raw[0].strip(), name=raw[1].strip(),
        memory_used_mib=int(raw[2]), compute_cap=raw[3].strip(),
        pids=[int(line.split(',')[1]) for line in apps.splitlines() if line.split(',')[0].strip() == uuid])


def stop(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try: child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage', 'authorization'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--gpu-uuid', required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage / 'src'))
    from wcomr.frozen_shared_production_r1 import (
        CONFIG, RUN, fingerprint, sha, write, validate, validate_launch_authority,
    )
    from wcomr.frozen_shared_post_r1 import GPU_TERMINAL_STATUS
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease, process_identity, same_live_process
    from wcomr.frozen_shared_cpu_acceptance_r1 import validate_bundle
    config, registration, _old, _inputs, _tables, _previous, bound, _shared = validate(args.project, args.stage)
    assert all(sha(args.stage / name) == digest for name, digest in registration['payload_sha256'].items())
    proof_path = args.stage / 'production-CPU-result.json'
    proof = json.loads(proof_path.read_text())
    validate_bundle(json.loads((args.stage / 'CPU-bundle-result.json').read_text()), registration['source_revision'])
    cpu_launch = json.loads((args.stage / 'CPU-launch.json').read_text())
    assert cpu_launch['source_revision'] == registration['source_revision']
    assert not same_live_process(cpu_launch['identity'])
    authority = json.loads(args.authorization.read_text())
    assert args.authorization.resolve() == (args.stage / 'launch-authorization.json').resolve()
    validate_launch_authority(config, bound, registration, proof, authority,
        revision=args.source_revision, gpu_uuid=args.gpu_uuid,
        config_sha256=sha(args.stage / CONFIG), proof_sha256=sha(proof_path),
        registration_sha256=sha(args.stage / 'registration.json'))
    assert proof['runner_source_sha256'] == sha(args.stage / 'scripts/run_wc_paper_N07_frozen_shared180_r1.py')
    pool = ApprovedCardBudgetPool(args.project)
    before = pool.read()
    assert before['cap_gpu_hours'] == config['cumulative_cap_GPUh']
    assert before['origin_used_gpu_hours'] == config['budget_origin_used_GPUh']
    lease = DeviceLease(args.project, args.gpu_uuid).acquire()
    root = args.project / 'outputs' / RUN
    own = process_identity(os.getpid())
    child = None; reserved = False; started = None
    state = dict(status='N07_SHARED180_ADMISSION_PENDING', pid=os.getpid(), start_ticks=own['start_ticks'],
        supervisor_identity=own, source_revision=args.source_revision, config_sha256=sha(args.stage / CONFIG),
        bound_input_fingerprint=fingerprint(bound), registration_sha256=sha(args.stage / 'registration.json'),
        launch_id=authority['launch_id'], run_id=RUN, gpu_uuid=args.gpu_uuid, scope_counts=config['scope_counts'],
        child_pid=None, child_identity=None, child_exit_code=None, runner_sha256=None)
    try:
        assert not root.exists()
        gpu = observe(args.gpu_uuid)
        job = dict(job_id=RUN, run_id=RUN, launch_id=authority['launch_id'], gpu_uuid=args.gpu_uuid,
            source_revision=args.source_revision, config_sha256=sha(args.stage / CONFIG),
            production_CPU_sha256=sha(proof_path), authorization_sha256=sha(args.authorization),
            bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'],
            forecast_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
            cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
            supervisor_pid=os.getpid(), supervisor_start_ticks=own['start_ticks'], stage=str(args.stage))
        if config['billed_limit_GPUh'] < 12:
            after = pool.reserve(job, gpu)
        else:
            after = pool.reserve_specific_whole_card(job, gpu, args.authorization)
        reserved = True; started = time.monotonic()
        root.mkdir()
        state.update(status='N07_SHARED180_GPU_RUNNING', admission=gpu, started_unix=time.time(),
                     pool_before=before, pool_after_reservation=after)
        write(root / 'supervisor.json', state)
        def interrupted(signum, frame):
            raise KeyboardInterrupt('Own N07 supervisor interrupted: ' + str(signum))
        signal.signal(signal.SIGTERM, interrupted)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=args.gpu_uuid, WC_SUPERVISOR_PID=str(os.getpid()),
            WC_LOCK_FD=str(lease.handle.fileno()), HF_HUB_CACHE=str(args.project / 'hfhub'),
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        command = [sys.executable, '-u', str(args.stage / 'scripts/run_wc_paper_N07_frozen_shared180_r1.py'),
            '--project', str(args.project), '--stage', str(args.stage), '--source-revision', args.source_revision,
            '--gpu-uuid', args.gpu_uuid]
        with (root / 'GPU.log').open('x') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                cwd=args.project / 'runtime', env=env, pass_fds=(lease.handle.fileno(),), start_new_session=True)
            state.update(child_pid=child.pid, child_identity=process_identity(child.pid), command=command)
            write(root / 'supervisor.json', state)
            while child.poll() is None:
                if (time.monotonic() - started) / 3600 >= config['billed_limit_GPUh'] - 30 / 3600:
                    state['own_billed_limit_stop'] = True; stop(child); break
                time.sleep(10)
            state['child_exit_code'] = child.wait()
    except BaseException as error:
        state.update(error_type=type(error).__name__, error=str(error))
        if not reserved:
            write(args.stage / 'supervisor-admission-failure.json',
                dict(state, status='N07_SHARED180_ADMISSION_FAILED_NO_GPU_CHILD', GPU_child_started=False))
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall = time.monotonic() - started
                # Even a rare output-directory creation error must settle its
                # original reservation; preserve a stage-local bill in that case.
                target = root if root.is_dir() else args.stage
                bill = dict(status='N07_SHARED180_ACTUAL_GPU_BILL', run_id=RUN,
                    launch_id=authority['launch_id'], source_revision=args.source_revision, gpu_uuid=args.gpu_uuid,
                    config_sha256=sha(args.stage / CONFIG), scope_counts=config['scope_counts'],
                    wall_seconds=wall, actual_GPUh=wall / 3600, billed_limit_GPUh=config['billed_limit_GPUh'],
                    original_output_root_available=target == root, ended_unix=time.time())
                billing_path = target / 'billing.json'; write(billing_path, bill)
                settled = pool.settle(RUN, bill['actual_GPUh'], sha(billing_path))
                state.update(status=GPU_TERMINAL_STATUS, wall_seconds=wall, actual_GPUh=bill['actual_GPUh'],
                    ended_unix=time.time(), billing_sha256=sha(billing_path), billing_ref=str(billing_path),
                    pool_after=settled, runner_sha256=sha(root / 'runner.json') if (root / 'runner.json').exists() else None)
                try: state['release'] = observe(args.gpu_uuid)
                except Exception as error: state['release'] = dict(status='TELEMETRY_UNAVAILABLE', error=str(error))
                write(target / 'supervisor.json', state)
        finally:
            lease.close()


if __name__ == '__main__': main()
