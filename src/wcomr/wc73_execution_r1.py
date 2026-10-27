"""Authorized WC73 increment. Immutable A/B identities, additive central finance."""
import copy,json,time
from pathlib import Path
from .gpu_budget_pool_v2 import BudgetPool,sha,finite
RUN='cara-wc73-r1-20261027'
MATRIX='plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml'
PLAN='plans/cara_wc_time_protocol_r1_20261027/EXECUTION_PLAN.json'
RA='plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json'
def read(p):return json.loads(Path(p).read_text())
def require(b,msg):
 if not b:raise ValueError(msg)
def hold(j):
 return j.get('kind')=='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD' and j.get('confirmed_GPU_submission') is False and j.get('actual_cost_unknown') is True and j.get('launch_id')=='NOT_A_CONFIRMED_GPU_SUBMISSION' and j.get('supervisor_pid') is None and j.get('supervisor_start_ticks') is None
def admit_host(value, host, exclude=None):
 """User 2026-10-27: one owned GPU job per registered host, shared total cap."""
 require(host in ('four_card','two_card'),'Unregistered selected host')
 active=[j for k,j in value['jobs'].items() if k!=exclude and j['status']=='RESERVED_OR_RUNNING' and not hold(j)]
 require(all(j.get('host') in ('four_card','two_card') for j in active),'Active job host unknown')
 require(not any(j['host']==host for j in active),'Selected host already has an owned GPU job')
 require(len(active)<=1,'More than one other-host owned GPU job')
 return True
class Pool(BudgetPool):
 @staticmethod
 def accounting(v):
  x=copy.deepcopy(v)
  for k,j in x['jobs'].items():
   if hold(j):j['gpu_uuid']='FINANCIAL_LIABILITY_ONLY:'+k
  return BudgetPool.accounting(x)
 def reserve(self,j,gpu):
  require(j['job_id']==RUN and j['billed_limit_GPUh']==12 and 0<j['forecast_GPUh']<=12,'Exact WC73 whole envelope')
  name,cap={'four_card':('RTX 6000 Ada','8.9'),'two_card':('RTX A6000','8.6')}[j['host']]
  require(gpu['uuid']==j['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==cap and not gpu['pids'] and 0<=gpu['memory_used_mib']<=1024,'Fresh selected physical GPU')
  with self.transaction() as v:
   require(v is not None and not v.get('budget_overrun_recorded') and RUN not in v['jobs'],'Recover original intent; no replay')
   admit_host(v,j['host'])
   require(self.accounting(v)['available_gpu_hours']>=12,'Whole card needs 12 GPUh')
   v['jobs'][RUN]=dict(copy.deepcopy(j),kind='V2',status='RESERVED_OR_RUNNING',whole_limit_GPUh=12,reserved_unix=time.time())
   self.commit(v,dict(type='WC73_WHOLE12_RESERVE',job_id=RUN));return copy.deepcopy(v)
 def finish_A(self,actual,bill,passed):
  require(finite(actual) and actual>=0 and len(bill)==64,'Finite original bill')
  if not passed:return self.settle(RUN,actual,bill)
  require(actual<=5,'Phase A hard cap; no B')
  with self.transaction() as v:
   j=v['jobs'][RUN];key=RUN+'-A-settled'
   require(j['status']=='RESERVED_OR_RUNNING','Original envelope missing')
   if key in v['jobs']:
    require(v['jobs'][key]['actual_GPUh']==actual and v['jobs'][key]['billing_sha256']==bill,'Conflicting A settlement');return copy.deepcopy(v)
   require(j['billed_limit_GPUh']==12,'Whole envelope changed')
   v['jobs'][key]=dict(copy.deepcopy(j),job_id=key,parent_run_id=RUN,status='SETTLED',billed_limit_GPUh=5,actual_GPUh=actual,billing_sha256=bill,settled_unix=time.time(),phase='A')
   j.update(billed_limit_GPUh=7,phase='B_PENDING_RELEASED_CPU_FREEZE',A_actual_GPUh=actual,A_billing_sha256=bill)
   self.commit(v,dict(type='WC73_SETTLE_A_KEEP_B7',job_id=RUN));return copy.deepcopy(v)

def validate(project,stage):
 stage=Path(stage);reg=read(stage/'registration.json');auth=read(stage/'pg-GPU-authorization.json')
 require(all(sha(stage/n)==h for n,h in reg['payload_sha256'].items()),'Staged source changed')
 require(all(sha(Path(project)/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),'Pinned runtime changed')
 c=read(stage/MATRIX);plan=read(stage/PLAN)
 require(sha(stage/MATRIX)==plan['science_matrix_sha256'],'Matrix differs')
 require(auth.get('one_owned_job_per_host_authorized') is True,'Explicit per-host concurrency authorization required')
 require(auth['direct_user_authorization'] and auth['whole_GPUh']==12 and auth['phase'] in ('A','B') and auth['run_id']==RUN,'Exact chat authority')
 require(auth['registration_sha256']==sha(stage/'registration.json') and auth['source_revision']==reg['source_revision'],'Authorization source differs')
 require(auth['scope_sha256']==c['scope_sha256'] and len(c['physical_matrix'])==73,'Scope differs')
 require(read(stage/'execution-CPU-proof.json')['passed'] is True,'Affected launch CPU proof absent')
 require(auth['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json'),'CPU receipt changed')
 return c,reg,auth
