"""Offline acceptance of the sole Euler35 Linux CPU terminal; no replay."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_euler35_sampler_cpu_r1 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return hashlib.sha256((json.dumps(v,indent=2)+'\n').encode()).hexdigest()

def accept():
 launch='reports/cara_euler35_sampler_Linux_CPU_launch_r1_20261101.json'
 capture='reports/cara_euler35_sampler_Linux_CPU_capture_r1_20261101.json'
 l,c=[json.loads((ROOT/p).read_text()) for p in (launch,capture)]
 assert l['exit_code']==c['exit_code']==0
 start=l['result'];cap=c['result'];reg=cap['registration'];proof=cap['CPU_proof'];state=cap['container_state']
 assert cap['launch']==start and Path(start['stage']).name==STAGE and start['container']==STAGE+'-cpu'
 assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0 and not state['Running'] and not state['OOMKilled']
 assert cap['registration_sha256']==encoded(reg)==start['registration_sha256']==proof['registration_sha256']
 assert cap['CPU_proof_sha256']==encoded(proof)
 base=json.loads((ROOT/BASE_CAPTURE).read_text())['result'];accepted_base=json.loads((ROOT/BASE_ACCEPTED).read_text())
 assert accepted_base['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted_base['total_controls_passed']==113
 revision=l['source_revision'];full=subprocess.check_output(['git','rev-parse',revision+'^{commit}'],cwd=ROOT,text=True).strip()
 overlay={p:hashlib.sha256(subprocess.check_output(['git','show',full+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
 assert reg['payload_sha256']==proof['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}
 assert all(sha(ROOT/p)==h for p,h in overlay.items())
 assert reg['runtime_source_sha256']==proof['runtime_source_sha256']==base['registration']['runtime_source_sha256']
 assert reg['base_registration_sha256']==base['registration_sha256'] and reg['parent_git_revision']==proof['source_revision']==c['source_revision']==revision
 assert cap['payload_intact'] and cap['runtime_intact'] and cap['host_config']==reg['expected_host_config']==LIMITS
 assert proof['actual_CPU_affinity']==[26] and proof['tests_run']==5 and proof['status']=='EULER35_SAMPLER_LINUX_TINY_CPU_PASS_NOT_GPU'
 assert start['started_unix']<=proof['started_unix']<proof['ended_unix']<=proof['started_unix']+300
 assert not any(proof[k] for k in ('actual_GPU_or_Docker_GPU_executed','model_weights_loaded','old_experiments_rerun','GPU_submissions','ledger_written'))
 actual=proof['actual'];rows=actual['checks']
 assert actual['status']=='EULER35_PINNED_FULL_PIPELINE_TINY_CPU_PASS_NOT_GPU'
 assert len(rows)==2 and [r['flow'] for r in rows]==[False,True]
 assert not actual['CUDA_initialized'] and not actual['cuda_initialized'] and not actual['real_weights_loaded'] and not actual['real_encoded_video']
 for row in rows:
  assert row['complete_paths']==4 and row['updates_per_path']==35 and row['CFG_calls_per_path']==70
  assert row['Native_allD_all70_branch_outputs_all35_latents_final_latent_RGB_RNG_equal'] and row['timed_untimed_allD_equal']
  assert row['WC_counters_before']==list(range(70)) and row['WC_reset_after_call70']
  assert row['ATS_coefficient']==4 and row['ATS_horizon_decoupled'] and row['scheduler_restored_on_success_and_failure']
 assert (proof['complete_tiny_paths'],proof['total_updates'],proof['total_CFG_calls'])==(8,280,560)
 return dict(status='EULER35_ORIGINAL_LINUX_FULL_TINY_CPU_ACCEPTED_NOT_GPU',source_revision=full,
  original_recorded_revision=revision,launch=start,container_state=state,host_config=LIMITS,
  launch_ref=launch,launch_sha256=sha(ROOT/launch),capture_ref=capture,capture_sha256=sha(ROOT/capture),
  registration_sha256=cap['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],affected_source_sha256=overlay,
  unit_controls=5,complete_tiny_paths=8,updates_per_path=35,CFG_calls_per_path=70,total_updates=280,total_CFG_calls=560,
  wall_seconds=proof['ended_unix']-proof['started_unix'],Native_allD_step_latent_RGB_RNG_equal=True,
  WC_reset_after_call70=True,ATS_coefficient=4,actual_Linux_CPU_accepted=True,
  real_weights_loaded=False,real_encoded_video=False,real_GPU_parity=False,scientific_method_frozen=False,
  GPU_submissions=0,ledger_written=False,old_experiments_rerun=False,acceptor_sha256=sha(__file__))

def main():
 result=accept();path=ROOT/'reports/cara_euler35_sampler_Linux_CPU_accepted_r1_20261101.json'
 with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ('status','complete_tiny_paths','wall_seconds')}))
if __name__=='__main__':main()
