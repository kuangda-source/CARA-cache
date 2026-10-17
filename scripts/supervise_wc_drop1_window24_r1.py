#!/usr/bin/env python3
"""One complete24 resident GPU job under the existing per-UUID pool."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def observe(uuid):
    values = subprocess.check_output(['nvidia-smi', '-i', uuid,
        '--query-gpu=uuid,name,memory.used,compute_cap', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True, timeout=10)
    return dict(unix=time.time(), uuid=values[0].strip(), name=values[1].strip(),
        memory_used_mib=int(values[2]), compute_cap=values[3].strip(),
        pids=[int(r.split(',')[1]) for r in apps.splitlines() if r.split(',')[0].strip() == uuid])


def stop(child):
    if child is None or child.poll() is not None: return
    os.killpg(child.pid, signal.SIGTERM)
    try: child.wait(timeout=10)
    except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('project', 'stage', 'authorization'): p.add_argument('--'+k, type=Path, required=True)
    p.add_argument('--source-revision', required=True); p.add_argument('--gpu-uuid', required=True)
    a = p.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''; sys.path.insert(0, str(a.stage/'src'))
    from wcomr.drop1_window24_production_r1 import CONFIG, CPU_RESULT, RUN, COUNTS, sha, write, validate
    from wcomr.drop1_window24_cpu_acceptance_r1 import BUNDLE, validate_bundle
    from wcomr.drop1_window24_execution_envelope_r1 import validate_authority, input_fingerprint
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease, process_identity
    c, reg, *_ = validate(a.project, a.stage)
    assert all(sha(a.stage/n) == h for n,h in reg['payload_sha256'].items())
    regsha = sha(a.stage/'registration.json'); configsha = sha(a.stage/CONFIG)
    proof = json.loads((a.stage/CPU_RESULT).read_text())
    accepted_path = a.stage/'window24-production-CPU-independent-acceptance.json'
    accepted = json.loads(accepted_path.read_text()); auth = json.loads(a.authorization.read_text())
    validate_bundle(json.loads((a.stage/BUNDLE).read_text()), proof, c, reg,
        registration_sha256=regsha, config_sha256=configsha, proof_sha256=sha(a.stage/CPU_RESULT))
    validate_authority(c, reg, proof, accepted, auth, source_revision=a.source_revision, gpu_uuid=a.gpu_uuid,
        registration_sha256=regsha, config_sha256=configsha, proof_sha256=sha(a.stage/CPU_RESULT), accepted_sha256=sha(accepted_path))
    pool = ApprovedCardBudgetPool(a.project); lease = DeviceLease(a.project, a.gpu_uuid)
    out = a.project/'outputs'/RUN; child = None; reserved = False; start = None; state = None
    try:
        lease.acquire(); assert not out.exists()
        before = pool.read()
        assert before['cap_gpu_hours'] == 226 and before['origin_used_gpu_hours'] == 79.99637737158223
        gpu = observe(a.gpu_uuid); ident = process_identity(os.getpid())
        job = dict(job_id=RUN, run_id=RUN, launch_id=auth['launch_id'], gpu_uuid=a.gpu_uuid,
            source_revision=a.source_revision, config_sha256=configsha, registration_sha256=regsha,
            production_CPU_sha256=sha(a.stage/CPU_RESULT), authorization_sha256=sha(a.authorization),
            independent_CPU_acceptance_sha256=sha(accepted_path), bound_input_fingerprint=input_fingerprint(c),
            cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223,
            forecast_GPUh=c['forecast_complete_GPUh'], billed_limit_GPUh=c['billed_limit_GPUh'],
            supervisor_pid=os.getpid(), supervisor_start_ticks=ident['start_ticks'], stage=str(a.stage), scope_counts=COUNTS)
        after = (pool.reserve(job, gpu) if c['billed_limit_GPUh'] < 12 else
                 pool.reserve_specific_whole_card(job, gpu, a.authorization))
        reserved = True; start = time.monotonic(); out.mkdir(parents=True)
        state = dict(status='WINDOW24_GPU_RUNNING', pid=os.getpid(), supervisor_identity=ident,
            source_revision=a.source_revision, run_id=RUN, launch_id=auth['launch_id'], gpu_uuid=a.gpu_uuid,
            config_sha256=configsha, registration_sha256=regsha, scope_counts=COUNTS,
            started_unix=time.time(), admission=gpu, pool_before=before, pool_after_reservation=after,
            child_pid=None, child_exit_code=None, runner_sha256=None, timing_claim=c['timing_claim'])
        write(out/'supervisor.json', state)
        def interrupted(signum, frame): raise KeyboardInterrupt('Own window24 supervisor interrupted: '+str(signum))
        signal.signal(signal.SIGTERM, interrupted)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=a.gpu_uuid, WC_SUPERVISOR_PID=str(os.getpid()),
            WC_LOCK_FD=str(lease.handle.fileno()), HF_HUB_CACHE=str(a.project/'hfhub'), HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        command = [sys.executable, '-u', str(a.stage/'scripts/run_wc_drop1_window24_r1.py'),
            '--project', str(a.project), '--stage', str(a.stage), '--source-revision', a.source_revision, '--gpu-uuid', a.gpu_uuid]
        with (out/'GPU.log').open('x') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=a.project/'runtime',
                env=env, pass_fds=(lease.handle.fileno(),), start_new_session=True)
            state.update(command=command, child_pid=child.pid, child_identity=process_identity(child.pid)); write(out/'supervisor.json', state)
            while child.poll() is None:
                if (time.monotonic()-start)/3600 >= c['billed_limit_GPUh']-30/3600:
                    state['own_billed_limit_stop'] = True; stop(child); break
                time.sleep(10)
            state['child_exit_code'] = child.wait()
    except BaseException as e:
        if state is not None: state.update(error_type=type(e).__name__, error=str(e))
        elif not reserved:
            with (a.stage/'window24-admission-failure.json').open('x') as h:
                json.dump(dict(status='WINDOW24_NO_GPU_CHILD_ADMISSION_FAILURE_RETAINED',
                    source_revision=a.source_revision, scope_counts=COUNTS, GPU_child_started=False,
                    GPUh=0, error_type=type(e).__name__, error=str(e)), h, indent=2)
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall = time.monotonic()-start
                bill = dict(status='WINDOW24_ACTUAL_GPU_BILL', run_id=RUN, launch_id=auth['launch_id'],
                    source_revision=a.source_revision, gpu_uuid=a.gpu_uuid, scope_counts=COUNTS,
                    wall_seconds=wall, actual_GPUh=wall/3600, billed_limit_GPUh=c['billed_limit_GPUh'], ended_unix=time.time())
                out.mkdir(parents=True, exist_ok=True); write(out/'billing.json', bill)
                settled = pool.settle(RUN, wall/3600, sha(out/'billing.json'))
                if state is None: state = dict(pid=os.getpid(), child_pid=None, child_exit_code=None)
                path = out/'runner.json'
                state.update(status='WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT', wall_seconds=wall,
                    actual_GPUh=wall/3600, ended_unix=time.time(), billing_sha256=sha(out/'billing.json'),
                    pool_after=settled, runner_sha256=sha(path) if path.exists() else None)
                try: state['release'] = observe(a.gpu_uuid)
                except Exception as e: state['release'] = dict(status='TELEMETRY_UNKNOWN_NOT_RELEASE_PROOF', error=str(e))
                write(out/'supervisor.json', state)
        finally:
            lease.close()


if __name__ == '__main__':
    main()
