#!/usr/bin/env python3
"""Host control for the complete deployment-tools CPU card, with real Docker.

All model work is excluded. Only the GPU process/telemetry boundary is an
explicit CPU fixture. Production dispatch, restore, settled-only watcher,
CPU post and CPU collector functions are the actual published functions.
"""
import argparse
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

from four_card_bank24_container_transport_r1 import atomic,identity,alive,stop_owned
from four_card_bank24_execution_tools_r1 import (build_template,spawn_once,restore_only,post_conditions,
    collect_once,validate_authorization,verify_registration,read,sha,ROOT,CONFIG,TARGET_STAGE)
from four_card_bank24_gpu_port_r1 import accept_capture


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture_controller_source():
    return '''import fcntl,json,os,sys,time
from pathlib import Path
stage=Path(sys.argv[1]);sys.path.insert(0,str(stage))
from four_card_bank24_container_transport_r1 import atomic,identity
from four_card_bank24_execution_tools_r1 import module,read,sha
L=read(stage/'scout-GPU-launch.json');project=Path(L['project']);out=project/'outputs'/L['run_id'];out.mkdir(parents=True)
with (stage/'CPU-controller-created-once.json').open('x') as f:f.write('{"CPU_FIXTURE_ONLY":true}')
poolmod=module('TEST_ONLY_registered_budget',stage/'bank24_sm89_budget_pool.py');pool=poolmod.BudgetPool(project)
lease=poolmod.DeviceLease(project,L['gpu_uuid']);lease.acquire();started=time.monotonic()
job=dict(job_id=L['run_id'],run_id=L['run_id'],launch_id=L['launch_id'],gpu_uuid=L['gpu_uuid'],
 source_revision=L['source_revision'],config_sha256=L['config_sha256'],production_CPU_sha256=L['production_CPU_sha256'],
 scope_counts=L['scope_counts'],supervisor_pid=os.getpid(),supervisor_start_ticks=identity(os.getpid())['start_ticks'],
 forecast_GPUh=L['forecast_GPUh'],billed_limit_GPUh=L['billed_limit_GPUh'],CPU_FIXTURE_ONLY_NOT_AUTHORITY=True)
gpu=dict(uuid=L['gpu_uuid'],name='NVIDIA RTX 6000 Ada Generation',compute_cap='8.9',memory_used_mib=0,pids=[])
pool.reserve(job,gpu);time.sleep(.5)
# Intentionally zero attempted neural paths: the production post must retain24.
atomic(out/'runner.json',dict(runs=[],request_memory_records=[],CPU_FIXTURE_ONLY=True))
wall=time.monotonic()-started
bill=dict(status='SCOUT_ACTUAL_GPU_BILL',run_id=L['run_id'],launch_id=L['launch_id'],source_revision=L['source_revision'],
 gpu_uuid=L['gpu_uuid'],scope_counts=L['scope_counts'],wall_seconds=wall,actual_GPUh=wall/3600,
 billed_limit_GPUh=L['billed_limit_GPUh'],CPU_FIXTURE_ONLY_NOT_ACTUAL_GPU=True,actual_real_GPUh_charged=0)
atomic(out/'billing.json',bill);settled=pool.settle(L['run_id'],wall/3600,sha(out/'billing.json'));lease.close()
atomic(out/'supervisor.json',dict(status='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',supervisor_identity=identity(os.getpid()),
 child_identity=None,child_pid=None,child_exit_code=7,runner_sha256=sha(out/'runner.json'),billing_sha256=sha(out/'billing.json'),
 owned_container_exit_verified=True,CPU_FIXTURE_ONLY_NOT_ACTUAL_GPU=True,original_UUID_FD_closed_after_settlement=True))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    job=a.manifest.parent;m=read(a.manifest);project=Path(m['workspace']);started=time.time()
    allowed=os.sched_getaffinity(0);os.sched_setaffinity(0,set(sorted(allowed)[:2]))
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(16*(1<<30),16*(1<<30)))
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1',WC_SCOUT_KIND='BANK24')
    def expired(number,frame):raise TimeoutError('Original full execution-tools CPU wall expired')
    signal.signal(signal.SIGALRM,expired);signal.alarm(m['maximum_wall_seconds'])
    lock=(project/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=dict(status='BANK24_FULL_EXECUTION_TOOLS_CPU_RUNNING',source_revision=m['source_revision'],
        worker_identity=identity(os.getpid()),started_unix=started,host_CPU_affinity=sorted(os.sched_getaffinity(0)),
        host_memory_address_limit_bytes=16*(1<<30),GPU_submissions=0,ledger_written=False,
        actual_authoritative_budget_opened=False,actual_GPU_UUID_leased=False,Cosmos_weights_loaded=0,CUDA_initialized=False,
        full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False,actual_nvidia_smi_queries=0)
    children=[]
    def save():state['updated_unix']=time.time();atomic(job/'health.json',state)
    try:
        with (job/'worker-once.json').open('x') as f:f.write('{"no_replay":true}\n')
        assert sha(__file__)==m['worker_sha256'] and all(sha(job/n)==v for n,v in m['payload_sha256'].items())
        upstream=Path(m['upstream_container_job']);accepted=read(job/'container-accepted.json')
        assert accepted['container_lifecycle_CPU_accepted'] and all(accepted['checks'].values())
        assert sha(upstream/'result.json')==m['upstream_result_sha256'] and sha(upstream/'manifest.json')==m['upstream_manifest_sha256']
        failed=m['failed_full_tools_R1'];prior=Path(failed['job'])
        assert sha(prior/'result.json')==failed['result_sha256'] and sha(prior/'manifest.json')==failed['manifest_sha256']
        state['prior_failed_R1_source']=failed['source_revision'];state['prior_failed_R1_result_sha256']=failed['result_sha256']
        support=load('original_environment_fingerprint',job/'repair_support.py')
        state['environment_metadata_before']=support.metadata_fingerprint(project/'envs/wc-cosmos-py310-cu128-r3')
        assert state['environment_metadata_before']==m['environment_metadata_sha256']
        assert all(sha(project/'runtime'/n)==v for n,v in m['runtime_source_sha256'].items())
        state['phase']='build_actual_registered_full24_production_template';save()
        sys.path.insert(0,str(job/'inputs/src'))
        with (job/'production-CLI-schema.log').open('x') as log:
            help_result=subprocess.run([sys.executable,str(job/'wc_four_card_bank24_execution_r1.py'),'--help'],stdout=log,stderr=subprocess.STDOUT,timeout=20)
            incomplete=subprocess.run([sys.executable,str(job/'wc_four_card_bank24_execution_r1.py'),'launch-gpu','--output',str(job/'NEVER_CREATED.json')],stdout=log,stderr=subprocess.STDOUT,timeout=20)
        assert help_result.returncode==0 and incomplete.returncode==2 and not (job/'NEVER_CREATED.json').exists()
        state['actual_production_CLI_schema']=dict(help_exit0=True,incomplete_GPU_launch_exit2=True,no_GPU_or_SSH_or_output=True,
            source_sha256=sha(job/'wc_four_card_bank24_execution_r1.py'))
        fixture=job/'TEST_ONLY';fixture.mkdir();root=fixture/'project';stage=root/'.sync'/TARGET_STAGE;stage.parent.mkdir(parents=True)
        template=build_template(job/'inputs',stage,m['source_revision'],m,job)
        assert template['generated_sha256']==m['expected_generated_sha256']
        state['production_template']=template;state['target_stage']=template['target_stage'];state['target_registration_sha256']=template['registration_sha256']
        atomic(stage/'CPU-TEST-ONLY.json',dict(CPU_fixture_only=True,actual_GPUh_charged=0))
        (root/'reports').mkdir();(root/'outputs').mkdir();(root/'.sync/gpu-locks').mkdir(parents=True)
        poolmod=load('actual_production_fixture_budget',stage/'bank24_sm89_budget_pool.py')
        budget=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=79.99637737158223,
            origin_gpu_jobs_launched=0,jobs={},events=[],CPU_FIXTURE_ONLY_NOT_AUTHORITY=True)
        budget.update(poolmod.BudgetPool.accounting(budget));atomic(root/'reports/gpu-budget-v2.json',budget)
        quote=template['planning_quote'];config=read(stage/'inputs'/CONFIG)
        fields=dict(status='SCOUT_COMPLETE_CARD_DISPATCHED_ADMISSION_PENDING',kind='BANK24',project=str(root),stage=str(stage),
            run_id='wc-scout-dev6-paired-native-full24-r1',source_revision=m['source_revision'],entry_source_revision=m['source_revision'],
            entry_stage=str(stage),registration_sha256=sha(stage/'registration.json'),entry_registration_sha256=sha(stage/'registration.json'),
            config_sha256=sha(stage/'inputs'/CONFIG),production_CPU_sha256='CPU_FIXTURE_ONLY_NOT_PRODUCTION_CPU',
            scope_counts=config['scope_counts'],matrix=quote['positions'],launch_id='CPU-TOOLS-FIXTURE',gpu_uuid='GPU-CPU-FULL-SCOPE-PROBE',
            forecast_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],CPU_FIXTURE_ONLY_NOT_GPU=True)
        probe=stage/'CPU-controller.py';probe.write_text(fixture_controller_source())
        state['fixture_controller_sha256']=sha(probe)
        state['phase']='actual_one_dispatch_original_restore_and_settled_only_CPU_post';save()
        # The short controller waits for its registered launch to be written.
        command=[sys.executable,'-c',"import pathlib,time,runpy,sys;p=pathlib.Path(sys.argv[1]);deadline=time.monotonic()+10\nwhile not (p/'scout-GPU-launch.json').exists():\n assert time.monotonic()<deadline;time.sleep(.01)\nsys.argv=[str(p/'CPU-controller.py'),str(p)];runpy.run_path(sys.argv[0],run_name='__main__')",str(stage)]
        watcher=['python3',str(stage/'watch_wc_four_card_bank24_post_r1.py'),'--stage',str(stage)]
        launch=spawn_once(stage,fields,command,watcher)
        state['dispatch_fixture_launch']=launch
        again=spawn_once(stage,fields,['INVALID_MUST_NOT_START'],['INVALID_MUST_NOT_START'])
        assert again==launch==restore_only(stage)
        state['same_handle_restored_without_second_Popen']=True
        deadline=time.monotonic()+180
        while alive(launch['supervisor_identity']) or alive(launch['post_watcher_identity']):
            if time.monotonic()>=deadline:raise TimeoutError('Owned fixture/post watcher exceeded bounded CPU plan')
            time.sleep(.1)
        post=read(stage/'post-CPU-exit.json');assert post['exit_code']==0 and post['original_GPU_settled_before_post'] is True
        assert post['CPU_container_exit_verified'] is True and post['CPU_container_peer_binding']['socket_peer_PID_matches_actual_Docker_PID'] is True
        state['actual_post_binding']=post
        assert post['readonly_budget_and_lock_verified'] is True and post['readonly_budget_before']==post['readonly_budget_after']
        assert post['readonly_budget_after']['pool']['sha256']==sha(root/'reports/gpu-budget-v2.json')
        assert post['readonly_budget_after']['lock']['sha256']==sha(root/'.sync/gpu-budget-v2.lock')
        state['readonly_budget_post_verified']=True
        final=read(stage/'CPU-final-results.json')
        assert len(final['rows'])==24 and all(r['status']=='NOT_REACHED_RETAINED' for r in final['rows'])
        assert final['scored_formal_paths']==0 and final['accepted_video_paths']==0
        assert all('LPIPS' not in r and 'final_latent_sha256' not in r for r in final['rows'])
        # Real guards against premature post, unknown container and held lease.
        refusals=[]
        for kind,modified,state_name in [
            ('live_original_parent',dict(launch,supervisor_identity=identity(os.getpid())),'ABSENT'),
            ('unknown_GPU_container',launch,'UNKNOWN')]:
            try:post_conditions(root,stage,modified,state_name)
            except (ValueError,BlockingIOError):refusals.append(kind)
            else:raise AssertionError('Unsafe post started: '+kind)
        lease=root/'.sync/gpu-locks'/('GPU-CPU-FULL-SCOPE-PROBE.lock')
        with lease.open('r') as held:
            fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:post_conditions(root,stage,launch,'ABSENT')
            except BlockingIOError:refusals.append('unreleased_original_UUID')
            else:raise AssertionError('Post accepted a held original lease')
            fcntl.flock(held,fcntl.LOCK_UN)
        budgetpath=root/'reports/gpu-budget-v2.json';original=budgetpath.read_bytes();bad=read(budgetpath)
        bad['jobs'][launch['run_id']]['status']='RESERVED_OR_RUNNING';atomic(budgetpath,bad)
        try:post_conditions(root,stage,launch,'ABSENT')
        except ValueError:refusals.append('unsettled_whole_reservation')
        else:raise AssertionError('Post accepted an unsettled whole card')
        finally:budgetpath.write_bytes(original)
        state['actual_post_refusals']=refusals
        telemetry_calls=[]
        def telemetry(uuid):
            telemetry_calls.append(uuid)
            return dict(own_GPU=uuid+', CPU_FIXTURE_ONLY, 0, 0',compute_apps='',GPU_telemetry_calls=1,
                CPU_FIXTURE_TELEMETRY_NOT_A_GPU_OBSERVATION=True)
        state['phase']='actual_CPU_container_scientific_terminal_collector_binding_full24';save()
        captured=collect_once(root,stage,launch,'terminal',stage/'terminal-CPU-observation',telemetry)
        assert telemetry_calls==[launch['gpu_uuid']] and captured['CPU_collector_binding']['host_verified_Docker_peer']['socket_peer_PID_matches_actual_Docker_PID'] is True
        assert captured['CPU_collector_binding']['host_verified_CPU_container_exit'] is True
        assert not any(captured['original_live_handles'].values())
        atomic(job/'CPU-fixture-terminal-capture.json',captured)
        # Keep the real observation timestamp and original launch unchanged.
        # A separate, labelled pure-function fixture covers offline acceptance
        # without waiting the real full-GPU planning ETA during a CPU check.
        control=captured['CPU_collector_binding']['fixture_offline_control']
        shutil.copyfile(stage/'terminal-CPU-observation/CPU-offline-acceptance-function-input.json',job/'CPU-offline-acceptance-function-input.json')
        assert control['registered_paths']==24 and control['formal_denominator']==18 and control['full_protocol_accepted'] is False
        assert control['all24_missing_retained'] is True and control['scored_formal_paths']==0
        state['fixture_terminal_control']=dict(capture_sha256=sha(job/'CPU-fixture-terminal-capture.json'),
            complete24_retained=True,zero_fabricated_scores=True,single_injected_telemetry_call=True,
            actual_Docker_collector_peer=captured['CPU_collector_binding']['host_verified_Docker_peer'],
            actual_CPU_collector_exit=captured['CPU_collector_binding']['host_verified_CPU_container_exit'],
            fixture_finance_formula_verified=control['finance_formula_verified'],actual_GPUh_charged=0,
            actual_observation_time_preserved=True,separate_pure_function_ETA_fixture_sha256=sha(job/'CPU-offline-acceptance-function-input.json'),
            full_neural_protocol_accepted=False)
        # Production entry cannot consume this fixture, stale budgets or an
        # old component/resource acceptance as complete production permission.
        try:validate_authorization(root,stage,{})
        except ValueError:state['actual_GPU_namespace_refused_CPU_fixture']=True
        else:raise AssertionError('GPU production entry accepted TEST_ONLY')
        state.update(status='BANK24_FULL_EXECUTION_TOOLS_CPU_PASS_NOT_NEURAL_OR_GPU',full_execution_tools_CPU_passed=True,
            original_scientific_numerical_paths_reexecuted=0,original_1789_and_extra29_reused=True,
            complete_scientific_denominator=24,actual_GPUh_charged=0,actual_authoritative_budget_opened=False)
    except BaseException as error:
        state.update(status='BANK24_FULL_EXECUTION_TOOLS_CPU_FAILURE_RETAINED',error_type=type(error).__name__)
        (job/'failure.log').write_text(traceback.format_exc())
    finally:
        if 'launch' in locals():
            for expected in [launch.get('supervisor_identity'),launch.get('post_watcher_identity')]:
                if alive(expected):os.killpg(expected['pid'],signal.SIGTERM)
        if 'support' in locals():
            state['environment_metadata_after']=support.metadata_fingerprint(project/'envs/wc-cosmos-py310-cu128-r3')
            state['runtime_critical_sources_unchanged']=all(sha(project/'runtime'/n)==v for n,v in m['runtime_source_sha256'].items())
        state.update(ended_unix=time.time(),wall_seconds=time.time()-started);save();atomic(job/'result.json',state)
        signal.alarm(0);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    return 0 if state.get('full_execution_tools_CPU_passed') else 1


if __name__=='__main__':raise SystemExit(main())
