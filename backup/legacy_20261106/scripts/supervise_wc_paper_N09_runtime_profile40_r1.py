#!/usr/bin/env python3
"""One original N09 full40 child, per-UUID lease and additive actual-wall bill."""
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
    from wcomr.runtime_profile40_production_r1 import (
        CONFIG, RUN, CPU_RESULT, validate, validate_authority, clean_registered_jobs,
    )
    from wcomr.runtime_profile40_post_r1 import GPU_TERMINAL_STATUS
    from wcomr.runtime_profile40_cpu_acceptance_r1 import validate_bundle, validate_proof
    from wcomr.frozen_shared_production_r1 import sha, write, fingerprint
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease, process_identity, same_live_process
    config, registration, _old, _inputs, _tables, _previous, bound, _shared = validate(project, stage)
    if not all(sha(stage / n) == h for n, h in registration['payload_sha256'].items()):
        raise ValueError('Original full40 payload differs from the registered source')
    proof_path = stage / CPU_RESULT; proof = json.loads(proof_path.read_text())
    bundle_path = stage / 'N09-CPU-bundle-result.json'
    validate_bundle(json.loads(bundle_path.read_text()), registration['source_revision'],
        registration_sha256=sha(stage / 'registration.json'), config_sha256=sha(stage / CONFIG),
        proof_sha256=sha(proof_path), payload_sha256=registration['payload_sha256'])
    validate_proof(proof, config, bound, registration, registration_sha256=sha(stage / 'registration.json'),
                   config_sha256=sha(stage / CONFIG))
    authority_path = stage / 'N09-launch-authorization.json'
    authority = json.loads(authority_path.read_text())
    validate_authority(config, bound, registration, proof, authority, revision=revision, gpu_uuid=uuid,
        config_sha256=sha(stage / CONFIG), proof_sha256=sha(proof_path),
        registration_sha256=sha(stage / 'registration.json'))
    if proof['runner_source_sha256'] != sha(stage / 'scripts/run_wc_paper_N09_runtime_profile40_r1.py'):
        raise ValueError('Original actual production CPU must bind this exact resident worker')
    cpu = json.loads((stage / 'N09-production-CPU-launch.json').read_text())
    cpu_exit = json.loads((stage / 'N09-production-CPU-exit.json').read_text())
    if (cpu['source_revision'] != revision or cpu['registration_sha256'] != sha(stage / 'registration.json')
            or same_live_process(cpu['identity']) or cpu_exit['exit_code'] != 0
            or cpu_exit['source_revision'] != revision
            or cpu_exit['registration_sha256'] != sha(stage / 'registration.json')
            or any(cpu_exit['original_CPU_identity'].get(k) != cpu['identity'].get(k)
                   for k in ('pid', 'start_ticks'))
            or cpu_exit['production_CPU_sha256'] != sha(proof_path)
            or cpu_exit['bundle_result_sha256'] != sha(bundle_path)):
        raise ValueError('The original production CPU process must terminate successfully before GPU admission')
    pool = ApprovedCardBudgetPool(project); before = pool.read()
    if (before['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or before['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']):
        raise ValueError('Preserve the original cumulative budget and immutable accounting origin')
    clean_registered_jobs(before, RUN)
    lease = DeviceLease(project, uuid).acquire()
    root = project / 'outputs' / RUN; own = process_identity(os.getpid())
    child = None; reserved = False; started = None
    state = dict(status='N09_FULL40_ADMISSION_PENDING', pid=os.getpid(), start_ticks=own['start_ticks'],
        supervisor_identity=own, run_id=RUN, source_revision=revision, launch_id=authority['launch_id'],
        gpu_uuid=uuid, scope_counts=config['scope_counts'], config_sha256=sha(stage / CONFIG),
        registration_sha256=sha(stage / 'registration.json'), bound_profile_fingerprint=fingerprint(bound),
        child_pid=None, child_identity=None, child_exit_code=None, runner_sha256=None,
        clean_repeated_latency_claim=False)
    try:
        if root.exists():raise FileExistsError('Original full40 output already exists; never launch twice')
        gpu = observe(uuid)
        job = dict(job_id=RUN, run_id=RUN, launch_id=authority['launch_id'], gpu_uuid=uuid,
            source_revision=revision, config_sha256=sha(stage / CONFIG), production_CPU_sha256=sha(proof_path),
            authorization_sha256=sha(authority_path), bound_profile_fingerprint=fingerprint(bound),
            bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'],
            forecast_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
            cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
            supervisor_pid=os.getpid(), supervisor_start_ticks=own['start_ticks'], stage=str(stage))
        after = (pool.reserve(job, gpu) if config['billed_limit_GPUh'] < 12
                 else pool.reserve_specific_whole_card(job, gpu, authority_path))
        reserved = True; started = time.monotonic(); root.mkdir()
        state.update(status='N09_FULL40_GPU_RUNNING', admission=gpu, started_unix=time.time(),
                     pool_before=before, pool_after_reservation=after)
        write(root / 'supervisor.json', state)
        def interrupted(signum, frame):
            raise KeyboardInterrupt('Own original N09 supervisor interrupted: ' + str(signum))
        signal.signal(signal.SIGTERM, interrupted)
        command = [sys.executable, '-u', str(stage / 'scripts/run_wc_paper_N09_runtime_profile40_r1.py'),
            '--project', str(project), '--stage', str(stage), '--source-revision', revision, '--gpu-uuid', uuid]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, WC_SUPERVISOR_PID=str(os.getpid()),
            WC_LOCK_FD=str(lease.handle.fileno()), HF_HUB_CACHE=str(project / 'hfhub'),
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        with (root / 'GPU.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                cwd=project / 'runtime', env=env, pass_fds=(lease.handle.fileno(),), start_new_session=True)
            state.update(command=command, child_pid=child.pid, child_identity=process_identity(child.pid))
            write(root / 'supervisor.json', state)
            while child.poll() is None:
                if (time.monotonic() - started) / 3600 >= config['billed_limit_GPUh'] - 30 / 3600:
                    state['own_billed_limit_stop'] = True; stop(child); break
                time.sleep(10)
            state['child_exit_code'] = child.wait()
    except BaseException as error:
        state.update(error_type=type(error).__name__, error=str(error))
        if not reserved:
            write(stage / 'N09-supervisor-admission-failure.json',
                dict(state, status='N09_FULL40_ADMISSION_FAILED_NO_GPU_CHILD', GPU_child_started=False))
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall = time.monotonic() - started; target = root if root.is_dir() else stage
                bill = dict(status='N09_FULL40_ACTUAL_GPU_BILL', run_id=RUN, launch_id=authority['launch_id'],
                    source_revision=revision, gpu_uuid=uuid, config_sha256=sha(stage / CONFIG),
                    scope_counts=config['scope_counts'], wall_seconds=wall, actual_GPUh=wall / 3600,
                    billed_limit_GPUh=config['billed_limit_GPUh'], original_output_root_available=target == root,
                    clean_repeated_latency_claim=False, ended_unix=time.time())
                path = target / ('billing.json' if target == root else 'N09-billing-fallback.json')
                write(path, bill); settled = pool.settle(RUN, bill['actual_GPUh'], sha(path))
                state.update(status=GPU_TERMINAL_STATUS, wall_seconds=wall, actual_GPUh=bill['actual_GPUh'],
                    ended_unix=time.time(), billing_sha256=sha(path), billing_ref=str(path), pool_after=settled,
                    runner_sha256=sha(root / 'runner.json') if (root / 'runner.json').exists() else None)
                try: state['release'] = observe(uuid)
                except Exception as error: state['release'] = dict(status='TELEMETRY_UNAVAILABLE', error=str(error))
                write(target / ('supervisor.json' if target == root else 'N09-supervisor-fallback.json'), state)
        finally:
            lease.close()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True); parser.add_argument('--gpu-uuid', required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage.resolve() / 'src'))
    run(args.project.resolve(), args.stage.resolve(), args.source_revision, args.gpu_uuid)


if __name__ == '__main__':main()
