"""Whole adaptive entry with declared clocks, no current COST112 outputs."""
import copy,json,sys,unittest
from pathlib import Path
from wcomr.policy_generator_r1.p1_repair_contract import *
from wcomr.policy_generator_r1.p1_repair_batch import run
from wcomr.policy_generator_r1.p1_repair_search import context,one_recovery,phase_legal
from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from wcomr.policy_generator_r1.interval_grammar import Profile,Edge,compile_policy
ROOT=Path(__file__).resolve().parents[1]

def inputs():
 card=json.loads((ROOT/'manifests/cara_cost112_scope_quote_r1_20261025.json').read_text())
 old=json.loads((ROOT/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json').read_text())['files']['bundle']['data']
 p={k:old['profile'][k] for k in ('horizon','protected_dense','max_source_age','min_C_anchors','min_A_anchors','alpha_candidates')};p['identity']=old['profile_identity']
 data=dict(profile=p,costs={k:old['costs'][k] for k in ('dense_seconds','C_seconds','A_seconds_by_alpha','shared_seconds','profile_identity','measurement_protocol','evidence_kind')},statistics=[{**{k:v for k,v in x.items() if k!='target'},'update':x['target']} for x in old['statistics']],CAL_FIT_members=old['fit_members'],weights=[1.]*36,label_basis=old['label_basis'],statistic_profile_identity=old['profile_identity'],budget_seconds=240.,Q=8,provenance={'declared_CPU_fixture':True})
 data['profile']['identity']=card['profile']['identity'];data['statistic_profile_identity']=card['profile']['identity'];data['costs']['profile_identity']=card['profile']['identity']
 m=dict(timing_model_validated=True,validation_rows=72,independent_clock_anchors=8,validation_refit=False,mean_absolute_relative_error=.001,maximum_underestimate_seconds=.5,no_false_feasible=True,fit_coefficients=dict(zip(('per_D','per_A'),card['cost_model']['coefficients'])))
 acceptance=dict(full_protocol_accepted=True,scientific={'timing':m},declared_CPU_fixture=True)
 return card,data,acceptance

def exercise(*,overshoot=False,selection_audit=True,fail_score=False,fail_slot=None,external_endpoint=None,external_score=None):
 card,data,acceptance=inputs();events=[];saved=[];index=[0]
 def endpoint(slot,plan=None,reference=None):
  if slot['id']==fail_slot:raise RuntimeError('DECLARED_REQUEST_FAILURE')
  events.append(('request',slot['id'],slot.get('clock_anchor_id')))
  if external_endpoint:return external_endpoint(slot,plan,reference)
  seconds=300. if plan is None or slot['kind']=='CLOCK' else 300.+5.759309912605651*(plan['counts']['D']-36)+.12491496618716978*plan['counts']['A']
  if overshoot and slot['kind']=='QUERY' and slot.get('query_slot',9)<4:seconds=250.
  return dict(status='COMPLETE',timing_boundary=TIME_BOUNDARY,full_request_seconds=seconds,core_seconds=seconds-5,solver_steps=36,guided_pairs=36)
 def score(row,ref):
  events.append(('score',row['id']))
  if fail_score:raise RuntimeError('DECLARED_SCORE_FAILURE')
  if external_score:return external_score(row,ref)
  return dict(LPIPS=.05)
 state=run(fit_members=data['CAL_FIT_members'],select_members=['cpu_select_0','cpu_select_1'],card=card,cost_acceptance=acceptance,native=endpoint,evaluate=endpoint,score=score,accept_native_clock=lambda rows:dict(declared_CPU_fixture=True,rows=rows),build_consumer=lambda clock:data,save=lambda s:saved.append(s),exposure_recheck=lambda:dict(passed=selection_audit,declared_CPU_fixture=True),elapsed_GPUh=lambda:0.,calibration_cap_GPUh=14.)
 return state,events,saved

class Repair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.card,cls.data,cls.acceptance=inputs();cls.ctx=context(cls.data,cls.card,[300.]*4);cls.result,cls.events,_=exercise()
 def test_full_scope_and_deferred_scoring(self):
  r=self.result;self.assertEqual(len(r['rows']),102);self.assertLessEqual(r['query_attempts'],8)
  self.assertEqual(r['status'],'P1_REPAIR_CAL_SELECTION_COMPLETE');self.assertIsNotNone(r['selected_policy'])
  self.assertTrue(all(x['status'] in ('COMPLETE','UNUSED_REGISTERED_UPPER_BOUND') for x in r['rows']))
  first_score=next(i for i,e in enumerate(self.events) if e[0]=='score')
  self.assertGreater(first_score,next(i for i,e in enumerate(self.events) if e[:2]==('request','anchor_0_3')))
 def test_same_member_strict_past_anchor(self):
  by={r['id']:r for r in self.result['rows']}
  for row in by.values():
   if row['status']=='COMPLETE' and 'clock_anchor_id' in row:
    a=by[row['clock_anchor_id']];self.assertEqual(a['member'],row['member']);self.assertEqual(a['kind'],'CLOCK');self.assertTrue(row['timing_prediction']['created_before_target_execution'])
 def test_all_phase_alpha_and_historical_identity(self):
  for x in self.result['candidates']:
   for i,(a,alpha) in enumerate(zip(x['proposal']['policy']['actions'],x['proposal']['policy']['shared_alpha']),1):
    if a=='A':self.assertEqual(alpha,1. if i<25 else .5)
  for role in STRONG:self.assertEqual(self.ctx['historical'][role],self.card['policies'][role])
 def test_all_first_overbudget_can_recover_once(self):
  r,events,_=exercise(overshoot=True);self.assertEqual(r['recovery']['mode'],'ONE_LOWER_D_RECOVERY');self.assertEqual(r['recovery']['iterations'],1);self.assertLessEqual(r['query_attempts'],8)
  first={x['proposal']['policy']['fingerprint']:x['proposal']['policy'] for x in r['candidates'] if x['query_slot']<4}
  for x in r['recovery']['proposals']:self.assertLess(x['policy']['counts']['D'],first[x['recovery_parent']]['counts']['D'])
 def test_rejected_selection_exposure_stops(self):
  with self.assertRaisesRegex(ValueError,'CAL_SELECT'):exercise(selection_audit=False)
 def test_score_failure_stops_without_invented_value(self):
  with self.assertRaisesRegex(RuntimeError,'SCORE_FAILURE'):exercise(fail_score=True)
 def test_failed_endpoint_not_retried(self):
  with self.assertRaisesRegex(RuntimeError,'REQUEST_FAILURE'):exercise(fail_slot='anchor_0_0')
 def test_gate_rejects_partial_or_failed_or_refit(self):
  for path,val in [('full_protocol_accepted',False),('timing_model_validated',False),('validation_rows',71),('validation_refit',True),('maximum_underestimate_seconds',2.01),('no_false_feasible',False)]:
   a=copy.deepcopy(self.acceptance)
   if path=='full_protocol_accepted':a[path]=val
   else:a['scientific']['timing'][path]=val
   with self.assertRaises(ValueError):timing_gate(a,self.card)
 def test_quote_full_no_dedup_credit(self):
  q=quote(self.card,43.2);self.assertEqual(len(q['path_allowance_seconds']),102);self.assertGreater(q['forecast_complete_GPUh'],11.9);self.assertTrue(q['specific_whole_card_approval_required']);self.assertEqual(q['cumulative_cap_GPUh'],226)
 def test_incomplete_recovery_cohort_rejected(self):
  first=[x['proposal'] for x in self.ctx['batch']['batch']]
  with self.assertRaises(ValueError):one_recovery(self.ctx,first,{})
if __name__=='__main__':unittest.main()
