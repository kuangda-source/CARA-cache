"""Declared synthetic whole112 terminal and failure controls; no GPU results."""
import copy,json,unittest
from pathlib import Path
from wcomr.policy_generator_r1.cost112_card import RUN,COUNTS,MANIFEST
from wcomr.policy_generator_r1.cost112_terminal import scientific,accept
from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from wcomr.policy_price_terminal_r1 import record,IMAGE
from wcomr.gpu_budget_pool_v2 import BudgetPool
from test_policy_price_terminal_r1 import h,put
ROOT=Path(__file__).resolve().parents[1]
METRIC=dict(alexnet_sha256='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02',linear_sha256='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0',version='0.1.4',metric_version='0.1',net='alex')

def result_fixture(slot,policy):
 diagnostic=slot['section']=='DIAGNOSTIC';seconds=320. if policy is None else 322.+6*(policy['counts']['D']-36)+.2*policy['counts']['A']
 r=dict(status='COMPLETE',solver_steps=36,guided_pairs=36,timing_boundary=TIME_BOUNDARY,full_request_seconds=seconds,core_seconds=seconds-1,audit=diagnostic,in_timing_guided_copies=36 if diagnostic else 0,in_timing_hashes=0,clean_deployment_timing=not diagnostic)
 if policy is not None:r.update(policy_fingerprint=policy['fingerprint'],teacher_calls=0,online_fitting=False,semantic_history=[dict(step=i+1,planned=a,actual=a,shared_alpha=policy['shared_alpha'][i] if a!='D' else None,fallback_reason=None) for i,a in enumerate(policy['actions'])])
 return r

def fixture():
 card=json.loads((ROOT/MANIFEST).read_text());v=dict(files={},requests={},artifact_checks={},scores={},original_live_handles=dict(runner=False,guardian=False,supervisor=False,post=False,container=False),own_UUID_lock_free=True)
 identity=dict(pid=101,start_ticks=501,uid=1000);source=h('CPU_ONLY');gpu='GPU-fixture';guardian=dict(pid=100,start_ticks=500)
 L=dict(run_id=RUN,launch_id='CPU112-fixture',source_revision=source,gpu_uuid=gpu,stage='/fixture',scope_counts=COUNTS,billed_limit_GPUh=11.9,forecast_GPUh=card['quote']['forecast_GPUh'],guardian_identity=guardian);v['launch']=L
 put(v,'card',card);put(v,'quote',card['quote']);L['config_sha256']=put(v,'config',dict(run_id=RUN,scope_counts=COUNTS,matrix=card['matrix'],forecast_complete_GPUh=L['forecast_GPUh'],billed_limit_GPUh=11.9))
 reg=dict(source_revision=source,stage='/fixture',runtime_source_sha256={'fixture.py':h('runtime')},payload_sha256={n:v['files'][k]['sha256'] for k,n in [('config','pg-config.json'),('quote','pg-whole-quote.json'),('card',MANIFEST)]});L['registration_sha256']=put(v,'registration',reg);v.update(payload_actual_sha256=reg['payload_sha256'],runtime_actual_sha256=reg['runtime_source_sha256'])
 put(v,'CPU_acceptance',dict(full_GPU_lifecycle_CPU_accepted=True,production_CPU_accepted=True,source_revision=source));auth=dict(L,independent_CPU_acceptance_sha256=v['files']['CPU_acceptance']['sha256']);L['authorization_sha256']=put(v,'authorization',auth)
 v['container']=dict(state=dict(Running=False,ExitCode=0,OOMKilled=False),image=IMAGE,readonly_root=True,pid_mode='host',manifest_sha256=L['registration_sha256'],device_requests=[dict(DeviceIDs=[gpu])])
 def snap(active,stamp=100):return dict(gpu_uuid=gpu,compute_mode='Exclusive_Process',compute_apps=[dict(identity,gpu_uuid=gpu)] if active else [],mps_processes=[],observed_unix=stamp)
 put(v,'guardian',dict(status='COST112_HOST_GUARDIAN_TERMINAL',container_exit_code=0,identity=guardian,gpu_uuid=gpu,source_revision=source,mode_admission=dict(verified_snapshot=snap(False)),mode_restoration=dict(restored=True,status='PRIOR_MODE_RESTORED_IDLE')))
 put(v,'supervisor',dict(child_exit_code=0,post_exit_code=0,exclusive_monitor_accepted=True,child_identity=identity,**{k:L[k] for k in ('source_revision','run_id','launch_id','gpu_uuid','scope_counts')}));put(v,'ready',dict(identity=identity));put(v,'grant',dict(runner=identity,gpu_uuid=gpu,source_revision=source))
 rows=[];t=100.
 def art(id,name):return dict(path='/fixture/'+id+'/'+name,sha256=h(id+name),bytes=1)
 for slot in card['matrix']:
  r=result_fixture(slot,card['policies'][slot['role']]);r.update(started_unix=t,ended_unix=t+329,video_artifact=art(slot['id'],'video.mp4'),final_latent_artifact=art(slot['id'],'latent.pt'));t+=330
  if slot['section']=='DIAGNOSTIC':r['guided_artifact']=art(slot['id'],'guided.pt')
  if slot['section'] in ('CALIBRATION','VALIDATION') and slot['role']!='NATIVE':
   from wcomr.policy_generator_r1.cost112_model import predict
   anchor=next(x for x in rows if x['slot']['id']==slot['clock_anchor_id']);r['timing_prediction']=predict(card,slot,anchor['result']['full_request_seconds'])
  req=dict(slot=slot,policy=card['policies'][slot['role']],result=copy.deepcopy(r));v['requests'][slot['id']]=req
  r['request_artifact']=art(slot['id'],'request.json')
  ck={k:r[k] for k in ('video_artifact','final_latent_artifact','request_artifact')};ck.update(frames=93,latent_tensor={'CPU_fixture':1})
  if slot['section']=='DIAGNOSTIC':ck.update(guided_artifact=r['guided_artifact'],guided_steps=36,guided_tensors=[{'CPU_fixture':i} for i in range(36)])
  v['artifact_checks'][slot['id']]=ck;rows.append(dict(slot=slot,status='COMPLETE',result=r))
 batch=dict(status='COMPLETE112_ORIGINALS_PENDING_AUDIT',scope_counts=COUNTS,rows=rows);put(v,'runner',dict(batch=batch,model_loads=1,pid=101,source_revision=source,registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256']))
 pairs=[]
 for s in card['matrix']:
  if s['role']=='PG_ALL_D':pairs.append((next(x['id'] for x in card['matrix'] if all(x[k]==s[k] for k in ('section','member','repeat')) and x['role']=='NATIVE'),s['id']))
  if s['section']=='ANCHOR':pairs.append((s['id'],next(x['id'] for x in card['matrix'] if x['role']=='PG_ALL_D' and x['member']==s['member'] and x['repeat']==s['repeat'] and x['section'] in ('CALIBRATION','VALIDATION'))))
  if s['section']=='DIAGNOSTIC':pairs.append((next(x['id'] for x in card['matrix'] if x['section']=='CALIBRATION' and x['member']==s['member'] and x['role']==s['role']),s['id']))
 v['controls']=[dict(left=a,right=b,latent_equal=True,RGB93_equal=True,left_rgb=dict(frames=93,sha256=h('rgb')),right_rgb=dict(frames=93,sha256=h('rgb'))) for a,b in pairs];v['all36_diagnostic_equal']=True
 put(v,'collection_verified',dict(controls=v['controls'],all36_diagnostic_equal=True,before_GPU_release=True))
 elapsed=t-99;journal=[dict(snapshot=snap(True,99+e),context_granted=True,monotonic_elapsed=e) for e in range(1,int(elapsed),30)];v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in journal)
 put(v,'monitor_final',dict(accepted=True,observations=len(journal),runner=identity,final_snapshot=snap(False,t),monitor_sha256=h(v['monitor_raw_utf8'])))
 bill=dict(wall_seconds=elapsed,actual_GPUh=elapsed/3600,ended_unix=t,**{k:L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')});put(v,'billing',bill)
 pool=dict(schema="WC_GPU_BUDGET_POOL_V2",origin_gpu_jobs_launched=0,cap_gpu_hours=226,origin_used_gpu_hours=1.,jobs={RUN:dict(status='SETTLED',actual_GPUh=bill['actual_GPUh'],launch_id=L['launch_id'],billing_sha256=v['files']['billing']['sha256'])});pool.update(BudgetPool.accounting(pool));v['pool']=pool
 scores={};by={r['slot']['id']:r['result'] for r in rows}
 for s in card['matrix']:
  if s['section'] not in ('CALIBRATION','VALIDATION') or s['role']=='NATIVE':continue
  ref=next(x for x in card['matrix'] if x['role']=='NATIVE' and all(x[k]==s[k] for k in ('section','member','seed','repeat')))
  value=dict(reference_sha256=by[ref['id']]['video_artifact']['sha256'],candidate_sha256=by[s['id']]['video_artifact']['sha256'],frames=93,pts=[[i,'1/16'] for i in range(93)],frame_distances=[0.]*93,mean_LPIPS=0.,metric_identity=METRIC,geometry=[432,768,3],resize_crop_subsample=False,device='cpu');put({'files':v['scores']},s['id'],value)
  scores[s['id']]=dict(reference_id=ref['id'],LPIPS=0.,score_artifact=dict(art(s['id'],'score.json'),sha256=v['scores'][s['id']]['sha256']))
 put(v,'score_progress',dict(status='CPU_SCORE_COMPLETE72',completed_pairs=72,planned_pairs=72,scores=scores,started_unix=t+1,release=dict(GPU_released=True,ledger_settled=True,lock_free=True,CUDA_hidden=True,billing_sha256=v['files']['billing']['sha256'],observed_unix=t+.5)))
 put(v,'post',dict(scientific=scientific(v),runner_sha256=v['files']['runner']['sha256']));put(v,'post_exit',dict(exit_code=0,CPU_only_after_UUID_release=True,final_result_sha256=v['files']['post']['sha256']))
 return v

class Combined(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.template=fixture()
 def setUp(self):self.v=copy.deepcopy(self.template)
 def change(self,key,fun):d=record(self.v,key);fun(d);put(self.v,key,d)
 def test_full112_finance(self):self.assertTrue(accept(self.v)['full_protocol_accepted'])
 def test_missing_path(self):
  self.change('runner',lambda d:d['batch']['rows'].pop())
  with self.assertRaises(ValueError):scientific(self.v)
 def test_alpha_change(self):
  key=next(k for k,x in self.v['requests'].items() if x['policy'] and x['policy']['counts']['A'])
  self.v['requests'][key]['policy']['shared_alpha'][21]=.123
  with self.assertRaises(ValueError):scientific(self.v)
 def test_score_before_release(self):
  self.change('score_progress',lambda d:d['release'].update(GPU_released=False))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_score_before_bill(self):
  self.change('score_progress',lambda d:d['release'].update(observed_unix=0))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_missing_score(self):
  self.v['scores'].pop(next(iter(self.v['scores'])))
  with self.assertRaises(ValueError):scientific(self.v)
 def test_corrupt_score(self):
  key=next(iter(self.v['scores']));d=record({'files':self.v['scores']},key);d['frame_distances'][0]=-1;put({'files':self.v['scores']},key,d)
  with self.assertRaises(ValueError):scientific(self.v)
 def test_missing_control(self):
  self.v['controls'].pop()
  with self.assertRaises(ValueError):scientific(self.v)
 def test_native_numerical_mismatch(self):
  self.v['artifact_checks']['DIAGNOSTIC_PG_ALL_D_0_1']['guided_tensors'][0]={'wrong':1}
  with self.assertRaises(ValueError):scientific(self.v)
 def test_foreign_context(self):
  d=[json.loads(x) for x in self.v['monitor_raw_utf8'].splitlines()];d[-1]['snapshot']['compute_apps'].append(dict(pid=999,uid=5,start_ticks=1));self.v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in d);self.change('monitor_final',lambda m:m.update(monitor_sha256=h(self.v['monitor_raw_utf8'])))
  with self.assertRaises(ValueError):accept(self.v)
 def test_unsettled(self):
  self.v['pool']['jobs'][RUN]['status']='RESERVED_OR_RUNNING'
  with self.assertRaises(ValueError):accept(self.v)
 def test_failed_cpu_score(self):
  self.change('supervisor',lambda d:d.update(post_exit_code=1))
  with self.assertRaises(ValueError):accept(self.v)
 def test_active_container(self):
  self.v['container']['state']['Running']=True
  with self.assertRaises(ValueError):accept(self.v)
 def test_source_changed(self):
  self.v['runtime_actual_sha256']={'changed':1}
  with self.assertRaises(ValueError):accept(self.v)
if __name__=='__main__':unittest.main()
