#!/usr/bin/env python3
"""Run the actual pinned Block/GPT2 MLP CPU controls, with CUDA forbidden."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('stage','runtime','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sys.path.insert(0,str(a.stage/'src'))
 os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 import torch
 assert not torch.cuda.is_initialized()
 def forbidden(*a,**kw):raise RuntimeError('P0 CPU forbids CUDA, downloads and external weights')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.load=forbidden
 reg=json.loads((a.stage/'registration.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert {n:sha(a.stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
 assert {n:sha(a.runtime/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
 spec=importlib.util.spec_from_file_location('p0_actual_Block_CPU',a.stage/'tests/check_partial_mlp_cpu.py')
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 state_spec=importlib.util.spec_from_file_location('p0_state_CPU',a.stage/'tests/check_partial_mlp_state_cpu.py')
 state_module=importlib.util.module_from_spec(state_spec);sys.modules[state_spec.name]=state_module;state_spec.loader.exec_module(state_module)
 start=time.perf_counter()
 v=m.run(a.runtime,state_control=state_module.run_control);assert v['status']=='P0_PINNED_BLOCK_GATHERED_MLP_CPU_PASS_NOT_COSMOS_OR_SPEED'
 assert len(v['complete_pair_checks'])==6 and len(v['cold_and_incompatible_full_safe_fallback_checks'])==2
 assert len(v['refusals'])==4 and v['second_branch_failure_complete_cache_rollback_and_poison_verified']
 extra=v['additional_projection_state_control']
 assert extra['status']=='P0_ADDITIONAL_PHYSICAL_INVENTORY_ROUNDTRIP_CPU_PASS'
 assert extra['complete_successful_counterfactual_pairs']==2 and len(extra['refusals'])==4
 assert extra['failed_second_branch_score_only_pair_retained'] and extra['all_projection_values_and_age_source_context_D_history_physically_restored']
 assert not v['CUDA_initialized'] and v['GPU_submissions']==0
 v.update(planned_scope=reg['CPU_scope'],payload_sha256=reg['payload_sha256'],CPU_wall_seconds=time.perf_counter()-start)
 assert not a.output.exists();a.output.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:v[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))

if __name__=='__main__':main()
