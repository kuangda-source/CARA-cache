#!/usr/bin/env python3
"""Capture one original N05 admission; never read scientific progress or relaunch."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PY = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def accept_admission(value):
    launch = value['launch']
    supervisor = value['supervisor']
    assert launch['run_id'] == 'wc-paper-n05-core11-cal4-full66-r1'
    assert supervisor['status'] == 'N05_CORE66_GPU_RUNNING'
    for key in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid'):
        assert supervisor[key] == launch[key], key
    assert supervisor['scope_counts'] == launch['scope_counts']
    assert supervisor['pid'] == launch['supervisor_pid']
    assert value['registration_sha256'] == launch['registration_sha256']
    for key, expected in (
        ('supervisor', launch['supervisor_identity']),
        ('child', supervisor['child_identity']),
    ):
        actual = value['processes'][key]
        assert actual['state'] not in (None, 'Z', 'X'), key
        assert actual['pid'] == expected['pid'], key
        assert actual['start_ticks'] == expected['start_ticks'], key
    post = value['processes']['post']
    assert post['state'] not in (None, 'Z', 'X')
    assert post['pid'] == launch['post_watcher_pid']
    assert post['start_ticks'] is not None
    assert 'watch_wc_paper_N05_post_cpu_r1.py' in post['command']
    assert str(launch['supervisor_pid']) in post['command']
    assert str(launch['supervisor_identity']['start_ticks']) in post['command']
    assert 'run_wc_paper_N05_core66_r1.py' in value['processes']['child']['command']
    assert value['own_UUID_lock_busy'] is True
    job = value['pool']['jobs'][launch['run_id']]
    assert job['status'] == 'RESERVED_OR_RUNNING'
    for key in ('source_revision', 'launch_id', 'gpu_uuid'):
        assert job[key] == launch[key], key
    assert job['billed_limit_GPUh'] == launch['billed_limit_GPUh'] == 9.5
    assert job['supervisor_pid'] == supervisor['pid']
    assert value['pool']['cap_gpu_hours'] == 104.97136333301378
    assert value['pool']['origin_used_gpu_hours'] == 79.99637737158223
    assert value['pool_accounting_independently_equal'] is True
    assert value['pool']['available_gpu_hours'] >= 0
    assert value['scientific_runner_or_partial_outputs_read'] is False
    return {
        'status': 'N05_CORE66_GPU_ADMISSION_AND_ORIGINAL_HANDLES_ACCEPTED',
        'source_revision': launch['source_revision'],
        'supervisor_pid': supervisor['pid'],
        'child_pid': supervisor['child_pid'],
        'post_watcher_pid': launch['post_watcher_pid'],
        'scope_counts': supervisor['scope_counts'],
        'pool_totals': {k: value['pool'][k] for k in (
            'used_gpu_hours', 'reserved_gpu_hours', 'available_gpu_hours')},
        'next_check_not_before_unix': launch['next_check_not_before_unix'],
        'scientific_result_claim': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    launch = json.loads(args.launch_ref.read_text())['dispatch']
    assert launch['run_id'] == 'wc-paper-n05-core11-cal4-full66-r1'
    assert launch['stage'].endswith('/.sync/wc-paper-n05-core66-production-cpu-r2-20261016')
    code = 'LAUNCH=' + repr(launch) + '\n' + r'''
import fcntl,json,pathlib,sys,time
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1]
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,sha
value=dict(launch=LAUNCH,observed_unix=time.time(),processes={},
 registration_sha256=sha(stage/'registration.json'),pool=BudgetPool(root).read(),
 scientific_runner_or_partial_outputs_read=False)
supervisor_path=root/'outputs'/LAUNCH['run_id']/'supervisor.json'
if supervisor_path.exists():
 value['supervisor']=json.loads(supervisor_path.read_text())
 value['supervisor_sha256']=sha(supervisor_path)
 for name,pid in [('supervisor',LAUNCH['supervisor_pid']),
                  ('child',value['supervisor'].get('child_pid')),
                  ('post',LAUNCH['post_watcher_pid'])]:
  if pid is not None:value['processes'][name]=process_identity(pid)
else:
 for filename in ('supervisor.log','supervisor-admission-failure.json'):
  path=stage/filename
  if path.exists():value[filename]=path.read_text(errors='replace')[-6000:]
value['pool_accounting_independently_equal']=all(
 value['pool'][key]==result for key,result in BudgetPool.accounting(value['pool']).items())
lock=root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')
with lock.open('r+') as handle:
 try:
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  value['own_UUID_lock_busy']=False
  fcntl.flock(handle,fcntl.LOCK_UN)
 except BlockingIOError:value['own_UUID_lock_busy']=True
print(json.dumps(value,allow_nan=False))
'''
    result = subprocess.run([
        'ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o',
        'ClearAllForwardings=yes', 'gkd_minchen', PY + ' -c ' + shlex.quote(code),
    ], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    value = json.loads(result.stdout)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print(json.dumps(accept_admission(value)))


if __name__ == '__main__':
    main()
