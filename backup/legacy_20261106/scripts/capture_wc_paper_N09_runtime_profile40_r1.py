#!/usr/bin/env python3
"""One original N09 snapshot: admission, half-time health, or full post-ETA collection."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time


def remote_code(launch, mode):
    return 'LAUNCH=' + repr(launch) + '\nMODE=' + repr(mode) + '\n' + r'''
import collections,fcntl,gzip,hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(LAUNCH['project']).resolve();stage=pathlib.Path(LAUNCH['stage']).resolve()
assert root==pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve() and stage.parent==root/'.sync'
assert LAUNCH['run_id']=='wc-paper-n09-runtime-profile40-r1' and MODE in ('admission','health','terminal')
out=(root/'outputs'/LAUNCH['run_id']).resolve();sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity
CONFIG='configs/wc_paper_N09_runtime_profile40_production_r1_20261016.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def original_path(parent,name):
 relative=pathlib.PurePosixPath(name);assert not relative.is_absolute() and '..' not in relative.parts
 p=(parent/relative).resolve();p.relative_to(parent)
 return p
def read(path):
 if not path.is_file():return dict(exists=False,path=str(path),sha256=None,data=None)
 raw=path.read_bytes();v=dict(exists=True,path=str(path),bytes=len(raw),sha256=sha(raw),data=None)
 try:v['data']=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
 except (ValueError,OSError,EOFError) as error:v['parse_error']=str(error)
 return v
raw=(stage/'registration.json').read_bytes();registration=json.loads(raw)
assert registration['source_revision']==LAUNCH['source_revision'] and sha(raw)==LAUNCH['registration_sha256']
actual={n:sha(original_path(stage,n).read_bytes()) if original_path(stage,n).is_file() else None
        for n in registration['payload_sha256']}
value=dict(status='N09_FULL40_ORIGINAL_ONCE_CAPTURE',mode=MODE,observed_unix=time.time(),launch=LAUNCH,
 registration=registration,registration_sha256=sha(raw),output_root=str(out),payload_actual_sha256=actual,
 payload_verified={n:actual[n]==h for n,h in registration['payload_sha256'].items()},original_processes={},
 GPU_submissions=0,ledger_written=False)
try:value['pool']=BudgetPool(root).read()
except Exception as error:value['pool_read_error']=str(error)
paths=[('supervisor',out/'supervisor.json'),('admission_failure',stage/'N09-supervisor-admission-failure.json')]
if MODE=='terminal':
 paths += [('config',stage/CONFIG),('authorization',stage/'N09-launch-authorization.json'),
  ('independent_CPU_acceptance',stage/'N09-production-CPU-independent-acceptance.json'),
  ('runner',out/'runner.json'),('billing',out/'billing.json'),('final',stage/'N09-CPU-final-results.json'),
  ('post_exit',stage/'N09-post-CPU-exit.json'),('production_CPU',stage/'N09-production-CPU-result.json'),
  ('production_CPU_bundle',stage/'N09-CPU-bundle-result.json'),('production_CPU_launch',stage/'N09-production-CPU-launch.json'),
  ('production_CPU_exit',stage/'N09-production-CPU-exit.json'),
  ('supervisor_fallback',stage/'N09-supervisor-fallback.json'),('billing_fallback',stage/'N09-billing-fallback.json')]
value['original_file_receipts']={}
for key,path in paths:
 info=read(path);value['original_file_receipts'][key]={k:v for k,v in info.items() if k!='data'}
 if info['data'] is not None:value[key]=info['data'];value[key+'_sha256']=info['sha256']
if MODE=='terminal' and value.get('config'):
 assert value['config_sha256']==LAUNCH['config_sha256']
 for key,ref in value['config']['references'].items():
  info=read(original_path(stage,ref['ref']));value['original_file_receipts'][key]={k:v for k,v in info.items() if k!='data'}
  if info['data'] is not None:value[key]=info['data'];value[key+'_sha256']=info['sha256']
 value['profile_scalar_originals']={}
 for row in value.get('runner',{}).get('runs',[]):
  asset=row.get('component_profile_artifact')
  if asset:
   p=pathlib.Path(asset['path']).resolve();p.relative_to(out);info=read(p)
   info['matches_original_row_identity']=info['exists'] and info['sha256']==asset['sha256'] and info['bytes']==asset['bytes']
   value['profile_scalar_originals'][str(p)]=info
if MODE=='health':
 path=out/'runner.json';runner=read(path)
 if runner['data'] is not None:
  data=runner['data'];rows=data.get('runs',[])
  value['technical_progress']=dict(status=data.get('status'),original_runner_positions=len(rows),
   registered_total=40,registered_warmup=10,registered_formal=30,
   generation_status_counts=dict(collections.Counter(r.get('status','UNKNOWN') for r in rows)),
   completed_by_mode=dict(collections.Counter(r.get('mode','UNKNOWN') for r in rows if r.get('status') in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED'))),
   modified_unix=path.stat().st_mtime,no_quality_timing_or_scalar_profile_readout=True)
ids={k:LAUNCH[k] for k in ('supervisor_pid','post_watcher_pid') if LAUNCH.get(k)}
if value.get('supervisor',{}).get('child_pid'):ids['child_pid']=value['supervisor']['child_pid']
for key,pid in ids.items():value['original_processes'][key]=process_identity(pid)
lock=root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')
value['own_UUID_lock_exists']=lock.is_file();value['own_UUID_lock_free']=False
if lock.is_file():
 with lock.open('r') as h:
  try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);value['own_UUID_lock_free']=True;fcntl.flock(h,fcntl.LOCK_UN)
  except BlockingIOError:pass
try:
 value['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],
  '--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 value['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
  '--format=csv,noheader,nounits'],text=True,timeout=10)
except Exception as error:value['GPU_telemetry_error']=str(error)
if MODE in ('health','terminal'):
 value['bounded_technical_logs']={}
 for key,p in [('GPU',out/'GPU.log'),('supervisor',stage/'N09-supervisor.log'),('CPU_post',stage/'N09-post-CPU.log')]:
  if p.is_file():
   with p.open('rb') as h:h.seek(max(0,p.stat().st_size-65536));tail=h.read(65536).decode(errors='replace')
   if MODE=='health':tail='\n'.join(line for line in tail.splitlines() if any(t in line.lower() for t in ('out of memory','traceback','exception','error','no space','failed')))[-16384:]
   value['bounded_technical_logs'][key]=tail[-16384:]
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=('admission','health','terminal'),default='terminal')
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original once-capture bytes')
    launch=json.loads(args.launch_ref.read_text())['dispatch']
    gate={'health':'midpoint_health_not_before_unix','terminal':'next_check_not_before_unix'}.get(args.mode)
    if gate and time.time()<launch[gate]:raise SystemExit('Before original N09 '+args.mode+' time; no SSH')
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen','python3 -c '+shlex.quote(remote_code(launch,args.mode))],capture_output=True,timeout=150)
    except (subprocess.TimeoutExpired,OSError) as error:
        result=dict(status='N09_CAPTURE_TRANSPORT_UNKNOWN_ORIGINAL_HANDLE_NO_RESTART',launch=launch,mode=args.mode,
            error_type=type(error).__name__,error=str(error),original_task_terminal=False,
            no_GPU_or_CPU_relaunch_authority=True,GPU_submissions=0,ledger_written=False)
        with args.output.open('xb') as h:h.write(gzip.compress(json.dumps(result).encode()))
        raise
    if call.returncode:
        result=dict(status='N09_CAPTURE_COMMAND_FAILED_ORIGINAL_HANDLE_NO_RESTART',launch=launch,mode=args.mode,
            transport_exit_code=call.returncode,stderr=call.stderr.decode(errors='replace')[-24576:],
            stdout=call.stdout.decode(errors='replace')[-24576:],original_task_terminal=False,
            no_GPU_or_CPU_relaunch_authority=True,GPU_submissions=0,ledger_written=False)
        with args.output.open('xb') as h:h.write(gzip.compress(json.dumps(result).encode()))
        raise RuntimeError('Original N09 collection failed; saved once, no relaunch')
    with args.output.open('xb') as h:h.write(call.stdout)
    value=json.loads(gzip.decompress(call.stdout))
    print(json.dumps(dict(receipt=str(args.output),mode=args.mode,original_processes=value['original_processes'],
        technical_progress=value.get('technical_progress'),original_runner_paths=len(value.get('runner',{}).get('runs',[])),
        final_status=value.get('final',{}).get('status'),post_exit=value.get('post_exit',{}).get('exit_code'))))


if __name__=='__main__':main()
