#!/usr/bin/env python3
"""Independent R2 CPU identity/source/lifecycle acceptance, not GPU permission."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.shared66_card import RUN,VERSION,COUNTS,MANIFEST,read,execution_quote
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def accept(v):
 c=v['container'];L=v['launch'];reg=v['registration'];p=v['proof']['data']
 def need(x,msg):
  if not x:raise ValueError(msg)
 need(not c['state']['Running'] and c['state']['ExitCode']==0 and not c['state']['OOMKilled'],'CPU exit0 required')
 need(c['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d' and c['readonly_root'] and not c['devices'] and not c['device_requests'] and c['nano_cpus']==10**9 and c['memory_bytes']==4*2**30,'GPU-hidden bounded CPU required')
 need(reg['namespace']==VERSION and reg['source_revision']==L['source_revision']==p['source_revision'] and reg['stage']==L['stage'],'Exact R2 registration')
 need(hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()==L['registration_sha256']==p['registration_sha256'],'Registration SHA changed')
 need(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Payload/runtime changed')
 need(hashlib.sha256((json.dumps(p,indent=2)+'\n').encode()).hexdigest()==v['proof']['sha256'],'Proof SHA changed')
 need(p['status']=='CAL66_R2_IDENTITY_QUOTE_LIFECYCLE_CPU_COMPLETE' and p['run_id']==RUN and p['scope_counts']==COUNTS,'Wrong R2 complete scope')
 need(p['actual_registered_stage_validate'] and p['actual_runtime_class_SHA_preserved'],'Actual stage/class binding missing')
 need(p['repaired_entry']['frozen_request_chain_CPU_accepted'] and p['repaired_entry']['complete_CPU_paths']==60 and p['repaired_entry']['preload_validated_slots']==66,'Actual repaired request CPU missing')
 need(p['original_scientific_manifest_SHA']==sha(ROOT/MANIFEST) and p['execution_quote']==execution_quote(read(ROOT/MANIFEST)),'Original science/new quote mismatch')
 need(p['identity_adaptations']==['src/wcomr/policy_generator_r1/shared66_card.py','src/wcomr/policy_generator_r1/shared66_terminal.py'] and p['unchanged_execution_files']==142,'Uncovered execution change')
 need(p['terminal_tests']>=60 and len(p['lifecycle']['checks'])==10 and all(x['status']=='PASS' and x['actual_sudo_calls']==x['actual_nvidia_smi_calls']==x['GPU_submissions']==0 for x in p['lifecycle']['checks']),'R2 supervisor/guardian tests missing')
 need(p['storage_lifecycle']['actual_tmpfs_ENOSPC'] and len(p['storage_lifecycle']['checks'])==6 and all(x['status']=='PASS' for x in p['storage_lifecycle']['checks']),'R2 storage failure tests missing')
 need(p['real_quality_models_CPU_accepted'] and p['historical_bridge_and_score_CPU_reused'] and p['post_CPU_planning']['within_original_CPU_envelope'],'Release scoring resources missing')
 need(not any(p[k] for k in ('CUDA_initialized','GPU_submissions','authoritative_ledger_written')),'CPU boundary exceeded')
 return dict(status='CAL66_R2_SOURCE_BOUND_CPU_ACCEPTED_NOT_GPU',source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=v['proof']['sha256'],
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,storage_ENOSPC_lifecycle_CPU_accepted=True,independent_quality_models_CPU_accepted=True,
  execution_source_sha256=reg['payload_sha256'],quality_binding_sha256=p['quality_binding_sha256'],
  registered_paths=66,LPIPS_pairs=48,quality_positions=156,forecast_GPUh=p['execution_quote']['forecast_GPUh'],billed_limit_GPUh=8,cumulative_cap_GPUh=226,
  GPU_submissions=0,ledger_written=False,GPU_dispatch_ready=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 v=accept(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:v[k] for k in ('status','registered_paths','forecast_GPUh','GPU_dispatch_ready')}))
if __name__=='__main__':main()
