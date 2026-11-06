import json,copy,hashlib,tempfile,unittest
from pathlib import Path
from wcomr.common_long_card_r1 import RUN,COUNTS,MANIFEST,CONFIG,matrix
from wcomr.common_long_finance_r1 import ENVELOPE,settle_original,HostBudgetPool
from wcomr.common_long_terminal_r1 import accept
from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json
from wcomr.policy_price_terminal_r1 import record
ROOT=Path(__file__).resolve().parents[1]
def put(v,key,obj):
 raw=json.dumps(obj,sort_keys=True);h=hashlib.sha256(raw.encode()).hexdigest();v['files'][key]=dict(exists=True,raw_utf8=raw,bytes=len(raw.encode()),sha256=h);return h

def fixture(host='two_card'):
 card=json.loads((ROOT/MANIFEST).read_text());v=dict(files={},original_live_handles=dict(runner=False,post=False,guardian=False,supervisor=False,container=False),own_UUID_lock_free=True)
 L=dict(host=host,run_id=RUN,launch_id='CPU-only',source_revision='a'*40,stage='/fixture',gpu_uuid='GPU-fixture',scope_counts=COUNTS,billed_limit_GPUh=3);v['launch']=L
 put(v,'card',card);put(v,'config',dict(scope_counts=COUNTS,matrix=matrix(card)))
 reg=dict(source_revision=L['source_revision'],stage=L['stage'],payload_sha256={MANIFEST:v['files']['card']['sha256'],CONFIG:v['files']['config']['sha256']},runtime_source_sha256={'runtime.py':'b'*64})
 L['registration_sha256']=put(v,'registration',reg);v.update(payload_actual_sha256=reg['payload_sha256'],runtime_actual_sha256=reg['runtime_source_sha256']);L['authorization_sha256']=put(v,'authorization',dict(L))
 runner=dict(pid=123,start_ticks=10,uid=1000)
 def snap(active):return dict(gpu_uuid=L['gpu_uuid'],compute_mode='Exclusive_Process',compute_apps=[dict(runner,gpu_uuid=L['gpu_uuid'])] if active else [],mps_processes=[],observed_unix=100)
 journal=[dict(snapshot=snap(True),context_granted=True,monotonic_elapsed=t) for t in (1,2)]
 v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in journal)
 put(v,'monitor_final',dict(accepted=True,runner=runner,observations=2,final_snapshot=snap(False),monitor_sha256=hashlib.sha256(v['monitor_raw_utf8'].encode()).hexdigest()))
 put(v,'ready',dict(identity=runner));put(v,'grant',dict(runner=runner,gpu_uuid=L['gpu_uuid'],source_revision=L['source_revision']))
 bill={k:L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')};bill.update(wall_seconds=4.,actual_GPUh=4/3600);put(v,'billing',bill)
 pool=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=1,origin_gpu_jobs_launched=0,jobs={RUN:dict(status='SETTLED',launch_id=L['launch_id'],actual_GPUh=bill['actual_GPUh'],billing_sha256=v['files']['billing']['sha256'])},events=[]);pool.update(BudgetPool.accounting(pool));v['pool']=pool
 put(v,'supervisor',dict(child_exit_code=0,post_exit_code=0))
 put(v,'collection',dict(matrix=matrix(card),rows=[dict(s,status='COMPLETE',full_request_seconds=300.,paper_denoise_decode_seconds=280.,timing_is_diagnostic=True,fingerprint={'guided':['x']*36,'final':'y','video':'z'}) for s in matrix(card)],states=[dict(prompt=r['name'],step=t) for r in card['requests'] for t in card['states']]))
 put(v,'post',dict(values=[dict(prompt=r['name'],step=t,scores={label:dict(MSE=0.) for label in card['labels']}) for r in card['requests'] for t in card['states']],states=12,readout_positions=84,CPU_only=True,video_quality_claim=False,billing_sha256=v['files']['billing']['sha256'],collection_sha256=v['files']['collection']['sha256']))
 put(v,'post_exit',dict(exit_code=0,CPU_only_after_UUID_release=True,final_result_sha256=v['files']['post']['sha256']))
 v.update(CPU_resources=dict(cores=2,memory_bytes=8*2**30,timeout_seconds=3600),source_and_asset_SHA_verified=True,storage_and_cross_disk_journal_verified=True)
 eid=RUN if host=='four_card' else ENVELOPE
 central=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=1,origin_gpu_jobs_launched=0,jobs={eid:dict(L,status='RESERVED_OR_RUNNING'),'old-unknown':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-unknown',billed_limit_GPUh=16.5)},events=[]);central.update(BudgetPool.accounting(central))
 return v,central

class Terminal(unittest.TestCase):
 def settle(self,v,c):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',c);pool=BudgetPool(root)
   v['central_settlement']=settle_original(pool,v);before=pool.read();settle_original(pool,v);self.assertEqual(before,pool.read());self.assertEqual(before['jobs']['old-unknown'],c['jobs']['old-unknown'])
 def test_both_hosts_exact_once(self):
  for host in ('four_card','two_card'):
   v,c=fixture(host);self.settle(v,c);self.assertFalse(accept(v)['science_promoted'])
 def test_failures_keep_money_but_refuse_acceptance(self):
  v,c=fixture();self.settle(v,c)
  for kind in ('score','paths','clock','GPU_live','lock','source','storage','CPU_memory','missing_bill','bad_alpha','monitor_gap','wrong_launch'):
   w=copy.deepcopy(v)
   if kind=='score':r=record(w,'post');r['readout_positions']=83;put(w,'post',r)
   elif kind=='paths':r=record(w,'collection');r['rows'].pop();put(w,'collection',r)
   elif kind=='clock':r=record(w,'collection');r['rows'][0]['paper_denoise_decode_seconds']=999;put(w,'collection',r)
   elif kind=='GPU_live':w['original_live_handles']['runner']=True
   elif kind=='lock':w['own_UUID_lock_free']=False
   elif kind=='source':w['payload_actual_sha256']={}
   elif kind=='storage':w['storage_and_cross_disk_journal_verified']=False
   elif kind=='CPU_memory':w['CPU_resources']['memory_bytes']=16*2**30
   elif kind=='missing_bill':w['files']['billing']['exists']=False
   elif kind=='bad_alpha':r=record(w,'card');r['alpha']['step_ge_25']=1.;put(w,'card',r)
   elif kind=='monitor_gap':w['monitor_raw_utf8']=''
   else:w['launch']['launch_id']='other'
   with self.subTest(kind=kind),self.assertRaises(ValueError):accept(w)
if __name__=='__main__':unittest.main()
