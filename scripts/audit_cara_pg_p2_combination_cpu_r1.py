#!/usr/bin/env python3
"""Accept the original complete composition CPU receipt, not GPU results."""
import argparse,copy,hashlib,json
from pathlib import Path
from audit_cara_pg_p2_production_cpu_r1 import accept as accept_entry

def accept(v):
 p=v['proof']['data']
 if hashlib.sha256((json.dumps(v['registration'],indent=2)+'\n').encode()).hexdigest()!=v['launch']['registration_sha256']:raise ValueError('Original registration bytes differ')
 if hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()!=v['proof']['sha256']:raise ValueError('Original complete CPU proof bytes differ')
 entry=copy.deepcopy(v);entry['proof']=dict(exists=True,data=p['entry'],sha256=p['entry_proof_sha256'])
 accepted=accept_entry(entry)
 if p['status']!='PG_P2_FULL_ENTRY_SUPERVISION_SCORE_TERMINAL_COMBINATION_CPU_PASS' or p['source_revision']!=v['launch']['source_revision'] or p['registration_sha256']!=v['launch']['registration_sha256']:raise ValueError('Wrong original composition')
 if p['CUDA_initialized'] or p['Cosmos_weights_loaded'] or p['GPU_submissions'] or p['authoritative_ledger_written'] or p['active_P1_stage_modified']:raise ValueError('CPU isolation exceeded')
 life=p['lifecycle'];scenarios={c['scenario'] for c in life['checks']}
 if scenarios!={'success','runner_failure','foreign_context','telemetry_failure_on_release','host_clean_restore','host_foreign_arrival_defer_restore'} or any(c['status']!='PASS' or c['GPU_submissions'] or c['actual_sudo_calls'] for c in life['checks']):raise ValueError('Incomplete actual lifecycle CPU')
 reg=v['registration']
 for field,name in [('production_supervisor_sha256','scripts/wc_cara_pg_p2_worker_r1.py'),('production_host_guardian_sha256','scripts/wc_cara_pg_p2_host_guardian_r1.py')]:
  if life[field]!=reg['payload_sha256'][name]:raise ValueError('Tested supervisor/guardian source mismatch')
 metric=p['full_video_metric']
 if not metric['actual_accepted_LPIPS_CPU'] or not metric['all93_original432x768'] or metric['identity_zero']!=0. or metric['Cosmos_generated_video']:raise ValueError('Actual full CPU score protocol failed')
 if not all(metric.get(k) is True for k in ('actual_endpoint_callback_serialization','metric_failure_propagated_raw_retained','same_slot_replay_refused')):raise ValueError('Actual callback/error composition missing')
 if p['final_budget_determined'] or p['terminal_combination']['actual_five_quality_models_loaded']:raise ValueError('Pending boundary overclaimed')
 if not p['terminal_combination']['quality1600_schema_controls']:raise ValueError('Quality full denominator missing')
 if not p['terminal_combination']['passed'] or p['terminal_combination']['tests_run']<32 or not p['terminal_combination']['complete518_denominator']:raise ValueError('Incomplete independent terminal combination')
 return dict(status='PG_P2_COMPLETE_PRODUCTION_COMBINATION_CPU_ACCEPTED_P1_BINDING_AND_BUDGET_PENDING',source_revision=accepted['source_revision'],registration_sha256=accepted['registration_sha256'],
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,production_entry_CPU_accepted=True,proof_sha256=v['proof']['sha256'],
  execution_source_sha256={n:h for n,h in reg['payload_sha256'].items() if n.startswith(('src/','scripts/','tests/'))},
  actual_guardrail_sampler_controls=48,actual_lifecycle_cases=6,terminal_fault_checks=p['terminal_combination']['tests_run'],actual_all93_frame_LPIPS=True,
  final_budget_determined=False,final_P1_bindings_accepted=False,actual_five_quality_models_loaded=False,GPU_dispatch_ready=False,hardware_exclusive_support_in_new_card_verified=False,GPU_submissions=0,quality_or_speed_result=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:v[k] for k in ('status','production_CPU_accepted','full_GPU_lifecycle_CPU_accepted','GPU_dispatch_ready')}))
if __name__=='__main__':main()
