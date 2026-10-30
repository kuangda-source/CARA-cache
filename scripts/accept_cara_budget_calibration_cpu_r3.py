"""Accept the frozen R3 CPU matrix; this grants no GPU dispatch authority."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cara_budget_calibration_cpu_hosts_r3 import STAGES
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG

TWO_CARD_R4_STAGE='cara-budget-calibration-CPU-a6000-r4-20261031'

COUNTS={'test_cara_budget_prepare_r1':9,'test_cara_budget_central_r1':11,
    'test_cara_budget_dispatch_r1':15,'test_cara_budget_runner_binding_r1':7,
    'test_cara_budget_lifecycle_r1':16,'test_cara_budget_calibration_r1':7,
    'test_cara_budget_storage_r1':13,'test_cara_budget_complete_r1':11,
    'test_cara_budget_container_r1':7,'test_cara_budget_guardian_journal_r1':13,
    'test_cara_budget_supervisor_r1':12,'test_cara_budget_host_guardian_r1':13}


def require(condition,message):
    if not condition:raise ValueError(message)


def encoded_sha(value):
    return hashlib.sha256((json.dumps(value,indent=2,allow_nan=False)+'\n').encode()).hexdigest()


def accept(capture,launch,plan,base,revision,*,published_bytes,package_receipt):
    require(re.fullmatch('[0-9a-f]{40}',revision) is not None,'Immutable source revision required')
    require(package_receipt['source_revision']==revision
        and package_receipt['plan_sha256']==encoded_sha(plan)
        and package_receipt['overlay_files']==len(plan['overlay_sha256']), 'Published package receipt differs')
    host=launch['host'];require(host in STAGES,'Registered CPU host required')
    expected={**base['payload_sha256'],**plan['overlay_sha256']}
    require(base['host']==host and encoded_sha(base)==plan['base_registration_sha256'],
            'Original host/base registration differs')
    for name,expected_sha in plan['overlay_sha256'].items():
        require(hashlib.sha256(published_bytes(name)).hexdigest()==expected_sha,'Published overlay differs: '+name)
    reg=capture['registration'];proof=capture['CPU_proof'];state=capture['container_state']
    stage_name=Path(reg['stage']).name
    allowed_stages=(STAGES[host],TWO_CARD_R4_STAGE) if host=='two_card' else (STAGES[host],)
    require(capture['launch']==launch and reg['stage']==launch['stage']
        and stage_name in allowed_stages and launch['container']==stage_name+'-cpu'
        and launch['status']=='PAPER_TIMING_CPU_LAUNCHED_NOT_GPU', 'Original CPU launch or stage differs')
    require(state['Status']=='exited' and not state['Running'] and state['Pid']==0
        and state['ExitCode']==0 and not state['OOMKilled'] and proof is not None,
        'Original CPU must exit normally with its complete proof')
    require(encoded_sha(reg)==capture['registration_sha256']==launch['registration_sha256']
        ==proof['registration_sha256'] and encoded_sha(proof)==capture['CPU_proof_sha256'],
        'Original registration/proof bytes differ')
    require(reg['host']==proof['host']==host and reg['parent_git_revision']==revision
        and reg['base_registration_sha256']==plan['base_registration_sha256']
        and reg['payload_sha256']==proof['payload_sha256']==expected
        and reg['runtime_source_sha256']==proof['runtime_source_sha256']==base['runtime_source_sha256']
        and capture['payload_intact'] and capture['runtime_intact'], 'Complete frozen source/runtime differs')
    require(capture['host_config']==reg['expected_host_config']==HOST_CONFIG,
        'Original1CPU/4GiB/no extra swap/no GPU resource boundary differs')
    card=json.loads(published_bytes('plans/cara_next_stage_20261028/mainline/r2/BUDGET_RUN_SPEC_R1.json'))
    require(proof['scope_sha256']==card['scope_sha256']
        and proof['status']=='CURRENT_COMPLETE_CALIBRATION_AND_EXECUTION_CONTROLS_CPU_NOT_GPU'
        and proof['spec_tests']==3 and proof['execution_control_tests']==134
        and proof['resource_bound']==dict(cpus=1,memory_GiB=4,work_seconds=2400,exit_seconds=60)
        and proof['actual_compile_threads']==1 and proof['compile_pools']==[]
        and not any(proof[k] for k in ('CUDA_initialized','Cosmos_model_weights_loaded','GPU_submissions',
            'ledger_written','whole_GPU_card_accepted','real_Docker_GPU_lifecycle_exercised',
            'real_64GiB_storage_exercised')) and proof['dispatch_child_spawn_simulated'] is True,
        'Complete CPU scope or simulation boundary differs')
    controls=proof['control_results'];indexed={r['module']:r for r in controls}
    require(len(controls)==len(indexed)==len(COUNTS) and set(indexed)==set(COUNTS)
        and all(indexed[n]['tests_run']==count and not any(indexed[n][k] for k in ('errors','failures','skipped'))
                for n,count in COUNTS.items()), 'All134 current controls must pass without Linux skips')
    require(len(indexed['test_cara_budget_supervisor_r1']['Linux_observations'])==11
        and len(indexed['test_cara_budget_host_guardian_r1']['Linux_observations'])==12,
        'Original Linux CPU scenario observations incomplete')
    numeric=proof['numeric'];require([r['flow'] for r in numeric['checks']]==[False,True]
        and numeric['cuda_initialized'] is False,'Both complete actual CPU sampler routes required')
    for row in numeric['checks']:
        required=dict(validation='COMPLETE112_CALIBRATION_ROUTES_CPU_NOT_GPU',complete_design_paths=112,
            complete_two_FIT_queries=51,SA_iterations=30,HC_iterations=1,HC_neighbors=20,
            successful_physical_paths=133,declared_failure_attempts=3,total_physical_attempts=136,
            complete93_frame_RGB=True,Native_allD_timing_RGB_and_full_CPU_RNG_equal=True,
            original_complete_recovery_without_generation=True,hooks_restored=True,
            CUDA_RNG_exercised=False,Cosmos_model_weights_loaded=False,real_GPU_executed=False,whole_GPU_card_accepted=False)
        require(all(row[k]==v for k,v in required.items()) and row['failures']==[
            dict(kind=k,physical_attempts=n,no_replay=True) for k,n in
            (('first_writer',1),('second_FIT_refusal',12),('policy_fallback',11))],
            'Complete112/51 query matrix or original failure/recovery scope differs')
    require(proof['ended_unix']>=proof['started_unix']>=launch['started_unix']
        and proof['ended_unix']-proof['started_unix']<=2400,'Original CPU work clock differs')
    return dict(status=('CURRENT_R4_CPU_MATRIX_ACCEPTED_NOT_GPU_DISPATCH' if stage_name==TWO_CARD_R4_STAGE
                        else 'CURRENT_R3_CPU_MATRIX_ACCEPTED_NOT_GPU_DISPATCH'),host=host,observed_unix=time.time(),
        launch=launch,source_revision=revision,scope_sha256=card['scope_sha256'],
        payload_sha256=expected,runtime_source_sha256=base['runtime_source_sha256'],
        registration_sha256=capture['registration_sha256'],CPU_proof_sha256=capture['CPU_proof_sha256'],
        full112_sampler_matrix_accepted=True,current_execution_control_matrix_accepted=True,
        actual_Linux_controls_accepted=True,execution_controls=134,spec_controls=3,
        complete_design_paths=224,complete_two_FIT_objectives=102,successful_physical_paths=266,
        declared_failure_attempts=6,total_physical_attempts=272,
        CPU_wall_seconds=proof['ended_unix']-proof['started_unix'],
        dispatcher_child_spawn_exercised=False,real_Docker_GPU_lifecycle_exercised=False,
        actual_64GiB_storage_exercised=False,whole_card_CPU_accepted=False,
        GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    for name in ('capture','original-launch','package','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    require(not args.output.exists(),'Fresh acceptance receipt required')
    def result(path):
        value=json.loads(path.read_text())
        require(value['exit_code']==0 and value.get('result') is not None,'Successful original transport receipt required')
        return value['result']
    def published(name):
        return subprocess.check_output(['git','show',args.source_revision+':'+name],cwd=ROOT,stderr=subprocess.PIPE)
    launch=result(args.original_launch)
    package_ref={'four_card':'reports/cara_budget_published_source_package_r2_20261031.json',
        'two_card':'reports/cara_budget_published_source_two_package_r2_20261031.json'}[launch['host']]
    if launch['host']=='two_card' and Path(launch['stage']).name==TWO_CARD_R4_STAGE:
        package_ref='reports/cara_budget_two_R4_published_source_r1_20261031.json'
    output=accept(result(args.capture),launch,
        json.loads((args.package/'source-plan.json').read_text()),
        json.loads((args.package/'base-registration.json').read_text()),args.source_revision,published_bytes=published,package_receipt=json.loads((ROOT/package_ref).read_text()))
    output.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        original_launch_ref=str(args.original_launch),original_launch_sha256=hashlib.sha256(args.original_launch.read_bytes()).hexdigest(),
        acceptor_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.output.open('x') as f:json.dump(output,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=output['status'],host=output['host'],GPU_dispatch_ready=False)))


if __name__=='__main__':main()
