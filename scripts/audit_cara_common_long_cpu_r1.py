"""Independent CPU terminal/source/denominator acceptance; no runtime dispatch."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AFFECTED=('src/wcomr/scout_common_long_r1.py','src/wcomr/scout_cfg_common_proposal_r1.py','src/wcomr/scout_parent_v22.py','src/wcomr/scout_readout_v22.py','src/wcomr/paper_latency_r1.py','tests/check_common_long_production_cpu_r1.py','scripts/check_cara_common_long_cpu_r1.py')
def accept(cap):
 c=cap['container_state'];assert c['Status']=='exited' and not c['Running'] and c['ExitCode']==0 and not c['OOMKilled']
 h=cap['host_config'];assert h['NanoCpus']==1_000_000_000 and h['Memory']==4*2**30 and not h['DeviceRequests'] and h['NetworkMode']=='none' and h['ReadonlyRootfs']
 assert cap['payload_intact'] and cap['runtime_intact'] and cap['GPU_submissions']==0 and not cap['ledger_written']
 p=cap['CPU_proof'];reg=cap['registration']
 sha=lambda b:hashlib.sha256(b).hexdigest()
 assert sha((json.dumps(p,indent=2,allow_nan=False)+'\n').encode())==cap['CPU_proof_sha256']
 assert sha((json.dumps(reg,indent=2)+'\n').encode())==cap['registration_sha256']
 assert p['registration_sha256']==cap['registration_sha256']==cap['launch']['registration_sha256']
 assert p['host']==reg['host']==cap['launch']['host'] and p['host'] in ('four_card','two_card')
 assert p['payload_sha256']==reg['payload_sha256'] and p['runtime_source_sha256']==reg['runtime_source_sha256']
 assert p['status']=='COMMON_LONG_AFFECTED_ENTRY_CPU_PASS_NOT_GPU'
 assert p['GPU_submissions']==0 and not any(p[k] for k in ('CUDA_initialized','model_weights_loaded','ledger_written','whole_method_card_accepted'))
 for n in AFFECTED:assert sha((ROOT/n).read_bytes())==reg['payload_sha256'][n],n
 n=p['numeric'];checks=n['checks']
 assert n['status']=='COMMON_LONG_REAL_SOURCE_CPU_PASS_NOT_GPU'
 assert n['actual_CPU_paths']==8 and n['selected_states']==24 and n['readout_positions']==168
 assert all(n[k] for k in ('short_A_exact','long_reference_exact','real_frozen_request','dual_clocks','teacher_free_candidate'))
 assert not n['candidate_free_running'] and not n['scientific_gate_evaluated']
 assert len(checks)==2 and {v['flow'] for v in checks}=={True,False}
 for v in checks:
  assert v['status']=='PASS' and v['actual_CPU_paths']==4 and v['time_mapping_rejections']==3
  assert len(v['requests'])==2 and len(v['failed_boundary_attempts'])==3
  assert not v['full_Cosmos_weights'] and not v['scientific_readout_gate_evaluated']
  for r in v['requests']:
   assert r['full36_OFF_ON_equal'] and r['final_latent_and_declared_CPU_RGB_equal'] and r['owner_released']
   assert r['selected_states']==6 and r['readout_positions']==42
  for f in v['failed_boundary_attempts']:assert f['original_error_preserved'] and f['adapter_uninstalled'] and f['no_replay']
 return dict(status='COMMON_LONG_AFFECTED_DUAL_HOST_CPU_ACCEPTED_NOT_GPU',host=p['host'],
  CPU_proof_sha256=cap['CPU_proof_sha256'],complete_CPU_paths=8,selected_states=24,
  readout_positions=168,affected_source_sha256={n:reg['payload_sha256'][n] for n in AFFECTED},
  real_GPU_latency_validated=False,whole_method_card_accepted=False,GPU_submissions=0,ledger_written=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 value=accept(json.loads(a.capture.read_text()));value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps({k:value[k] for k in ('status','host','complete_CPU_paths','real_GPU_latency_validated')}))
if __name__=='__main__':main()
