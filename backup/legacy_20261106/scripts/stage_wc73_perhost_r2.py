"""Rebind unused WC73 payload to explicit per-host concurrency; no GPU dispatch."""
import json,hashlib,base64,subprocess
from pathlib import Path
from cara_two_card_transport_r1 import four_ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import sys,json,base64,hashlib,shutil,time
from pathlib import Path
p=json.load(sys.stdin);r=Path('/data20t/gaokuangda/worldcache_workspace');old=Path(p['old_stage']);s=r/'.sync/cara-wc73-execution-ada-r2-20261027'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert not s.exists() and not any((d/'GPU-intent.json').exists() for d in (r/'.sync').glob('cara-wc73-execution-*')),'Recover original; no duplicate stages after intent'
reg=json.loads((old/'registration.json').read_text());assert sha(old/'registration.json')==p['old_registration_sha256'];s.mkdir()
for n,h in reg['payload_sha256'].items():
 assert sha(old/n)==h;f=s/n;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,f)
for n,b in p['patches'].items():
 f=s/n;f.write_bytes(base64.b64decode(b));assert sha(f)==p['patch_sha256'][n];reg['payload_sha256'][n]=p['patch_sha256'][n]
reg.update(source_revision=p['source_revision'],stage=str(s),base_source_revision=json.loads((old/'registration.json').read_text())['source_revision'],per_host_concurrency_increment=True)
(s/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
shutil.copyfile(old/'history104-storage.json',s/'history104-storage.json');(s/'execution-CPU-proof.json').write_text(json.dumps(p['CPU_proof'],indent=2)+'\n')
auth=json.loads((old/'pg-GPU-authorization.json').read_text());auth.update(source_revision=p['source_revision'],registration_sha256=sha(s/'registration.json'),CPU_proof_sha256=sha(s/'execution-CPU-proof.json'),one_owned_job_per_host_authorized=True,concurrency_user_quote=p['user_quote'])
(s/'pg-GPU-authorization.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
sys.path[:0]=[str(s/'src'),str(s/'scripts')]
from wcomr.wc73_execution_r1 import validate,Pool,admit_host,RUN
from wcomr.history104_storage_r2 import storage_for
from wcomr.wc73_exclusive_r1 import observe
from wcomr.gpu_budget_pool_v2 import DeviceLease
validate(r,s);storage=storage_for(s);check=storage.check();assert not any(storage.output.iterdir())
v=Pool(r).read();assert RUN not in v['jobs'] and v['available_gpu_hours']>=12;admit_host(v,'four_card')
with DeviceLease(r,auth['gpu_uuid']):pass
snap=observe(auth['gpu_uuid']);assert snap['compute_apps']==[] and snap['mps_processes']==[] and snap['compute_mode'] in ('Default','Exclusive_Process')
receipt=dict(status='WC73_PER_HOST_R2_ADMITTED_NOT_DISPATCHED',stage=str(s),source_revision=p['source_revision'],registration_sha256=sha(s/'registration.json'),authorization_sha256=sha(s/'pg-GPU-authorization.json'),CPU_proof_sha256=sha(s/'execution-CPU-proof.json'),gpu_uuid=auth['gpu_uuid'],launch_id=auth['launch_id'],observed_unix=time.time(),idle_snapshot=snap,storage_check=check,ledger={k:v[k] for k in ('cap_gpu_hours','used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},patch_sha256=p['patch_sha256'],GPU_submissions=0)
(s/'stage-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
'''
def main():
 old=json.loads((ROOT/'reports/cara_wc73_execution_stage_20261027.json').read_text());paths=['src/wcomr/wc73_execution_r1.py','scripts/wc_wc73_worker_r1.py'];raw={n:(ROOT/n).read_bytes() for n in paths};hashes={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()};refs={}
 for h in ('four_card','two_card'):
  f=ROOT/f'reports/cara_wc73_perhost_{h}_CPU_terminal_r6_20261027.json';x=json.loads(f.read_text());assert x['source_intact'] and x['container_state']['ExitCode']==0 and not x['container_state']['Running'] and not x['host_config']['DeviceRequests'] and x['proof']['passed'] and x['proof']['per_host_tests']==6
  assert all(x['proof']['source_sha256'][n]==v for n,v in hashes.items());refs[h]=dict(path=str(f.relative_to(ROOT)),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
 proof=dict(passed=True,prior_full_proof_sha256=old['CPU_proof_sha256'],per_host_CPU_refs=refs,patched_sources=hashes,science_and_timing_unchanged=True,GPU_submissions=0)
 quote='Ada 空闲就直接跑 WC73，允许两台服务器各运行一个独占任务，不用等 COMMON_LONG6 R2 结束。WC73 仍限 12 GPUh，A 验证不过就停，通过后冻结参数再跑 B，启动后告诉我预计完成时间。'
 data=dict(old_stage=old['stage'],old_registration_sha256=old['registration_sha256'],patches={n:base64.b64encode(b).decode() for n,b in raw.items()},patch_sha256=hashes,CPU_proof=proof,user_quote=quote,source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
 v=four_ssh(REMOTE,data,timeout=90);f=ROOT/'reports/cara_wc73_execution_stage_per_host_r2_20261027.json';assert not f.exists();f.write_text(json.dumps(v,indent=2)+'\n');print(v)
if __name__=='__main__':main()
