"""P1 R2 whole bounded scope; COST112 is a prerequisite, never training data."""
import math
from .interval_grammar import digest
from .historical_bridge import DEPLOYMENT_LIMIT_SECONDS
VERSION='CARA_PG_P1_REPAIR102_R1'
RUN='cara-pg-p1-repair102-cal-fit4-select2-ada-r1'
STRONG=('S26_C','S26_A_PHASE','SHARED26_C')
MANIFEST='manifests/cara_PG_P1_repair102_whole_quote_r1_20261025.json'
CPU_PROOF='PG-repair-combination-CPU.json'
COUNTS=dict(maximum_paths=102,Native_paths=8,fullD_clock_paths=14,
 candidate_warm_paths=16,candidate_FIT_paths=32,candidate_SELECT_paths=8,
 strong_warm_paths=6,strong_FIT_paths=12,strong_SELECT_paths=6,
 maximum_score_pairs=58,maximum_score_frames=5394,maximum_guided_pairs=3672,
 maximum_CFG_calls=7344,loads=1,new_candidate_queries=8,fixed_baseline_policies=3,
 maximum_distinct_evaluated_policies=11,CAL_FIT=4,CAL_SELECT=2,DEV=0,TEST=0)

def matrix():
 rows=[]
 def add(id,kind,split,i,**kw):rows.append(dict(id=id,kind=kind,split=split,member_index=i,**kw))
 for i in (1,2):add('native_warm_'+str(i),'NATIVE','WARM',0)
 for i in range(4):add('native_fit_'+str(i),'NATIVE','CAL_FIT',i)
 for i in range(4):add('bootstrap_'+str(i),'CLOCK','CAL_FIT',i)
 for role in STRONG:
  for j in (1,2):add(role+'_warm_'+str(j),'STRONG','WARM',0,role=role)
 for q in range(8):
  for j in (1,2):add(f'q{q}_warm_{j}','QUERY','WARM',0,query_slot=q)
 for phase in (0,1):
  for i in range(4):
   anchor=f'anchor_{phase}_{i}';add(anchor,'CLOCK','CAL_FIT',i,phase=phase)
   if phase==0:
    for role in STRONG:add(f'{role}_fit_{i}','STRONG','CAL_FIT',i,role=role,clock_anchor_id=anchor)
   for q in range(4*phase,4*phase+4):add(f'q{q}_fit_{i}','QUERY','CAL_FIT',i,query_slot=q,clock_anchor_id=anchor)
 for i in range(2):
  add(f'native_select_{i}','NATIVE','CAL_SELECT',i)
  anchor=f'anchor_select_{i}';add(anchor,'CLOCK','CAL_SELECT',i)
  for role in STRONG:add(f'{role}_select_{i}','STRONG','CAL_SELECT',i,role=role,clock_anchor_id=anchor)
  for q in range(4):add(f'select_{q}_{i}','QUERY','CAL_SELECT',i,selection_slot=q,clock_anchor_id=anchor)
 assert len(rows)==102 and len({r['id'] for r in rows})==102
 return rows

def timing_gate(acceptance,card):
 if acceptance.get('full_protocol_accepted') is not True:raise ValueError('Complete COST112 acceptance required')
 m=acceptance.get('scientific',{}).get('timing',{})
 if not (m.get('timing_model_validated') is True and m.get('validation_rows')==72 and m.get('independent_clock_anchors')==8
         and m.get('validation_refit') is False and m.get('mean_absolute_relative_error',1)<=.01
         and m.get('maximum_underestimate_seconds',999)<=2 and m.get('no_false_feasible') is True):
  raise ValueError('Independent frozen COST112 timing gate not passed')
 if m.get('fit_coefficients')!=dict(zip(('per_D','per_A'),card['cost_model']['coefficients'])):raise ValueError('Timing coefficients changed')
 return dict(COST112_acceptance_sha256=digest(acceptance),model_sha256=digest(card['cost_model']),new_fit=False)

def quote(old104card,metric_seconds):
 # All unknown candidate requests are charged at the observed PG fullD maximum,
 # NOT the desired .8 budget or an assumed speedup. No alias credit.
 clocks=old104card['quote']['arm_seconds'];terms={}
 for r in matrix():
  role=r.get('role');seconds=clocks[role] if role else clocks['NATIVE' if r['kind']=='NATIVE' else 'PG_ALL_D']
  if r['split']=='WARM':seconds*=1.1
  terms[r['id']]=seconds
 extra=dict(model_load=360.,online58_full93_CPU_LPIPS=58*max(60.,metric_seconds),
            graph_and_one_recovery=1200.,raw_copy_hash_and_safe_release=1440.)
 forecast=math.ceil((sum(terms.values())+sum(extra.values()))*1.25)/3600
 limit=math.ceil(forecast*1.10*2)/2
 return dict(version=VERSION,scope_counts=COUNTS,matrix=matrix(),path_allowance_seconds=terms,
   additional_seconds=extra,planning_margin=1.25,forecast_complete_GPUh=forecast,billed_limit_GPUh=limit,
   cumulative_cap_GPUh=226,deployment_limit_seconds=DEPLOYMENT_LIMIT_SECONDS,relative_native_budget=.8,
   proposal_margin_seconds=6.,specific_whole_card_approval_required=limit>=12,
   physical_dedup_credit_seconds=0,prior_budget_reused=False,GPU_dispatch_ready=False,
   status='FULL_SCOPE_QUOTED_PENDING_COST112_CPU_ADMISSION_AND_SPECIFIC_BUDGET')
