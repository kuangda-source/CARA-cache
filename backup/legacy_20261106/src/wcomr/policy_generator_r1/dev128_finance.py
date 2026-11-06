"""Single-envelope settlement and dual-host ledger port, bounded to DEV128.

Production writes require an already registered original job. Tests use isolated
fixture ledgers; this module has no SSH/dispatch/initialization entrypoint.
"""
import copy,math,time
from .dev128_card import RUN,COUNTS
from .continuation_preparation import require
from ..gpu_budget_pool_v2 import BudgetPool,finite
from ..policy_price_terminal_r1 import record
ENVELOPE=RUN+'-external-budget-envelope'

def financial_hold(job):
 return (job.get('kind')=='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD'
         and job.get('confirmed_GPU_submission') is False and job.get('actual_cost_unknown') is True
         and job.get('launch_id')=='NOT_A_CONFIRMED_GPU_SUBMISSION'
         and job.get('supervisor_pid') is None and job.get('supervisor_start_ticks') is None)

class HostBudgetPool(BudgetPool):
 @staticmethod
 def accounting(value):
  # Preserve the entire authoritative liability row. Only the local duplicate-
  # device check sees a separate financial identity for a proven retired hold.
  scoped=copy.deepcopy(value)
  for key,job in scoped['jobs'].items():
   if financial_hold(job):job['gpu_uuid']='FINANCIAL_LIABILITY_ONLY:'+key
  return BudgetPool.accounting(scoped)
 def reserve(self,job,gpu):
  require(job['run_id']==job['job_id']==RUN and job['scope_counts']==COUNTS,'Not DEV128')
  forecast,limit=job['forecast_GPUh'],job['billed_limit_GPUh']
  host=job['host'];name,cap={'four_card':('RTX 6000 Ada','8.9'),'two_card':('RTX A6000','8.6')}[host]
  require(finite(forecast) and finite(limit) and 0<forecast<=limit<=12,'Bounded complete quote required')
  require(all(job.get(k) for k in ('source_revision','config_sha256','launch_id')),'Missing identity')
  require(gpu['uuid']==job['gpu_uuid'] and name in gpu['name'] and gpu['compute_cap']==cap and finite(gpu['memory_used_mib']) and 0<=gpu['memory_used_mib']<=1024 and not gpu['pids'],'Wrong or busy physical host GPU')
  with self.transaction() as value:
   require(value is not None and value['cap_gpu_hours']==226 and not value.get('budget_overrun_recorded'),'Ledger blocked')
   require(RUN not in value['jobs'],'Existing original job must recover')
   require(limit<=self.accounting(value)['available_gpu_hours']+1e-10,'Cumulative cap')
   require(not any(j['status']=='RESERVED_OR_RUNNING' and not financial_hold(j) and j['gpu_uuid']==job['gpu_uuid'] for j in value['jobs'].values()),'UUID reserved')
   value['jobs'][RUN]=dict(copy.deepcopy(job),status='RESERVED_OR_RUNNING',kind='V2',reserved_unix=time.time())
   self.commit(value,dict(type='DEV128_RESERVE_ON_SELECTED_HOST',job_id=RUN));return copy.deepcopy(value)

def financial_original(v):
 L=v['launch'];b=record(v,'billing');job=v['pool']['jobs'][RUN]
 for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):require(b[k]==L[k],'Bill/launch mismatch: '+k)
 require(math.isfinite(b['wall_seconds']) and b['wall_seconds']>0 and b['actual_GPUh']==b['wall_seconds']/3600,'No estimated or corrupt bill')
 require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'],'Original handles/lock still active')
 require(job['status']=='SETTLED' and job['launch_id']==L['launch_id'] and job['actual_GPUh']==b['actual_GPUh'] and job['billing_sha256']==v['files']['billing']['sha256'],'Original host settlement missing')
 require(v['pool']['cap_gpu_hours']==226 and all(v['pool'][k]==x for k,x in HostBudgetPool.accounting(v['pool']).items()),'Host ledger arithmetic')
 return b

def settle_original(pool,v):
 """Idempotent: failed scientific runs still settle exact original GPU charges."""
 b=financial_original(v);L=v['launch'];eid=RUN if L['host']=='four_card' else ENVELOPE
 before=pool.read();j=before['jobs'][eid]
 for k in ('run_id','stage','source_revision','gpu_uuid','launch_id','billed_limit_GPUh'):require(j[k]==L[k],'Wrong central envelope: '+k)
 require(before['cap_gpu_hours']==226,'Wrong central cap')
 after=pool.settle(eid,b['actual_GPUh'],v['files']['billing']['sha256'])
 require(all(after['jobs'][k]==x for k,x in before['jobs'].items() if k!=eid),'Unrelated or unknown liability changed')
 return dict(central_before=before,central_after=after,envelope_id=eid,billing_sha256=v['files']['billing']['sha256'],host=L['host'],launch_id=L['launch_id'],scientific_acceptance_implied=False,same_money_not_two_charges=True)

def audit_settlement(v):
 b=financial_original(v);L=v['launch'];s=v['central_settlement'];before=s['central_before'];after=s['central_after'];eid=RUN if L['host']=='four_card' else ENVELOPE
 require(s['envelope_id']==eid and s['host']==L['host'] and s['launch_id']==L['launch_id'] and s['billing_sha256']==v['files']['billing']['sha256'],'Central binding differs')
 require(s['same_money_not_two_charges'] and s['scientific_acceptance_implied'] is False,'Finance is not science')
 require(before['cap_gpu_hours']==after['cap_gpu_hours']==226,'Central budget changed')
 require(all(after[k]==x for k,x in HostBudgetPool.accounting(after).items()),'Central totals differ')
 require(set(before['jobs'])==set(after['jobs']) and all(after['jobs'][k]==x for k,x in before['jobs'].items() if k!=eid),'Original other reservations changed')
 j=after['jobs'][eid]
 for k in ('run_id','stage','source_revision','gpu_uuid','launch_id','billed_limit_GPUh'):require(j[k]==L[k],'Central original identity differs')
 require(j['status']=='SETTLED' and j['actual_GPUh']==b['actual_GPUh'] and j['billing_sha256']==s['billing_sha256'],'Central not settled')
 require(L['host']=='four_card' or RUN not in after['jobs'],'Two-card cost charged twice centrally')
 return dict(financial_terminal_accepted=True,actual_GPUh=b['actual_GPUh'],science_accepted=False)
