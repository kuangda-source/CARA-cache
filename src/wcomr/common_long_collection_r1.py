"""Six-path collection and CPU tensor rescoring; no fit or GPU dispatch."""
import math,time,json
from pathlib import Path
import torch
from .common_long_card_r1 import matrix,require,sha
from .gpu_budget_pool_v2 import atomic_json
from .scout_readout_v22 import actual_guided_error
from .scout_common_long_r1 import ALL_LABELS
from .mid_coverage import tree_digest

def collect(root, manifest, request, *, check_space, byte_limit, save):
 root=Path(root);assets=root/'assets';assets.mkdir(parents=True,exist_ok=False)
 rows=[dict(s,status='NOT_REACHED') for s in matrix(manifest)];states=[];used=0;off={}
 def checkpoint():save(dict(rows=rows,states=[dict(prompt=s['prompt'],step=s['step']) for s in states]))
 checkpoint()
 for row in rows:
  row['status']='RUNNING';checkpoint()
  def sink(v):
   nonlocal used
   require(row['enabled'] and v['context'][0]==row['prompt'],'state owner')
   require(v['step'] in manifest['states'] and (v['context'][0],v['step']) not in {(x['prompt'],x['step']) for x in states},'state denominator')
   # Only tensors needed for independent local scoring; no gain fit or checkpoints.
   item=dict(prompt=row['prompt'],step=v['step'],xi=v['xi'],sigma=v['sigma'],
    source_anchor_steps=v['source_anchor_steps'],parent_fingerprint=v['context'][2],teacher=v['teacher'],
    outputs={label:v['readouts'][label]['outputs'] for label in ALL_LABELS},
    alpha={label:v['readouts'][label]['alpha'] for label in ALL_LABELS},
    online_scores=v['summary'],readout_head_pairs=v['readout_head_pairs'],
    cost={label:{k:v['readouts'][label][k] for k in ('diagnostic_readout_seconds','device_peak_allocated_cumulative_bytes','peak_is_cumulative_not_incremental','clock_includes_roundtrip_copy_hash')} for label in ALL_LABELS})
   from .partial_mlp_deployment_state import tensor_bytes
   check_space();require(used+tensor_bytes(item)+2**20<=byte_limit,'asset byte budget')
   p=assets/f'{len(states):02d}.pt'
   with p.open('xb') as f:torch.save(item,f)
   used+=p.stat().st_size;require(used<=byte_limit,'serialized capacity')
   states.append(dict(prompt=row['prompt'],step=v['step'],path=str(p),sha256=sha(p),bytes=p.stat().st_size))
  try:
   check_space();r=request(row['prompt'],row['enabled'],sink,root/row['id'])
   require(r['status']=='COMPLETE' and r['guided_pairs']==r['solver_steps']==36,'full parent')
   require(len(r['guided'])==36,'all guided states')
   fp=dict(guided=[tree_digest(x) for x in r['guided']],final=tree_digest(r['final_latent']),video=sha(r['video_path']))
   if row['section']=='OFF':off[row['prompt']]=fp
   if row['section']=='ON':require(fp==off[row['prompt']],'OFF/ON all36/final/video differs')
   t=r['paper_timing'];require(not t['deployment_latency_eligible'],'shadow not clean latency')
   row.update(status='COMPLETE',fingerprint=fp,full_request_seconds=r['full_request_seconds'],
     paper_denoise_decode_seconds=r['paper_denoise_decode_seconds'],timing_is_diagnostic=True)
  except BaseException as e:row.update(status='TECH_FAILED',error_type=type(e).__name__,error=str(e));checkpoint();raise
  checkpoint()
 require(len(states)==12 and len(off)==2,'all state/control denominator')
 result=dict(status='COMMON_LONG6_COLLECTED_PENDING_CPU',rows=rows,states=states,stored_bytes=used,
  matrix=matrix(manifest),scope=manifest['scope'],manifest_sha256=__import__('hashlib').sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest())
 atomic_json(root/'collection.json',result);return result

def rescore(collection, manifest):
 require(len(collection['rows'])==6 and all(r['status']=='COMPLETE' for r in collection['rows']),'six complete paths')
 require(collection['matrix']==matrix(manifest),'matrix changed')
 expected={(r['name'],s) for r in manifest['requests'] for s in manifest['states']}
 require(len(collection['states'])==12 and {(r['prompt'],r['step']) for r in collection['states']}==expected,'12 exact states')
 values=[]
 for ref in collection['states']:
  p=Path(ref['path']);require(not p.is_symlink() and p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'],'tensor original SHA')
  v=torch.load(p,map_location='cpu',weights_only=True)
  require((v['prompt'],v['step'])==(ref['prompt'],ref['step']) and set(v['outputs'])==set(ALL_LABELS),'readout identity')
  step=v['step'];age=step-v['source_anchor_steps'][-1]
  require(v['readout_head_pairs']==(13 if age<3 else 16),'head billing')
  scores={}
  for label in ALL_LABELS:
   require(v['alpha'][label]==(1. if step<25 else .5),'original alpha')
   scores[label]=actual_guided_error(v['outputs'][label],v['teacher'])
   for k,n in scores[label].items():
    old=v['online_scores'][label][k]
    require(math.isclose(n,old,rel_tol=1e-6,abs_tol=1e-8),'original/recomputed '+label+'/'+k)
  if age<3:require(all(torch.equal(x,y) for x,y in zip(v['outputs']['A_PHASE'],v['outputs']['R4_COMMON_LONG'])),'short exact A')
  values.append(dict(prompt=v['prompt'],step=step,scores=scores,cost=v['cost']))
 return dict(status='COMMON_LONG6_CPU_SCORED_PENDING_TERMINAL',states=12,readout_positions=84,values=values,
  CPU_only=True,scientific_gate_evaluated=False,video_quality_claim=False)
