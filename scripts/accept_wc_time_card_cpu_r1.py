"""Independent saved-evidence review; no launch, reservation or server access."""
import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'plans/cara_wc_time_protocol_r1_20261027'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def accept():
 sources=['src/wcomr/wc_time_card_r1.py','src/wcomr/paper_latency_r1.py','src/wcomr/wc_time_protocol_p0.py','tests/check_wc_time_card_r1.py','plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json']
 control=['src/wcomr/wc_time_collection_r1.py','src/wcomr/wc_time_diagnostics_r1.py','tests/test_wc_time_lifecycle_r1.py']
 hosts={}
 for host in ('four_card','two_card'):
  n=f'reports/cara_wc_seven_{host}_CPU_terminal_r2_20261027.json';cap=read(n);p=cap['CPU_proof'];state=cap['container_state'];cfg=cap['host_config']
  assert not state['Running'] and state['ExitCode']==0 and cap['payload_intact'] and cap['runtime_intact'] and not cfg['DeviceRequests'] and cfg['NetworkMode']=='none'
  assert p['status']=='WC_SEVEN_ROLE_COMBINATION_CPU_PASS_NOT_GPU' and not p['CUDA_initialized'] and not p['model_weights_loaded']
  assert {x['flow'] for x in p['numeric']['checks']}=={True,False}
  for x in p['numeric']['checks']:assert len(x['roles'])==7 and x['registered_paths']==73 and x['extra_OFF_comparisons']==7 and x['true_native_allD_equal'] and x['all_seven_timing_OFF_ON_equal'] and x['all_seven_refusal_decode_writer_cleanup']
  assert all(p['payload_sha256'][f]==sha(f) for f in sources)
  ln=f'reports/cara_wc_lifecycle_{host}_CPU_terminal_r2_20261027.json';l=read(ln);lp=l['CPU_proof'];assert l['container_state']['ExitCode']==0 and not l['container_state']['Running'] and not l['host_config']['DeviceRequests']
  assert lp['status']=='WC_TIME_LIFECYCLE_CPU_PASS' and lp['tests']==4 and not lp['CUDA_initialized']
  assert all(lp['payload_sha256'][f]==sha(f) for f in control)
  sn=f'reports/cara_wc_time_score_{host}_CPU_r1_20261027.json';s=read(sn);assert s['exit_code']==0 and s['proof']['status']=='BOUND_ALEX_PIQ_REAL_WEIGHT_SYNTHETIC_CPU_PASS' and not s['proof']['CUDA_initialized']
  assert s['script_sha256']==sha('scripts/check_wc_time_score_cpu_r1.py')
  hosts[host]=dict(numerical_receipt=n,numerical_sha256=sha(n),lifecycle_receipt=ln,lifecycle_sha256=sha(ln),metric_receipt=sn,metric_sha256=sha(sn),complete_tiny_paths=160,registered_slot_paths=146,numerical_wall_seconds=p['ended_unix']-p['started_unix'],lifecycle_wall_seconds=lp['CPU_wall_seconds'],metric_wall_seconds=s['wall_seconds'],CUDA_initialized=False,GPU_submissions=0)
 quote=read('plans/cara_wc_time_protocol_r1_20261027/WHOLE_QUOTE.json')
 for h,v in quote['hosts'].items():
  assert len(v['positions'])==73 and sum(x['paths'] for x in v['phases'].values())==73
  assert all(x['forecast_GPUh']<x['proposed_hard_GPUh'] for x in v['phases'].values())
  assert v['forecast_complete_GPUh']<v['proposed_whole_hard_GPUh']==12
  assert sum(x['proposed_hard_GPUh'] for x in v['phases'].values())==12
 old=read('plans/cara_wc_time_protocol_p0_20261027/REFERENCE_SHA_INVENTORY.json');assert all(sha(p)==h for p,h in old['references'].items())
 return dict(status='SEVEN_ROLE_AND_LIFECYCLE_DUAL_CPU_ACCEPTED_NO_GPU',hosts=hosts,active_timing_implementation='wcomr.paper_latency_r1',P0_clock_archived_not_installed=True,source_sha256={p:sha(p) for p in sources+control},quote_sha256=sha('plans/cara_wc_time_protocol_r1_20261027/WHOLE_QUOTE.json'),old_protected_references_unchanged=True,GPU_submissions=0,real_GPU_equivalence_passed=False,GPU_execution_authorized=False,limitations=['Tiny CPU weights/attention/decode/mock writer; true pinned Native/Block/RF/WC/solver bodies','Real quality weights CPU synthetic availability; not new scientific scores','Host device/context and actual GPU execution are fresh admission obligations'])
if __name__=='__main__':
 r=accept();(OUT/'CPU_ACCEPTANCE.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
