#!/usr/bin/env python3
"""Recover a fenced, already admitted Window24 handle; never submit GPU work."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


REMOTE = r'''
import hashlib,json,math,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
stage=root/U['stage'];auth=U['authorization'];run=auth['whole_card_run']
assert stage.parent==root/'.sync' and run=='wc-drop1-correction-window-cal4-full24-r1'
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,same_live_process,atomic_json
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
assert sha(stage/'registration.json')==auth['registration_sha256']
assert reg['source_revision']==auth['source_revision']
fence=json.loads((stage/'window24-GPU-dispatch-fence.json').read_text())
assert fence['launch_id']==auth['launch_id']==S['launch_id']
assert json.loads((stage/'window24-GPU-authorization.json').read_text())==auth
assert sha(stage/'window24-GPU-authorization.json')==AUTH_SHA
assert sha(stage/'window24-production-CPU-independent-acceptance.json')==auth['independent_CPU_acceptance_sha256']
assert sha(stage/'window24-production-CPU-result.json')==auth['production_CPU_sha256']
assert sha(stage/'configs/wc_drop1_correction_window_full24_production_r1_20261018.json')==auth['config_sha256']
sup=json.loads((root/'outputs'/run/'supervisor.json').read_text())
assert sup['status']=='WINDOW24_GPU_RUNNING'
for key in ('launch_id','source_revision','gpu_uuid','config_sha256','registration_sha256','scope_counts'):
 assert sup[key]==S[key]==auth[key]
assert sup['supervisor_identity']['start_ticks']==S['supervisor_identity']['start_ticks']
assert same_live_process(sup['supervisor_identity'])
actual=process_identity(sup['supervisor_identity']['pid'])
assert str(stage/'scripts/supervise_wc_drop1_window24_r1.py') in actual['command']
pool=BudgetPool(root).read();job=pool['jobs'][run]
assert job['status']=='RESERVED_OR_RUNNING' and job['supervisor_pid']==actual['pid']
assert job['supervisor_start_ticks']==actual['start_ticks']
assert job['launch_id']==auth['launch_id'] and job['authorization_sha256']==AUTH_SHA
assert not (stage/'window24-GPU-launch.json').exists()
assert not (stage/'post-watcher.log').exists() and not (stage/'post-CPU-exit.json').exists()
post_script=str(stage/'scripts/watch_wc_drop1_window24_post_cpu_r1.py')
assert sha(pathlib.Path(post_script))==reg['payload_sha256']['scripts/watch_wc_drop1_window24_post_cpu_r1.py']
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:argv=(proc/'cmdline').read_bytes().split(bytes([0]))
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 assert not (len(argv)>1 and argv[1].decode(errors='replace')==post_script),'Original post already exists: recover only'
with (stage/'window24-post-recovery-dispatch-fence.json').open('x') as f:
 json.dump(dict(launch_id=auth['launch_id'],original_supervisor=actual,recovery_source_sha256=SOURCE_SHA,created_unix=time.time()),f)
 f.flush();os.fsync(f.fileno())
started=sup['started_unix']
receipt=dict(status='WINDOW24_COMPLETE24_DISPATCHED_ADMISSION_PENDING',source_revision=auth['source_revision'],
 launch_id=auth['launch_id'],stage=str(stage),project=str(root),run_id=run,gpu_uuid=auth['gpu_uuid'],
 registration_sha256=auth['registration_sha256'],config_sha256=auth['config_sha256'],production_CPU_sha256=auth['production_CPU_sha256'],
 authorization_sha256=AUTH_SHA,independent_CPU_acceptance_sha256=auth['independent_CPU_acceptance_sha256'],
 bound_input_fingerprint=auth['bound_input_fingerprint'],scope_counts=auth['scope_counts'],supervisor_pid=actual['pid'],supervisor_identity=actual,
 post_watcher_pid=None,post_watcher_identity=None,command=actual['command'].rstrip().split(' '),started_unix=started,
 forecast_complete_GPUh=auth['forecast_complete_GPUh'],billed_limit_GPUh=auth['billed_limit_GPUh'],
 halfway_check_not_before_unix=started+math.ceil(auth['forecast_complete_GPUh']*1800),
 next_check_not_before_unix=started+math.ceil(auth['forecast_complete_GPUh']*3600+900),
 actual_GPU_admission_accepted_by_dispatch=False,new_quality_or_speed_result=False,
 original_missing_receipt_reconstructed=True,started_unix_basis='ORIGINAL_SUPERVISOR_GPU_ADMISSION',
 original_dispatch_fence_created_unix=fence['created_unix'],recovered_at_unix=time.time(),GPU_relaunches=0,
 recovery_source_sha256=SOURCE_SHA,recovery_capture_sha256=CAPTURE_SHA,original_unknown_receipt_sha256=UNKNOWN_SHA)
atomic_json(stage/'window24-GPU-launch.json',receipt)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[sys.executable,post_script,'--project',str(root),'--stage',str(stage),
 '--supervisor-pid',str(actual['pid']),'--supervisor-start-ticks',str(actual['start_ticks'])]
try:
 with (stage/'post-watcher.log').open('xb') as f:
  post=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=env)
 identity=process_identity(post.pid)
 receipt.update(post_watcher_pid=post.pid,post_watcher_identity=identity,post_command=command)
 atomic_json(stage/'window24-GPU-launch.json',receipt)
 for attempt in range(20):
  if identity.get('command') and post_script in identity['command']:break
  time.sleep(.025);identity=process_identity(post.pid)
 assert identity['state'] not in (None,'Z','X') and post_script in identity['command']
 receipt.update(post_watcher_pid=post.pid,post_watcher_identity=identity,post_command=command)
except BaseException as exc:
 receipt.update(post_recovery_error_type=type(exc).__name__,post_recovery_error=str(exc));raise
finally:
 atomic_json(stage/'window24-GPU-launch.json',receipt)
 print(json.dumps(receipt,allow_nan=False))
'''


def validate_recovery(unknown, captured):
    if unknown['status'] != 'WINDOW24_GPU_DISPATCH_OBSERVATION_UNKNOWN_NO_REPLAY':
        raise ValueError('Original unknown dispatch must be retained')
    if captured.get('unknown_launch') != unknown or captured.get('GPU_submissions') != 0:
        raise ValueError('Exact read-only original recovery capture required')
    auth = unknown['authorization']; sup = captured.get('supervisor_technical') or {}
    if sup.get('status') != 'WINDOW24_GPU_RUNNING' or captured.get('post_log_exists'):
        raise ValueError('Only a live original supervisor with missing post registration is eligible')
    for key in ('launch_id', 'source_revision', 'gpu_uuid', 'config_sha256', 'registration_sha256', 'scope_counts'):
        if sup.get(key) != auth.get(key):
            raise ValueError('Original supervisor identity or complete scope differs: '+key)
    actual = captured['matching_original_stage_processes']
    if len(actual) != 1 or actual[0]['pid'] != sup['supervisor_identity']['pid'] or actual[0]['start_ticks'] != sup['supervisor_identity']['start_ticks']:
        raise ValueError('Exactly one authenticated original supervisor required')
    if 'window24-GPU-launch.json' in captured['files'] or 'post-CPU-exit.json' in captured['files']:
        raise ValueError('An existing receipt/post must be recovered rather than dispatched again')
    if captured['UUID_locks'][auth['gpu_uuid']]['free']:
        raise ValueError('Original admitted GPU lease required')
    return sup, captured['files']['window24-GPU-authorization.json']['sha256']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('unknown-launch','recovery-capture','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Never replay an original recovery operation')
    u_raw=a.unknown_launch.read_bytes();c_raw=a.recovery_capture.read_bytes()
    unknown=json.loads(u_raw);captured=json.loads(gzip.decompress(c_raw));sup,auth_sha=validate_recovery(unknown,captured)
    source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    code='U='+repr(unknown)+'\nS='+repr(sup)+'\nAUTH_SHA='+repr(auth_sha)+'\nSOURCE_SHA='+repr(source_sha)+'\nCAPTURE_SHA='+repr(hashlib.sha256(c_raw).hexdigest())+'\nUNKNOWN_SHA='+repr(hashlib.sha256(u_raw).hexdigest())+'\n'+REMOTE
    error=None
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c '+shlex.quote(code)],capture_output=True,timeout=65)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        result=dict(dispatch=json.loads(call.stdout),authorization=unknown['authorization'],transport_exit_code=0,
                    original_unknown_launch_ref=str(a.unknown_launch),original_recovery_capture_ref=str(a.recovery_capture),
                    recovered_original_task_only=True,GPU_relaunches=0,recovery_source_sha256=source_sha)
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as exc:
        error=str(exc)
        result=dict(status='ORIGINAL_WINDOW24_RECOVERY_OBSERVATION_UNKNOWN_NEVER_REPLAY',error=error,
                    launch_id=unknown['launch_id'],GPU_relaunches=0,recovery_source_sha256=source_sha)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,allow_nan=False))
    if error is not None:raise RuntimeError(error)


if __name__=='__main__':main()
