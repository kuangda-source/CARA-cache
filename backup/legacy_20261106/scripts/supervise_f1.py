"""Run the two frozen smoke arms serially within the remaining F0/F1 budget.

Persist process identity, GPU admission, exit status, and GPU memory samples.
Only this supervisor's process group is terminated on a deadline/conflict.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--project', type=Path, required=True)
p.add_argument('--runtime', type=Path, required=True)
p.add_argument('--python', required=True)
p.add_argument('--gpu-uuid', required=True)
p.add_argument('--output', type=Path, required=True)
probes = p.add_mutually_exclusive_group()
probes.add_argument('--w1-clean-timing',action='store_true',help='Proposed original8 paired3-repeat14400s cost window; requires separately approved8h ledger')
probes.add_argument('--w1-vqa-controls',action='store_true',help='Original8 all42 x3 judge input controls, at most300 seconds from existing budget')
probes.add_argument('--w1-vqa',action='store_true',help='Original CAL8 small-judge VQA, at most900 seconds from existing total budget')
probes.add_argument('--w1-imaging',action='store_true',help='All original CAL8 MUSIQ pairs, at most600 seconds from existing total budget')
probes.add_argument('--w1-replay',action='store_true',help='Frozen official-schedule scalar CAL8 replay, at most3000 seconds from existing total budget')
probes.add_argument('--w1d-cal',action='store_true',help='CAL-first8 batch, at most6000 seconds from existing total budget')
probes.add_argument('--stage-witness', action='store_true', help='Two fresh official processes, aggregate 900 seconds')
probes.add_argument('--w1-same-state', action='store_true', help='W1 three approximators on same official states, at most 900 seconds')
probes.add_argument('--w1-parity', action='store_true', help='W1 official shadow off/on gate, at most 900 seconds')
probes.add_argument('--guardrail-only', action='store_true', help='F0 full safety pipeline compatibility probe, at most 420 seconds')
probes.add_argument('--probe-only', action='store_true', help='F0 core-model load only, at most 420 seconds; no generation')
p.add_argument('--w1-recent-calibration', action='store_true', help='With --w1-same-state: one latest-anchor-pair scalar revision')
p.add_argument('--deterministic-decode', action='store_true', help='With --stage-witness: scoped cuDNN deterministic decode')
a = p.parse_args()
if a.deterministic_decode and not a.stage_witness:
    p.error('--deterministic-decode requires --stage-witness')
if a.w1_recent_calibration and not a.w1_same_state:
    p.error('--w1-recent-calibration requires --w1-same-state')
is_probe = a.w1_clean_timing or a.w1_vqa_controls or a.w1_vqa or a.w1_imaging or a.w1_replay or a.w1d_cal or a.stage_witness or a.probe_only or a.guardrail_only or a.w1_parity or a.w1_same_state
project, runtime, output = a.project.resolve(), a.runtime.resolve(), a.output.resolve()
lock_path = project / '.sync/f1.lock'; lock_path.parent.mkdir(parents=True, exist_ok=True)
lock = lock_path.open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
budget_path = project / 'reports/budget.json'
budget = json.loads(budget_path.read_text())
remaining = (budget['cap_gpu_hours'] - budget['used_gpu_hours']) * 3600
if remaining <= 0: raise SystemExit('Budget exhausted')
if a.w1_clean_timing and (budget['cap_gpu_hours'] < 8 or remaining < 14400):
    raise SystemExit('Next timing window decision pending or insufficient full-window balance; budget unchanged')
output.mkdir(parents=True, exist_ok=False)
state = {'pid': os.getpid(), 'gpu_uuid': a.gpu_uuid, 'status': 'PREPARING', 'arms': []}

def save(path, value):
    tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); tmp.replace(path)

def query_gpu():
    memory = subprocess.check_output(['nvidia-smi', '-i', a.gpu_uuid,
        '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True, timeout=8).strip()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True, timeout=8)
    pids = [int(line.split(',')[1]) for line in apps.splitlines() if line.split(',')[0].strip() == a.gpu_uuid]
    return {'unix': time.time(), 'memory_used_mib': int(memory.split(',')[0]),
            'utilization_percent': int(memory.split(',')[1]), 'pids': pids}

def stop(child):
    if child.poll() is not None: return
    os.killpg(child.pid, signal.SIGTERM)
    try: child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL); child.wait()

save(output / 'supervisor.json', state)
gate_started = time.monotonic()
for mode in (('w1_clean_timing',) if a.w1_clean_timing else ('w1_vqa_controls',) if a.w1_vqa_controls else ('w1_vqa',) if a.w1_vqa else ('w1_imaging',) if a.w1_imaging else ('w1_replay',) if a.w1_replay else ('w1d_cal',) if a.w1d_cal else ('stage_a','stage_b') if a.stage_witness else ('w1_same_state',) if a.w1_same_state else ('w1_parity',) if a.w1_parity else ('guardrail_pipeline',) if a.guardrail_only else ('core_model_load',) if a.probe_only else ('native', 'worldcache')):
    admission = query_gpu()
    if admission['pids'] or admission['memory_used_mib'] > 1024:
        state.update(status='RESOURCE_BUSY', admission=admission); break
    seconds_left = remaining - sum(arm['wall_seconds'] for arm in state['arms'])
    if seconds_left <= 0: state['status'] = 'BUDGET_STOP'; break
    if a.stage_witness:
        seconds_left = min(seconds_left, 900 - (time.monotonic() - gate_started))
        if seconds_left <= 10: state['status'] = 'PROBE_TIMEOUT'; break
    elif is_probe:
        seconds_left = min(seconds_left, 14400 if a.w1_clean_timing else 300 if a.w1_vqa_controls else 900 if a.w1_vqa else 600 if a.w1_imaging else 3000 if a.w1_replay else 6000 if a.w1d_cal else 900 if (a.w1_parity or a.w1_same_state) else 420)
    command = ['timeout', '--kill-after=10', str(max(1, int(seconds_left) - 10)),
               a.python, str(project / 'scripts/run_f1_case_set.py'), '--project', str(project),
               '--mode', mode, '--gpu-uuid', a.gpu_uuid, '--output', str(output / mode)]
    if is_probe:
        command = ['timeout', '--kill-after=10', str(max(1, int(seconds_left) - 10)), a.python,
                   str(project / ('scripts/run_w1_clean_timing.py' if a.w1_clean_timing else 'scripts/run_w1_vqa_controls.py' if a.w1_vqa_controls else 'scripts/run_w1_vqa.py' if a.w1_vqa else 'scripts/run_w1_imaging.py' if a.w1_imaging else 'scripts/run_w1_replay.py' if a.w1_replay else 'scripts/run_w1d_cal.py' if a.w1d_cal else 'scripts/check_stage_witness.py' if a.stage_witness else 'scripts/check_w1_parity.py' if (a.w1_parity or a.w1_same_state) else 'scripts/check_guardrail_pipeline.py' if a.guardrail_only else 'scripts/check_model_load.py')), '--project', str(project),
                   '--gpu-uuid', a.gpu_uuid, '--receipt', str((output / mode / 'witness.json') if a.stage_witness else output / ('w1-clean-timing.json' if a.w1_clean_timing else 'w1-vqa-controls.json' if a.w1_vqa_controls else 'w1-vqa.json' if a.w1_vqa else 'w1-imaging.json' if a.w1_imaging else 'w1-replay.json' if a.w1_replay else 'w1d-cal.json' if a.w1d_cal else 'w1-same-state.json' if a.w1_same_state else 'w1-parity.json' if a.w1_parity else 'guardrail-pipeline.json' if a.guardrail_only else 'core-model-load.json'))]
    if a.deterministic_decode:
        command.append('--deterministic-decode')
    if a.w1_same_state:
        command.append('--same-state')
        if a.w1_recent_calibration:
            command.append('--same-state-recent')
    env = dict(os.environ, PYTHONPATH='.:packages/cosmos-oss:packages/cosmos-cuda',
               CUDA_VISIBLE_DEVICES=a.gpu_uuid, HF_HUB_CACHE=str(project / 'hfhub'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    if a.w1_vqa or a.w1_vqa_controls:
        env.update(USE_TF='0',FORCE_QWENVL_VIDEO_READER='decord')
    started = time.time()
    with (output / f'{mode}.log').open('w') as log, (output / f'{mode}-gpu.jsonl').open('w') as monitor:
        child = subprocess.Popen(command, cwd=runtime, env=env, stdout=log, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True, pass_fds=(lock.fileno(),))
        state.update(status='RUNNING', current_mode=mode, child_pid=child.pid,
                     child_started_unix=started, admission=admission, command=command)
        save(output / 'supervisor.json', state)
        reason = None
        try:
            while child.poll() is None:
                if time.time() - started >= max(0, seconds_left - 10):
                    reason = 'PROBE_TIMEOUT' if is_probe else 'BUDGET_STOP'; stop(child); break
                observed = query_gpu(); monitor.write(json.dumps(observed) + '\n'); monitor.flush()
                for pid in observed['pids']:
                    try: group = os.getpgid(pid)
                    except ProcessLookupError: continue
                    if group != child.pid:
                        reason = 'GPU_CONFLICT'; stop(child); break
                if reason: break
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired: pass
        except BaseException:
            reason = 'SUPERVISOR_ERROR'; stop(child); raise
        finally:
            stop(child)
            wall = time.time() - started
            state['arms'].append({'mode': mode, 'pid': child.pid, 'exit_code': child.returncode,
                                  'wall_seconds': wall, 'stop_reason': reason})
            budget['used_gpu_hours'] += wall / 3600
            budget['gpu_jobs_launched'] += 1
            budget['status'] = ('W1_CLEAN_TIMING_REQUIRES_REVIEW' if a.w1_clean_timing else 'W1_VQA_CONTROLS_REQUIRES_REVIEW' if a.w1_vqa_controls else 'W1_VQA_REQUIRES_REVIEW' if a.w1_vqa else 'W1_IMAGING_REQUIRES_REVIEW' if a.w1_imaging else 'W1_REPLAY_REQUIRES_REVIEW' if a.w1_replay else 'W1D_CAL_REQUIRES_REVIEW' if a.w1d_cal else 'STAGE_WITNESS_REQUIRES_REVIEW' if a.stage_witness else 'W1_SAME_STATE_REQUIRES_REVIEW' if a.w1_same_state else 'W1_PARITY_REQUIRES_REVIEW' if a.w1_parity else 'F0_GUARDRAIL_PROBE_REQUIRES_REVIEW' if a.guardrail_only else 'F0_LOAD_PROBE_REQUIRES_REVIEW' if a.probe_only
                                else 'F1_EXECUTION_REQUIRES_RESULT_REVIEW')
            budget['accounting'] = 'Conservative single-GPU process wall time including imports, loading, failure and flush; see supervisor receipts'
            save(budget_path, budget)
            state['status'] = reason or ('ARM_EXITED' if child.returncode == 0 else 'FAILED')
            save(output / 'supervisor.json', state)
    if reason or child.returncode != 0: break
else:
    state['status'] = ('W1_CLEAN_TIMING_EXITED_REQUIRES_REVIEW' if a.w1_clean_timing else 'W1_VQA_CONTROLS_EXITED_REQUIRES_REVIEW' if a.w1_vqa_controls else 'W1_VQA_EXITED_REQUIRES_REVIEW' if a.w1_vqa else 'W1_IMAGING_EXITED_REQUIRES_REVIEW' if a.w1_imaging else 'W1_REPLAY_EXITED_REQUIRES_REVIEW' if a.w1_replay else 'W1D_CAL_EXITED_REQUIRES_REVIEW' if a.w1d_cal else 'STAGE_WITNESS_EXITED_REQUIRES_REVIEW' if a.stage_witness else 'W1_SAME_STATE_EXITED_REQUIRES_REVIEW' if a.w1_same_state else 'W1_PARITY_EXITED_REQUIRES_REVIEW' if a.w1_parity else 'GUARDRAIL_PROBE_EXITED_REQUIRES_REVIEW' if a.guardrail_only else 'CORE_LOAD_EXITED_REQUIRES_STATE_REVIEW' if a.probe_only
                       else 'PAIR_EXITED_AWAITING_RECEIPT_AND_VIDEO_REVIEW')
save(output / 'supervisor.json', state)
