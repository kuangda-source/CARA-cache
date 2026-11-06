"""Independent whole six-slot CPU combination acceptance; never GPU admission."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/wcomr/policy_generator_r1/production_exclusive.py','tests/test_common_long_proc_race_r2.py','src/wcomr/common_long_card_r2.py','src/wcomr/common_long_collection_r1.py','src/wcomr/common_long_finance_r2.py','src/wcomr/common_long_terminal_r2.py','src/wcomr/scout_common_long_r1.py','src/wcomr/paper_latency_r1.py','scripts/run_cara_common_long6_r2.py','scripts/postprocess_cara_common_long6_r2.py','scripts/wc_common_long6_worker_r2.py','scripts/wc_common_long6_host_guardian_r2.py','scripts/capture_common_long6_terminal_r2.py','scripts/check_common_long_combination_cpu_r2.py','tests/check_common_long_combination_cpu_r2.py','tests/check_common_long_lifecycle_cpu_r2.py','tests/check_common_long_storage_cpu_r2.py','tests/test_common_long_terminal_r2.py']
def accept(v):
 c=v['container_state'];assert c['Status']=='exited' and c['ExitCode']==0 and not c['OOMKilled'] and not c['Running']
 h=v['host_config'];assert h['NanoCpus']==2*10**9 and h['Memory']==8*2**30 and not h['DeviceRequests'] and h['NetworkMode']=='none' and h['ReadonlyRootfs']
 assert v['payload_intact'] and v['runtime_intact'] and v['GPU_submissions']==0 and not v['ledger_written']
 p=v['CPU_proof'];reg=v['registration'];digest=lambda x:hashlib.sha256(x).hexdigest()
 assert digest((json.dumps(p,indent=2,allow_nan=False)+'\n').encode())==v['CPU_proof_sha256']
 assert digest((json.dumps(reg,indent=2)+'\n').encode())==v['registration_sha256']==p['registration_sha256']==v['launch']['registration_sha256']
 assert p['host']==reg['host']==v['launch']['host'] and p['status']=='COMMON_LONG_COMBINATION_CPU_PASS_NOT_GPU'
 assert not any(p[k] for k in ('CUDA_initialized','model_weights_loaded','GPU_submissions','ledger_written'))
 for n in SOURCES:assert digest((ROOT/n).read_bytes())==reg['payload_sha256'][n],n
 n=p['numeric'];assert n['actual_CPU_paths']==12 and n['selected_states']==24 and n['readout_positions']==168
 assert len(n['checks'])==2 and {x['flow'] for x in n['checks']}=={True,False}
 for x in n['checks']:
  assert x['status']=='PASS' and x['actual_CPU_paths']==6 and x['states']==12 and x['readout_positions']==84
  assert x['all_OFF_ON_controls'] and x['CPU_rescore_from_saved_tensors'] and x['source_bound_frozen_requests'] and x['corruption_cases_rejected']==2
 life=p['lifecycle'];assert len(life['checks'])==4 and all(x['status']=='PASS' and x['real_child_exited'] and x['original_lease_released'] for x in life['checks'])
 st=p['storage'];assert len(st['checks'])==6 and st['actual_tmpfs_ENOSPC'] and all(x['status']=='PASS' for x in st['checks'])
 assert p['terminal_tests']==2 and p['proc_race_tests']==5
 return dict(status='COMMON_LONG_COMBINATION_CPU_ACCEPTED_NOT_GPU',host=p['host'],source_sha256={n:reg['payload_sha256'][n] for n in SOURCES},
  complete_CPU_paths=12,CPU_scored_states=24,CPU_scored_readout_positions=168,real_child_lifecycle_cases=4,storage_fault_cases=6,
  terminal_financial_tests=2,terminal_mutations=12,CPU_proof_sha256=v['CPU_proof_sha256'],production_CPU_accepted=True,
  GPU_authorized=False,hardware_exclusivity_verified_this_turn=False,scientific_promotion=False,ledger_written=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();v=accept(json.loads(a.capture.read_text()));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest());a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ('status','host','complete_CPU_paths','CPU_scored_readout_positions')}))
