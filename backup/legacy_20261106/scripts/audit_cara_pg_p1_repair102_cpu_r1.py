#!/usr/bin/env python3
"""Independent bounded CPU entry acceptance; never authorizes GPU dispatch."""
import argparse,copy,hashlib,json
from pathlib import Path
from audit_cara_pg_p1_production_cpu_r1 import accept as entry_accept

def accept(capture):
 p=capture['proof']['data']
 if hashlib.sha256((json.dumps(p,indent=2,allow_nan=False)+'\n').encode()).hexdigest()!=capture['proof']['sha256']:raise ValueError('Proof bytes changed')
 original=copy.deepcopy(capture);original['proof']=dict(exists=True,data=p['entry'],sha256=p['entry_proof_sha256']);entry=entry_accept(original)
 if p['status']!='P1_REPAIR102_ENTRY_ADAPTIVE_SCORE_REPLAY_CPU_PASS' or p['source_revision']!=entry['source_revision'] or p['registration_sha256']!=entry['registration_sha256']:raise ValueError('Wrong repair source identity')
 if any(p[k] for k in ('CUDA_initialized','GPU_submissions','ledger_written','current112_modified','actual_COST112_accepted','GPU_dispatch_ready')):raise ValueError('CPU evidence boundary exceeded')
 a=p['adaptive'];m=p['real_metric'];r=a['independent_replay']
 if a['registered_positions']!=102 or not 0<a['executed_CPU_paths']<=102 or a['tests']<10 or not a['decision_tamper_rejected'] or not a['original_request_replay_rejected'] or not a['synthetic_COST112_gate']:raise ValueError('Incomplete adaptive controls')
 if r['registered_positions']!=102 or r['executed_paths']!=a['executed_CPU_paths'] or r['scored_pairs']!=a['score_pairs'] or r['queries']>8:raise ValueError('Replay denominator mismatch')
 if not m['all93frames'] or m['LPIPS']!=0 or m['identity']['version']!='0.1.4':raise ValueError('Actual full metric entry missing')
 return dict(status='P1_REPAIR102_PRODUCTION_ENTRY_CPU_ACCEPTED_GPU_BINDING_PENDING',source_revision=entry['source_revision'],registration_sha256=entry['registration_sha256'],proof_sha256=capture['proof']['sha256'],production_entry_CPU_accepted=True,
  actual_Cosmos_entry_paths=18,adaptive_registered_positions=102,adaptive_executed_CPU_paths=a['executed_CPU_paths'],actual_LPIPS93=True,independent_adaptive_replay=True,tests=a['tests'],
  actual_COST112_accepted=False,full_GPU_lifecycle_CPU_accepted=False,GPU_dispatch_ready=False,GPU_submissions=0,quality_or_speed_result=False,
  pending=['complete_COST112_independent_timing_acceptance','specific_full_quote_authorization','new_supervisor_capture_financial_terminal_combination','fresh_exposure_source_ledger_idle_GPU_storage_admission'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=accept(json.loads(a.capture.read_text()));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 with a.output.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(v['status'])
