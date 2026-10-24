"""Frozen phase-alpha proposals with a single count-lowering recovery branch."""
import statistics
from .interval_grammar import Profile,Edge,compile_policy
from .proposal_tables import Costs,QuadraticStats,make_proxy_graph
from .budgeted_planner import ScoredEdge,solve,two_topologies
from .historical_bridge import historical_policies,runtime_budget
from .search_protocol import initial_batch,joint_neighbors


def phase_legal(edge):
 return not edge.window or all(edge.alpha==(1. if t<25 else .5) for t in range(edge.window[0],edge.window[1]+1))


def context(data,card,bootstrap_seconds):
 p=dict(data['profile']);p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates']);profile=Profile(**p)
 if profile.identity!=card['profile']['identity']:raise ValueError('Cost112 and clean-price execution profile differ')
 old=dict(data['costs']);old['dense_seconds']=tuple(old['dense_seconds']);old['C_seconds']=tuple(old['C_seconds']);old['A_seconds_by_alpha']={float(k):tuple(v) for k,v in old['A_seconds_by_alpha'].items()}
 stats={(r['member'],r['source'],r['update']):QuadraticStats(r['e2'],r['ed'],r['d2'],r['fusion_contract']) for r in data['statistics']}
 if len(stats)!=1624:raise ValueError('Complete accepted1624 labels required')
 graph=make_proxy_graph(profile,statistics=stats,fit_members=tuple(data['CAL_FIT_members']),costs=Costs(**old),weights=tuple(data['weights']),label_basis=data['label_basis'],statistic_profile_identity=data['statistic_profile_identity'])
 if graph['missing_cells']:raise ValueError('No label imputation')
 if len(bootstrap_seconds)!=4 or any(x<=0 for x in bootstrap_seconds):raise ValueError('Four independent bootstrap fullD clocks required')
 anchor=statistics.mean(bootstrap_seconds);dD,dA=card['cost_model']['coefficients']
 # .001 is an accounting gauge ensuring positive edge costs. It is exactly
 # canceled from the shared term; it is neither fitted nor a new action price.
 epsilon=.001;shared=anchor-36*dD-36*epsilon
 if shared<0:raise ValueError('Clock/profile outside frozen cost model')
 costs=Costs((dD+epsilon,)*36,(epsilon,)*36,{a:(dA+epsilon,)*36 for a in profile.alpha_candidates},shared,profile.identity,'VALIDATED_PRECEDING_FULLD_MODEL_PROPOSAL','OBSERVED_COMPONENT_PROPOSAL_COSTS')
 scored=tuple(ScoredEdge(s.edge,costs.edge_seconds(s.edge),s.proxy_loss) for s in graph['graph'] if phase_legal(s.edge))
 budget=min(data['budget_seconds'],257.7712338712067);ceiling=budget-6.
 result=count_solve(profile,scored,anchor,dD,dA,ceiling)
 hist=historical_policies(profile);controls={}
 for mode,suffix in [('C','C'),('A','A_PHASE')]:
  eligible=[]
  for n in (25,24):
   plan=hist[f'S{n}_{suffix}'];pred=anchor+dD*(n-36)+dA*plan['counts']['A']
   if pred<=ceiling:eligible.append(dict(policy=plan,predicted_seconds=pred,proxy_loss=None,boundary_control=True))
  controls[mode]=eligible[0] if eligible else None
 batch=initial_batch(controls,two_topologies(result))
 for b in batch['batch']:b['roles']=[r.replace('SIMPLE','BOUNDARY') for r in b['roles']]
 return dict(profile=profile,costs=costs,graph=scored,batch=batch,historical=hist,budget_seconds=budget,
             proposal_ceiling_seconds=ceiling,bootstrap_mean_seconds=anchor,coefficients=(dD,dA))


def one_recovery(ctx,first,observations):
 """At most four new proposals from complete first-batch FIT, no loop/refit.

 Feasible first batch: refine best two. None feasible: choose two smallest
 measured overshoots and require at least one fewer D in every recovery child.
 Missing/refused/nonfinite cohorts cause a stop, not substitution.
 """
 if not first:return dict(mode='NO_FIRST_BATCH',proposals=[])
 if set(observations)!={x['policy']['fingerprint'] for x in first}:raise ValueError('Full first cohort required')
 means={}
 for proposal in first:
  fp=proposal['policy']['fingerprint'];rows=observations[fp]
  if len(rows)!=4 or len({r['member'] for r in rows})!=4 or any(r['status']!='COMPLETE' for r in rows):raise ValueError('Incomplete recovery cohort')
  if any(not 0<r['full_request_seconds']<float('inf') or not 0<=r['LPIPS']<float('inf') for r in rows):raise ValueError('Nonfinite recovery evidence')
  means[fp]=(statistics.mean(r['full_request_seconds'] for r in rows),statistics.mean(r['LPIPS'] for r in rows))
 feasible=[p for p in first if means[p['policy']['fingerprint']][0]<=ctx['budget_seconds']]
 order=sorted(feasible or first,key=lambda p:(means[p['policy']['fingerprint']][1 if feasible else 0],p['policy']['fingerprint']))[:2]
 graph=ctx['graph'];costs=ctx['costs'];seen={p['policy']['fingerprint'] for p in first};out=[]
 for parent in order:
  plan=parent['policy'];ceiling=ctx['proposal_ceiling_seconds']
  if not feasible:
   dD,dA=ctx['coefficients'];n=plan['counts']['D']-1
   # Conservative phase-A allowance makes nD a genuine upper bound, even if
   # a neighbor replaces all A by C. This may remove more than one D.
   ceiling=min(ceiling,ctx['bootstrap_mean_seconds']+dD*(n-36))
  candidates=joint_neighbors(ctx['profile'],graph,costs,[plan],budget_seconds=ceiling,quantum_seconds=.001,seen=seen,maximum=4,variants_per_boundary=4)
  for p in candidates:
   if not feasible and p['policy']['counts']['D']>=plan['counts']['D']:continue
   p=dict(p,recovery_parent=plan['fingerprint'],recovery_branch='REFINE' if feasible else 'LOWER_D')
   if p['policy']['fingerprint'] not in seen:out.append(p);seen.add(p['policy']['fingerprint'])
 out.sort(key=lambda p:(p['proxy_loss'],p['predicted_seconds'],p['policy']['fingerprint']))
 return dict(mode='ONE_REFINEMENT' if feasible else 'ONE_LOWER_D_RECOVERY',proposals=out[:4],iterations=1,
             thresholds_refitted=False,extra_query_allowed=False)


def count_solve(profile,graph,anchor,dD,dA,ceiling):
 """Exact finite (boundary,nD,nA,anchor-count) proxy DP, four paths/state.

 Keeping counts avoids thousands of near-identical millisecond rounding states.
 The six-second proposal allowance is unchanged; no clock fitting happens here.
 """
 from .interval_grammar import required_anchors
 starts={}
 for s in graph:starts.setdefault(s.edge.start,[]).append(s)
 states={1:{(0,0,0):[(0.,())]}}
 for t in range(1,37):
  for (nd,na,anchors),paths in list(states.get(t,{}).items()):
   for item in starts.get(t,()):
    e=item.edge;added=0 if not e.window else e.window[1]-e.window[0]+1
    after=min(anchors+1,profile.anchor_cap)
    if after<required_anchors(profile,e):continue
    key=(nd+1,na+added,after)
    if anchor+dD*(key[0]-36)+dA*key[1]>ceiling:continue
    dest=states.setdefault(e.end,{}).setdefault(key,[])
    dest.extend((loss+item.proxy_loss,edges+(e,)) for loss,edges in paths)
    dest.sort(key=lambda x:(x[0],tuple(e.key for e in x[1])));del dest[4:]
 candidates=[]
 for (nd,na,_),paths in states.get(37,{}).items():
  for loss,edges in paths:
   policy=compile_policy(profile,edges);prediction=anchor+dD*(nd-36)+dA*na
   policy['budget_predicted_seconds']=prediction
   candidates.append(dict(policy=policy,proxy_loss=loss,predicted_seconds=prediction))
 candidates.sort(key=lambda p:(p['proxy_loss'],p['predicted_seconds'],p['policy']['fingerprint']))
 return dict(proposals=candidates[:32],count_state=True,refit=False)
