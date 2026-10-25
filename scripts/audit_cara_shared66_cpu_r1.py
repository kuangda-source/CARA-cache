#!/usr/bin/env python3
"""Independent CPU combination acceptance, never permission or quality evidence."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.shared66_card import quote_audit,read,MANIFEST

def accept(v):
 c=v['container'];L=v['launch'];reg=v['registration'];p=v['proof']['data']
 def need(condition,message):
  if not condition:raise ValueError(message)
 need(not c['state']['Running'] and c['state']['ExitCode']==0 and not c['state']['OOMKilled'],'Original CPU exit0 required')
 need(c['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d' and c['readonly_root'] and not c['devices'] and not c['device_requests'] and c['nano_cpus']==10**9 and c['memory_bytes']==4*2**30,'Bounded GPU-hidden CPU image required')
 need(reg['namespace']=='CARA_SHARED66_COMBINATION_R1' and reg['source_revision']==L['source_revision']==p['source_revision'] and reg['stage']==L['stage'],'Original source/stage binding')
 need(hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()==L['registration_sha256']==p['registration_sha256'],'Registration bytes changed')
 need(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'Payload/runtime changed')
 need(hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()==v['proof']['sha256'],'Proof bytes changed')
 need(p['status']=='SHARED66_COLLECTION_RELEASE_SCORE_TERMINAL_COMBINATION_CPU_PASS','Full CPU proof required')
 need(not any(p[k] for k in ('CUDA_initialized','Cosmos_weights_loaded','GPU_submissions','authoritative_ledger_written','independent_quality_models_loaded','quality_resource_CPU_accepted')),'CPU evidence boundary changed')
 need(p['reused_entry']['production_entry_CPU_accepted'] and all(reg['payload_sha256'][n]==h for n,h in p['unchanged_entry_SHA'].items()) and len(p['unchanged_entry_SHA'])==5,'Same accepted request closure required')
 expected=dict(paths=66,controls=6,requests_serialized=66,score_pairs=48,score_frames=4464,quality_videos=52,quality_positions=156,synthetic_endpoints_and_scores=True,score_resume_without_GPU_replay=True,quality_resume_without_GPU_replay=True,pre_release_score_refused=True,same_slot_replay_refused=True)
 if p['collection'].get('original_scoring_failure_receipts_retained'):expected['original_scoring_failure_receipts_retained']=True
 need(p['collection']==expected,'Full registered66 combination required')
 need(p['full_video_metric']['real_LPIPS93'] and not p['full_video_metric']['Cosmos_generated_video'],'Actual93 frame LPIPS callback required')
 need(p['terminal_tests']>=34 and len(p['lifecycle']['checks']) in (6,9) and all(x['status']=='PASS' and x['actual_sudo_calls']==x['actual_nvidia_smi_calls']==x['GPU_submissions']==0 for x in p['lifecycle']['checks']),'Actual supervisor/guardian CPU scenarios required')
 need(p['storage_lifecycle']['actual_tmpfs_ENOSPC'] and len(p['storage_lifecycle']['checks'])==6 and all(x['status']=='PASS' for x in p['storage_lifecycle']['checks']),'Actual ENOSPC/storage scenarios required')
 need(set(p['historical_originals']['originals'])=={'S26_C','SHARED26_C','NATIVE35'} and p['historical_originals']['read_only'],'Historical originals must be actually decoded')
 need(p['quote']==quote_audit(read(ROOT/MANIFEST)),'Complete quote differs')
 if 'reused_collection_original' in p:
  reuse=p['reused_collection_original'];name='reports/cara_shared_CAL66_combination_CPU_terminal_r1_20261025.json';raw=(ROOT/name).read_bytes();old=json.loads(raw)
  need(reg['payload_sha256'][name]==reuse['capture_sha256']==hashlib.sha256(raw).hexdigest(),'Reused collection capture changed')
  accept(old)
  need(reuse['proof_sha256']==old['proof']['sha256'] and reuse['new66_collection_runs']==0 and all(reg['payload_sha256'][n]==h==old['registration']['payload_sha256'][n] for n,h in reuse['unchanged_source_SHA'].items()),'Reused collection closure changed')
 return dict(status='CAL66_FULL_COMBINATION_CPU_ACCEPTED_NOT_GPU',source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=v['proof']['sha256'],
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,storage_ENOSPC_lifecycle_CPU_accepted=True,
  original_scoring_failure_receipts_retained=p['collection'].get('original_scoring_failure_receipts_retained',False),
  post_CPU_resource_limits_verified=len(p['lifecycle']['checks'])==9,
  execution_source_sha256={n:h for n,h in reg['payload_sha256'].items() if n.startswith(('src/','scripts/','tests/'))},registered_paths=66,LPIPS_pairs=48,LPIPS_frames=4464,independent_quality_positions=156,
  real_LPIPS93=True,independent_quality_models_CPU_accepted=False,hardware_exclusivity_verified=False,GPU_dispatch_ready=False,
  pending=['independent_quality_model_resources_CPU','GPU_permission','fresh_exclusive_storage_ledger_admission'],
  forecast_GPUh=p['quote']['forecast_GPUh'],proposed_limit_GPUh=8.0,cumulative_cap_GPUh=226,GPU_submissions=0,ledger_written=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps(v))
if __name__=='__main__':main()
