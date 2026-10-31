"""Accept the original exited bounded CPU recovery proof; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from cara_s_endpoint_reuse_cpu_r2 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.policy_price_terminal_r1 import require


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_sha(value):return hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()


def accept(captured,launched):
    require(captured['exit_code']==0,'Original capture required')
    c=captured['result'];recovered=launched['exit_code']!=0
    require(launched['action']=='prepare' and launched['host']=='two_card' and launched['stage_name']==STAGE,
            'Original prepare binding required')
    if recovered:
        require(launched['result'] is None and launched['unknown_requires_original_capture'] is True,
                'Unknown transport must retain its original prepare binding')
        l=c['launch']
        require(l['started_unix']>=launched['started_unix'],'Recovered launch predates original prepare')
    else:l=launched['result']
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
    require(proof['status']=='ENDPOINT_REUSE_ADMISSION_CPU_COMPLETE_NOT_WHOLE_CARD'
            and proof['host']=='two_card' and proof['tests_run']==48
            and proof['dispatch_container_controls']==24 and proof['reuse_controls']==13 and proof['entry_controls']==10 and proof['entry_model_and_CUDA_simulated'] is True and proof['actual_Linux_child_controls']==1
            and proof['failures']==proof['errors']==proof['skipped']==0,
            'Complete endpoint dispatch/container/child CPU scope required')
    observations=proof['observations']
    require(len(observations)==1,'Original Linux child evidence required')
    observation=observations[0];identity=observation['original_identity']
    require(identity['pid']>0 and identity['start_ticks']>0 and bool(identity['host_view'])
            and observation['child_exit_code']==1
            and all(observation[k] is True for k in ('exact_guardian_entry','real_Popen_and_private_pipe',
                'guardian_launch_identity_equal','original_child_ended','original_failure_journal_and_bill_complete',
                'no_allocation_attempted','no_replay','sources_unchanged','synthetic_metadata_only'))
            and observation['actual_GPU_resources_exercised'] is False
            and observation['actual_GPUh']==0 and observation['ledger_written'] is False,
            'Original child identity, failed allocation closure and no replay required')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=180
            and proof['work_seconds']==180 and proof['exit_seconds']==30
            and all(proof[k] is False for k in ('whole_GPU_card_accepted','actual_GPU_resources_exercised',
                'real_Docker_GPU_lifecycle_exercised','actual_64GiB_storage_exercised',
                'actual_Cosmos_model_load','active_experiment_outputs_read','ledger_written'))
            and proof['GPU_submissions']==0,'Bounded CPU-only dispatch evidence required')
    from wcomr.cara_s_endpoint_reuse_admission_r1 import expected_sources
    from wcomr.cara_fast_spec_r1 import digest
    proposal_ref='plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'
    scores_ref='reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json'
    require(proof['original_proposal_ref']==proposal_ref and proof['original_scores_ref']==scores_ref
            and proof['original_proposal_sha256']==sha(ROOT/proposal_ref)==reg['payload_sha256'][proposal_ref]
            and proof['original_scores_sha256']==sha(ROOT/scores_ref)==reg['payload_sha256'][scores_ref],
            'Registered original proposal and complete score bytes required')
    proposal=json.loads((ROOT/proposal_ref).read_text());scores=json.loads((ROOT/scores_ref).read_text())
    sources=expected_sources(proposal,scores);actual=proof['actual_original_reuse']
    expected=[]
    for source in sources:
        expected.extend([dict(path=source['path'],sha256=source['sha256'],bytes=source['bytes']),
                         dict(path=str(Path(source['path']).with_suffix('.json')),sha256=source['argument_file_sha256'])])
    require(actual['status']=='ORIGINAL_ENDPOINT_REUSE_ASSETS_VERIFIED'
            and actual['CPU_fixture_only'] is False and actual['original_videos']==actual['original_argument_files']==16
            and actual['reused_score_rows']==12 and len(actual['files'])==32
            and actual['proposal_scope_sha256']==proposal['scope_sha256']
            and actual['original_scores_digest']==digest(scores), 'Complete original16 video/argument identity required')
    require(all(row['path']==want['path'] and row['sha256']==want['sha256'] and row['bytes']>0
                and row['stable_during_read'] is True and bool(row['resolved_path'])
                and ('bytes' not in want or row['bytes']==want['bytes'])
                for row,want in zip(actual['files'],expected))
            and actual['read_bytes']==sum(r['bytes'] for r in actual['files']),
            'Every original video and argument hash must match')
    require(proof['started_unix']<=actual['started_unix']<=actual['ended_unix']<=proof['ended_unix']
            and actual['metrics_computed']==actual['GPU_submissions']==0
            and actual['ledger_written'] is False and actual['active_GPU_outputs_read'] is False
            and actual['future_availability_proven'] is False and proof['metrics_computed']==0,
            'Read-only completed assets are not future admission or rescoring')
    return dict(status='ENDPOINT_REUSE_ADMISSION_CPU_ACCEPTED_NOT_WHOLE_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,launch_recovered_from_original_capture=recovered,
        container_state=state,host_config=LIMITS,registration_sha256=c['registration_sha256'],
        CPU_proof_sha256=c['CPU_proof_sha256'],metadata_controls=47,reuse_controls=13,entry_controls=10,entry_model_and_CUDA_simulated=True,actual_Linux_child_controls=1,
        total_controls_passed=48,actual_original_reuse=actual,CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        original_child=observation,whole_GPU_card_accepted=False,actual_GPU_resources_exercised=False,
        real_Docker_GPU_lifecycle_exercised=False,actual_Cosmos_model_load=False,
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
