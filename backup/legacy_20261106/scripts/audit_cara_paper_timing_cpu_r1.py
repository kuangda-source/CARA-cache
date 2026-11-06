"""Independent CPU terminal/source/denominator acceptance; no runtime dispatch."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AFFECTED=('src/wcomr/paper_latency_r1.py','src/wcomr/method_experiment_timing_r1.py','scripts/check_cara_paper_timing_cpu_r1.py','tests/test_paper_latency_r1.py','tests/check_cara_paper_timing_cpu_r1.py')
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
 assert p['status']=='PAPER_TIMING_AFFECTED_ENTRY_CPU_PASS_NOT_GPU' and p['boundary_tests']==7
 assert p['GPU_submissions']==0 and not any(p[k] for k in ('CUDA_initialized','model_weights_loaded','ledger_written','whole_method_card_accepted'))
 for n in AFFECTED:assert sha((ROOT/n).read_bytes())==reg['payload_sha256'][n],n
 checks=p['numeric']['checks'];assert len(checks)==2 and {v['flow'] for v in checks}=={True,False}
 for v in checks:
  assert v['status']=='PASS' and v['host']==p['host'] and v['complete_paths']==9
  assert v['frozen_request_unchanged'] and v['original_full_clock_formula_preserved'] and v['restored_after_all_paths']
  assert v['request_schema']=='cosmos_predict2.config.InferenceArguments'
  assert v['pinned_sampler_pipeline_RF_WC'] and not v['actual_Cosmos_weights'] and not v['real_generated_video']
  assert v['event_order']==['prepare','loop_start','loop_end','decode','timed_end']
  assert v['failures']==['decode','writer','prepare','modified_live_sampler','nested_request']
  assert [r['role'] for r in v['roles']]==['NATIVE35','NATIVE26','S25_A_PHASE','SHARED25_C']
  for r in v['roles']:
   assert r['updates']==(27 if r['role']=='NATIVE26' else 36)
   assert r['all_guided_final_mock_RGB_equal'] and r['original_alpha_history_equal'] and r['clock_nested']
 return dict(status='PAPER_TIMING_AFFECTED_DUAL_HOST_ENTRY_CPU_ACCEPTED_NOT_GPU',host=p['host'],registration_sha256=p['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],affected_source_sha256={n:reg['payload_sha256'][n] for n in AFFECTED},complete_CPU_paths=18,flow_modes=2,roles=4,boundary_tests=7,original_full_clock_preserved=True,real_GPU_latency_validated=False,whole_method_card_accepted=False,GPU_submissions=0,ledger_written=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 value=accept(json.loads(a.capture.read_text()));value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps({k:value[k] for k in ('status','host','complete_CPU_paths','real_GPU_latency_validated')}))
if __name__=='__main__':main()
