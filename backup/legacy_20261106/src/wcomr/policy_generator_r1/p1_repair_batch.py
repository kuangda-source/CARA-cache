"""102-position sequential P1 entry. Collect a clock block before CPU scoring."""
import copy,math,statistics
from .p1_repair_contract import COUNTS,matrix,STRONG,timing_gate
from .p1_repair_search import context,one_recovery
from .interval_grammar import Edge,compile_policy
from .continuation_preparation import TIME_BOUNDARY
from .search_protocol import choose_observed


def run(*,fit_members,select_members,card,cost_acceptance,native,evaluate,score,
        accept_native_clock,build_consumer,save,exposure_recheck,elapsed_GPUh,calibration_cap_GPUh):
 if len(set(fit_members+select_members))!=6 or len(fit_members)!=4 or len(select_members)!=2:raise ValueError('Frozen4+2 identities')
 binding=timing_gate(cost_acceptance,card)
 state=dict(status='P1_REPAIR_BOOTSTRAP',rows=[dict(r,status='NOT_REACHED') for r in matrix()],scope_counts=COUNTS,
   dependency=binding,query_attempts=0,candidates=[],aliases=[],selected_policy=None,TEST_used=False,
   information_exposure=dict(prior_development_layouts=11,new_adaptive_quota=8,fixed_comparison_layouts=3))
 rows={r['id']:r for r in state['rows']};refs={};plans={};roles={};records=[];ctx=None
 def checkpoint():save(copy.deepcopy(state))
 def call(id,plan=None):
  row=rows[id]
  if row['status']!='NOT_REACHED':raise ValueError('Original position cannot replay')
  if elapsed_GPUh()>=calibration_cap_GPUh:raise RuntimeError('Whole-card GPUh cap')
  group=select_members if row['split']=='CAL_SELECT' else fit_members
  row.update(member=group[row['member_index']],seed=0,status='RUNNING')
  if plan:row['fingerprint']=plan['fingerprint']
  if 'clock_anchor_id' in row:
   anchor=rows[row['clock_anchor_id']]
   if anchor['status']!='COMPLETE' or anchor['member']!=row['member']:raise ValueError('Missing strict-past same-input clock')
   dD,dA=card['cost_model']['coefficients'];c=plan['counts']
   row['timing_prediction']=dict(anchor_id=anchor['id'],anchor_seconds=anchor['full_request_seconds'],
     predicted_seconds=anchor['full_request_seconds']+dD*(c['D']-36)+dA*c['A'],created_before_target_execution=True)
  checkpoint()
  try:
   v=native(dict(row)) if plan is None else evaluate(dict(row),plan,refs.get(row['member']))
   if v.get('status') not in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'):raise ValueError('Original terminal request required')
   if v['status']=='COMPLETE' and (v.get('timing_boundary')!=TIME_BOUNDARY or v.get('solver_steps')!=36 or v.get('guided_pairs')!=36 or not 0<v.get('full_request_seconds',0)<math.inf):raise ValueError('Full36 request clock required')
   if (set(v)&set(row)) - {'status'}:raise ValueError('Registered slot rewritten')
   row.update(v);checkpoint()
   if row['kind'] in ('NATIVE','CLOCK') and row['status']!='COMPLETE':raise ValueError('Native/clock refusal cannot be replaced')
   return row
  except BaseException as e:row.update(status='TECH_FAILED',error=str(e));checkpoint();raise
 def scored(ids):
  # All block clocks have been saved first. LPIPS cannot lengthen a target's
  # anchor horizon. The complete CPU work is still billed while GPU is held.
  for id in ids:
   r=rows[id]
   if r['status']=='COMPLETE':
    v=score(copy.deepcopy(r),refs[r['member']]);loss=v.get('LPIPS')
    if type(loss) not in (int,float) or not 0<=loss<math.inf:raise ValueError('Missing complete93 LPIPS')
    r.update(v)
   records.append(dict(fingerprint=r['fingerprint'],prompt=r['member'],seed=0,split=r['split'],status=r['status'],LPIPS=r.get('LPIPS'),measured_seconds=r.get('full_request_seconds'),timing_protocol=TIME_BOUNDARY,profile_identity=ctx['profile'].identity,endpoint_basis='NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS'))
  checkpoint()
 def register(proposals,start):
  added=[]
  for i,item in enumerate(proposals):
   if i>=4:raise ValueError('Finite batch4 required')
   prop=item['proposal'];fp=prop['policy']['fingerprint'];q=start+i
   if fp in plans:
    state['aliases'].append(dict(query_slot=q,fingerprint=fp,roles=item['roles']))
    for role in item['roles']:roles[role]=fp
    continue
   if state['query_attempts']>=8:raise ValueError('Ninth query refused')
   plans[fp]=prop['policy'];state['query_attempts']+=1
   entry=dict(query_slot=q,proposal=prop,roles=item['roles']);state['candidates'].append(entry);added.append(entry)
   for role in item['roles']:roles[role]=fp
   for j in (1,2):call(f'q{q}_warm_{j}',prop['policy'])
  return added
 def phase(entries,index):
  todo=[]
  for i in range(4):
   call(f'anchor_{index}_{i}',fullD)
   if index==0:
    for role in STRONG:todo.append(call(f'{role}_fit_{i}',ctx['historical'][role])['id'])
   for entry in entries:todo.append(call(f'q{entry["query_slot"]}_fit_{i}',entry['proposal']['policy'])['id'])
  scored(todo)
 def rank(split,ids,ceiling):
  return choose_observed([r for r in records if r['split']==split and r['fingerprint'] in ids],members=tuple((m,0) for m in (fit_members if split=='CAL_FIT' else select_members)),candidate_fingerprints=ids,budget_seconds=ctx['budget_seconds'],timing_protocol=TIME_BOUNDARY,profile_identity=ctx['profile'].identity,split=split,loss_ceiling=ceiling)
 checkpoint()
 try:
  for j in (1,2):call('native_warm_'+str(j))
  for i,m in enumerate(fit_members):refs[m]=call('native_fit_'+str(i))
  clock=accept_native_clock([refs[m] for m in fit_members]);data=build_consumer(clock)
  # Profile is available before bootstrap, while proposal costs are not.
  from .interval_grammar import Profile
  p=dict(data['profile']);p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates']);profile=Profile(**p)
  fullD=compile_policy(profile,[Edge(i,i+1) for i in range(1,37)])
  bootstrap=[call('bootstrap_'+str(i),fullD)['full_request_seconds'] for i in range(4)]
  ctx=context(data,card,bootstrap);state.update(budget_seconds=ctx['budget_seconds'],native_clock=clock,bootstrap_seconds=bootstrap,consumer_provenance=data['provenance'])
  for role in STRONG:
   for j in (1,2):call(f'{role}_warm_{j}',ctx['historical'][role])
  first=register(ctx['batch']['batch'],0);state['status']='P1_REPAIR_FIRST4';phase(first,0)
  observations={x['proposal']['policy']['fingerprint']:[rows[f'q{x["query_slot"]}_fit_{i}'] for i in range(4)] for x in first}
  recovery=one_recovery(ctx,[x['proposal'] for x in first],observations);state['recovery']=recovery
  entries=register([dict(proposal=p,roles=['RECOVERY_'+str(i)]) for i,p in enumerate(recovery['proposals'])],4)
  if entries:state['status']='P1_REPAIR_ONCE4';phase(entries,1)
  ranked=rank('CAL_FIT',list(plans),1e100) if plans else dict(order=[])
  finalists=[r['fingerprint'] for r in ranked['order'][:2]];controls=[roles.get('BOUNDARY_C'),roles.get('BOUNDARY_A')]
  if not finalists or any(x is None for x in controls):state['status']='BUDGET_NOT_VERIFIED';return state
  frozen=list(dict.fromkeys(finalists+controls));assert len(frozen)<=4
  state.update(selection_frozen=frozen,finalists=finalists,boundary_controls=controls,status='P1_REPAIR_SELECT_FROZEN');checkpoint()
  ex=exposure_recheck()
  if ex.get('passed') is not True:raise ValueError('Fresh full CAL_SELECT identity audit required')
  state['SELECT_exposure_recheck']=ex;todo=[]
  for i,m in enumerate(select_members):
   refs[m]=call(f'native_select_{i}');call(f'anchor_select_{i}',fullD)
   for role in STRONG:todo.append(call(f'{role}_select_{i}',ctx['historical'][role])['id'])
   for q,fp in enumerate(frozen):todo.append(call(f'select_{q}_{i}',plans[fp])['id'])
  scored(todo)
  control=[r for r in records if r['split']=='CAL_SELECT' and r['fingerprint'] in controls]
  if len(control)!=2*len(set(controls)) or any(r['status']!='COMPLETE' for r in control):state['status']='SELECT_CONTROLS_INCOMPLETE_NO_SELECTION';return state
  ceiling={m:min(r['LPIPS'] for r in control if r['prompt']==m)+.01 for m in select_members}
  selection=rank('CAL_SELECT',frozen,ceiling);chosen=selection['selected']
  state.update(selection=selection,selected_policy=plans[chosen['fingerprint']] if chosen else None,status='P1_REPAIR_CAL_SELECTION_COMPLETE' if chosen else 'BUDGET_NOT_VERIFIED')
  return state
 except BaseException as e:state.update(status='P1_REPAIR_TECHNICAL_STOP',error_type=type(e).__name__,error=str(e));raise
 finally:
  if state['status'] in ('P1_REPAIR_CAL_SELECTION_COMPLETE','BUDGET_NOT_VERIFIED','SELECT_CONTROLS_INCOMPLETE_NO_SELECTION'):
   for r in state['rows']:
    if r['status']=='NOT_REACHED':r['status']='UNUSED_REGISTERED_UPPER_BOUND'
  state['actual_billed_GPUh_observed']=elapsed_GPUh();checkpoint()
