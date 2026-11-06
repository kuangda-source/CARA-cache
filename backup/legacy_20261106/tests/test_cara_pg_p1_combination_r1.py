"""Complete acceptance faults using declared synthetic endpoint/price evidence."""
import copy,hashlib,json,time,unittest
from pathlib import Path
from wcomr.policy_generator_r1.production_batch import run
from wcomr.policy_generator_r1.production_terminal import scientific,accept
from wcomr.policy_generator_r1.production_evidence import native_clock,validate_score
from wcomr.policy_generator_r1.production_contract import COUNTS,matrix
from wcomr.policy_generator_r1.continuation_preparation import generator_input,TIME_BOUNDARY
from wcomr.policy_generator_r1.production_stage import RUN
from wcomr.policy_price_terminal_r1 import record
from test_policy_price_terminal_r1 import fixture as price_fixture,put,h
from wcomr.gpu_budget_pool_v2 import BudgetPool
ROOT=Path(__file__).resolve().parents[1]


def fixture():
 v,old,oldacc=price_fixture();fit=old['files']['bundle']['data']['fit_members'];select=['av_animal_dear_1_0','industry_057']
 new=record(v,'bundle');new['costs']['dense_seconds']=[1.]*36;new['costs']['C_seconds']=[.05]*36
 new['costs']['A_seconds_by_alpha']={'.5':[.1]*36,'1.0':[.2]*36};new['costs']['shared_seconds']=1.
 oldraw=(json.dumps(old['files']['bundle']['data'],ensure_ascii=False,indent=2)+'\n')
 def rawput(key,raw):v['files'][key]=dict(exists=True,raw_utf8=raw,bytes=len(raw.encode()),sha256=h(raw))
 rawput('old_bundle',oldraw);put(v,'new_bundle',new)
 priceacc=dict(status='FULL_PRICE_ORIGINALS_EXCLUSIVITY_AND_FINANCE_ACCEPTED',full_protocol_accepted=True,clean_action_prices_accepted=True,
  exclusive_monitoring={'accepted':True},replacement_bundle_sha256=v['files']['new_bundle']['sha256'],original_label_bundle_sha256=h(oldraw))
 put(v,'price_acceptance',priceacc);put(v,'old_acceptance',oldacc)
 v['select_members']=select;v['requests']={};v['scores']={};v['artifact_checks']={}
 L=v['launch'];L.update(run_id=RUN,scope_counts=COUNTS,billed_limit_GPUh=10.5,forecast_GPUh=8.844444444444445)
 q=json.loads((ROOT/'manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json').read_text());put(v,'quote',q)
 config=dict(run_id=RUN,scope_counts=COUNTS,matrix=matrix(),forecast_complete_GPUh=L['forecast_GPUh'],billed_limit_GPUh=10.5);L['config_sha256']=put(v,'config',config)
 reg=record(v,'registration');reg['payload_sha256']={name:v['files'][key]['sha256'] for key,name in [('config','pg-config.json'),('quote','pg-whole-quote.json'),('old_bundle','pg-old-labels.json'),('new_bundle','pg-clean-prices.json'),('old_acceptance','pg-old-acceptance.json'),('price_acceptance','pg-price-acceptance.json')]}
 L['registration_sha256']=put(v,'registration',reg);v['payload_actual_sha256']=reg['payload_sha256'];v['container']['manifest_sha256']=L['registration_sha256']
 cpu=record(v,'CPU_acceptance');cpu['registration_sha256']=L['registration_sha256'];put(v,'CPU_acceptance',cpu)
 auth={k:val for k,val in L.items() if k!='authorization_sha256'};auth['independent_CPU_acceptance_sha256']=v['files']['CPU_acceptance']['sha256'];L['authorization_sha256']=put(v,'authorization',auth)
 sup=record(v,'supervisor');sup.update(run_id=RUN,scope_counts=COUNTS);put(v,'supervisor',sup)
 guard=record(v,'guardian');guard['status']='PG_P1_HOST_GUARDIAN_TERMINAL';put(v,'guardian',guard)
 identity=sup['child_identity'];metric=dict(CPU_FIXTURE_ONLY=True);seq=[100.];journal=[];clockholder={};consumerholder={};saved=[]
 def sample(stamp):return dict(snapshot=dict(gpu_uuid=L['gpu_uuid'],compute_mode='Exclusive_Process',compute_apps=[dict(identity,gpu_uuid=L['gpu_uuid'])],mps_processes=[],observed_unix=stamp),context_granted=True,monotonic_elapsed=stamp-99)
 journal.append(sample(99.))
 def artifact(identifier,suffix):return dict(path='/fixture/'+identifier+'/'+suffix,sha256=h(identifier+suffix),bytes=1)
 def endpoint(slot,policy=None,reference=None):
  t=seq[0];seq[0]+=1.;identifier=slot['id'];journal.append(sample(seq[0]));
  result=dict(status='COMPLETE',timing_boundary=TIME_BOUNDARY,full_request_seconds=36. if policy is None else 25.,core_seconds=35. if policy is None else 24.,solver_steps=36,guided_pairs=36,
   started_unix=t,ended_unix=t+.5,video_artifact=artifact(identifier,'video.mp4'),final_latent_artifact=artifact(identifier,'final-latent.pt'))
  if policy:result.update(semantic_history=[dict(step=i+1,planned=a,actual=a,fallback_reason=None) for i,a in enumerate(policy['actions'])],teacher_calls=0,online_fitting=False)
  req=dict(slot=slot,policy=policy,result=copy.deepcopy(result));put({'files':v['requests']},identifier,req)
  result['request_artifact']=dict(artifact(identifier,'request.json'),sha256=v['requests'][identifier]['sha256'])
  v['artifact_checks'][identifier]=dict(video_artifact=result['video_artifact'],final_latent_artifact=result['final_latent_artifact'],frames=93)
  if policy and slot['split']!='WARM':
   score=dict(reference_sha256=reference['video_artifact']['sha256'],candidate_sha256=result['video_artifact']['sha256'],frames=93,pts=[[i,'1/16'] for i in range(93)],frame_distances=[.05]*93,mean_LPIPS=sum([.05]*93)/93,metric_identity=metric,geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
   put({'files':v['scores']},identifier,score);result.update(LPIPS=score['mean_LPIPS'],score_artifact=dict(artifact(identifier,'score.json'),sha256=v['scores'][identifier]['sha256']))
  return result
 def clock(rows):
  raw=''.join(json.dumps(x)+'\n' for x in journal);v['native_monitor_prefix_raw_utf8']=raw
  c=native_clock(rows,fit_members=fit,profile_identity=new['profile_identity'],monitor_raw=raw,runner=identity,gpu_uuid=L['gpu_uuid'],now=seq[0],source_revision=L['source_revision'],launch_id=L['launch_id'])
  clockholder.update(c);put(v,'native_clock',c);return c
 def consumer(c):
  data=generator_input(v['files']['new_bundle']['raw_utf8'].encode(),priceacc,oldraw.encode(),oldacc,c);consumerholder.update(data);put(v,'consumer',data);return data
 batch=run(fit_members=fit,select_members=select,native=endpoint,evaluate=endpoint,build_consumer=consumer,accept_native_clock=clock,
  calibration_cap_GPUh=10.5,elapsed_GPUh=lambda:0.,save=lambda s:saved.append(copy.deepcopy(s)),exposure_recheck=lambda:dict(passed=True,CPU_FIXTURE_ONLY=True))
 put(v,'runner',dict(batch=batch,model_loads=1,metric_identity=metric,pid=identity['pid'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256']))
 v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in journal)
 final=record(v,'monitor_final');final.update(observations=len(journal),monitor_sha256=h(v['monitor_raw_utf8']));put(v,'monitor_final',final)
 bill=dict(wall_seconds=seq[0]-98.,actual_GPUh=(seq[0]-98.)/3600,**{k:L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')});put(v,'billing',bill)
 v['pool']['jobs'][RUN]=dict(status='SETTLED',launch_id=L['launch_id'],actual_GPUh=bill['actual_GPUh'],billing_sha256=v['files']['billing']['sha256']);v['pool'].update(BudgetPool.accounting(v['pool']))
 science=scientific(v);put(v,'post',dict(scientific=science,runner_sha256=v['files']['runner']['sha256']));put(v,'post_exit',dict(exit_code=0,CPU_only_after_UUID_release=True,final_result_sha256=v['files']['post']['sha256']))
 return v


class Combined(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.template=fixture()
 def setUp(self):self.v=copy.deepcopy(self.template)
 def change(self,key,fun):d=record(self.v,key);fun(d);put(self.v,key,d)
 def test_complete_replay_and_finance(self):
  a=accept(self.v);self.assertTrue(a['full_protocol_accepted']);self.assertEqual(a['scientific']['complete_registered_slots'],64);self.assertLessEqual(a['scientific']['query_attempts'],8)
 def test_original_score_nonfinite_rejected(self):
  key=next(iter(self.v['scores']));score=record({'files':self.v['scores']},key);score['frame_distances'][0]=float('nan');put({'files':self.v['scores']},key,score)
  with self.assertRaises(ValueError):scientific(self.v)
 def test_rank_scalar_cannot_override_original93(self):
  self.change('runner',lambda d:next(r for r in d['batch']['rows'] if r.get('LPIPS') is not None).update(LPIPS=0.))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_policy_selection_tampering(self):
  self.change('runner',lambda d:d['batch']['selected'].update(mean_loss=-1))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_missing_denominator_rejected(self):
  self.change('runner',lambda d:d['batch']['rows'].pop())
  with self.assertRaises(ValueError):scientific(self.v)
 def test_dirty_native_budget_rejected(self):
  self.change('native_clock',lambda d:d.update(before_candidate_endpoints=False))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_foreign_exclusive_context_rejected(self):
  rows=[json.loads(x) for x in self.v['monitor_raw_utf8'].splitlines()];rows[-1]['snapshot']['compute_apps'].append(dict(pid=999,uid=1005,start_ticks=3))
  self.v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in rows);self.change('monitor_final',lambda d:d.update(monitor_sha256=h(self.v['monitor_raw_utf8'])))
  with self.assertRaises(ValueError):accept(self.v)
 def test_unsettled_bill_rejected(self):
  self.v['pool']['jobs'][RUN]['status']='RESERVED_OR_RUNNING'
  with self.assertRaises(ValueError):accept(self.v)
 def test_failed_child_rejected(self):
  self.change('supervisor',lambda d:d.update(child_exit_code=1))
  with self.assertRaises(ValueError):accept(self.v)
 def test_running_container_rejected(self):
  self.v['container']['state']['Running']=True
  with self.assertRaises(ValueError):accept(self.v)
 def test_extra_artifact_score_rejected(self):
  self.v['scores']['unregistered']=next(iter(self.v['scores'].values()))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_omitted_prefix_rejected(self):
  self.v['native_monitor_prefix_raw_utf8']=''
  with self.assertRaises(ValueError):scientific(self.v)
if __name__=='__main__':unittest.main()
