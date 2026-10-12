"""Compact live/terminal receipts; never copy tensor/video or change ledger."""
import argparse,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
CODE=r'''import pathlib,json,hashlib,time,subprocess,fcntl
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-supported-gate-production-r1-20261012';output=root/'outputs/wc-supported-source-gate-full36-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'observed_unix':time.time(),'stage':str(stage),'output':str(output)}
reg=json.loads((stage/'registration.json').read_text());r['source_revision']=reg['source_revision']
r['payload_verified']={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()}
for key,path in [('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),('production_CPU',stage/'production-CPU-result.json')]:
 if path.exists():
  value=json.loads(path.read_text());r[key+'_sha256']=sha(path)
  if key in ('runner','final'):
   rows_key='runs' if key=='runner' else 'rows'
   if key=='final':value['GPU_supervisor']=None
   for row in value.get(rows_key,[]):
    history=row.pop('source_history',None);row.pop('A_history',None)
    if history:
     row['compact_source_history']=[{'step':h['step'],'action':h['action'],'protected':h['protected'],
      'readout':h['A_readout']['readout_action'],'heads':h['A_readout']['extra_heads'],
      'decision':h['source_policy'].get('decision'),
      'event':h['source_policy'].get('event_math')} for h in history]
  r[key]=value
ledger=root/'reports/budget.json';r['ledger']=json.loads(ledger.read_text());r['ledger_sha256']=sha(ledger)
r['GPU']=subprocess.check_output(['nvidia-smi','-i','GPU-cebf7119-cf03-23b9-e192-cd196332b704','--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True).strip()
launch=stage/'GPU-launch.json';ids={}
if launch.exists():
 v=json.loads(launch.read_text());ids={k:v[k] for k in ('supervisor_pid','post_watcher_pid')}
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
r['original_processes']={k:(root.__class__('/proc')/str(v)).exists() for k,v in ids.items()}
lock=(root/'.sync/f1.lock').open('a+')
try:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r['kernel_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
except BlockingIOError:r['kernel_lock_free']=False
lock.close()
for key,path in [('GPU.log_tail',output/'GPU.log'),('production-CPU.log_tail',stage/'production-CPU.log'),('post-CPU.log_tail',stage/'post-CPU.log')]:
 if path.exists():r[key]='\n'.join(path.read_text(errors='replace').splitlines()[-5:])
print(json.dumps(r,allow_nan=False))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='reports/wc_supported_gate_live_or_terminal_capture_20261012.json');a=p.parse_args()
 value=json.loads(subprocess.check_output(HOST+['python3 -'],input=CODE,text=True));f=R/a.output;f.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
 runner=value.get('runner',{});runs=runner.get('runs',[]);last=runs[-1] if runs else {}
 print(json.dumps({'source_revision':value['source_revision'],'runner_status':runner.get('status'),
  'finished':sum(r['status']!='RUNNING' for r in runs),'planned':54,'latest':{k:last.get(k) for k in ('id','status','core_seconds')},
  'final_status':value.get('final',{}).get('status'),'GPU':value['GPU'],'original_processes':value['original_processes'],
  'kernel_lock_free':value['kernel_lock_free'],'payload_all_verified':all(value['payload_verified'].values()),
  'used_GPUh':value['ledger']['used_gpu_hours'],'cap_GPUh':value['ledger']['cap_gpu_hours'],'bytes':f.stat().st_size}))
if __name__=='__main__':main()
