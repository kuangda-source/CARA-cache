"""Accept the original exited bounded CPU scoring proof; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from cara_s_endpoint_score_cpu_r1 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.policy_price_terminal_r1 import require


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_sha(value):return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured,launched):
    require(captured['exit_code']==launched['exit_code']==0,'Original launch and capture required')
    c,l=captured['result'],launched['result']
    reg,proof,state=c['registration'],c['CPU_proof'],c['container_state']
    require(c['launch']==l and l['host']=='two_card' and Path(l['stage']).name==STAGE
            and l['container']==STAGE+'-cpu','Original endpoint CPU identity differs')
    require(state['Status']=='exited' and state['Running'] is False and state['Pid']==0
            and state['ExitCode']==0 and state['OOMKilled'] is False and proof is not None,
            'Original exited zero proof required')
    require(c['registration_sha256']==encoded_sha(reg)==l['registration_sha256']==proof['registration_sha256']
            and c['CPU_proof_sha256']==encoded_sha(proof),'Original proof bytes differ')
    base=json.loads((ROOT/BASE_CAPTURE).read_text())['result']
    accepted=json.loads((ROOT/BASE_ACCEPTED).read_text())
    require(accepted['capture_sha256']==sha(ROOT/BASE_CAPTURE) and accepted['total_controls_passed']==113,
            'Accepted source base differs')
    revision=launched['source_revision']
    overlay={p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT)).hexdigest() for p in OVERLAY}
    require(reg['payload_sha256']=={**base['registration']['payload_sha256'],**overlay}==proof['payload_sha256']
            and reg['runtime_source_sha256']==base['registration']['runtime_source_sha256']==proof['runtime_source_sha256']
            and reg['base_registration_sha256']==base['registration_sha256']
            and reg['parent_git_revision']==proof['source_revision']==captured['source_revision']==revision
            and c['payload_intact'] is True and c['runtime_intact'] is True,'Original source/runtime differs')
    require(c['host_config']==reg['expected_host_config']==LIMITS and proof['actual_CPU_affinity']==[26],
            'Original CPU resource limits differ')
    require(proof['status']=='ENDPOINT_ACTUAL_SCORING_CPU_COMPLETE_NOT_WHOLE_CARD'
            and proof['host']=='two_card' and proof['total_controls_passed']==19,
            'Complete CPU denominator differs')
    require(proof['metadata_controls']==dict(tests_run=13,failures=0,errors=0,skipped=0),
            'All score acceptance controls must pass')
    actual=proof['actual'];cases=actual['cases']
    require(actual['status']=='ACTUAL_CROSS_SCOPE_COMPLETE_SCORER_CPU_PASS'
            and len(cases)==2 and [c['alias'] for c in cases]==[False,True],
            'Both complete12 and alias8 scoring cases required')
    sources=('scripts/score_cara_s_endpoint_fidelity_r1.py','src/wcomr/cara_s_endpoint_scores_r1.py',
             'src/wcomr/cara_fast_fidelity_r1.py','src/wcomr/cara_s_endpoint_scoring_manifest_r1.py')
    for case in cases:
        require(case['new_pairs']==(8 if case['alias'] else 12) and case['frames_per_pair']==93
                and case['temporal_pairs']==92 and case['logical_positions']==24
                and case['original_rows_unchanged']==12 and case['original_scopes_preserved'] is True
                and case['infinite_PSNR_pairs']>0 and case['undefined_gradient_pairs']>0
                and case['no_replay'] is True,'Complete score identity/curve/alias controls differ')
        require(case['execution']['manifest_sha256']==case['manifest_sha256'],'Original scorer manifest differs')
    failed=actual['failed_case']
    require(failed['status']=='FAILED_DENOMINATOR_RETAINED' and failed['complete_registered_pairs']==12
            and failed['completed_rows']==1 and failed['frame_count_of_completed_row']==93
            and failed['no_replay'] is True,'Failed scorer must preserve complete denominator and original intent')
    for index,execution in enumerate([c['execution'] for c in cases]+[failed['execution']]):
        require(execution['kind']=='ACTUAL_CPU_FIXTURE_CHILD' and execution['original_process_ended'] is True
                and execution['GPU_hidden'] is True and (execution['exit_code']==0)==(index<2)
                and 0<execution['wall_seconds']<=720
                and execution['source_actual_sha256']=={p:reg['payload_sha256'][p] for p in sources},
                'Original bounded scorer process/source differs')
        identity,observation=execution['original_identity'],execution['original_observation']
        require(observation['status']=='ORIGINAL_NOT_LIVE' and observation['original_live'] is False
                and observation['original_pid']==identity['pid'] and observation['original_start_ticks']==identity['start_ticks']
                and observation['observed_host_view']==identity['host_view'],'Original scorer handle is not proved ended')
    require(actual['new_synthetic_pairs_scored']==20 and actual['failure_fixture_pairs_scored']==1
            and actual['old_experiment_videos_rescored']==actual['original_scientific_scores_computed']==0
            and actual['metric_weights_loaded'] is True and actual['generative_model_loaded'] is False
            and actual['whole_GPU_card_accepted'] is False,'Synthetic actual-metric scope differs')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=900
            and proof['work_seconds']==900 and proof['exit_seconds']==60
            and proof['synthetic_lifecycle_and_historical_scores'] is True and proof['temporary_ledger_only'] is True
            and all(proof[k] is False for k in ('whole_GPU_card_accepted','active_experiment_outputs_read','ledger_written'))
            and proof['GPU_submissions']==0,'CPU-only or bounded runtime differs')
    return dict(status='ENDPOINT_ACTUAL_SCORING_CPU_ACCEPTED_NOT_WHOLE_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        total_controls_passed=19,metadata_controls_passed=13,complete_scoring_cases=2,
        partial_failure_controls=1,no_replay_controls=3,new_synthetic_pairs_scored=20,failure_fixture_pairs_scored=1,
        synthetic_metric_frames=1953,original_rows_unchanged_per_case=12,formal_positions_per_case=24,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        actual_original_experiment_videos_read=False,original_scientific_scores_computed=0,whole_GPU_card_accepted=False,
        active_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','launch','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Preserve original acceptance')
    result=accept(json.loads(args.capture.read_text()),json.loads(args.launch.read_text()))
    result.update(capture_ref=str(args.capture),capture_sha256=sha(args.capture),launch_ref=str(args.launch),
                  launch_sha256=sha(args.launch),acceptor_sha256=sha(__file__))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','total_controls_passed','CPU_wall_seconds')}))


if __name__=='__main__':main()
