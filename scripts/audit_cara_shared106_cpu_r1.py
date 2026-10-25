#!/usr/bin/env python3
"""Independent CPU combination acceptance, never permission or quality evidence."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.shared106_card import quote_audit,read,MANIFEST

def accept(v):
 c=v['container'];L=v['launch'];reg=v['registration'];p=v['proof']['data']
 def need(condition,message):
  if not condition:raise ValueError(message)
 need(not c['state']['Running'] and c['state']['ExitCode']==0 and not c['state']['OOMKilled'],'Original CPU exit0 required')
 need(c['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d' and c['readonly_root'] and not c['devices'] and not c['device_requests'] and c['nano_cpus']==10**9 and c['memory_bytes']==4*2**30,'Bounded GPU-hidden CPU image required')
 need(reg['namespace']=='CARA_SHARED106_COMBINATION_R1' and reg['source_revision']==L['source_revision']==p['source_revision'] and reg['stage']==L['stage'],'Original source/stage binding')
 need(hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()==L['registration_sha256']==p['registration_sha256'],'Registration bytes changed')
 need(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Payload/runtime changed')
 need(hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()==v['proof']['sha256'],'Proof bytes changed')
 need(p['status']=='SHARED106_COLLECTION_RELEASE_SCORE_TERMINAL_COMBINATION_CPU_PASS','Full CPU proof required')
 need(not any(p[k] for k in ('CUDA_initialized','Cosmos_weights_loaded','GPU_submissions','authoritative_ledger_written','independent_quality_models_loaded','quality_resource_CPU_accepted')),'CPU evidence boundary changed')
 need(p['reused_entry']['production_entry_CPU_accepted'] and all(reg['payload_sha256'][n]==h for n,h in p['unchanged_entry_SHA'].items()) and len(p['unchanged_entry_SHA'])==5,'Same accepted request closure required')
 expected=dict(paths=106,controls=22,requests_serialized=106,score_pairs=72,score_frames=6696,quality_videos=76,quality_positions=228,synthetic_endpoints_and_scores=True,score_resume_without_GPU_replay=True,quality_resume_without_GPU_replay=True,pre_release_score_refused=True,same_slot_replay_refused=True)
 need(p['collection']==expected,'Full registered106 combination required')
 need(p['full_video_metric']['real_LPIPS93'] and not p['full_video_metric']['Cosmos_generated_video'],'Actual93 frame LPIPS callback required')
 need(p['terminal_tests']>=34 and len(p['lifecycle']['checks'])==6 and all(x['status']=='PASS' and x['actual_sudo_calls']==x['actual_nvidia_smi_calls']==x['GPU_submissions']==0 for x in p['lifecycle']['checks']),'Actual supervisor/guardian CPU scenarios required')
 need(p['storage_lifecycle']['actual_tmpfs_ENOSPC'] and len(p['storage_lifecycle']['checks'])==6 and all(x['status']=='PASS' for x in p['storage_lifecycle']['checks']),'Actual ENOSPC/storage scenarios required')
 need(p['quote']==quote_audit(read(ROOT/MANIFEST)),'Complete quote differs')
 return dict(status='CAL106_FULL_COMBINATION_CPU_ACCEPTED_NOT_GPU',source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=v['proof']['sha256'],
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,registered_paths=106,LPIPS_pairs=72,LPIPS_frames=6696,independent_quality_positions=228,
  real_LPIPS93=True,independent_quality_models_CPU_accepted=False,hardware_exclusivity_verified=False,GPU_dispatch_ready=False,
  pending=['independent_quality_model_resources_CPU','GPU_permission','fresh_exclusive_storage_ledger_admission'],
  forecast_GPUh=p['quote']['forecast_GPUh'],proposed_limit_GPUh=11.5,cumulative_cap_GPUh=226,GPU_submissions=0,ledger_written=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps(v))
if __name__=='__main__':main()
