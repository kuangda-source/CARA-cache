#!/usr/bin/env python3
"""Actual CPU container transport/failure/post controls, never neural paths."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from four_card_bank24_container_transport_r1 import (receive,run_inherited,retain_full_rows,atomic,identity,socket_path)
from four_card_bank24_gpu_port_r1 import generate,full_quote,require_full_CPU,validate_handoff,sha,read


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def process_cache_environment(job,username):
    return load('accepted_process_cache',Path(job)/'resource_worker.py').process_cache_environment(job,username)


def child_probe_source():
    return '''import fcntl,json,os,sys,time
from pathlib import Path
kind,directory,lease,namespace=sys.argv[1:]
directory=Path(directory);fd=int(os.environ['WC_LOCK_FD'])
assert os.getppid()==int(os.environ['WC_SUPERVISOR_PID'])
assert str(Path('/proc/self/fd/%d'%fd).resolve())==lease
assert os.readlink('/proc/self/ns/pid')==namespace
stat=os.fstat(fd)
with Path(lease).open('r') as second:
 try:fcntl.flock(second,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:pass
 else:raise AssertionError('Original host lease was not inherited')
plan=json.loads((directory/'plan.json').read_text());actual=[]
for row in plan:
 if kind=='timeout':time.sleep(30)
 actual.append(dict(row,status='CPU_CONTROL_VISITED_NOT_NEURAL_OUTPUT'))
 value=dict(kind=kind,child_pid=os.getpid(),parent_pid=os.getppid(),lease_device=stat.st_dev,lease_inode=stat.st_ino,
  actual=actual,CUDA_initialized=False,GPU_submissions=0,scientific_outputs_created=0)
 (directory/'child-result.json').write_text(json.dumps(value))
 if kind=='failure' and len(actual)==3:sys.exit(7)
'''


def negative_post_source(job,fixture_project,stage):
    return '''import json,os,runpy,sys
from pathlib import Path
job=Path(JOB);sys.path[:0]=[str(job/'generated'),str(job),str(job/'inputs/src')]
os.environ['WC_SCOUT_KIND']='BANK24'
import torch
def forbidden(*a,**k):raise RuntimeError('Negative post fixture cannot load tensors, models or CUDA')
torch.load=forbidden;torch.cuda._lazy_init=forbidden
import bank24_fourcard_lifecycle_r1 as contract
config=json.loads((job/'inputs/configs/wc_scout_bank24_production_entry_r1_20261018.json').read_text())
# Mock only the dependency boundary, never post arithmetic, rows or results.
# Positive admission is tested separately to REFUSE without actual full CPU.
contract.bound_dependency=lambda *args:(dict(entry_source_revision='CPU_FIXTURE_ONLY_NOT_GPU',entry_registration_sha256='CPU_FIXTURE_ONLY'),config,dict(source_revision='CPU_FIXTURE_ONLY_NOT_GPU'),None,None)
sys.argv=['negative-post','--project',PROJECT,'--stage',STAGE]
runpy.run_path(str(job/'generated/bank24-fourcard-post.py'),run_name='__main__')
assert not torch.cuda.is_initialized()
'''.replace('JOB',repr(str(job))).replace('PROJECT',repr(str(fixture_project))).replace('STAGE',repr(str(stage)))
def negative_post_probe(job,generated,planned,fixture_project,finished_child):
    stage=job/'post-failure-fixture';stage.mkdir()
    root=fixture_project/'outputs/wc-scout-dev6-paired-native-full24-r1';root.mkdir(parents=True)
    # A documented negative fixture: zero neural outputs and no quality fields.
    atomic(root/'runner.json',dict(source_revision='CPU_FIXTURE_ONLY_NOT_GPU',runs=[],request_memory_records=[]))
    atomic(root/'supervisor.json',dict(status='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',
        supervisor_identity=finished_child,child_identity=None,runner_sha256=sha(root/'runner.json'),child_exit_code=7))
    atomic(stage/'registration.json',dict(source_revision='CPU_FIXTURE_ONLY_NOT_GPU'))
    probe=job/'negative-post-probe.py';probe.write_text(negative_post_source(job,fixture_project,stage))
    with (job/'negative-post-probe.log').open('x') as log:
        call=subprocess.run([sys.executable,str(probe)],stdout=log,stderr=subprocess.STDOUT,timeout=120)
    assert call.returncode==0
    final=read(stage/'CPU-final-results.json')
    assert len(final['rows'])==24 and all(r['status']=='NOT_REACHED_RETAINED' for r in final['rows'])
    assert final['accepted_video_paths']==final['scored_formal_paths']==0
    assert all('LPIPS' not in r and 'final_latent_sha256' not in r for r in final['rows'])
    return dict(status='REAL_PUBLISHED_POST_NEGATIVE_PATH_FULL24_NO_SCORES',exit_code=call.returncode,
        probe_sha256=sha(probe),post_source_sha256=sha(generated/'bank24-fourcard-post.py'),
        registered_paths=24,formal_denominator=18,all_missing_retained=True,actual_neural_paths=0,
        actual_93_RGB_or_LPIPS_verified=False,quality_fields_fabricated=False,
        explicit_dependency_mock_only=True,scored_formal_paths=0,CPU_final_sha256=sha(stage/'CPU-final-results.json'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    job=a.manifest.parent;m=read(a.manifest);root=Path(m['workspace']);started=time.time()
    resource=load('accepted_resource_contract',job/'resource_worker.py');support=load('accepted_environment_metadata',job/'repair_support.py')
    state=dict(status='BANK24_CROSS_CONTAINER_LIFECYCLE_CPU_RUNNING',source_revision=m['source_revision'],
        worker_identity=identity(os.getpid()),started_unix=started,commands=[],GPU_submissions=0,ledger_written=False,
        actual_authoritative_ledger_opened=False,actual_GPU_UUID_leased=False,Cosmos_weights_loaded=0,CUDA_initialized=False,
        full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False)
    def save():state['updated_unix']=time.time();atomic(job/'health.json',state)
    fd=None
    try:
        with (job/'worker-once.json').open('x') as out:json.dump(dict(source_revision=m['source_revision']),out)
        assert sha(__file__)==m['worker_sha256'] and all(sha(job/n)==v for n,v in m['payload_sha256'].items())
        assert not list(Path('/dev').glob('nvidia*'))
        state['process_identity_and_cache']=resource.verify_process_cache_environment(job,m['container_process_user_name'])
        env=root/'envs/wc-cosmos-py310-cu128-r3'
        state['environment_metadata_before']=support.metadata_fingerprint(env)
        assert state['environment_metadata_before']==m['environment_metadata_sha256']
        assert all(sha(root/'runtime'/n)==v for n,v in m['runtime_source_sha256'].items())
        previous=Path(m['upstream_component_job'])
        assert sha(previous/'result.json')==m['upstream_component_result_sha256'] and sha(previous/'manifest.json')==m['upstream_component_manifest_sha256']
        accepted=read(job/'component-accepted.json');assert accepted['execution_adapter_CPU_accepted'] and all(accepted['checks'].values())
        state['phase']='actual_host_to_container_original_FD_and_PID_contract';save()
        fd,receipt=receive(socket_path(job),m['CPU_transport_nonce'],sha(a.manifest))
        state['actual_host_to_container_FD']=receipt
        assert receipt['peer_identity']['pid']==os.getpid() and receipt['container_actual_pid_mode']=='host'
        assert receipt['container_actual_readonly_root'] is True and not receipt['container_devices'] and not receipt['container_device_requests']
        os.environ['WC_SCOUT_KIND']='BANK24';sys.path.insert(0,str(job/'inputs/src'))
        bodies,binding=generate(job/'inputs');generated=job/'generated';generated.mkdir()
        for name,body in bodies.items():(generated/name).write_text(body)
        state['generated_sha256']={n:sha(generated/n) for n in bodies};state['port_binding']=binding
        config=read(job/'inputs/configs/wc_scout_bank24_production_entry_r1_20261018.json')
        original_quote=read(job/'inputs/reports/wc_scout_BANK24_whole_quote_R1_20261018.json')
        quote=full_quote(original_quote,config['scope_counts']);atomic(job/'whole24-planning-quote.json',quote)
        state['whole24_planning_quote']=quote
        planned=quote['positions'];state['scope_counts']=config['scope_counts']
        pool_module=load('actual_generated_budget_methods',generated/'bank24_sm89_budget_pool.py')
        fixture=job/'TEST_ONLY';(fixture/'reports').mkdir()
        initial=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=79.99637737158223,
            origin_gpu_jobs_launched=0,jobs={},events=[],CPU_FIXTURE_ONLY_NOT_AUTHORITY=True)
        initial.update(pool_module.BudgetPool.accounting(initial));atomic(fixture/'reports/gpu-budget-v2.json',initial)
        pool=pool_module.BudgetPool(fixture);child_source=job/'CPU-child.py';child_source.write_text(child_probe_source())
        scenarios=[];state['phase']='actual_inherited_FD_children_success_failure_timeout_and_additive_fixture';save()
        for kind in ['normal','failure','timeout']:
            directory=fixture/kind;directory.mkdir();atomic(directory/'plan.json',planned)
            job_id='wc-scout-dev6-paired-native-full24-r1'+('' if kind=='normal' else '-'+kind)
            fake_gpu=dict(uuid='GPU-CPU-LIFECYCLE-PROBE',name='NVIDIA RTX 6000 Ada Generation',compute_cap='8.9',memory_used_mib=0,pids=[])
            fake_job=dict(job_id=job_id,gpu_uuid=fake_gpu['uuid'],launch_id='CPU-FIXTURE-'+kind,
                source_revision=m['source_revision'],config_sha256=sha(job/'inputs/configs/wc_scout_bank24_production_entry_r1_20261018.json'),
                forecast_GPUh=3.4,billed_limit_GPUh=4.5,CPU_FIXTURE_ONLY_NOT_ACTUAL_GPU=True)
            pool.reserve(fake_job,fake_gpu)
            command=[sys.executable,str(child_source),kind,str(directory),receipt['path'],receipt['host_pid_namespace']]
            with (directory/'child.log').open('x') as log:
                outcome=run_inherited(command,fd,dict(os.environ,CUDA_VISIBLE_DEVICES=''),.6 if kind=='timeout' else 20,log)
            rows=read(directory/'child-result.json')['actual'] if (directory/'child-result.json').is_file() else []
            complete=retain_full_rows(planned,rows)
            assert len(complete)==24 and outcome['child_exited']
            assert outcome['exit_code']==(0 if kind=='normal' else 7) if kind!='timeout' else outcome.get('owned_timeout_stop') is True
            assert len(rows)==(24 if kind=='normal' else 3 if kind=='failure' else 0)
            bill=dict(CPU_FIXTURE_ONLY_NOT_ACTUAL_GPU=True,fixture_wall_seconds=outcome['wall_seconds'],
                fixture_wall_divided_by3600=outcome['wall_seconds']/3600,actual_GPUh_charged=0)
            atomic(directory/'fixture-billing.json',bill);pool.settle(job_id,bill['fixture_wall_divided_by3600'],sha(directory/'fixture-billing.json'))
            scenarios.append(dict(kind=kind,subprocess=outcome,visited_slots=len(rows),retained_slots=len(complete),
                missing_slots=sum(r['status']=='NOT_REACHED_RETAINED' for r in complete),
                fixture_bill=bill,scientific_outputs_created=0))
        state['scenarios']=scenarios
        budget=pool.read();assert budget['reserved_gpu_hours']==0
        assert abs(budget['used_gpu_hours']-79.99637737158223-sum(r['fixture_bill']['fixture_wall_divided_by3600'] for r in scenarios))<1e-12
        state['fixture_budget_summary']=dict(fixture_only=True,test_fixture_budget_JSON_written=True,settled_fixture_jobs=len(budget['jobs']),
            whole_reservations_released=True,additive_actual_wall_formula_verified=True,
            actual_authoritative_budget_opened=False,actual_GPUh_charged=0)
        state['phase']='published_post_full24_failure_retention_and_real_admission_refusals';save()
        state['post_negative_path']=negative_post_probe(job,generated,planned,fixture,scenarios[0]['subprocess']['child_identity'])
        refused=[]
        for name,call in [('missing_full_CPU',lambda:require_full_CPU(job,m['source_revision'])),
                          ('missing_authoritative_handoff',lambda:validate_handoff(root,{}))]:
            try:call()
            except (ValueError,FileNotFoundError):refused.append(name)
            else:raise AssertionError('Incomplete actual GPU admission accepted')
        state['actual_admission_refusals']=refused
        state.update(status='BANK24_CROSS_CONTAINER_LIFECYCLE_CPU_PASS_NOT_GPU_OR_FULL_DISPATCH_PORT',
            container_lifecycle_CPU_passed=True,remaining=['portable_GPU_dispatch_and_post_watcher_cli_binding',
                'actual_scientific_terminal_collector_container_binding','full_new_host_scope_CPU_acceptance',
                'actual_CUDA_compatibility','actual_new_host_measured_prices','single_authoritative_v2_handoff'])
    except BaseException as error:
        state.update(status='BANK24_CROSS_CONTAINER_LIFECYCLE_CPU_FAILURE_RETAINED',error_type=type(error).__name__)
        (job/'failure.log').write_text(traceback.format_exc())
    finally:
        if fd is not None:os.close(fd)
        state['environment_metadata_after']=support.metadata_fingerprint(root/'envs/wc-cosmos-py310-cu128-r3')
        state['runtime_critical_sources_unchanged']=all(sha(root/'runtime'/n)==v for n,v in m['runtime_source_sha256'].items())
        state.update(ended_unix=time.time(),wall_seconds=time.time()-started);save();atomic(job/'result.json',state)
    return 0 if state.get('container_lifecycle_CPU_passed') else 1


if __name__=='__main__':raise SystemExit(main())
