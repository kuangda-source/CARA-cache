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
from cara_s_endpoint_pipeline_cpu_r4 import STAGE,OVERLAY
from cara_s_initialization_selector_cpu_r1 import BASE_CAPTURE,BASE_ACCEPTED,LIMITS
from wcomr.policy_price_terminal_r1 import require
from wcomr.cara_s_endpoint_scores_r1 import SCORER_SOURCES


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
    require(proof['status']=='ENDPOINT_COLLECTION_TO_SCORE_TINY_CPU_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE'
            and proof['host']=='two_card' and proof['production_paths']==114
            and proof['historical_tiny_paths']==32 and proof['actual_new_metric_pairs']==40
            and proof['actual_metric_frames']==3720 and proof['complete_logical_acceptances']==4,
            'Complete collection and actual scoring denominator required')
    checks=proof['numeric']['checks']
    require(len(checks)==2 and {r['flow'] for r in checks}=={False,True},'Both original flow modes required')
    identities=[]
    for check in checks:
        require(check['status']=='PASS' and check['actual_collection_paths']==57 and check['historical_tiny_paths']==16
                and check['actual_new_metric_pairs']==20 and check['original_experiment_pairs_rescored']==0,
                'Complete per-flow counts required')
        cases=check['cases']
        require(len(cases)==2 and [r['alias'] for r in cases]==[False,True],'Both complete physical scopes required')
        for case in cases:
            require(case['status']=='PASS' and case['flow']==check['flow']
                    and case['physical_paths']==(25 if case['alias'] else 32)
                    and case['new_pairs']==(8 if case['alias'] else 12)
                    and case['logical_positions']==24 and case['reused_rows_unchanged']==12
                    and case['RGB_controls']==9 and case['full_frames_per_video']==93
                    and case['replay_refused'] is True and case['temporary_ledger_only'] is True
                    and case['actual_Cosmos_weights'] is False and case['original_experiment_outputs_read'] is False,
                    'Actual complete pipeline case differs')
            execution=case['score_execution'];identity=execution['original_identity'];observed=execution['original_observation']
            require(execution['source_actual_sha256']=={p:reg['payload_sha256'][p] for p in SCORER_SOURCES}
                    and execution['manifest_sha256']==execution['manifest_label_sha256'],
                    'Original actual metric kernel and manifest binding required')
            identities.append((identity['pid'],identity['start_ticks']))
            require(execution['kind']=='ACTUAL_CPU_FIXTURE_CHILD' and execution['exit_code']==0
                    and execution['original_process_ended'] is True and execution['GPU_hidden'] is True
                    and execution['container_state']['ExitCode']==0 and execution['container_state']['OOMKilled'] is False
                    and observed['original_live'] is False and observed['status']=='ORIGINAL_NOT_LIVE'
                    and observed['original_pid']==identity['pid'] and observed['original_start_ticks']==identity['start_ticks']
                    and observed['observed_host_view']==identity['host_view']
                    and execution['cli_observation']['original_live'] is False,
                    'Actual original scoring processes must have ended successfully')
    require(len(set(identities))==4,'Four distinct original scorers required')
    require(l['started_unix']<=proof['started_unix']<=proof['ended_unix']
            and proof['ended_unix']-proof['started_unix']<=1200 and proof['work_seconds']==1200 and proof['exit_seconds']==60
            and proof['actual_compile_threads']==1 and proof['compile_pools']==[]
            and proof['internal_Docker_simulated'] is True and proof['internal_lifecycle_simulated'] is True
            and proof['CUDA_initialized'] is False and proof['Cosmos_model_weights_loaded'] is False
            and proof['actual_original_budget_outputs_read'] is False and proof['actual_budget_policy_bound'] is False
            and proof['actual_historical_RGB_accepted'] is False and proof['whole_GPU_card_accepted'] is False
            and proof['GPU_submissions']==0 and proof['ledger_written'] is False,
            'Original bounded CPU-only scope differs')
    return dict(status='ENDPOINT_COLLECTION_TO_SCORE_TINY_CPU_ACCEPTED_NOT_WHOLE_GPU_CARD',observed_unix=time.time(),
        source_revision=revision,launch=l,launch_recovered_from_original_capture=recovered,container_state=state,host_config=LIMITS,
        registration_sha256=c['registration_sha256'],CPU_proof_sha256=c['CPU_proof_sha256'],
        complete_pipeline_cases=4,actual_collection_paths=114,historical_tiny_paths=32,
        actual_new_metric_pairs=40,actual_metric_frames=3720,original_pairs_rescored=0,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],actual_original_Linux_processes=True,
        internal_Docker_simulated=True,internal_lifecycle_simulated=True,actual_Cosmos_weights=False,
        whole_GPU_card_accepted=False,active_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','launch','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Preserve original acceptance')
    result=accept(json.loads(args.capture.read_text()),json.loads(args.launch.read_text()))
    result.update(capture_ref=str(args.capture),capture_sha256=sha(args.capture),launch_ref=str(args.launch),
                  launch_sha256=sha(args.launch),acceptor_sha256=sha(__file__))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','complete_pipeline_cases','CPU_wall_seconds')}))


if __name__=='__main__':main()
