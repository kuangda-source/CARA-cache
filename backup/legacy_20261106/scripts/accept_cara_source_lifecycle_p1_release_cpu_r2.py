"""Accept only the ended original R2 CPU; never dispatch or recompute metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from cara_source_lifecycle_p1_release_cpu_r2 import STAGE,OVERLAY


def accept(launch_file,capture_file,*,expected_stage=STAGE,overlay=OVERLAY):
    read=lambda p:json.loads(Path(p).read_bytes())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    launch,capture=read(launch_file),read(capture_file)
    assert launch['exit_code']==capture['exit_code']==0
    cap,launched=capture['result'],launch['result'];reg,state,proof=cap['registration'],cap['container_state'],cap['CPU_proof']
    assert cap['launch']==launched and Path(launched['stage']).name==expected_stage
    assert proof is not None and state['Status']=='exited' and state['Pid']==state['ExitCode']==0
    assert not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
    assert cap['host_config']==reg['expected_host_config']==LIMITS and cap['payload_intact'] and cap['runtime_intact']
    revision=launch['source_revision']
    assert revision==capture['source_revision']==reg['parent_git_revision']==proof['source_revision']
    assert subprocess.check_output(['git','rev-parse',revision],cwd=ROOT,text=True).strip()==revision
    encode=lambda v:(json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    assert hashlib.sha256(encode(reg)).hexdigest()==cap['registration_sha256']==proof['registration_sha256']
    raw=encode(proof);assert hashlib.sha256(raw).hexdigest()==cap['CPU_proof_sha256']
    base=read(ROOT/BASE_CAPTURE)['result'];original=read(ROOT/BASE_ACCEPTED)
    assert original['capture_sha256']==sha(ROOT/BASE_CAPTURE) and original['total_controls_passed']==113
    payload={**base['registration']['payload_sha256'],**{
        n:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in overlay}}
    assert proof['payload_sha256']==reg['payload_sha256']==payload
    assert proof['runtime_source_sha256']==reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']
    from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUNTIME_ENTRY
    assert proof['supplemental_runtime_sha256']==json.loads(subprocess.check_output(['git','show',revision+':'+RUNTIME_ENTRY],cwd=ROOT))['files']
    assert proof['status']=='P1_ORIGINAL_RELEASED_ENTRY_FILES_AND_POST_SCORES_LINUX_CPU_PASS'
    assert proof['tests_run']==4 and proof['reused_original_R1_controls']==21 and proof['reused_control_tests_replayed'] is False
    old=read(ROOT/'reports/cara_v1_P1_release_Linux_CPU_original_failure_r1_20261102.json')
    assert proof['reused_original_R1_capture_sha256']==old['capture_sha256']==sha(ROOT/old['capture_ref'])
    assert proof['actual_CPU_affinity']==[26] and proof['work_seconds']==1200 and proof['exit_seconds']==60
    assert launched['started_unix']<=proof['started_unix']<proof['ended_unix']<=launched['started_unix']+1200
    post=proof['post_release']
    assert post['status']=='P1_REAL_FULL146_READER_AND_ORIGINAL_POST_SCORE_CPU_PASS'
    assert post['semantic_positions']==146 and post['source_labels']==64 and post['identity_controls']==12
    assert post['logical_quality_positions']==52 and 46<=post['physical_video_latent_reads']<=142
    assert 0<post['original_postrelease_new_pairs']<=32 and post['all_frames']==93 and post['geometry']==[64,64,3]
    assert post['actual_metric_weights'] and post['internal_service_and_internal_scores_simulated']
    assert post['actual_original_Linux_service_and_postscore_processes_ended']
    assert post['immutable_reader_recovery_no_callbacks'] and post['no_replay']
    assert set(post['refusals'])=={'no_original_release','service_unknown','saved_arguments',
        'changed_internal_response','failed_original_score_full_denominator'}
    assert post['failure_denominator']==post['original_postrelease_new_pairs'] and post['failure_completed_pairs']==1
    for key in ('post_score_execution','failed_score_execution'):
        execution=post[key];identity=execution['original_identity'];observation=execution['original_observation']
        assert execution['kind']=='ACTUAL_CPU_FIXTURE_CHILD' and execution['original_process_ended'] and execution['GPU_hidden']
        assert observation['original_live'] is False and observation['original_pid']==identity['pid']
        assert observation['original_start_ticks']==identity['start_ticks'] and observation['observed_host_view']==identity['host_view']
        assert (execution['exit_code']==0)==(key=='post_score_execution')
    assert all(proof[k] is False for k in ('prior_accepted_components_replayed','whole_GPU_entry_accepted',
        'P1_GPU_authorized','actual_central_ledger_accessed','ledger_written')) and proof['GPU_submissions']==0
    assert all(post[k] is False for k in ('production_model_weights_loaded','old_algorithm_or_metric_experiments_repeated',
        'production_GPU_entry_accepted','ledger_written')) and post['GPU_submissions']==0
    return dict(status='ORIGINAL_P1_RELEASED146_SCORE52_CPU_ACCEPTED_NOT_WHOLE_GPU_ENTRY',source_revision=revision,
        CPU_stage=expected_stage,launch_ref=str(launch_file),launch_sha256=sha(launch_file),capture_ref=str(capture_file),
        capture_sha256=sha(capture_file),registration_sha256=cap['registration_sha256'],original_proof_sha256=cap['CPU_proof_sha256'],
        original_CPU_ended=True,original_container_state=state,new_analysis_controls=4,reused_R1_controls=21,
        reused_controls_replayed=False,semantic_positions=146,physical_video_latent_reads=post['physical_video_latent_reads'],
        source_labels=64,identity_controls=12,logical_quality_positions=52,new_real93_metric_pairs=post['original_postrelease_new_pairs'],
        internal_metric_pairs_simulated=post['original_sealed_internal_pairs'],original_metrics_recomputed=0,
        failure_denominator=post['failure_denominator'],failure_completed_pairs=1,post_release=post,
        whole_GPU_entry_accepted=False,P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False),raw


def main(*,expected_stage=STAGE,overlay=OVERLAY):
    parser=argparse.ArgumentParser()
    for key in ('launch','capture','output','proof-output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists() and not args.proof_output.exists()
    accepted,raw=accept(args.launch,args.capture,expected_stage=expected_stage,overlay=overlay)
    with args.proof_output.open('xb') as stream:stream.write(raw)
    accepted['original_proof_ref']=str(args.proof_output)
    with args.output.open('x') as stream:json.dump(accepted,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=accepted['status'],new_real_pairs=accepted['new_real93_metric_pairs'],P1_GPU_authorized=False)))


if __name__=='__main__':main()
