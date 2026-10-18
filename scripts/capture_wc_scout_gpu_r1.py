#!/usr/bin/env python3
"""One original-task admission/health/final observation, no new execution."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

REMOTE=r'''
import collections,fcntl,gzip,hashlib,json,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project']);out=root/'outputs'/L['run_id']
assert stage.relative_to(root).parts[0]=='.sync'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==L['source_revision']
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,same_live_process
def read(path):
 if not path.is_file():return None
 raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
sup=read(out/'supervisor.json') or {};runner=read(out/'runner.json') or {}
handles={'supervisor':L.get('supervisor_identity'),'post':L.get('post_watcher_identity'),'runner':sup.get('child_identity')}
processes={k:process_identity(x['pid']) for k,x in handles.items() if x}
live={k:bool(x and processes.get(k) and x['start_ticks']==processes[k]['start_ticks'] and processes[k]['state'] not in (None,'Z','X')) for k,x in handles.items()}
value=dict(status='SCOUT_ORIGINAL_ONCE_CAPTURE',mode=MODE,observed_unix=time.time(),launch=L,
 registration_sha256=sha(stage/'registration.json'),pool=BudgetPool(root).read(),original_processes=processes,
 original_live_handles=live,expected_original_handles=handles,GPU_submissions=0,ledger_written=False,own_UUID_lock_exists=False,own_UUID_lock_free=False)
try:
 value['own_GPU']=subprocess.check_output(['nvidia-smi','-i',L['gpu_uuid'],'--query-gpu=uuid,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 value['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
except (OSError,subprocess.SubprocessError) as e:value['GPU_telemetry_error']=str(e)
lock=root/'.sync/gpu-locks'/(L['gpu_uuid']+'.lock')
if lock.is_file():
 value['own_UUID_lock_exists']=True
 with lock.open('r') as h:
  try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);value['own_UUID_lock_free']=True;fcntl.flock(h,fcntl.LOCK_UN)
  except BlockingIOError:pass
value['other_reservation_identities']={k:process_identity(j['supervisor_pid']) for k,j in value['pool']['jobs'].items()
 if k!=L['run_id'] and j['status']=='RESERVED_OR_RUNNING' and j['gpu_uuid']==L['gpu_uuid'] and j.get('supervisor_pid')}
if MODE!='terminal' or any(live.values()):
 rows=runner.get('runs',[])
 value.update(scientific_partial_read=False,technical_progress=dict(supervisor_status=sup.get('status'),runner_status=runner.get('status'),
  planned_slots=L['scope_counts']['total_paths'],observed_slots=len(rows),states=dict(collections.Counter(r.get('status','UNKNOWN') for r in rows)),not_reached=L['scope_counts']['total_paths']-len(rows)))
 value['admission_job']=value['pool']['jobs'].get(L['run_id'])
 if MODE=='terminal':value['status']='SCOUT_ORIGINAL_STILL_RUNNING_TECHNICAL_ONLY'
else:
 value.update(registration=reg,payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
  runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']})
 meta=read(stage/('manifests/scout_'+L['kind'].lower()+'_lifecycle_dependency_r1_20261018.json'));entry=pathlib.Path(meta['entry_stage'])
 value.update(entry_registration=read(entry/'registration.json'),entry_registration_sha256=sha(entry/'registration.json'),
  entry_payload_actual_sha256={n:sha(entry/n) for n in read(entry/'registration.json')['payload_sha256']})
 for key,path in [('supervisor',out/'supervisor.json'),('runner',out/'runner.json'),('billing',out/'billing.json'),
  ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),
  ('production_CPU',stage/'scout-lifecycle-CPU-proof.json'),('CPU_bundle',stage/'scout-lifecycle-CPU-bundle.json'),
  ('CPU_independent',stage/'scout-lifecycle-CPU-independent-acceptance.json'),('CPU_launch',stage/'scout-lifecycle-CPU-launch.json'),
  ('authorization',stage/'scout-GPU-authorization.json'),('upstream',stage/'scout-upstream-capture.json.gz'),
  ('upstream_acceptance',stage/'scout-upstream-acceptance.json'),
  ('dependency',stage/('manifests/scout_'+L['kind'].lower()+'_lifecycle_dependency_r1_20261018.json')),
  ('config',stage/meta['config_ref']),('admission_failure',stage/'scout-admission-failure.json')]:
  if path.is_file():value[key]=read(path);value[key+'_sha256']=sha(path)
 value['entry_config_file_sha256']=sha(entry/meta['config_ref'])
 value['original_artifacts']={}
 for row in (value.get('final',{}).get('rows',[])+runner.get('runs',[])+
             value.get('final',{}).get('Native_reference_bindings',[])+value.get('final',{}).get('old_CAL_bindings',[])):
  for name in ('final_artifact','warm_guided_artifact','scout_vectors_artifact','video_artifact'):
   if name not in row:continue
   info=row[name];path=pathlib.Path(info['path']).resolve()
   assert path.is_relative_to((root/'outputs').resolve())
   if info['path'] not in value['original_artifacts']:
    value['original_artifacts'][info['path']]=dict(sha256=sha(path),bytes=path.stat().st_size) if path.is_file() else dict(missing=True)
for key,path in [('GPU',out/'GPU.log'),('supervisor',stage/'supervisor.log'),('post',stage/'post-CPU.log')]:
 if path.is_file():
  with path.open('rb') as h:h.seek(0,2);n=h.tell();h.seek(max(0,n-65536));tail=h.read().decode(errors='replace')
  value.setdefault('error_tags',{})[key]=[x for x in ('CUDA out of memory','Traceback','RuntimeError','AssertionError','No space left') if x in tail]
  if MODE=='terminal' and not any(live.values()):value[key+'_log_tail']=tail[-18000:]
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--mode',choices=['admission','halfway','terminal'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Read the original receipt offline, never observe twice')
    launch=json.loads(a.launch_ref.read_text())['dispatch']
    if launch['status']!='SCOUT_COMPLETE_CARD_DISPATCHED_ADMISSION_PENDING' or launch['scope_counts']['total_paths'] not in (12,24):
        raise ValueError('Original whole scout handle required')
    key={'halfway':'halfway_check_not_before_unix','terminal':'next_check_not_before_unix'}.get(a.mode)
    if key and time.time()<launch[key]:raise ValueError('Before original check time; no SSH')
    code='L='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+REMOTE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],capture_output=True,timeout=600)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
    except (OSError,subprocess.TimeoutExpired,RuntimeError) as e:
        value=dict(status='SCOUT_OBSERVATION_UNKNOWN_NOT_TASK_TERMINAL',launch=launch,
            error_type=type(e).__name__,error=str(e),original_task_terminal=False,no_GPU_relaunch_authority=True)
        with a.output.open('xb') as h:h.write(gzip.compress(json.dumps(value).encode()))
        raise
    with a.output.open('xb') as h:h.write(call.stdout)
    value=json.loads(gzip.decompress(call.stdout))
    print(json.dumps(dict(receipt=str(a.output),status=value['status'],mode=a.mode,
        original_processes=value['original_processes'],technical_progress=value.get('technical_progress'),
        final_status=value.get('final',{}).get('status'),own_UUID_lock_free=value['own_UUID_lock_free'],
        collector_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())))


if __name__=='__main__':main()
