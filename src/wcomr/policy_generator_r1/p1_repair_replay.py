"""Independent adaptive replay from raw request/score originals; not finance."""
import copy
from .p1_repair_batch import run
from .production_evidence import validate_score
from .interval_grammar import digest

def replay(*,card,accepted,consumer,native_clock,fit,select,requests,scores,metric_identity,exposure,reported,cap):
 used=[];scored=[]
 def endpoint(slot,policy=None,reference=None):
  raw=requests[slot['id']]
  if raw['slot']!=slot or raw['policy']!=policy:raise ValueError('Frozen original request/policy differs')
  if slot['id'] in used:raise ValueError('Request replay')
  used.append(slot['id']);return copy.deepcopy(raw['result'])
 def score(row,ref):
  s=scores[row['id']];v=validate_score(s['data'],ref['video_artifact'],row['video_artifact'],metric_identity)
  scored.append(row['id']);return dict(LPIPS=v,score_artifact=s['artifact'])
 result=run(fit_members=fit,select_members=select,card=card,cost_acceptance=accepted,native=endpoint,evaluate=endpoint,score=score,
   accept_native_clock=lambda rows:native_clock,build_consumer=lambda clock:consumer,save=lambda s:None,exposure_recheck=lambda:exposure,
   elapsed_GPUh=lambda:reported['actual_billed_GPUh_observed'],calibration_cap_GPUh=cap)
 if set(used)!=set(requests) or set(scored)!=set(scores):raise ValueError('Original request/score denominator differs')
 if digest(result)!=digest(reported):raise ValueError('Independent selection replay differs')
 return dict(status='P1_REPAIR_INDEPENDENT_ADAPTIVE_REPLAY_ACCEPTED',registered_positions=102,executed_paths=len(used),scored_pairs=len(scored),
   queries=result['query_attempts'],selected_policy=result.get('selected_policy'),full_financial_and_exclusive_acceptance=False)
