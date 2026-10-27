"""Stage the authorized Ada envelope from accepted CPU payload; no GPU submission."""
import json,hashlib,base64,subprocess
from pathlib import Path
from cara_two_card_transport_r1 import four_ssh
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import sys,json,hashlib,base64,shutil,time,os,subprocess
from pathlib import Path
p=json.load(sys.stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');base=Path(p['base']);stage=root/'.sync/cara-wc73-execution-ada-r1-20261027';assert not stage.exists(),'Recover original stage, never replace'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
reg0=json.loads((base/'registration.json').read_text());assert all(sha(base/n)==h for n,h in reg0['payload_sha256'].items())
proof=json.loads((base/'CPU-proof.json').read_text());assert proof['passed'] and not proof['CUDA_initialized']
assert all(proof['payload_sha256'][n]==h for n,h in p['critical_sources'].items())
rootcpu=Path(p['runtime_base']);runtime=json.loads((rootcpu/'registration.json').read_text())['runtime_source_sha256'];assert all(sha(root/'runtime'/n)==h for n,h in runtime.items())
stage.mkdir(mode=0o700)
for n,h in p['payload_sha256'].items():
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True)
 if n in p['changed']:target.write_bytes(base64.b64decode(p['changed'][n]))
 else:shutil.copyfile(base/n,target)
 assert sha(target)==h,n
reg=dict(namespace='WC73_AUTHORIZED_EXECUTION_INCREMENT',host='four_card',stage=str(stage),source_revision=p['revision'],phase='A',payload_sha256=p['payload_sha256'],runtime_source_sha256=runtime)
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
for n,v in [('history104-storage.json',p['storage']),('execution-CPU-proof.json',p['CPU_acceptance'])]:(stage/n).write_text(json.dumps(v,indent=2)+'\n')
card=json.loads((stage/'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml').read_text())
auth=dict(direct_user_authorization=True,user_quote=p['user_quote'],run_id='cara-wc73-r1-20261027',launch_id='cara-wc73-ada-original-r1-20261027',phase='A',host='four_card',gpu_uuid='GPU-19d4d100-f845-018d-ec30-def1553c01f5',whole_GPUh=12,source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),scope_sha256=card['scope_sha256'],forecast_GPUh=9.507472926825152,cpuset_cpus='24,25',CPU_score_cpuset='24-27')
(stage/'pg-GPU-authorization.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.wc73_execution_r1 import validate,Pool,hold
from wcomr.history104_storage_r2 import storage_for
from wcomr.gpu_budget_pool_v2 import DeviceLease
from wcomr.wc73_exclusive_r1 import observe
validate(root,stage);storage=storage_for(stage);storage.check()
with DeviceLease(root,auth['gpu_uuid']):pass
pool=Pool(root).read();assert pool['available_gpu_hours']>=12
active_owned=[k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and not hold(j)]
snap=observe(auth['gpu_uuid']);assert snap['compute_apps']==[] and snap['mps_processes']==[] and snap['compute_mode'] in ('Default','Exclusive_Process')
mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024;assert mem>=50*2**30
# Verify inherited helper identity as used by the accepted mode-owner implementation.
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';helpers={str(f):sha(f) for f in bank.glob('four_card_bank24*.py')}
receipt=dict(status='WC73_STAGED_AUTHORIZED_NOT_GPU_SUBMITTED',stage=str(stage),source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'pg-GPU-authorization.json'),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),gpu_uuid=auth['gpu_uuid'],launch_id=auth['launch_id'],observed_unix=time.time(),idle_snapshot=snap,storage_check=storage.check(),MemAvailable=mem,ledger={k:pool[k] for k in ('cap_gpu_hours','used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},inherited_host_helper_sha256=helpers,admission_blocking_owned_jobs=active_owned,GPU_submissions=0)
(stage/'stage-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
'''
def main():
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 caps={h:json.loads((ROOT/f'reports/cara_wc73_admission_{h}_CPU_terminal_r5_20261027.json').read_text()) for h in ('four_card','two_card')}
 for c in caps.values():assert c['proof']['passed'] and c['container_state']['ExitCode']==0 and not c['container_state']['Running'] and c['payload_intact'] and not c['host_config']['DeviceRequests']
 base=caps['four_card']['launch']['stage'];basehash=caps['four_card']['proof']['payload_sha256']
 names=set(basehash)
 # Keep this snapshot's payload exactly bound to current local sources, plus frozen science inputs.
 names.update(['configs/f1_setup.json','configs/wc_ra_comparison_production_r2_20261010.json','manifests/wc_h0_eval_mode_contract_20261003.json','reports/cara_CAL66_quality_binding_20261025.json'])
 for dirname in ('plans/cara_wc_time_protocol_p0_20261027','plans/cara_wc_time_protocol_r1_20261027'):
  names.update(str(p.relative_to(ROOT)) for p in (ROOT/dirname).iterdir() if p.is_file())
 raw={n:subprocess.check_output(['git','show','HEAD:'+n],cwd=ROOT) for n in sorted(names)};hashes={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}
 critical=[n for n in names if 'wc73' in n and (n.startswith('src/') or n.startswith('scripts/')) and 'prepare_' not in n and 'stage_' not in n]
 for cap in caps.values():assert all(cap['proof']['payload_sha256'][n]==hashes[n] for n in critical)
 proof=dict(passed=True,critical_sources={n:hashes[n] for n in critical},dual_host_receipts={h:dict(path=f'reports/cara_wc73_admission_{h}_CPU_terminal_r5_20261027.json',sha256=sha(ROOT/f'reports/cara_wc73_admission_{h}_CPU_terminal_r5_20261027.json')) for h in caps},original_seven_role_acceptance_sha256=sha(ROOT/'plans/cara_wc_time_protocol_r1_20261027/CPU_ACCEPTANCE.json'),GPU_submissions=0)
 (ROOT/'plans/cara_wc73_execution_r1_20261027/CPU_ACCEPTANCE.json').write_text(json.dumps(proof,indent=2)+'\n')
 data=dict(base=base,runtime_base='/data20t/gaokuangda/worldcache_workspace/.sync/cara-wc-seven-CPU-ada-r2-20261027',payload_sha256=hashes,changed={n:base64.b64encode(raw[n]).decode() for n in names if basehash.get(n)!=hashes[n]},critical_sources=proof['critical_sources'],CPU_acceptance=proof,revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),storage=json.loads((ROOT/'reports/cara_wc73_private_storage_20261027.json').read_text())['storage_contract'],user_quote=json.loads((ROOT/'plans/cara_wc73_execution_r1_20261027/AUTHORIZATION.json').read_text())['user_quote'])
 r=four_ssh(REMOTE,data,timeout=180);f=ROOT/'reports/cara_wc73_execution_stage_20261027.json';assert not f.exists();f.write_text(json.dumps(r,indent=2)+'\n');print({k:r[k] for k in ('status','stage','source_revision','ledger')})
if __name__=='__main__':main()
