"""Read original local terminal evidence only; no launch, GPU or settlement."""
import argparse,json,hashlib,sys,fcntl,os
from pathlib import Path

def capture(project,stage,launch):
 from wcomr.common_long_card_r2 import RUN,read,sha,CONFIG,MANIFEST
 from wcomr.gpu_budget_pool_v2 import process_identity
 from wcomr.history104_storage_r2 import storage_for
 out=project/'outputs'/RUN
 paths={'registration':stage/'registration.json','config':stage/CONFIG,'card':stage/MANIFEST,
 'authorization':stage/'pg-GPU-authorization.json','ready':stage/'pg-runner-context-ready.json','grant':stage/'pg-runner-context-granted.json',
 'guardian':stage/'pg-host-guardian.json',**{k:out/n for k,n in {'billing':'billing.json','monitor_final':'exclusive-monitor-final.json','supervisor':'supervisor.json','post_exit':'post-exit.json','post':'post-results.json','collection':'collection.json'}.items()}}
 files={}
 for k,p in paths.items():
  if not p.exists():files[k]=dict(exists=False);continue
  raw=p.read_bytes();files[k]=dict(exists=True,raw_utf8=raw.decode(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 def obj(k):return json.loads(files[k]['raw_utf8']) if files[k]['exists'] else {}
 state=obj('supervisor');guardian=obj('guardian');handles={}
 for k,i in dict(supervisor=state.get('supervisor_identity'),runner=state.get('child_identity'),post=state.get('post_identity'),guardian=guardian.get('identity')).items():
  current=process_identity(i['pid']) if i else {};handles[k]=bool(i and current.get('start_ticks')==i.get('start_ticks') and current.get('state') not in (None,'Z','X'))
 # Do not create a missing lock or infer container exit from its CLI PID.
 lock=project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock');free=False
 if lock.exists():
  with lock.open('r') as f:
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);free=True;fcntl.flock(f,fcntl.LOCK_UN)
   except BlockingIOError:pass
 import subprocess
 ins=subprocess.run(['docker','inspect',stage.name+'-gpu'],capture_output=True,text=True,timeout=15)
 if ins.returncode:handles['container']=True
 else:handles['container']=json.loads(ins.stdout)[0]['State']['Running']
 reg=obj('registration');storage=storage_for(stage);storagecheck=storage.check()
 journal={k:storage.journal.read(k) for k in ('billing','accounting')}
 post=obj('post');res=post.get('resource_limits',{})
 return dict(launch=launch,files=files,pool=read(project/'reports/gpu-budget-v2.json'),original_live_handles=handles,own_UUID_lock_free=free,
  monitor_raw_utf8=(out/'exclusive-monitor.jsonl').read_text(),
  payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(project/'runtime'/n) for n in reg['runtime_source_sha256']},
  CPU_resources=dict(cores=res.get('affinity_cpus'),memory_bytes=res.get('address_space_bytes'),timeout_seconds=3600),
  source_and_asset_SHA_verified=all(sha(Path(x['path']))==x['sha256'] and Path(x['path']).stat().st_size==x['bytes'] for x in obj('collection').get('states',[])),
  storage_and_cross_disk_journal_verified=journal['billing']==obj('billing') and journal['accounting']['billing_sha256']==files['billing']['sha256'],storage_snapshot=storagecheck,
  financial_settlement_required=True,science_accepted=False)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('project','stage','launch','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output.exists();sys.path.insert(0,str(a.stage/'src'));a.output.write_text(json.dumps(capture(a.project,a.stage,json.loads(a.launch.read_text())),indent=2)+'\n')
