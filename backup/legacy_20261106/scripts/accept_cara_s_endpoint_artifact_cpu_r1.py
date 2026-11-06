"""Accept the original exited bounded CPU artifact proof; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from cara_s_endpoint_artifact_cpu_r1 import STAGE,OVERLAY
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
    require(proof['status']=='ENDPOINT_ARTIFACT_REAL_VIDEO_CPU_COMPLETE_NOT_WHOLE_CARD'
            and proof['host']=='two_card' and proof['total_controls_passed']==25,
            'Complete CPU denominator differs')
    require(proof['metadata_controls']==dict(tests_run=15,failures=0,errors=0,skipped=0),
            'All metadata controls must pass')
    media=proof['media'];cases=media['cases']
    require(media['status']=='REAL_PYAV_COMPLETE_ENDPOINT_MEDIA_CPU_PASS'
            and len(cases)==2 and [c['alias'] for c in cases]==[False,True],
            'Both full32 and alias25 real-video cases required')
    for case in cases:
        require(case['physical_videos']==(25 if case['alias'] else 32)
                and case['new_scoring_pairs']==(8 if case['alias'] else 12)
                and case['original_Native_reads']==4 and case['logical_positions']==24
                and case['reused_rows']==12 and case['identity_controls']==9
                and case['all_frames']==93 and case['geometry']==[16,16,3]
                and case['original_scopes_preserved'] is True and case['metrics_computed']==0,
                'Full frame, scope or logical/physical denominator differs')
    require(media['failure_controls']==['short','long','geometry','fps','hash','RGB_replay','RGB_allD','PTS_offset']
            and media['complete_new_video_reads']==57 and media['complete_original_Native_reads']==8
            and media['complete_frame_reads']==6045
            and all(media[k] is False for k in ('actual_original_experiment_videos_read','model_loaded','whole_GPU_card_accepted'))
            and media['metrics_computed']==0 and media['tensor_contents']=='SYNTHETIC_BYTES_FOR_FILE_INTEGRITY_ONLY',
            'Complete real-video failure controls and synthetic scope required')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=900
            and proof['work_seconds']==900 and proof['exit_seconds']==60
            and proof['synthetic_lifecycle_and_historical_scores'] is True and proof['temporary_ledger_only'] is True
            and all(proof[k] is False for k in ('whole_GPU_card_accepted','active_experiment_outputs_read','ledger_written'))
            and proof['GPU_submissions']==0,'CPU-only or bounded runtime differs')
    return dict(status='ENDPOINT_ARTIFACT_REAL_VIDEO_CPU_ACCEPTED_NOT_WHOLE_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        total_controls_passed=25,metadata_controls_passed=15,real_video_cases=2,real_video_failure_controls=8,
        complete_new_video_reads=57,complete_original_Native_reads=8,complete_frame_reads=6045,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        actual_original_experiment_videos_read=False,metrics_computed=0,whole_GPU_card_accepted=False,
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
