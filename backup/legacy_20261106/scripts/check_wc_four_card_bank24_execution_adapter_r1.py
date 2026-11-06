#!/usr/bin/env python3
"""New-host execution-input and reversible SM89 adapter CPU; no GPU launch."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

import four_card_bank24_execution_adapter_r1 as adapter


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def process_cache_environment(job, username):
    return module('accepted_resource_cache',Path(job)/'resource_worker.py').process_cache_environment(job,username)


def exercise_controls(original_pool, adapted_pool):
    """Execute real reserve/settle methods against in-memory transactions only."""
    context={'__name__':'published_SM89_budget_cpu'}
    exec(compile(adapted_pool,'<reversibly-adapted-budget-pool>','exec'),context)
    base=context['BudgetPool']
    class MemoryOnlyPool(base):
        def __init__(self):
            self.value=dict(schema=context['SCHEMA'],cap_gpu_hours=226.,
                origin_used_gpu_hours=79.99637737158223,origin_gpu_jobs_launched=0,
                jobs={},events=[])
        @contextmanager
        def transaction(self):yield copy.deepcopy(self.value)
        def commit(self,value,event):
            value.update(self.accounting(value));value['events'].append(copy.deepcopy(event))
            self.value=copy.deepcopy(value)
    gpu=dict(uuid='GPU-CPU-CONTROL-ONLY',name='NVIDIA RTX 6000 Ada Generation',
        compute_cap='8.9',memory_used_mib=0,pids=[])
    job=dict(job_id='CPU-CONTROL-ONLY',gpu_uuid=gpu['uuid'],launch_id='NOT_A_DISPATCH',
        source_revision=adapter.LIFECYCLE_SOURCE,config_sha256='a'*64,
        forecast_GPUh=3.4,billed_limit_GPUh=4.5)
    checks={}
    def refused(label,call):
        try:call()
        except (ValueError,KeyError):checks[label]=True
        else:raise AssertionError('Unsafe admission accepted: '+label)
    for label,delta in [('SM86',dict(compute_cap='8.6')),('A6000',dict(name='NVIDIA RTX A6000')),
            ('occupied_zero_utilization',dict(memory_used_mib=48000)),('compute_owner',dict(pids=[123])),
            ('negative_memory',dict(memory_used_mib=-1)),('NaN_memory',dict(memory_used_mib=float('nan')))]:
        refused(label,lambda delta=delta:MemoryOnlyPool().reserve(job,{**gpu,**delta}))
    refused('whole12_requires_specific_card',lambda:MemoryOnlyPool().reserve({**job,'billed_limit_GPUh':12},gpu))
    refused('forecast_exceeds_full_limit',lambda:MemoryOnlyPool().reserve({**job,'forecast_GPUh':5},gpu))
    pool=MemoryOnlyPool();pool.reserve(job,gpu)
    checks['whole_limit_reserved_not_actual_fee']=pool.value['reserved_gpu_hours']==4.5 and pool.value['used_gpu_hours']==79.99637737158223
    refused('same_handle_replay',lambda:pool.reserve(job,gpu))
    refused('same_UUID_double_owner',lambda:pool.reserve({**job,'job_id':'SECOND'},gpu))
    poor=MemoryOnlyPool();poor.value['jobs']['PRIOR_ACTUAL']=dict(status='SETTLED',actual_GPUh=145.)
    refused('insufficient_whole_balance',lambda:poor.reserve(job,gpu))
    pool.settle(job['job_id'],1.25,'b'*64)
    checks['additive_actual_and_release']=pool.value['used_gpu_hours']==81.24637737158223 and pool.value['reserved_gpu_hours']==0
    unchanged=copy.deepcopy(pool.value);pool.settle(job['job_id'],1.25,'b'*64)
    checks['same_settlement_idempotent']=pool.value==unchanged
    refused('conflicting_actual',lambda:pool.settle(job['job_id'],1.5,'b'*64))
    # Failure/stop still bills the actual whole wall; no free technical probe.
    stopped=MemoryOnlyPool();stopped.reserve(job,gpu);stopped.settle(job['job_id'],.02,'c'*64)
    checks['failed_start_has_additive_actual_fee']=stopped.value['used_gpu_hours']==80.01637737158223
    for key in ['full_new_host_scope_production_CPU_accepted','container_supervisor_and_terminal_lifecycle_accepted',
                'whole_card_new_host_quote_accepted','single_authoritative_v2_handoff_accepted']:
        refused('missing_'+key,lambda key=key:adapter.require_gpu_prerequisites({key:False}))
    original_context={'__name__':'original_budget_cpu'}
    exec(compile(original_pool,'<original-budget-pool>','exec'),original_context)
    require_fields=base.accounting(pool.value)==original_context['BudgetPool'].accounting(pool.value)
    checks['unchanged_accounting_on_same_full_history']=require_fields
    adapter.require(all(checks.values()), 'Full execution/finance controls required')
    return dict(checks=checks,actual_GPU_ledger_opened=False,ledger_written=False,
                filesystem_transactions_executed=0,actual_reservations=0,
                all_finance_controls='IN_MEMORY_TEST_ONLY_NOT_CURRENT_AUTHORITY')


def probe_source(job):
    return '''import json,sys
from pathlib import Path
job=Path(JOB)
sys.path.insert(0,str(job))
import torch
def forbidden(*a,**kw):raise RuntimeError('Adapter CPU prohibits weights, CUDA and downloads')
torch.load=forbidden;torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
import four_card_bank24_execution_adapter_r1 as a
from check_wc_four_card_bank24_execution_adapter_r1 import exercise_controls
metadata=a.read(job/'execution-metadata-registration.json')
verified=a.verify_inputs(job/'inputs',metadata['original_payload_sha256'],metadata['additional_metadata_sha256'])
data,real=a.reconstruct(job/'inputs')
bundle,binding=a.generated_bundle(job/'inputs')
generated=job/'generated';generated.mkdir()
for name,body in bundle.items():(generated/name).write_text(body)
original=(job/'inputs/src/wcomr/gpu_budget_pool_v2.py').read_text()
controls=exercise_controls(original,bundle['bank24_sm89_budget_pool.py'])
assert not torch.cuda.is_initialized()
print(json.dumps(dict(verified=verified,real_inputs=real,binding=binding,controls=controls,
 generated_sha256={n:a.digest(v.encode()) for n,v in bundle.items()},
 remaining=a.REMAINING,full_new_host_scope_production_CPU_accepted=False,
 actual_CUDA_compatibility_accepted=False,whole_card_new_host_quote_accepted=False,
 GPU_dispatch_ready=False,Cosmos_weights_loaded=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)))
print('BANK24_SM89_REAL_INPUTS_AND_REVERSIBLE_ADAPTER_CPU_OK')
'''.replace('JOB',repr(str(job)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True,type=Path)
    args=parser.parse_args();job=args.manifest.parent;m=adapter.read(args.manifest)
    resource=module('existing_resource_cpu_contract',job/'resource_worker.py')
    support=module('existing_environment_identity',job/'repair_support.py')
    root=Path(m['workspace']);started=time.time()
    state=dict(status='BANK24_SM89_EXECUTION_ADAPTER_CPU_RUNNING',source_revision=m['source_revision'],
        worker_sha256=adapter.digest(Path(__file__).read_bytes()),commands=[],started_unix=started,
        full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False,
        Cosmos_weights_loaded=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)
    def save():state['updated_unix']=time.time();resource.atomic(job/'health.json',state)
    try:
        with (job/'worker-once.json').open('x') as stream:json.dump(dict(source_revision=m['source_revision']),stream)
        assert state['worker_sha256']==m['worker_sha256']
        assert all(adapter.digest((job/n).read_bytes())==h for n,h in m['payload_sha256'].items())
        assert not list(Path('/dev').glob('nvidia*'))
        state['process_identity_and_cache']=resource.verify_process_cache_environment(job,m['container_process_user_name'])
        env=root/'envs/wc-cosmos-py310-cu128-r3'
        state['environment_metadata_before']=support.metadata_fingerprint(env)
        assert state['environment_metadata_before']==m['environment_metadata_sha256']
        assert all(adapter.digest((root/'runtime'/n).read_bytes())==h for n,h in m['runtime_source_sha256'].items())
        proof=adapter.read(job/'frontend-accepted.json')
        assert proof['host_boundary_CPU_accepted'] is True and all(proof['checks'].values())
        previous=Path(m['upstream_frontend_job'])
        assert adapter.digest((previous/'result.json').read_bytes())==m['upstream_frontend_result_sha256']
        assert adapter.digest((previous/'manifest.json').read_bytes())==m['upstream_frontend_manifest_sha256']
        state['phase']='real_execution_metadata_and_reversible_SM89_lifecycle_components';save()
        probe=job/'adapter-CPU-probe.py';probe.write_text(probe_source(job));begin=time.time()
        with (job/'adapter-CPU-probe.log').open('xb') as log:
            run=subprocess.run([sys.executable,str(probe)],stdout=log,stderr=subprocess.STDOUT,timeout=600)
        text=(job/'adapter-CPU-probe.log').read_text(errors='replace')
        marker='BANK24_SM89_REAL_INPUTS_AND_REVERSIBLE_ADAPTER_CPU_OK'
        state['commands'].append(dict(exit_code=run.returncode,wall_seconds=time.time()-begin,
            exact_marker=marker in text.splitlines(),probe_source_sha256=adapter.digest(probe.read_bytes())))
        save();assert run.returncode==0 and marker in text.splitlines()
        rows=[json.loads(line) for line in text.splitlines() if line.startswith('{') and '"real_inputs"' in line]
        assert len(rows)==1;state['execution_adapter_CPU']=rows[0]
        state.update(status=adapter.ADAPTER_STATUS,execution_adapter_CPU_passed=True,
            phase='CPU_complete_remaining_container_supervisor_terminal_quote_and_authority',remaining=adapter.REMAINING)
    except BaseException as error:
        state.update(status='BANK24_SM89_EXECUTION_ADAPTER_CPU_FAILURE_RETAINED',error_type=type(error).__name__)
        (job/'failure.log').write_text(traceback.format_exc())
    finally:
        state['environment_metadata_after']=support.metadata_fingerprint(root/'envs/wc-cosmos-py310-cu128-r3')
        state['runtime_critical_sources_unchanged']=all(adapter.digest((root/'runtime'/n).read_bytes())==h for n,h in m['runtime_source_sha256'].items())
        state.update(ended_unix=time.time(),wall_seconds=time.time()-started);save();resource.atomic(job/'result.json',state)
    return 0 if state.get('execution_adapter_CPU_passed') else 1


if __name__=='__main__':raise SystemExit(main())
