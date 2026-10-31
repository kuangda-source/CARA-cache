"""Verify saved original CPU terminal evidence; no remote actions or scorer replay."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_endpoint7_interfaces_cpu_r1 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return hashlib.sha256((json.dumps(v,indent=2)+'\n').encode()).hexdigest()
def main():
 launch='reports/cara_endpoint7_interfaces_CPU_launch_r1_20261101.json'
 capture='reports/cara_endpoint7_interfaces_CPU_capture_r1_20261101.json'
 l,c=[json.loads((ROOT/p).read_text()) for p in (launch,capture)]
 assert l['exit_code']==c['exit_code']==0
 start=l['result'];cap=c['result'];reg=cap['registration'];proof=cap['CPU_proof'];state=cap['container_state']
 assert cap['launch']==start and Path(start['stage']).name==STAGE and start['container']==STAGE+'-cpu'
 assert state['Status']=='exited' and state['ExitCode']==0 and state['Pid']==0 and not state['Running'] and not state['OOMKilled']
 assert cap['registration_sha256']==encoded(reg)==start['registration_sha256']==proof['registration_sha256']
 assert cap['CPU_proof_sha256']==encoded(proof)
 base=json.loads((ROOT/BASE_CAPTURE).read_text())['result'];base_ok=json.loads((ROOT/BASE_ACCEPTED).read_text())
 assert base_ok['capture_sha256']==sha(ROOT/BASE_CAPTURE) and base_ok['total_controls_passed']==113
 revision=l['source_revision'];full=subprocess.check_output(['git','rev-parse',revision+'^{commit}'],cwd=ROOT,text=True).strip()
 overlay={p:hashlib.sha256(subprocess.check_output(['git','show',full+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
 assert reg['payload_sha256']==proof['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}
 assert all(sha(ROOT/p)==h for p,h in overlay.items())
 assert reg['runtime_source_sha256']==proof['runtime_source_sha256']==base['registration']['runtime_source_sha256']
 assert reg['base_registration_sha256']==base['registration_sha256'] and reg['parent_git_revision']==proof['source_revision']==c['source_revision']==revision
 assert cap['payload_intact'] and cap['runtime_intact'] and cap['host_config']==reg['expected_host_config']==LIMITS
 assert proof['actual_CPU_affinity']==[26] and proof['metadata_controls']==9
 assert proof['status']=='ENDPOINT7_ACTUAL_INTERFACE_AND_SCORE_CPU_COMPLETE_NOT_WHOLE_CARD'
 assert start['started_unix']<=proof['started_unix']<proof['ended_unix']<=proof['started_unix']+1200
 assert not any(proof[k] for k in ('original_numeric46_rerun','whole_GPU_card_accepted','active_experiment_outputs_read','GPU_submissions','ledger_written'))
 actual=proof['actual'];assert len(actual['cases'])==1
 case=actual['cases'][0];failure=actual['failed_case']
 assert case['new_pairs']==16 and case['logical_positions']==28 and case['original_rows_unchanged']==12
 assert case['frames_per_pair']==93 and case['temporal_pairs']==92 and case['no_replay']
 assert case['execution']['exit_code']==0 and case['execution']['original_observation']['original_live'] is False
 assert failure['complete_registered_pairs']==16 and failure['completed_rows']==1 and failure['no_replay']
 assert failure['status']=='FAILED_DENOMINATOR_RETAINED' and failure['execution']['exit_code']!=0
 assert failure['execution']['original_observation']['original_live'] is False
 assert actual['new_synthetic_pairs_scored']==16 and actual['failure_fixture_pairs_scored']==1 and actual['old_experiment_videos_rescored']==0
 report=dict(status='ENDPOINT7_ORIGINAL_INTERFACE_AND_SCORING_CPU_ACCEPTED_NOT_WHOLE_CARD',
  source_revision=full,original_recorded_revision=revision,launch=start,container_state=state,host_config=LIMITS,
  registration_sha256=cap['registration_sha256'],CPU_proof_sha256=cap['CPU_proof_sha256'],
  launch_ref=launch,launch_sha256=sha(ROOT/launch),capture_ref=capture,capture_sha256=sha(ROOT/capture),
  affected_source_sha256=overlay,metadata_controls=9,actual_complete_synthetic_pairs=16,
  full_frames_per_pair=93,logical_positions=28,original_rows_reused_unchanged=12,identity_controls=13,
  failure_registered_pairs=16,failure_completed_pairs=1,no_replay_controls=True,
  wall_seconds=proof['ended_unix']-proof['started_unix'],synthetic_lifecycle_and_historical_scores=True,
  original_numeric46_rerun=False,old_experiment_videos_rescored=0,whole_card_CPU_accepted=False,
  remaining=['Complete analysis/figure integration','Bound production storage and complete asset packet','Final source composition and fresh admission','Separate seven GPUh and original-central transaction authority'],
  GPU_submissions=0,ledger_written=False)
 path=ROOT/'reports/cara_endpoint7_interfaces_CPU_accepted_r1_20261101.json'
 with path.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],wall_seconds=report['wall_seconds'])))
if __name__=='__main__':main()
