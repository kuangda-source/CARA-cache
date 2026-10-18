#!/usr/bin/env python3
"""One whole frozen scout job under the existing per-UUID pool."""
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
    from wcomr.scout_gpu_lifecycle_r1 import (bound_dependency, read, sha, validate_authority,
        verify_upstream, CPU_PROOF, dependency_ref, RUNS, counts)
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease, process_identity, atomic_json
    write = atomic_json
    meta, c, reg, entrycap, entryaccepted = bound_dependency(a.project, a.stage)
    DEPENDENCY = dependency_ref(a.stage)
    RUN = RUNS[c['kind']]; COUNTS = counts(c['kind']); CONFIG = meta['config_ref']; CPU_RESULT = CPU_PROOF
    regsha = sha(a.stage/'registration.json'); configsha = sha(a.stage/CONFIG)
    proof = read(a.stage/CPU_PROOF)
    accepted_path = a.stage/'scout-lifecycle-CPU-independent-acceptance.json'
    accepted = read(accepted_path); auth = read(a.authorization)
    assert accepted['lifecycle_CPU_accepted'] and accepted['registration_sha256'] == regsha
    assert proof['registration_sha256'] == regsha and accepted['proof_sha256'] == sha(a.stage/CPU_PROOF)
    assert accepted['kind'] == c['kind'] and accepted['scope_counts'] == COUNTS
    validate_authority(auth, c, regsha, sha(accepted_path), sha(a.stage/CPU_PROOF), sha(a.stage/DEPENDENCY))
    assert auth['source_revision'] == reg['source_revision'] == a.source_revision and auth['gpu_uuid'] == a.gpu_uuid
    up = a.stage/'scout-upstream-capture.json.gz'; upa = a.stage/'scout-upstream-acceptance.json'
    assert sha(up) == auth['upstream_capture_sha256'] and sha(upa) == auth['upstream_acceptance_sha256']
    gatepath = a.stage/'scout-frozen-CAL-gate.json'
    gate = read(gatepath) if c['kind'] == 'BANK24' else None
    if gate is not None: assert sha(gatepath) == auth['frozen_gate_sha256']
    verify_upstream(c['kind'], read(up), read(upa), gate)
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
            independent_CPU_acceptance_sha256=sha(accepted_path), dependency_sha256=sha(a.stage/DEPENDENCY),
            cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223,
            forecast_GPUh=c['forecast_complete_GPUh'], billed_limit_GPUh=c['billed_limit_GPUh'],
            supervisor_pid=os.getpid(), supervisor_start_ticks=ident['start_ticks'], stage=str(a.stage), scope_counts=COUNTS)
        after = (pool.reserve(job, gpu) if c['billed_limit_GPUh'] < 12 else
                 pool.reserve_specific_whole_card(job, gpu, a.authorization))
        reserved = True; start = time.monotonic(); out.mkdir(parents=True)
        state = dict(status='SCOUT_GPU_RUNNING', pid=os.getpid(), supervisor_identity=ident,
            source_revision=a.source_revision, run_id=RUN, launch_id=auth['launch_id'], gpu_uuid=a.gpu_uuid,
            config_sha256=configsha, registration_sha256=regsha, scope_counts=COUNTS,
            started_unix=time.time(), admission=gpu, pool_before=before, pool_after_reservation=after,
            child_pid=None, child_exit_code=None, runner_sha256=None, timing_claim=c['timing_claim'], entry_source_revision=meta['entry_source_revision'], entry_registration_sha256=meta['entry_registration_sha256'])
        write(out/'supervisor.json', state)
        def interrupted(signum, frame): raise KeyboardInterrupt('Own scout supervisor interrupted: '+str(signum))
        signal.signal(signal.SIGTERM, interrupted)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=a.gpu_uuid, WC_SUPERVISOR_PID=str(os.getpid()),
            WC_LOCK_FD=str(lease.handle.fileno()), WC_SCOUT_KIND=c['kind'], HF_HUB_CACHE=str(a.project/'hfhub'), HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        command = [sys.executable, '-u', str(Path(meta['entry_stage'])/'scripts/run_wc_scout_production_entry_r1.py'),
            '--project', str(a.project), '--stage', meta['entry_stage'], '--source-revision', meta['entry_source_revision'], '--gpu-uuid', a.gpu_uuid]
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
            with (a.stage/'scout-admission-failure.json').open('x') as h:
                json.dump(dict(status='SCOUT_NO_GPU_CHILD_ADMISSION_FAILURE_RETAINED',
                    source_revision=a.source_revision, scope_counts=COUNTS, GPU_child_started=False,
                    GPUh=0, error_type=type(e).__name__, error=str(e)), h, indent=2)
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall = time.monotonic()-start
                bill = dict(status='SCOUT_ACTUAL_GPU_BILL', run_id=RUN, launch_id=auth['launch_id'],
                    source_revision=a.source_revision, gpu_uuid=a.gpu_uuid, scope_counts=COUNTS,
                    wall_seconds=wall, actual_GPUh=wall/3600, billed_limit_GPUh=c['billed_limit_GPUh'], ended_unix=time.time())
                out.mkdir(parents=True, exist_ok=True); write(out/'billing.json', bill)
                settled = pool.settle(RUN, wall/3600, sha(out/'billing.json'))
                if state is None: state = dict(pid=os.getpid(), child_pid=None, child_exit_code=None)
                path = out/'runner.json'
                state.update(status='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT', wall_seconds=wall,
                    actual_GPUh=wall/3600, ended_unix=time.time(), billing_sha256=sha(out/'billing.json'),
                    pool_after=settled, runner_sha256=sha(path) if path.exists() else None)
                try: state['release'] = observe(a.gpu_uuid)
                except Exception as e: state['release'] = dict(status='TELEMETRY_UNKNOWN_NOT_RELEASE_PROOF', error=str(e))
                write(out/'supervisor.json', state)
        finally:
            lease.close()


if __name__ == '__main__':
    main()
