#!/usr/bin/env python3
"""Actual new-host CPU frontend checks; never claims a ported GPU lifecycle."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from four_card_bank24_host_contract_r1 import read, digest, legacy_bindings, quote_inventory


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_cache_environment(job, username):
    return load('existing_resource_process_contract', Path(job)/'resource_worker.py').process_cache_environment(job, username)


def integration_source(job, guarded=None):
    prefix = '''import json,os,sys
from pathlib import Path
job=Path(JOB)
sys.path.insert(0,str(job/'closure/src'))
os.environ['WC_SCOUT_KIND']='BANK24'
'''.replace('JOB', repr(str(job)))
    if guarded is None:
        resource = load('frozen_resource_guard_source', job/'resource_worker.py')
        guarded = resource.guarded_source((job/'repair_support.py').read_text())
    body = '''
import copy
from types import SimpleNamespace
from cosmos_predict2.config import InferenceArguments,SetupArguments
from wcomr import scout_production_entry_r1 as entry
from wcomr.scout_production_entry_adapter_r1 import adapt
c=json.loads((job/'closure/configs/wc_scout_bank24_production_entry_r1_20261018.json').read_text())
entry.validate_contract(c)
source=(job/'closure/scripts/run_wc_drop1_full18_r1.py').read_text()
adapted=adapt(source)
compile(adapted,'<unchanged-frozen-scout-adaptation>','exec')
assert 'torch.cuda.get_device_capability()==(8,6)' in adapted
samples=[InferenceArguments(**r) for r in c['requests']]
for sample,request in zip(samples,c['requests']):
 assert all(sample.model_dump(mode='json')[k]==v for k,v in request.items())
setupdata=json.loads((job/'closure/configs/f1_setup.json').read_text())
setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(job/'NEVER_CREATED')})
assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
rows=entry.matrix([s.name for s in samples])
assert len(rows)==24
refusals=[]
for row in rows:
 sample=next(s for s in samples if s.name==row['scene'])
 dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
 try:
  entry.execute(dummy,sample,row['method'],table_parameters=None,previous_parameters=None,
   runtime=job/'closure/runtime',wc=None,rf=None,settings={},calibration=None,specs=None,
   inference_module=None,output=job/'NEVER_CREATED',expected_shape=None,
   audit=row['section']=='WARMUP',observer=row['observer'])
 except ValueError as error:assert str(error)=='Ordinary guardrails required'
 else:raise AssertionError('Unprotected original execution entry was accepted')
 refusals.append(row['id'])
mutations={'scope_counts':{**entry.COUNTS,'formal_paths':17},'methods':c['methods'][:-1],
 'A_method':'W1_ONE_PHASE','P_enabled':True,'F_B_enabled':True,'online_teachers':True,
 'training':True,'autonomy_exclusive_upper_GPUh':8,'cumulative_cap_GPUh':77.,
 'billed_limit_GPUh':12.,'timing_claim':'CLEAN_LATENCY',
 'plans':{**c['plans'],'A21':['D']*36}}
for key,value in mutations.items():
 bad=copy.deepcopy(c);bad[key]=value
 try:entry.validate_contract(bad)
 except ValueError:pass
 else:raise AssertionError('Frozen production scope mutation accepted: '+key)
assert not torch.cuda.is_initialized() and not (job/'NEVER_CREATED').exists()
print(json.dumps(dict(real_Cosmos_requests=6,full_matrix_positions=len(rows),matrix=rows,
 guard_refusals=refusals,scope_mutations_refused=list(mutations),
 frozen_original_runner_adaptation_compiled=True,
 original_runner_SM86_constraint_retained_and_explicit=True,
 GPU_runner_port_accepted=False,new_host_scope_production_CPU_accepted=False,
 model_weights_loaded=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)))
print('BANK24_FOUR_CARD_FROZEN_FRONTEND_CPU_BOUNDARY_OK')
'''
    return prefix+guarded+'\n'+body


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,required=True)
    args=parser.parse_args();job=args.manifest.parent;m=read(args.manifest)
    root=Path(m['workspace']);begin=time.time()
    support=load('existing_metadata_contract',job/'repair_support.py')
    resource=load('existing_process_contract',job/'resource_worker.py')
    state=dict(status='BANK24_NEW_HOST_CPU_BOUNDARY_RUNNING',source_revision=m['source_revision'],
        worker_sha256=digest(Path(__file__).read_bytes()),manifest_sha256=digest(args.manifest.read_bytes()),
        commands=[],started_unix=begin,GPU_submissions=0,ledger_written=False,
        Cosmos_weights_loaded=0,CUDA_initialized=False,new_host_scope_production_CPU_accepted=False,
        actual_CUDA_compatibility_accepted=False,GPU_dispatch_ready=False)
    def save():
        state['updated_unix']=time.time()
        resource.atomic(job/'health.json',state)
    try:
        with (job/'worker-once.json').open('x') as stream:json.dump(dict(source_revision=m['source_revision']),stream)
        assert state['worker_sha256']==m['worker_sha256']
        assert all(digest((job/n).read_bytes())==h for n,h in m['payload_sha256'].items())
        assert not list(Path('/dev').glob('nvidia*'))
        state['process_identity_and_cache']=resource.verify_process_cache_environment(job,m['container_process_user_name'])
        env=root/'envs/wc-cosmos-py310-cu128-r3'
        state['environment_metadata_before']=support.metadata_fingerprint(env)
        assert state['environment_metadata_before']==m['environment_metadata_sha256']
        assert all(digest((root/'runtime'/n).read_bytes())==h for n,h in m['runtime_source_sha256'].items())
        previous=Path(m['upstream_resource_job'])
        assert digest((previous/'result.json').read_bytes())==m['upstream_resource_result_sha256']
        assert digest((previous/'manifest.json').read_bytes())==m['upstream_resource_manifest_sha256']
        accepted=read(job/'resource-accepted.json')
        assert accepted['offline_environment_resources_accepted'] is True and all(accepted['checks'].values())
        state['phase']='all1789_frozen_dependency_files_and_original_gate';save()
        cap=read(job/'legacy-CPU-capture.json.gz');old=read(job/'legacy-CPU-accepted.json')
        entry=read(job/'closure/reports/wc_scout_BANK24_real_entry_CPU_R1_collection_20261018.json.gz')
        config=read(job/'closure/configs/wc_scout_bank24_production_entry_r1_20261018.json')
        assert old['capture_sha256']==digest((job/'legacy-CPU-capture.json.gz').read_bytes())
        state['legacy_bindings']=legacy_bindings(cap,old,entry,read(job/'frozen-gate.json'),config)
        actual={n:digest((job/'closure'/n).read_bytes()) for n in cap['registration']['payload_sha256']}
        assert actual==cap['registration']['payload_sha256']
        state['frozen_dependency_files_verified']=len(actual)
        state['entry_dependency_files_verified']=len(entry['registration']['payload_sha256'])
        state['full_closure_sha256']=digest(json.dumps(actual,sort_keys=True).encode())
        state['phase']='six_real_requests_and24_guarded_frontend_positions';save()
        source=integration_source(job);probe=job/'bank24-host-frontend-probe.py';probe.write_text(source)
        started=time.time()
        with (job/'bank24-host-frontend-probe.log').open('xb') as output:
            run=subprocess.run([sys.executable,str(probe)],stdout=output,stderr=subprocess.STDOUT,timeout=600)
        text=(job/'bank24-host-frontend-probe.log').read_text(errors='replace')
        marker='BANK24_FOUR_CARD_FROZEN_FRONTEND_CPU_BOUNDARY_OK'
        command=dict(phase=state['phase'],exit_code=run.returncode,wall_seconds=time.time()-started,
            exact_marker=marker in text.splitlines(),probe_source_sha256=digest(probe.read_bytes()))
        state['commands'].append(command);save();assert run.returncode==0 and command['exact_marker']
        results=[json.loads(line) for line in text.splitlines() if line.startswith('{') and '"real_Cosmos_requests"' in line]
        assert len(results)==1;state['actual_frontend_CPU']=results[0]
        state['whole_quote_inventory']=quote_inventory(config,results[0]['matrix'],
            read(job/'closure/reports/wc_scout_BANK24_whole_quote_R1_20261018.json'))
        state.update(status='BANK24_NEW_HOST_FRONTEND_CPU_BOUNDARY_PASS_REMAINING_LIFECYCLE_AND_PRICE_GATES',
            host_boundary_CPU_passed=True,old_scientific_sources_modified=False,
            numerical_CPU_paths_reexecuted=0,legacy_production_CPU_reexecuted=False,
            remaining=['new_host_GPU_lifecycle_and_SM89_port_CPU','real_CUDA_compatibility',
                       'whole_card_new_host_measured_quote','single_authoritative_v2_handoff'])
    except BaseException as error:
        state.update(status='BANK24_NEW_HOST_CPU_BOUNDARY_FAILURE_RETAINED',error_type=type(error).__name__)
        (job/'failure.log').write_text(traceback.format_exc())
    finally:
        state['environment_metadata_after']=support.metadata_fingerprint(root/'envs/wc-cosmos-py310-cu128-r3')
        state['environment_metadata_unchanged']=state.get('environment_metadata_before')==state['environment_metadata_after']
        state['runtime_critical_sources_unchanged']=all(digest((root/'runtime'/n).read_bytes())==h for n,h in m['runtime_source_sha256'].items())
        state.update(ended_unix=time.time(),wall_seconds=time.time()-begin);save();resource.atomic(job/'result.json',state)
    return 0 if state.get('host_boundary_CPU_passed') else 1


if __name__=='__main__':raise SystemExit(main())
