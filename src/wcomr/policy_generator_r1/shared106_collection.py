"""Full registered106 collection, durable evidence, GPU-free scoring and audit."""
import copy,json,math,time,hashlib
from pathlib import Path
from .shared106_card import COUNTS,check_card,read
from .production_evidence import artifact,verify_artifact,score_videos,validate_score,sha
from .continuation_preparation import require,TIME_BOUNDARY
from ..gpu_budget_pool_v2 import atomic_json

FORMAL=('QUALITY',)

def collect(card,out,execute,save):
 check_card(card);out=Path(out)
 state=dict(status='RUNNING',rows=[dict(slot=copy.deepcopy(s),status='NOT_REACHED') for s in card['matrix']],scope_counts=COUNTS)
 save(copy.deepcopy(state))
 try:
  for row in state['rows']:
   slot=row['slot'];directory=out/slot['id'];require(not directory.exists(),'Original slot replay forbidden')
   row['status']='RUNNING';save(copy.deepcopy(state));start=time.time()
   result=execute(slot,card['roles'][slot['role']]['policy'],directory)
   result.update(started_unix=start,ended_unix=time.time(),clean_deployment_timing=slot['section']!='DIAGNOSTIC')
   import torch
   latent=result.pop('final_latent',None);guided=result.pop('guided',None)
   if latent is not None:
    with (directory/'final-latent.pt').open('xb') as f:torch.save(dict(final_latent=latent),f)
    result['final_latent_artifact']=artifact(directory/'final-latent.pt',out)
   if guided is not None:
    with (directory/'guided.pt').open('xb') as f:torch.save(dict(guided=guided),f)
    result['guided_artifact']=artifact(directory/'guided.pt',out)
   if result['status']=='COMPLETE':result['video_artifact']=artifact(result['video_path'],out)
   result=json.loads(json.dumps(result,allow_nan=False))
   atomic_json(directory/'request.json',dict(slot=slot,policy=card['roles'][slot['role']]['policy'],result=result))
   result['request_artifact']=artifact(directory/'request.json',out)
   row['result']=result;save(copy.deepcopy(state))
   require(result['status']=='COMPLETE','Original refusal/failure retained; whole106 cannot accept')
   require(result['solver_steps']==result['guided_pairs']==slot['actual_updates'] and latent is not None,'Incomplete full36')
   require((guided is not None)==(slot['section']=='DIAGNOSTIC'),'Diagnostic scope changed')
   row['status']='COMPLETE';save(copy.deepcopy(state))
  state['status']='COMPLETE106_ORIGINALS_PENDING_AUDIT';return state
 except BaseException as e:
  row.update(status='TECH_FAILED',error_type=type(e).__name__,error=str(e));state['status']='FAILED106_DENOMINATOR_RETAINED';raise
 finally:save(copy.deepcopy(state))

def audit_rows(card,state,requests,artifact_checks):
 check_card(card);require(state['scope_counts']==COUNTS and state['status']=='COMPLETE106_ORIGINALS_PENDING_AUDIT','Incomplete106 state')
 require(len(state['rows'])==106 and set(requests)=={s['id'] for s in card['matrix']}==set(artifact_checks),'Missing/extra106 originals')
 clocks=[];last_end=None
 for slot,row in zip(card['matrix'],state['rows']):
  require(row['slot']==slot and row['status']=='COMPLETE','Changed order or failed row')
  result=row['result'];req=requests[slot['id']];checks=artifact_checks[slot['id']]
  require(req==dict(slot=slot,policy=card['roles'][slot['role']]['policy'],result={k:v for k,v in result.items() if k!='request_artifact'}),'Original request differs')
  require(result['status']=='COMPLETE' and result['solver_steps']==result['guided_pairs']==slot['actual_updates'],'Incomplete solver')
  require(checks['frames']==93 and all(checks[k]==result[k] for k in ('video_artifact','final_latent_artifact','request_artifact')),'Original video/latent/request differs')
  require(result['timing_boundary']==TIME_BOUNDARY and 0<result['core_seconds']<=result['full_request_seconds'] and math.isfinite(result['full_request_seconds']),'Invalid full clock')
  require(result['started_unix']<=result['ended_unix'] and (last_end is None or last_end<=result['started_unix']),'Overlapping/reordered requests');last_end=result['ended_unix']
  diagnostic=slot['section']=='DIAGNOSTIC';require(result['clean_deployment_timing']==(not diagnostic) and result['audit']==diagnostic,'Diagnostic clock leakage')
  require(result['in_timing_guided_copies']==(slot['actual_updates'] if diagnostic else 0) and result['in_timing_hashes']==0,'Unexpected measurement instrumentation')
  if diagnostic:require(checks['guided_artifact']==result['guided_artifact'] and checks['guided_steps']==36,'Missing all36 diagnostic original')
  else:require('guided_artifact' not in result,'Unregistered guided copies')
  policy=req['policy']
  if policy is None:
   spec=card['roles'][slot['role']];grid=next(x for x in card['schedules'] if x['requested_steps']==spec['requested_steps'])
   require(result['requested_steps']==spec['requested_steps'] and result['actual_updates']==slot['actual_updates'] and result['full_block_calls']==[2*slot['actual_updates']]*2 and result['cache_installed'] is False and result['scheduler_timesteps']==grid['timesteps'],'Native grid/full-block witness changed')
  if policy is not None:
   history=result['semantic_history'];require(len(history)==36 and result['policy_fingerprint']==policy['fingerprint'] and result['teacher_calls']==0 and not result['online_fitting'],'Policy/teacher changed')
   for i,h in enumerate(history):
    require(h['step']==i+1 and h['planned']==h['actual']==policy['actions'][i] and h['fallback_reason'] is None,'Fallback or changed mask cannot support clean fixed-mask timing')
    require(h['shared_alpha']==(policy['shared_alpha'][i] if h['actual']!='D' else None),'Historical alpha changed')
  if slot['section'] in ('QUALITY','TIMING_REPEAT'):
   clocks.append(dict(slot,status='COMPLETE',complete_request_boundary=True,diagnostic=False,seconds=result['full_request_seconds']))
 return clocks

def tensor_digest(t):
 t=t.detach().cpu().contiguous();return dict(dtype=str(t.dtype),shape=list(t.shape),sha256=hashlib.sha256(t.view(__import__('torch').uint8).numpy().tobytes()).hexdigest())

def gather(card,state,out):
 import torch
 from ..rv0_video_reader import probe_video,decoded_video
 out=Path(out);requests={};checks={}
 for row in state['rows']:
  if row['status']!='COMPLETE':continue
  s=row['slot'];r=row['result'];requests[s['id']]=read(verify_artifact(r['request_artifact'],out))
  ck={k:artifact(verify_artifact(r[k],out),out) for k in ('video_artifact','final_latent_artifact','request_artifact')}
  ck['frames']=probe_video(r['video_artifact']['path'])['frames']
  ck['latent_tensor']=tensor_digest(torch.load(r['final_latent_artifact']['path'],map_location='cpu',weights_only=True)['final_latent'])
  if 'guided_artifact' in r:
   ck['guided_artifact']=artifact(verify_artifact(r['guided_artifact'],out),out)
   gg=torch.load(r['guided_artifact']['path'],map_location='cpu',weights_only=True)['guided'];ck['guided_steps']=len(gg);ck['guided_tensors']=[tensor_digest(t) for t in gg]
  checks[s['id']]=ck
 clocks=audit_rows(card,state,requests,checks)
 rows={r['slot']['id']:r for r in state['rows']};pairs=control_pairs(card)
 rgb={}
 for ident in {k for p in pairs for k in p}:
  with decoded_video(rows[ident]['result']['video_artifact']['path']) as v:
   h=hashlib.sha256()
   count=0
   for frame,pts,base in v:h.update(frame.tobytes());count+=1
   rgb[ident]=dict(frames=count,sha256=h.hexdigest())
 controls=[]
 for left,right in pairs:
  require(checks[left]['latent_tensor']==checks[right]['latent_tensor'] and rgb[left]==rgb[right],'Native/PG allD or audit/lean final/RGB mismatch')
  controls.append(dict(left=left,right=right,latent_equal=True,RGB93_equal=True,left_rgb=rgb[left],right_rgb=rgb[right]))
 return dict(requests=requests,artifact_checks=checks,controls=controls,clocks=clocks)

def score_after_release(card,state,out,metric,identity,release,save):
 require(release['GPU_released'] and release['ledger_settled'] and release['lock_free'] and release['CUDA_hidden'],'GPU release proof required before scoring')
 require(state['status']=='COMPLETE106_ORIGINALS_PENDING_AUDIT','Complete generation required')
 out=Path(out);rows=state['rows'];done={r['slot']['id']:r['result'] for r in rows};scores={}
 planned=[s for s in card['matrix'] if s['section'] in FORMAL and s['role']!='NATIVE35'];require(len(planned)==72,'Full72 score denominator')
 progress=dict(status='CPU_SCORE_RUNNING',planned_pairs=72,completed_pairs=0,release=release,scores=scores,started_unix=time.time());save(copy.deepcopy(progress))
 try:
  for s in planned:
   ref=next(x for x in card['matrix'] if all(x[k]==s[k] for k in ('section','member','seed','repeat')) and x['role']=='NATIVE35')
   path=out/s['id']/'score.json'
   # Resume only an intact score for this exact pair and metric; never replay GPU.
   if path.exists():value=read(path)
   else:
    value=score_videos(done[ref['id']]['video_artifact'],done[s['id']]['video_artifact'],metric,root=out,metric_identity=identity)
    validate_score(value,done[ref['id']]['video_artifact'],done[s['id']]['video_artifact'],identity);atomic_json(path,value)
   lp=validate_score(value,done[ref['id']]['video_artifact'],done[s['id']]['video_artifact'],identity)
   scores[s['id']]=dict(reference_id=ref['id'],score_artifact=artifact(path,out),LPIPS=lp)
   progress['completed_pairs']=len(scores);save(copy.deepcopy(progress))
  progress['status']='CPU_SCORE_COMPLETE72';return progress
 except BaseException as e:
  progress.update(status='CPU_SCORE_FAILED_ORIGINALS_RETAINED',error_type=type(e).__name__,error=str(e))
  failures=out/'score-failures';failures.mkdir(exist_ok=True)
  with (failures/(str(time.time_ns())+'.json')).open('x') as f:json.dump(progress,f,allow_nan=False)
  raise
 finally:progress['ended_unix']=time.time();save(copy.deepcopy(progress))


def control_pairs(card):
 pairs=[]
 for s in card['matrix']:
  if s['section'] in ('TIMING_REPEAT','DIAGNOSTIC'):
   ref=next(x for x in card['matrix'] if x['section']=='QUALITY' and all(x[k]==s[k] for k in ('role','member','seed')))
   pairs.append((ref['id'],s['id']))
 require(len(pairs)==22,'20 repeats and2 diagnostic controls required')
 return pairs
