#!/usr/bin/env python3
"""One original full960 scoring child, UUID lease and additive whole-wall bill."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def observe(uuid):
    fields = subprocess.check_output(['nvidia-smi', '-i', uuid,
        '--query-gpu=uuid,name,memory.used,compute_cap', '--format=csv,noheader,nounits'],
        text=True, timeout=10).strip().split(',')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True, timeout=10)
    return dict(unix=time.time(), uuid=fields[0].strip(), name=fields[1].strip(),
        memory_used_mib=int(fields[2]), compute_cap=fields[3].strip(),
        pids=[int(line.split(',')[1]) for line in apps.splitlines() if line.split(',')[0].strip() == uuid])


def stop(child):
    if child is not None and child.poll() is None:
        try: os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            child.wait(); return
        try: child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()


def run(project, stage, revision, uuid):
    from wcomr.automatic_quality_production_r1 import CONFIG, load, read, validate_authority
    from wcomr.automatic_quality_models_r1 import sha
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease, atomic_json, process_identity, same_live_process
    config, registration, bundle, _accepted, _CPU_registration, _resources = load(stage)
    authority_path = stage / 'N10-launch-authorization.json'; authority = read(authority_path)
    proof_path = stage / 'CPU-scoring-entry-result.json'; proof = read(proof_path)
    validate_authority(config, registration, bundle, proof, authority, revision=revision,
        gpu_uuid=uuid, config_sha256=sha(stage / CONFIG), registration_sha256=sha(stage / 'registration.json'),
        proof_sha256=sha(proof_path), worker_sha256=sha(stage / 'scripts/score_wc_paper_N10_full960_r1.py'))
    CPU = read(stage / 'N10-production-CPU-launch.json')
    if (CPU['source_revision'] != revision or CPU['registration_sha256'] != sha(stage / 'registration.json')
            or same_live_process(CPU['identity'])
            or read(stage / 'N10-production-CPU-exit.json')['exit_code'] != 0):
        raise ValueError('The original production CPU process must finish successfully before GPU admission')
    pool = ApprovedCardBudgetPool(project); before = pool.read()
    if (before['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or before['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']
            or any(job['status'] == 'RESERVED_OR_RUNNING' for job in before['jobs'].values())):
        raise ValueError('Preserve the original pool and let all earlier mainline GPU tasks finish')
    lease = DeviceLease(project, uuid).acquire()
    run_id = config['run_id']; output = project / 'outputs' / run_id
    own = process_identity(os.getpid()); child = None; reserved = False; started = None
    state = dict(status='N10_FULL960_ADMISSION_PENDING', source_revision=revision, run_id=run_id,
        launch_id=authority['launch_id'], gpu_uuid=uuid, supervisor_identity=own,
        config_sha256=sha(stage / CONFIG), registration_sha256=sha(stage / 'registration.json'),
        input_bundle_fingerprint=bundle['fingerprint'], scope_counts=config['scope_counts'],
        child_identity=None, child_exit_code=None, generation_latency_claim=False)
    try:
        if output.exists(): raise FileExistsError('Original scoring output already exists; never launch twice')
        gpu = observe(uuid)
        job = dict(job_id=run_id, run_id=run_id, launch_id=authority['launch_id'], gpu_uuid=uuid,
            source_revision=revision, config_sha256=sha(stage / CONFIG),
            production_CPU_sha256=sha(proof_path), authorization_sha256=sha(authority_path),
            bound_input_fingerprint=bundle['fingerprint'], scope_counts=config['scope_counts'],
            forecast_GPUh=config['forecast_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
            cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
            supervisor_pid=os.getpid(), supervisor_start_ticks=own['start_ticks'], stage=str(stage))
        after = (pool.reserve(job, gpu) if config['billed_limit_GPUh'] < 12
                 else pool.reserve_specific_whole_card(job, gpu, authority_path))
        reserved = True; started = time.monotonic(); output.mkdir()
        state.update(status='N10_FULL960_GPU_RUNNING', admission=gpu, started_unix=time.time(),
            pool_before=before, pool_after_reservation=after)
        atomic_json(output / 'supervisor.json', state)
        def interrupted(signum, frame): raise KeyboardInterrupt('Original scoring supervisor interrupted: '+str(signum))
        signal.signal(signal.SIGTERM, interrupted)
        command = [sys.executable, '-u', str(stage / 'scripts/score_wc_paper_N10_full960_r1.py'),
            '--project', str(project), '--stage', str(stage), '--source-revision', revision, '--gpu-uuid', uuid]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, WC_SUPERVISOR_PID=str(os.getpid()),
            WC_LOCK_FD=str(lease.handle.fileno()), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        with (output / 'GPU.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                cwd=project, env=env, pass_fds=(lease.handle.fileno(),), start_new_session=True)
            state.update(command=command, child_identity=process_identity(child.pid))
            atomic_json(output / 'supervisor.json', state)
            while child.poll() is None:
                if (time.monotonic()-started)/3600 >= config['billed_limit_GPUh']-30/3600:
                    state['own_billed_limit_stop'] = True; stop(child); break
                time.sleep(10)
            state['child_exit_code'] = child.wait()
    except BaseException as error:
        state.update(error_type=type(error).__name__, error=str(error))
        if not reserved:
            atomic_json(stage / 'N10-supervisor-admission-failure.json',
                dict(state, status='N10_ADMISSION_FAILED_NO_GPU_CHILD', GPU_child_started=False))
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall = time.monotonic()-started; target = output if output.is_dir() else stage
                bill = dict(status='N10_FULL960_ACTUAL_SCORING_GPU_BILL', run_id=run_id,
                    launch_id=authority['launch_id'], source_revision=revision, gpu_uuid=uuid,
                    config_sha256=sha(stage / CONFIG), scope_counts=config['scope_counts'],
                    wall_seconds=wall, actual_GPUh=wall/3600, billed_limit_GPUh=config['billed_limit_GPUh'],
                    generation_latency_claim=False, original_output_root_available=target == output,
                    ended_unix=time.time())
                billing = target / ('billing.json' if target == output else 'N10-billing-fallback.json')
                atomic_json(billing, bill)
                settled = pool.settle(run_id, bill['actual_GPUh'], sha(billing))
                state.update(status='N10_FULL960_ORIGINAL_GPU_TERMINAL_NOT_QUALITY_ACCEPTANCE',
                    ended_unix=time.time(), wall_seconds=wall, actual_GPUh=bill['actual_GPUh'],
                    billing_sha256=sha(billing), billing_ref=str(billing), pool_after=settled,
                    runner_sha256=sha(output / 'runner.json') if (output / 'runner.json').exists() else None)
                try: state['release'] = observe(uuid)
                except Exception as error: state['release'] = dict(status='TELEMETRY_UNAVAILABLE', error=str(error))
                atomic_json(target / ('supervisor.json' if target == output else 'N10-supervisor-fallback.json'), state)
        finally: lease.close()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'): parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True); parser.add_argument('--gpu-uuid', required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage.resolve() / 'src'))
    run(args.project.resolve(), args.stage.resolve(), args.source_revision, args.gpu_uuid)


if __name__ == '__main__': main()
