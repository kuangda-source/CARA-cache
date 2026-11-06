"""One atomic administrative import; no model, CUDA or GPU process."""
import base64,hashlib,json,subprocess,time
from pathlib import Path
from wc_four_card_resource_cpu_r4 import ssh,write

FILES={
 'transition.py':'scripts/four_card_human_authority_transition_r1.py',
 'base.json':'reports/wc_four_card_v2_historical_full_pool_base_20261020.json',
 'pool.json':'reports/wc_four_card_v2_authority_initial_pool_20261022.json',
 'proof.json':'reports/wc_four_card_v2_unique_human_authority_proof_20261022.json',
 'human.json':'reports/wc_four_card_only_direct_human_authorization_20261022.json',
 'route-exit.json':'reports/wc_two_card_owned_local_route_retirement_fence_20261022.json'}
CODE=r'''
import base64,fcntl,hashlib,importlib.util,json,os,resource,sys,time
from pathlib import Path
d=json.load(sys.stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');job=root/'bootstrap/wc-fourcard-human-authority-r1-20261022'
assert not job.exists(),'Existing authority import must be restored; never replay'
assert not (root/'reports/gpu-budget-v2.json').exists(),'Existing real budget must not be overwritten'
assert not (root/'.sync/wc-bank24-fourcard-full-execution-r2-20261022/scout-GPU-dispatch-fence.json').exists()
assert not (root/'outputs/wc-scout-dev6-paired-native-full24-r1').exists()
resource.setrlimit(resource.RLIMIT_AS,(16*(1<<30),16*(1<<30)))
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
job.mkdir(mode=0o700)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name,b in d['files'].items():
 assert Path(name).name==name
 raw=base64.b64decode(b);assert hashlib.sha256(raw).hexdigest()==d['file_sha256'][name];(job/name).write_bytes(raw)
(job/'manifest.json').write_text(json.dumps(d['manifest'],indent=2)+'\n')
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
transition=module('bound_human_transition',job/'transition.py');budget=module('original_unchanged_budget',job/'original-budget.py')
base,pool,proof,human,route=[json.loads((job/n).read_text()) for n in ['base.json','pool.json','proof.json','human.json','route-exit.json']]
rebuilt=transition.build(base,human,route,proof['writer_epoch'],pool['events'][-1]['unix'],budget.BudgetPool.accounting)
assert rebuilt==pool;verified=transition.validate(base,pool,budget.BudgetPool.accounting)
assert proof['old_host_remote_fence_observed'] is False and proof['old_host_current_state']=='UNKNOWN'
assert proof['transition_module_sha256']==sha(job/'transition.py') and all(proof['checks'].values())
(root/'.sync').mkdir(exist_ok=True);(root/'reports').mkdir(exist_ok=True)
lockpath=root/'.sync/gpu-budget-v2.lock';assert not lockpath.is_symlink()
with lockpath.open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (root/'reports/gpu-budget-v2.json').exists()
 for path,src in [(root/proof['old_authoritative_snapshot_ref'],job/'base.json'),(root/'reports/wc_four_card_v2_unique_human_authority_proof_20261022.json',job/'proof.json')]:
  assert not path.exists()
  with path.open('xb') as f:f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
 budget.atomic_json(root/'reports/gpu-budget-v2.json',pool)
 assert sha(root/'reports/gpu-budget-v2.json')==d['file_sha256']['pool.json']
 assert sha(root/proof['old_authoritative_snapshot_ref'])==proof['old_authoritative_snapshot_sha256']
 actual=json.loads((root/'reports/gpu-budget-v2.json').read_text());transition.validate(base,actual,budget.BudgetPool.accounting)
 fcntl.flock(lock,fcntl.LOCK_UN)
with lockpath.open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
value=dict(status='FOUR_CARD_HUMAN_AUTHORITY_ACTUALLY_IMPORTED_AND_INDEPENDENTLY_READ_BACK',observed_unix=time.time(),job=str(job),
 source_revision=d['manifest']['source_revision'],manifest_sha256=sha(job/'manifest.json'),file_sha256={n:sha(job/n) for n in d['files']},
 writer_epoch=proof['writer_epoch'],pool_sha256=sha(root/'reports/gpu-budget-v2.json'),pool=actual,
 snapshot_sha256=sha(root/proof['old_authoritative_snapshot_ref']),proof_sha256=sha(job/'proof.json'),transition_audit=verified,
 own_budget_lock_released=True,old_host_remote_fence_observed=False,old_host_current_state='UNKNOWN',
 GPU_submissions=0,CUDA_initialized=False,Cosmos_weights_loaded=0,old_host_commands=0)
(job/'result.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 assert not a.output.exists()
 source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 files={n:Path(ref).read_bytes() for n,ref in FILES.items()}
 for n,ref in FILES.items():assert files[n]==subprocess.check_output(['git','show',source+':'+ref])
 files['original-budget.py']=subprocess.check_output(['git','show','2bd41dc8fa19f42353e03a7c78b7264b4b2695c6:src/wcomr/gpu_budget_pool_v2.py'])
 hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
 intent=Path('.sync/four-card-human-authority-r1-20261022-dispatch-intent.json');assert not intent.exists()
 write(intent,dict(started_unix=time.time(),source_revision=source,file_sha256=hashes))
 manifest=dict(source_revision=source,file_sha256=hashes,administrative_import_only=True,GPU_submissions=0)
 value=ssh(CODE,dict(manifest=manifest,files={n:base64.b64encode(b).decode() for n,b in files.items()},file_sha256=hashes),timeout=120)
 write(a.output,value)
 print(json.dumps(dict(output=str(a.output),status=value['status'],source_revision=value.get('source_revision'),pool_sha256=value.get('pool_sha256'),audit=value.get('transition_audit'))))

if __name__=='__main__':main()
