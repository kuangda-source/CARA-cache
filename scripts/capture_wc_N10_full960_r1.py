#!/usr/bin/env python3
"""One original N10 admission/health/final capture; never starts new work."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
REMOTE=r'''
import base64,collections,fcntl,gzip,hashlib,json,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
M=json.loads(sys.stdin.buffer.read());L=M['launch'];MODE=M['mode']
stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project']);out=root/'outputs'/L['run_id']
assert stage.relative_to(root).parts[0]=='.sync'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==L['source_revision']
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity
def artifact(path,raw_body=False):
 if not path.is_file():return dict(exists=False)
 before=path.stat();raw=path.read_bytes();after=path.stat()
 assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
 r=dict(exists=True,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),raw_base64=base64.b64encode(raw).decode())
 if not raw_body:
  try:r['data']=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
  except Exception as e:r.update(parse_error_type=type(e).__name__,parse_error=str(e),raw_base64=base64.b64encode(raw).decode())
 return r
sup=artifact(out/'supervisor.json')
if not sup['exists']:sup=artifact(stage/'N10-supervisor-fallback.json')
s=sup.get('data') or {};runner=artifact(out/'runner.json');rr=runner.get('data') or {}
handles=dict(supervisor=L['supervisor_identity'],child=s.get('child_identity'))
processes={k:process_identity(x['pid']) for k,x in handles.items() if x}
live={k:bool(x and x['pid']==processes[k]['pid'] and x['start_ticks']==processes[k]['start_ticks']
 and processes[k]['state'] not in (None,'Z','X')) for k,x in handles.items() if x}
v=dict(status='N10_FULL960_ORIGINAL_ONCE_CAPTURE',mode=MODE,observed_unix=time.time(),launch=L,
 registration_sha256=sha(stage/'registration.json'),original_processes=processes,expected_original_handles=handles,
 original_live_handles=live,pool=BudgetPool(root).read(),files={},GPU_submissions=0,ledger_written=False,
 own_UUID_lock_exists=False,own_UUID_lock_free=False)
try:
 v['own_GPU']=subprocess.check_output(['nvidia-smi','-i',L['gpu_uuid'],'--query-gpu=uuid,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 v['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
except Exception as e:v['GPU_telemetry_error']=str(e)
lock=root/'.sync/gpu-locks'/(L['gpu_uuid']+'.lock')
if lock.is_file():
 v['own_UUID_lock_exists']=True
 with lock.open('r') as h:
  try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_UUID_lock_free']=True;fcntl.flock(h,fcntl.LOCK_UN)
  except BlockingIOError:pass
v['other_reservation_identities']={name:process_identity(j['supervisor_pid']) for name,j in v['pool']['jobs'].items()
 if name!=L['run_id'] and j['status']=='RESERVED_OR_RUNNING' and j['gpu_uuid']==L['gpu_uuid']}
if MODE!='terminal' or any(live.values()):
 v.update(scientific_partial_read=False,technical_progress=dict(supervisor_status=s.get('status'),runner_status=rr.get('status'),
  registered_metric_positions=960,original_child_exit_code=s.get('child_exit_code')),
  original_admission_job=v['pool']['jobs'].get(L['run_id']))
 if MODE=='terminal':v['status']='N10_FULL960_STILL_RUNNING_TECHNICAL_ONLY'
else:
 v.update(registration=reg,registration_artifact=artifact(stage/'registration.json'),
  payload_actual_sha256={n:sha(stage/n) if (stage/n).is_file() else None for n in reg['payload_sha256']})
 v['files'].update(supervisor=sup,runner=runner,journal=artifact(out/'original-metric-events.jsonl',True),metrics=artifact(out/'metric-results.json.gz'))
 bill=artifact(out/'billing.json')
 if not bill['exists']:bill=artifact(stage/'N10-billing-fallback.json')
 v['files']['billing']=bill
 for name,ref in [('production_CPU','CPU-scoring-entry-result.json'),('production_bundle','N10-production-CPU-bundle-result.json'),
  ('CPU_launch','N10-production-CPU-launch.json'),('CPU_exit','N10-production-CPU-exit.json'),
  ('CPU_independent_remote','N10-production-CPU-independent-acceptance.json'),('authorization','N10-launch-authorization.json'),
  ('config','N10-production-config.json'),('admission_failure','N10-supervisor-admission-failure.json')]:v['files'][name]=artifact(stage/ref)
 config=v['files']['config'].get('data')
 if config:
  for name in ('accepted_inputs','model_CPU_acceptance','model_CPU_registration','model_resources','unpriced_scope','whole_card_cost'):
   v['files'][name]=artifact(stage/config['references'][name]['ref'])
for name,path in [('GPU',out/'GPU.log'),('supervisor',stage/'N10-supervisor.log')]:
 if path.is_file():
  with path.open('rb') as h:h.seek(0,2);size=h.tell();h.seek(max(0,size-32000));tail=h.read().decode(errors='replace')
  v.setdefault('error_tags',{})[name]=[x for x in ('CUDA out of memory','Traceback','RuntimeError','AssertionError','No space left') if x in tail]
  if MODE=='terminal' and not any(live.values()):v[name+'_log_tail']=tail
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--mode',choices=['admission','health','terminal'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Use the existing original capture offline, not a duplicate observation')
    envelope=json.loads(a.launch_ref.read_text());launch=envelope['dispatch']
    if launch['status']!='N10_FULL960_DISPATCHED_ADMISSION_PENDING':raise ValueError('No original full960 GPU task handle')
    key={'health':'midpoint_health_not_before_unix','terminal':'next_check_not_before_unix'}.get(a.mode)
    if key and time.time()<launch[key]:raise ValueError('Before original N10 check time; no SSH')
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PYTHON+' -c '+shlex.quote(REMOTE)],
            input=json.dumps(dict(launch=launch,mode=a.mode)).encode(),capture_output=True,timeout=180)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        value=json.loads(gzip.decompress(call.stdout))
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        value=dict(status='N10_OBSERVATION_UNKNOWN_NOT_TASK_TERMINAL',launch=launch,error_type=type(e).__name__,error=str(e),no_GPU_relaunch_authority=True)
        with a.output.open('xb') as h:h.write(gzip.compress(json.dumps(value).encode()))
        raise
    if a.mode=='terminal' and value['status']=='N10_FULL960_ORIGINAL_ONCE_CAPTURE':
        try:
            raw=Path(envelope['CPU_capture_ref']).read_bytes();text=Path(envelope['CPU_acceptance_ref']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=envelope['CPU_capture_sha256'] or hashlib.sha256(text).hexdigest()!=envelope['CPU_acceptance_sha256']:
                raise ValueError('Original accepted CPU file bytes changed')
            value.update(CPU_capture=json.loads(gzip.decompress(raw)),CPU_capture_sha256=hashlib.sha256(raw).hexdigest(),
                CPU_independent=json.loads(text),CPU_independent_sha256=hashlib.sha256(text).hexdigest(),
                CPU_capture_raw_base64=base64.b64encode(raw).decode(),CPU_independent_raw_base64=base64.b64encode(text).decode())
        except (OSError,ValueError) as e:
            # Keep the original server observation even if local CPU provenance is unavailable.
            value['local_CPU_provenance_error']=str(e)
    value['collector_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with a.output.open('xb') as h:h.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
    print(json.dumps(dict(receipt=str(a.output),status=value['status'],mode=a.mode,
        original_live_handles=value.get('original_live_handles'),technical_progress=value.get('technical_progress'),
        original_terminal_metrics_available=value.get('files',{}).get('metrics',{}).get('exists'))))


if __name__=='__main__':main()
