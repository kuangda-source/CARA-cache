#!/usr/bin/env python3
"""Read original terminal handles and preserve native evidence; never submit work.

Run locally from the repository after the bound GPU and CPU drivers exit.
Failures are retained without scoring or accepting a successful subset.
"""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys


LAUNCH = Path('reports/wc_cfg_guided_teacher_r1_GPU_launch_20261009.json')
PREFIX = 'reports/wc_cfg_guided_teacher_r1_terminal_20261009_'


def main():
    launch = json.loads(LAUNCH.read_text())
    remote = 'L=' + repr(launch) + '\n' + r'''
import base64,fcntl,gzip,hashlib,json,math,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=pathlib.Path(L['stage']);post=pathlib.Path(L['post_CPU_stage'])
run=root/'outputs'/L['run_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sup=json.loads((run/'supervisor.json').read_text())
receipt=json.loads((post/'receipt.json').read_text())
pids=[L['supervisor_pid'],sup['child_pid'],L['post_CPU_pid']]
if 'CPU_child_pid' in receipt:pids.append(receipt['CPU_child_pid'])
live=[pid for pid in pids if pathlib.Path('/proc/'+str(pid)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_HANDLES_STILL_LIVE_NO_TERMINAL_CAPTURE',
  'original_live_PIDs':live,'GPU_status':sup['status'],'CPU_status':receipt['status'],
  'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert sup['pid']==L['supervisor_pid'] and receipt['pid']==L['post_CPU_pid']
assert sup['source_revision']==receipt['source_revision']==L['source_revision']
assert sup['status']=='EXITED_REQUIRES_RESULT_AUDIT'
assert receipt['bound_supervisor_pid']==sup['pid']
if 'bound_child_pid' in receipt:assert receipt['bound_child_pid']==sup['child_pid']
assert sha(stage/'teacher-config.json')==L['config_sha256']
c=json.loads((stage/'teacher-config.json').read_text())
payload={name:sha(stage/name) for name in c['payload_sha256']}
assert payload==c['payload_sha256'] and len(payload)==64
assert sha(post/'driver.py')==L['post_driver_sha256']
binding=json.loads((post/'binding.json').read_text())
assert binding['source_revision']==L['source_revision'] and binding['supervisor_pid']==sup['pid']
assert binding['stage']==L['stage'] and binding['run_id']==L['run_id']
assert binding['scorer_sha256']==payload['scripts/audit_score_wc_cfg_guided_teacher_cpu.py']
assert c['preregistration']['scope_counts']==L['planned_scope']
assert not sup['legacy_seconds_deadline_active']
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==sup['budget_after'] and not any('inflight' in key for key in budget)
assert sup['budget_before']==L['budget_before']
assert math.isclose(budget['used_gpu_hours'],L['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
assert budget['cap_gpu_hours']==50 and budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
gpu=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
assert not any(line.split(',')[0].strip()==c['gpu_uuid'] for line in apps.splitlines())
files={'runner':run/'diagnostic/receipt.json','supervisor':run/'supervisor.json',
 'CPU_receipt':post/'receipt.json','CPU_driver_log':post/'driver.log','GPU_log':run/'run.log',
 'GPU_monitor':run/'gpu-monitor.jsonl','budget':root/'reports/budget.json',
 'config':stage/'teacher-config.json','CPU_binding':post/'binding.json','CPU_driver':post/'driver.py'}
for key,name in [('CPU_score','score.json'),('CPU_score_log','score.log')]:
 if (post/name).exists():files[key]=post/name
success=sup.get('exit_code')==receipt.get('exit_code')==0
if success:
 assert receipt['status']=='TEACHER_POST_GPU_CPU_AUDIT_SCORE_COMPLETE'
 assert sha(post/'score.json')==receipt['score_sha256']
 score=json.loads((post/'score.json').read_text())
 assert score['status']=='TEACHER_COMPLETE_TWO_VIDEO_FIVE_STATE_FOUR_CELL_TWO_REPEAT_RAW_AUDIT_AND_CPU_SCORES_NOT_ENDPOINT'
 assert score['scope']==L['planned_scope'] and score['source_revision']==L['source_revision']
 assert (score['local_CFG_pairs'],score['diagnostic_net_calls'],score['raw_tensor_count'],score['strict_repeat_groups'],score['complete_real_components'])==(40,80,120,20,1216)
 assert len(score['videos'])==2 and len(score['origins'])==5 and not score['CUDA_initialized']
 assert score['budget']==budget and score['runner_sha256']==sha(run/'diagnostic/receipt.json')
 for key in ('endpoint_or_absolute_physics_quality_claim','formal_RV_labels','independent_CONF','clean_speed_measurement'):assert score[key] is False
items={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 items[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
 'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'TEACHER_ORIGINAL_TERMINAL_FAILURE_NATIVE_CAPTURE_SCOPE_RETAINED',
 'observed_unix':time.time(),'source_revision':L['source_revision'],'run_id':L['run_id'],
 'original_PIDs_absent':pids,'GPU_exit_code':sup.get('exit_code'),'CPU_exit_code':receipt.get('exit_code'),
 'GPU_status':sup['status'],'CPU_status':receipt['status'],'planned_scope':L['planned_scope'],
 'config_sha256':L['config_sha256'],'payload_after_sha256':payload,
 'post_driver_sha256':sha(post/'driver.py'),'post_binding_sha256':sha(post/'binding.json'),
 'lock_released':True,'GPU_observation':gpu,'compute_apps':apps,'budget_settled':budget,
 'actual_GPU_wall_seconds':sup['wall_seconds'],'GPU_submissions_by_capture':0,
 'terminal_capture_is_not_endpoint_quality_or_CONF':True}
print(json.dumps({'capture':capture,'native':items}))
'''
    process = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
        input=remote, text=True, capture_output=True, timeout=55,
    )
    if process.returncode:
        raise RuntimeError(process.stderr[-5000:])
    result = json.loads(process.stdout)
    capture = result['capture']
    if not result['native']:
        print(json.dumps(capture))
        return 2
    output = Path(PREFIX + 'capture.json')
    targets = {key: Path(PREFIX + key + '_native.gz') for key in result['native']}
    assert not output.exists() and all(not path.exists() for path in targets.values())
    verified = {}
    for key, item in result['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True)
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        verified[key] = (compressed, raw)
    capture['files'] = {}
    for key, item in result['native'].items():
        targets[key].write_bytes(verified[key][0])
        capture['files'][key] = {k: v for k, v in item.items() if k != 'gzip_base64'}
        capture['files'][key]['local_path'] = str(targets[key])
    Path('reports/budget.json').write_bytes(verified['budget'][1])
    output.write_text(json.dumps(capture, indent=2) + '\n')
    print(json.dumps({key: capture[key] for key in (
        'status', 'original_PIDs_absent', 'GPU_exit_code', 'CPU_exit_code',
        'planned_scope', 'actual_GPU_wall_seconds', 'GPU_observation', 'budget_settled',
    )}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
