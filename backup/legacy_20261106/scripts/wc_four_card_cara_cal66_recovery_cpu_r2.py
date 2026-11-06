#!/usr/bin/env python3
"""Bounded immutable historical/PG entry equivalence CPU; never dispatches GPUs."""
import argparse,base64,gzip,hashlib,json,subprocess,sys
from pathlib import Path
from wc_four_card_cara_pg_cpu_r1 import DEPLOY,CAPTURE,BASE
from wc_four_card_policy_assets_r1 import ssh,write,read,REPO
from four_card_policy_assets_port_r1 import ROOT
sys.path.insert(0,str(REPO/'src'))
from wcomr.immutable_stage_payload_r1 import local_python_closure
ENTRY=['scripts/check_cara_cal66_recovery_launch_cpu_r2.py','scripts/run_cara_shared66_r1.py',
 'scripts/wc_cara_shared66_worker_r1.py','scripts/wc_cara_shared66_host_guardian_r1.py','scripts/postprocess_cara_shared66_r1.py',
 'tests/check_cara_shared66_lifecycle_cpu_r1.py','tests/check_shared66_storage_cpu_r1.py',
 'tests/test_cara_shared66_combination_r1.py','tests/test_cara_pg_p2_quality_binding_r1.py','tests/test_policy_price_terminal_r1.py',
 'scripts/audit_cara_cal66_entry_cpu_r2.py']
EXTRA=['reports/cara_history104_R2_terminal_20261024_2315.json','manifests/cara_shared_CAL66_scope_quote_r1_20261025.json','reports/cara_CAL66_frozen_entry_CPU_progress_r3_20261025_2030.json','reports/cara_CAL66_frozen_recovery_preparation_accepted_r2_20261025.json','reports/cara_CAL66_complete_CPU_preparation_and_quote_20261025.json','reports/cara_CAL66_quality_binding_20261025.json','manifests/cara_CAL66_full_recovery_quote_r2_20261025.json']
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['deploy','capture']);p.add_argument('--stage-name');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Preserve original CPU receipt')
 if a.command=='capture':
  code=CAPTURE.replace("stage/'PG-production-CPU.json'","stage/'shared66-recovery-CPU.json'")
  code=code.replace('print(json.dumps(out))',"print(json.dumps(dict(compressed_original=__import__('base64').b64encode(__import__('gzip').compress(json.dumps(out).encode())).decode())))")
  wire=ssh(code,read(a.launch_ref))
  v=json.loads(gzip.decompress(base64.b64decode(wire['compressed_original']))) if 'compressed_original' in wire else wire
 else:
  revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
  names=set(local_python_closure(REPO,ENTRY))|set(EXTRA)|{str(p.relative_to(REPO)) for p in (REPO/'src/wcomr/policy_generator_r1').glob('*.py')}
  # Keep the already accepted SM89 budget port in the registered base;
  # the repository's historical SM86 file is not a replacement for it.
  names.discard('src/wcomr/gpu_budget_pool_v2.py')
  files={};hashes={}
  for n in sorted(names):
   raw=subprocess.check_output(['git','show',revision+':'+n],cwd=REPO);assert raw==(REPO/n).read_bytes(),'Commit exact PG composition source first'
   files[n]=base64.b64encode(raw).decode();hashes[n]=hashlib.sha256(raw).hexdigest()
  old=read(REPO/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json')
  code=DEPLOY.replace('cara-pg-p1-CPU-','cara-shared66-recovery-CPU-').replace('CARA_PG_P1_CPU_R1','CARA_SHARED66_RECOVERY_R2').replace('check_cara_pg_p1_production_cpu_r1.py','check_cara_cal66_recovery_launch_cpu_r2.py').replace("str(stage/'PG-production-CPU.json')","str(stage/'shared66-recovery-CPU.json')")
  code=code.replace("command[command.index('--memory')+1]='4g'","command[0:0]=[];command[command.index('--entrypoint'):command.index('--entrypoint')]=['--tmpfs','/fault:rw,size=64m,mode=1777','--tmpfs','/fixture:rw,size=256m,mode=1777'];command[command.index('--memory')+1]='4g'")
  setup="""sys.path.insert(0,str(stage/'src'))
from wcomr.policy_generator_r1.shared66_card import RUN,VERSION,COUNTS,MANIFEST,read,execution_quote
card=read(stage/MANIFEST);quote=execution_quote(card)
config=dict(version=VERSION,run_id=RUN,scope_counts=COUNTS,matrix=card['matrix'],forecast_complete_GPUh=quote['forecast_GPUh'],billed_limit_GPUh=8.0,storage_contract_required=True,thermal_telemetry_required=True)
for name,value in [('pg-config.json',config),('pg-whole-quote.json',quote)]:
 (stage/name).write_text(json.dumps(value,indent=2)+chr(10));names.add(name)
"""
  code=code.replace("new=dict(namespace=",setup+"new=dict(namespace=")
  code=code.replace("runtime_source_sha256=reg['runtime_source_sha256']","runtime_source_sha256={**reg['runtime_source_sha256'],'cosmos_predict2/config.py':sha(root/'runtime/cosmos_predict2/config.py')}")
  v=ssh(code,dict(root=ROOT,base=BASE,base_registration_sha256=old['registration_sha256'],stage_name=a.stage_name,revision=revision,files=files,hashes=hashes))
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','container','resource_admission')}))
if __name__=='__main__':main()
