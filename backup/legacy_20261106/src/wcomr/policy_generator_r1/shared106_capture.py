"""Original full106 capture and value checks, without CUDA or GPU replay."""
import hashlib,json
from pathlib import Path
from .shared106_card import RUN,MANIFEST,read
from .shared106_collection import gather

def collect(project,stage,launch):
 root=Path(project);stage=Path(stage);out=root/'outputs'/RUN
 value=dict(files={},launch=launch,scores={},quality_scores={})
 def keep(key,path,target=None):
  target=value['files'] if target is None else target;path=Path(path);target[key]=dict(exists=path.exists())
  if path.exists():
   raw=path.read_bytes();target[key].update(raw_utf8=raw.decode(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 for key,name in [('runner','runner.json'),('collection_verified','collection-verified.json'),('score_progress','score-progress.json'),('post','post-results.json'),('post_exit','post-exit.json'),('supervisor','supervisor.json'),('billing','billing.json'),('monitor_final','exclusive-monitor-final.json'),('quality_plan','quality/plan.json'),('quality_progress','quality-progress.json')]:keep(key,out/name)
 for key,name in [('registration','registration.json'),('config','pg-config.json'),('quote','pg-whole-quote.json'),('CPU_acceptance','pg-independent-CPU-acceptance.json'),('authorization','pg-GPU-authorization.json'),('guardian','pg-host-guardian.json'),('ready','pg-runner-context-ready.json'),('grant','pg-runner-context-granted.json'),('card',MANIFEST)]:keep(key,stage/name)
 value['monitor_raw_utf8']=(out/'exclusive-monitor.jsonl').read_text() if (out/'exclusive-monitor.jsonl').exists() else ''
 if (out/'runner.json').exists() and read(out/'runner.json').get('batch',{}).get('status')=='COMPLETE106_ORIGINALS_PENDING_AUDIT':
  value.update(gather(read(stage/MANIFEST),read(out/'runner.json')['batch'],out))
  for s in read(stage/MANIFEST)['matrix']:
   if s['section'] in ('QUALITY',) and s['role']!='NATIVE35':keep(s['id'],out/s['id']/'score.json',value['scores'])
 for i in range(228):keep(str(i),out/'quality'/(str(i)+'.json'),value['quality_scores'])
 try:
  from ..history104_storage_r2 import storage_for
  guard=storage_for(stage);snapshot=guard.check()
  value['storage']=dict(checked=True,contract_sha256=hashlib.sha256((stage/'history104-storage.json').read_bytes()).hexdigest(),snapshot=snapshot,
   journal={k:guard.journal.read(k) for k in ('billing','accounting','supervisor','guardian')})
 except Exception as error:value['storage']=dict(checked=False,error_type=type(error).__name__,error=str(error))
 return value
