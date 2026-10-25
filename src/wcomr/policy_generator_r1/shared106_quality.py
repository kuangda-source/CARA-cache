"""Release-gated 76 videos x3 original metrics, with immutable resumable rows.

Synthetic callbacks are used only in declared CPU combination tests. Production
uses the original source/weight-bound factory; missing model CPU proof blocks it.
"""
import copy,json,time
from pathlib import Path
from .shared106_card import check_card,digest,read
from .continuation_preparation import require
from .production_evidence import artifact,verify_artifact
from .p2_quality_entry import validate_sources_and_decoder
from ..automatic_quality_batch_r1 import validate_result
from ..automatic_quality_r1 import sampling_spec,text_sha
from ..gpu_budget_pool_v2 import atomic_json
DIMENSIONS=('MUSIQ_LONGER512','subject_consistency','motion_smoothness')

def plan(card,state,members,identity,out):
 check_card(card)
 require(state['status']=='COMPLETE106_ORIGINALS_PENDING_AUDIT' and len(state['rows'])==106,'Complete106 required')
 rows=[]
 for slot,r in zip(card['matrix'],state['rows']):
  require(r['slot']==slot and r['status']=='COMPLETE','Changed generation row')
  if slot['section']!='QUALITY':continue
  member=members[slot['member']];video=r['result']['video_artifact'];verify_artifact(video,out)
  req=read(verify_artifact(r['result']['request_artifact'],out))
  require(req['slot']==slot and req['result']=={k:v for k,v in r['result'].items() if k!='request_artifact'},'Request/video binding changed')
  require(text_sha(member['prompt'])==member['prompt_sha256'],'Prompt bytes changed')
  for dim in DIMENSIONS:
   rows.append(dict(case_id=slot['member'],method=slot['id'],dimension=dim,seed=slot['seed'],role=slot['role'],
    prompt=member['prompt'],prompt_sha256=member['prompt_sha256'],input_status='READY_TO_SCORE',
    video_path=video['path'],video_sha256=video['sha256'],request_sha256=r['result']['request_artifact']['sha256'],
    scorer_fingerprint=digest(identity),expected_sampling=sampling_spec(dim)))
 require(len(rows)==228,'76 x3 quality denominator')
 p=dict(rows=rows,evaluator_identity=identity);p['sha256']=digest(p);return p

def checked_plan(p):
 require(p['sha256']==digest({k:v for k,v in p.items() if k!='sha256'}),'Quality plan changed')
 require(len(p['rows'])==228 and len({(r['method'],r['dimension']) for r in p['rows']})==228 and len({r['method'] for r in p['rows']})==76,'Quality positions changed')
 require(all(sum(r['dimension']==d for r in p['rows'])==76 for d in DIMENSIONS),'Metric denominator changed')

def validate(p,row,result):
 validate_result(row,result);validate_sources_and_decoder(p['evaluator_identity'],result)

def execute(p,factory,out,release,save):
 checked_plan(p);require(all(release[k] for k in ('GPU_released','ledger_settled','lock_free','CUDA_hidden')),'Release before quality')
 out=Path(out);out.mkdir(exist_ok=True);saved=out/'plan.json'
 if saved.exists():require(read(saved)==p,'Resume cannot substitute quality plan')
 else:atomic_json(saved,p)
 state=dict(status='QUALITY_RUNNING',plan_sha256=p['sha256'],rows=[dict(planned=r,status='NOT_REACHED') for r in p['rows']],model_lifecycle=[],release=release,started_unix=time.time())
 save(copy.deepcopy(state))
 try:
  for dim in DIMENSIONS:
   life=dict(dimension=dim,status='ENTERING');state['model_lifecycle'].append(life)
   with factory(dim) as scorer:
    require(scorer.dimension==dim and scorer.scorer_fingerprint==digest(p['evaluator_identity']),'Wrong metric identity')
    for i,r in enumerate(state['rows']):
     row=r['planned']
     if row['dimension']!=dim:continue
     target=out/(str(i)+'.json');raw=out/(str(i)+'.raw.json');r['status']='RUNNING';save(copy.deepcopy(state))
     if target.exists():
      result=read(target);require(raw.exists() and read(raw)==result,'Original raw and accepted score differ')
     else:
      require(not raw.exists(),'Unaccepted raw original needs explicit recovery, never overwrite')
      result=scorer.score(copy.deepcopy(row));atomic_json(raw,result)
      validate(p,row,result);atomic_json(target,result)
     validate(p,row,result);r.update(status='SCORED',result=result,score_artifact=artifact(target,out));save(copy.deepcopy(state))
   life['status']='RELEASED'
  state['status']='QUALITY_COMPLETE228';return state
 except BaseException as e:
  state.update(status='QUALITY_FAILED_ORIGINALS_RETAINED',error_type=type(e).__name__,error=str(e))
  failures=out/'failures';failures.mkdir(exist_ok=True)
  with (failures/(str(time.time_ns())+'.json')).open('x') as f:json.dump(state,f,allow_nan=False)
  raise
 finally:state['ended_unix']=time.time();save(copy.deepcopy(state))

def audit(p,state):
 checked_plan(p)
 require(state['status']=='QUALITY_COMPLETE228' and state['plan_sha256']==p['sha256'] and len(state['rows'])==228,'Complete quality required')
 require(state['model_lifecycle']==[dict(dimension=d,status='RELEASED') for d in DIMENSIONS],'Every metric released')
 for planned,row in zip(p['rows'],state['rows']):
  require(row['planned']==planned and row['status']=='SCORED','Quality position changed');validate(p,planned,row['result'])
 return dict(videos=76,dimensions=list(DIMENSIONS),positions=228,full_VBench=False)
