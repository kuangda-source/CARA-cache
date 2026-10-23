#!/usr/bin/env python3
"""Bind P2 diagnostic inputs only after independently rechecking full P1/CPU."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.policy_generator_r1.continuation_preparation import require,history_matrix
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.policy_generator_r1.production_terminal import accept as accept_p1,record
from audit_cara_pg_p2_production_cpu_r1 import accept as accept_cpu
from audit_cara_pg_p2_combination_cpu_r1 import accept as accept_combination


def checked(capture,acceptance,fn):
 raw=capture.read_bytes();saved=json.loads(acceptance.read_bytes())
 require(saved['capture_sha256']==hashlib.sha256(raw).hexdigest(),'Independent acceptance does not bind original capture')
 original=json.loads(raw);actual=fn(original)
 require(all(saved.get(k)==v for k,v in actual.items()),'Independent acceptance changed under recomputation')
 return original,actual


def roles_from_batch(batch):
 require(batch['status']=='PG_P1_CAL_SELECTION_COMPLETE' and batch['selected_policy'] is not None,'P1 selected policy required')
 controls=set(batch['simple_controls'])
 strong=next((r for r in batch['selection']['order'] if r['fingerprint'] in controls),None)
 require(strong is not None,'No feasible simple SELECT control; do not choose from diagnostic results')
 policies={r['proposal']['policy']['fingerprint']:r['proposal']['policy'] for r in batch['candidates']}
 return dict(CARA=batch['selected_policy'],SIMPLE=policies[strong['fingerprint']])


def main():
 p=argparse.ArgumentParser()
 for k in ('p1-capture','p1-acceptance','cpu-capture','cpu-acceptance','combination-capture','combination-acceptance','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();require(not a.output.exists(),'Preserve original handoff')
 p1,acceptance=checked(a.p1_capture,a.p1_acceptance,accept_p1)
 require(acceptance['PG_P2_input_ready'] is True,'P1 cannot release P2 input yet')
 cpu,ca=checked(a.cpu_capture,a.cpu_acceptance,accept_cpu)
 combo,co=checked(a.combination_capture,a.combination_acceptance,accept_combination)
 require(co['production_CPU_accepted'] is True and co['full_GPU_lifecycle_CPU_accepted'] is True,'Complete P2 composition CPU required')
 require(ca['production_entry_CPU_accepted'] is True,'P2 actual entry CPU required')
 for name,h in cpu['registration']['payload_sha256'].items():
  if name.startswith('src/wcomr/policy_generator_r1/p2_'):
   require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'Current P2 production source differs from accepted CPU')
 consumer=record(p1,'consumer');batch=record(p1,'runner')['batch'];roles=roles_from_batch(batch)
 fields=dict(consumer['profile']);fields['protected_dense']=tuple(fields['protected_dense']);fields['alpha_candidates']=tuple(fields['alpha_candidates'])
 matrix=history_matrix(Profile(**fields),roles,consumer['CAL_FIT_members'][:2])
 references=[]
 for slot in matrix['rows']:
  matches=[r for r in batch['rows'] if r['split']=='CAL_FIT' and r.get('fingerprint')==slot['policy_fingerprint'] and r.get('member')==slot['member'] and r.get('seed')==slot['seed'] and r['status']=='COMPLETE']
  require(len(matches)==1,'History needs its exact accepted own-policy P1 reference')
  row=matches[0]
  references.append(dict(member=slot['member'],seed=slot['seed'],policy_fingerprint=slot['policy_fingerprint'],section=slot['section'],
      P1_request_sha256=row['request_artifact']['sha256'],video_artifact=row['video_artifact'],final_latent_artifact=row['final_latent_artifact']))
 output=dict(status='P2_ORIGINAL_P1_POLICY_AND_NATIVE_HISTORY_CPU_BOUND_NOT_DISPATCH',profile=consumer['profile'],roles=roles,
  history_matrix=matrix,history_OFF_reference_bindings=references,Native_schedules=ca['schedule_rows'],CAL_FIT_members=consumer['CAL_FIT_members'],
  source_bindings=[dict(ref=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in
   (a.p1_capture,a.p1_acceptance,a.cpu_capture,a.cpu_acceptance,a.combination_capture,a.combination_acceptance)],
  P1_selected_policy_frozen=True,new_DEV_selected=False,whole_P2_quote_rebinding_required=True,
  whole_P2_GPU_lifecycle_CPU_pending=False,final_whole_card_binding_pending=True,real_quality_models_CPU_pending=True,
  final_budget_determined=False,GPU_dispatch_ready=False,GPU_submissions=0)
 with a.output.open('x') as f:json.dump(output,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=output['status'],history_paths=matrix['physical_paths'],GPU_dispatch_ready=False)))
if __name__=='__main__':main()
