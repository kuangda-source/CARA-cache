#!/usr/bin/env python3
import argparse,copy,hashlib,json
from pathlib import Path
from audit_cara_pg_p1_production_cpu_r1 import accept as accept_entry

def accept(v):
 p=v['proof']['data'];reg=v['registration']
 if hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()!=v['proof']['sha256']:raise ValueError('Proof SHA changed')
 entry=copy.deepcopy(v);entry['proof']=dict(exists=True,data=p['entry'],sha256=p['entry_proof_sha256']);a=accept_entry(entry)
 if p['status']!='HISTORY104_FULL_COLLECTION_RELEASE_SCORE_TERMINAL_CPU_PASS' or p['source_revision']!=a['source_revision'] or p['registration_sha256']!=a['registration_sha256']:raise ValueError('Wrong combination identity')
 if any(p[k] for k in ('CUDA_initialized','Cosmos_weights_loaded','GPU_submissions','authoritative_ledger_written')):raise ValueError('CPU boundary exceeded')
 if not p['historical148_accepted']['production_entry_CPU_accepted'] or p['historical148_accepted']['complete_CPU_paths']!=148:raise ValueError('Historical entry acceptance missing')
 if not p['unchanged_historical_execution_SHA'] or any(reg['payload_sha256'][n]!=h for n,h in p['unchanged_historical_execution_SHA'].items()):raise ValueError('Historical accepted source changed')
 c=p['collection'];required=('complete72_score_schedule','score_failure_raw_retained','score_resume_no_GPU_replay','pre_release_score_refused','same_slot_replay_refused')
 if c['paths']!=104 or c['requests_serialized']!=104 or c['controls']!=15 or c['diagnostic_guided_artifacts']!=4 or not all(c[k] for k in required):raise ValueError('Whole collection/score composition missing')
 if not p['full_video_metric']['real_LPIPS93'] or p['full_video_metric']['identity_zero']!=0 or p['terminal_tests']<14:raise ValueError('Real complete scoring/terminal checks missing')
 storage=p.get('storage_lifecycle')
 if storage is not None:
  if storage['status']!='HISTORY104_STORAGE_REAL_ENOSPC_SUPERVISOR_CPU_PASS' or not storage['actual_tmpfs_ENOSPC'] or storage['GPU_submissions'] or storage['authoritative_ledger_written'] or len(storage['checks'])!=6 or any(c['status']!='PASS' for c in storage['checks']):raise ValueError('Storage ENOSPC lifecycle incomplete')
  if any(reg['payload_sha256'][n]!=h for n,h in storage['source_sha256'].items()):raise ValueError('Storage lifecycle source binding differs')
 life=p['lifecycle'];expected={'success','runner_failure','foreign_context','telemetry_failure_on_release','host_clean_restore','host_foreign_arrival_defer_restore'}
 if {c['scenario'] for c in life['checks']}!=expected or any(c['status']!='PASS' or c['GPU_submissions'] or c['actual_sudo_calls'] for c in life['checks']):raise ValueError('Full actual lifecycle missing')
 for field,name in [('production_supervisor_sha256','scripts/wc_cara_history104_worker_r1.py'),('production_host_guardian_sha256','scripts/wc_cara_history104_host_guardian_r1.py')]:
  if life[field]!=reg['payload_sha256'][name]:raise ValueError('Supervisor/guardian identity mismatch')
 result=dict(status='HISTORY104_PRODUCTION_COMBINATION_CPU_ACCEPTED_GPU_PENDING',source_revision=a['source_revision'],registration_sha256=a['registration_sha256'],proof_sha256=v['proof']['sha256'],production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,actual_paths104=True,actual_LPIPS93=True,historical148_reused_unchanged=True,execution_source_sha256={n:h for n,h in reg['payload_sha256'].items() if n.startswith(('src/','scripts/','tests/'))},GPU_dispatch_ready=False,GPU_submissions=0)
 if storage is not None:result['storage_ENOSPC_lifecycle_CPU_accepted']=True
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=accept(json.loads(a.capture.read_text()));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(v['status'])
