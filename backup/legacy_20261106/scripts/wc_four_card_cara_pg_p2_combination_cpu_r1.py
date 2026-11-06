#!/usr/bin/env python3
"""Bounded immutable CPU composition, independent of the running price stage."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path
from wc_four_card_cara_pg_cpu_r1 import DEPLOY,CAPTURE,BASE
from wc_four_card_policy_assets_r1 import ssh,write,read,REPO
from four_card_policy_assets_port_r1 import ROOT
sys.path.insert(0,str(REPO/'src'))
from wcomr.immutable_stage_payload_r1 import local_python_closure
ENTRY=['scripts/check_cara_pg_p2_combination_cpu_r1.py','scripts/check_cara_pg_p2_production_cpu_r1.py',
 'scripts/wc_cara_pg_p2_worker_r1.py','scripts/wc_cara_pg_p2_host_guardian_r1.py',
 'tests/check_cara_pg_p2_lifecycle_cpu_r1.py','tests/test_cara_pg_p2_combination_r1.py',
 'tests/check_cara_pg_p2_sampling_cpu_r1.py','tests/check_cara_pg_production_sampling_cpu_r1.py',
 'tests/test_cara_pg_p2_production_batch.py','scripts/check_wc_policy_price_refresh_cpu_r1.py',
 'tests/test_cara_pg_p2_terminal_r1.py','tests/test_cara_pg_p1_combination_r1.py','tests/test_policy_price_terminal_r1.py']
EXTRA=['plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json','manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json',
 'manifests/wc_policy_price_refresh_full1624_whole_quote_r1_20261023.json','reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json',
 'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json','reports/dataset_source_group_audit_20260930.json']
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['deploy','capture']);p.add_argument('--stage-name');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Preserve original composition receipt')
 if a.command=='capture':v=ssh(CAPTURE.replace("stage/'PG-production-CPU.json'","stage/'PG-P2-combination-CPU.json'"),read(a.launch_ref))
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
  code=DEPLOY.replace('cara-pg-p1-CPU-','cara-pg-p2-CPU-').replace('CARA_PG_P1_CPU_R1','CARA_PG_P2_CPU_R1').replace('check_cara_pg_p1_production_cpu_r1.py','check_cara_pg_p2_combination_cpu_r1.py').replace("str(stage/'PG-production-CPU.json')","str(stage/'PG-P2-combination-CPU.json')")
  v=ssh(code,dict(root=ROOT,base=BASE,base_registration_sha256=old['registration_sha256'],stage_name=a.stage_name,revision=revision,files=files,hashes=hashes))
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','container','resource_admission')}))
if __name__=='__main__':main()
