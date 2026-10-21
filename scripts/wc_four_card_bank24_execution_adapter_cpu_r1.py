#!/usr/bin/env python3
"""Single-dispatch CPU verification of a separate BANK24 SM89 host adapter."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import time

from four_card_bank24_execution_adapter_r1 import (ADAPTER_STATUS,REMAINING,WORKSPACE,
    digest,read,require,generated_bundle,reconstruct)
from wc_four_card_resource_cpu_r4 import ssh,write
from wc_four_card_bank24_host_cpu_r1 import CAPTURE as HOST_CAPTURE

RUN='wc-fourcard-bank24-execution-adapter-cpu-r1-20261022'
LOCAL=Path('.sync/four-card-bank24-execution-adapter-r1-20261022')
RECIPE=Path('manifests/wc_four_card_bank24_execution_adapter_cpu_r1_20261022.json')
METADATA='manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json'
FRONT='reports/wc_four_card_BANK24_host_CPU_R1_'
PAYLOADS={'worker.py':'scripts/check_wc_four_card_bank24_execution_adapter_r1.py',
    'check_wc_four_card_bank24_execution_adapter_r1.py':'scripts/check_wc_four_card_bank24_execution_adapter_r1.py',
    'supervisor.py':'scripts/supervise_wc_four_card_resource_cpu_r4.py',
    'resource_worker.py':'scripts/finish_wc_four_card_resources_cpu_r4.py',
    'repair_support.py':'scripts/repair_wc_four_card_environment_r2.py',
    'four_card_bank24_execution_adapter_r1.py':'scripts/four_card_bank24_execution_adapter_r1.py',
    'four_card_bank24_host_contract_r1.py':'scripts/four_card_bank24_host_contract_r1.py',
    'execution-metadata-registration.json':METADATA,
    'frontend-accepted.json':FRONT+'independent_acceptance_20261022.json'}


def sha(path):return digest(Path(path).read_bytes())


def freeze():
    require(not RECIPE.exists(),'Existing CPU recipe must remain immutable')
    cap=read(FRONT+'terminal_20261022.json');accepted=read(FRONT+'independent_acceptance_20261022.json')
    require(accepted['host_boundary_CPU_accepted'] and all(accepted['checks'].values()),'Actual independently accepted frontend required')
    require(accepted['capture_sha256']==sha(FRONT+'terminal_20261022.json'),'Frontend capture identity differs')
    metadata=read(METADATA);m=cap['manifest']
    import sys
    sys.path.insert(0,'.venv/lib/python3.9/site-packages')
    inputs,expected=reconstruct(LOCAL/'inputs');bundle,binding=generated_bundle(LOCAL/'inputs')
    recipe=dict(version='BANK24_FOUR_CARD_REAL_INPUTS_SM89_EXECUTION_ADAPTER_CPU_R1',
        workspace=WORKSPACE,run_id=RUN,CPU_scope='REAL_METADATA_AND_REVERSIBLE_SM89_COMPONENTS_NOT_CONTAINER_GPU_LIFECYCLE',
        scope_counts=expected['scope_counts'],frozen_scientific_lifecycle_source=metadata['source_revision'],
        frozen_scientific_entry_source='c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9',
        metadata_registration_ref=METADATA,metadata_registration_sha256=sha(METADATA),
        metadata_archive_sha256=metadata['metadata_archive_sha256'],metadata_archive_bytes=metadata['metadata_archive_bytes'],
        upstream_frontend_job=cap['launch']['job'],upstream_frontend_source=cap['launch']['source_revision'],
        upstream_frontend_result_sha256=digest((json.dumps(cap['result'],indent=2)+'\n').encode()),
        upstream_frontend_manifest_sha256=cap['manifest_sha256'],
        frontend_acceptance_ref=FRONT+'independent_acceptance_20261022.json',
        frontend_acceptance_sha256=sha(FRONT+'independent_acceptance_20261022.json'),
        expected_real_inputs=expected,expected_generated_sha256={n:digest(b.encode()) for n,b in bundle.items()},
        expected_adaptation_binding=binding,remaining=REMAINING,
        environment_metadata_sha256=m['environment_metadata_sha256'],runtime_source_sha256=m['runtime_source_sha256'],
        container_image_id=m['container_image_id'],container_process_user_name='gaokuangda',
        offline_only=True,torch_cache_readonly=True,resume_completed_resolver=True,explicit_process_identity_cache=True,
        CPU_limit=2,memory_limit_GiB=16,planning_seconds=180,maximum_wall_seconds=900,
        halfway_after_start_seconds=60,terminal_after_start_seconds=300,
        old_numerical_or_frontend_or_resource_CPU_reexecution=False,full_new_host_scope_production_CPU_accepted=False,
        actual_CUDA_compatibility_accepted=False,whole_card_new_host_quote_accepted=False,
        GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)
    write(RECIPE,recipe)
    return dict(status='BANK24_SM89_ADAPTER_CPU_RECIPE_FROZEN_NOT_DISPATCHED',recipe_ref=str(RECIPE),
        original_files=1789,additional_metadata_files=metadata['additional_metadata_files'],
        real_input_fingerprint=expected['input_evidence_fingerprint'],GPU_submissions=0)


SETUP=r'''
import base64,fcntl,gzip,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);m=d['manifest'];root=Path(m['workspace']);job=root/'bootstrap'/m['run_id']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if job.exists():
 print(json.dumps(dict(status='EXISTING_STAGE_RESTORE_ONLY',job=str(job),launch=json.loads((job/'launch.json').read_text()) if (job/'launch.json').is_file() else None)));sys.exit(0)
assert job.name=='wc-fourcard-bank24-execution-adapter-cpu-r1-20261022' and job.parent.resolve()==(root/'bootstrap').resolve()
free=shutil.disk_usage(root).free
memory=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert free>=128*(1<<30) and memory>=18*(1<<30)
previous=Path(m['upstream_frontend_job'])
assert previous.resolve().parent==(root/'bootstrap').resolve() and previous.name=='wc-fourcard-bank24-host-cpu-r1-20261022'
assert sha(previous/'manifest.json')==m['upstream_frontend_manifest_sha256'] and sha(previous/'result.json')==m['upstream_frontend_result_sha256']
assert json.loads((previous/'result.json').read_text())['host_boundary_CPU_passed'] is True
assert json.loads((previous/'manifest.json').read_text())['source_revision']==m['upstream_frontend_source']
assert json.loads((previous/'supervisor-result.json').read_text())['exit_code']==0
old=subprocess.run(['docker','inspect',previous.name,'--format','{{.State.Running}}'],capture_output=True,text=True,timeout=20)
assert old.returncode!=0 or old.stdout.strip()=='false'
image=subprocess.run(['docker','image','inspect',m['container_image_id'],'--format','{{.Id}}'],capture_output=True,text=True,timeout=20)
assert image.returncode==0 and image.stdout.strip()==m['container_image_id']
lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files={n:base64.b64decode(v) for n,v in d['files'].items()}
assert all(Path(n).name==n for n in files) and {n:hashlib.sha256(b).hexdigest() for n,b in files.items()}==m['payload_sha256']
metadata=json.loads(files['execution-metadata-registration.json'])
assert metadata['original_denominator']==1789 and len(metadata['original_payload_sha256'])==1789
closure={}
for name,expected in metadata['original_payload_sha256'].items():
 path=previous/'closure'/name
 assert not path.is_symlink() and path.resolve().is_relative_to((previous/'closure').resolve())
 body=path.read_bytes();assert hashlib.sha256(body).hexdigest()==expected;closure[name]=body
encoded=base64.b64decode(d['metadata_archive'])
assert len(encoded)==m['metadata_archive_bytes'] and hashlib.sha256(encoded).hexdigest()==m['metadata_archive_sha256']
namespace={};exec(compile(files['four_card_bank24_host_contract_r1.py'],'<published-safe-archive-contract>','exec'),namespace)
extra=namespace['archive_members'](encoded,metadata['additional_metadata_sha256'])
assert not set(closure).intersection(extra)
job.mkdir(mode=0o700)
for name,body in files.items():(job/name).write_bytes(body)
for name,body in {**closure,**extra}.items():
 target=job/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
manifest=job/'manifest.json';manifest.write_text(json.dumps(m,indent=2)+'\n');fingerprint=sha(manifest)
(job/'dispatch-fence.json').write_text(json.dumps(dict(source_revision=m['source_revision'],manifest_sha256=fingerprint,created_unix=time.time()))+'\n')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close();started=time.time()
with (job/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(job/'supervisor.py'),'--manifest',str(manifest)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=job)
stat=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
launch=dict(status='FOUR_CARD_BANK24_EXECUTION_ADAPTER_CPU_SINGLE_DISPATCHED',source_revision=m['source_revision'],job=str(job),
 identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=started,manifest_sha256=fingerprint,
 payload_sha256=m['payload_sha256'],scope_counts=m['scope_counts'],
 halfway_not_before_unix=started+m['halfway_after_start_seconds'],final_not_before_unix=started+m['terminal_after_start_seconds'],
 maximum_wall_seconds=m['maximum_wall_seconds'],planning_seconds=m['planning_seconds'],
 preflight=dict(data_disk_free_bytes=free,MemAvailable_bytes=memory,original_frontend_exited_and_accepted=True,
 original1789_reused_from_server_not_retransferred=True,additional_metadata_files=len(extra)),
 GPU_submissions=0,ledger_written=False,full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False)
(job/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''

CAPTURE=HOST_CAPTURE.replace("job/'closure'/n","job/'inputs'/n").replace(" cap=json.loads(__import__('gzip').decompress((job/'legacy-CPU-capture.json.gz').read_bytes()))",
    " metadata=json.loads((job/'execution-metadata-registration.json').read_text())\n cap={'registration':{'payload_sha256':metadata['original_payload_sha256']}}")
CAPTURE=CAPTURE.replace('bank24-host-frontend-probe.py','adapter-CPU-probe.py').replace('ORIGINAL_BANK24_HOST_CPU_BOUNDARY_CAPTURE','ORIGINAL_BANK24_EXECUTION_ADAPTER_CPU_CAPTURE')
CAPTURE=CAPTURE.replace(" v['independent_probe_source_sha256']=", " v['independent_extra_metadata_sha256']={n:sha(job/'inputs'/n) for n in metadata['additional_metadata_sha256']}\n v['independent_generated_sha256']={p.name:sha(p) for p in (job/'generated').glob('*.py')}\n v['independent_probe_source_sha256']=")


def launch(output):
    require(not output.exists(),'Never overwrite a dispatch receipt')
    recipe=read(RECIPE);metadata=read(METADATA)
    require(sha(METADATA)==recipe['metadata_registration_sha256'],'Metadata registration changed')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]==source,'Publish exact source first')
    for ref in list(PAYLOADS.values())+[str(RECIPE),str(Path(__file__).relative_to(Path.cwd())) if Path(__file__).is_absolute() else __file__]:
        rel=str(Path(ref).resolve().relative_to(Path.cwd()))
        require(subprocess.check_output(['git','show',source+':'+rel])==Path(ref).read_bytes(),'Published dispatch input differs')
    files={n:Path(p).read_bytes() for n,p in PAYLOADS.items()}
    manifest=dict(recipe,source_revision=source,recipe_ref=str(RECIPE),
        payload_sha256={n:digest(b) for n,b in files.items()},worker_sha256=digest(files['worker.py']),supervisor_sha256=digest(files['supervisor.py']))
    write(LOCAL/'dispatch-intent.json',dict(source_revision=source,job=WORKSPACE+'/bootstrap/'+RUN,created_unix=time.time(),no_replay=True))
    archive=Path(metadata['metadata_archive_ref']);require(sha(archive)==recipe['metadata_archive_sha256'],'Metadata transport changed')
    result=ssh(SETUP,dict(manifest=manifest,files={n:base64.b64encode(b).decode() for n,b in files.items()},
        metadata_archive=base64.b64encode(archive.read_bytes()).decode()),timeout=180)
    write(output,result)
    return dict(output=str(output),status=result['status'],identity=result.get('identity'),job=result.get('job'),GPU_submissions=0)


def capture(kind,launch_ref,output):
    require(not output.exists(),'Existing collection must be read offline')
    L=read(launch_ref);require(L['status']=='FOUR_CARD_BANK24_EXECUTION_ADAPTER_CPU_SINGLE_DISPATCHED','Recover original actual CPU handle')
    if kind!='admission':require(time.time()>=L['halfway_not_before_unix' if kind=='halfway' else 'final_not_before_unix'],'Before actual once-only check')
    result=ssh('L='+repr(L)+'\nMODE='+repr(kind)+'\n'+CAPTURE,timeout=180)
    result.update(launch_ref=str(launch_ref),launch_sha256=sha(launch_ref));write(output,result)
    return dict(output=str(output),status=result['status'],original_supervisor_live=result.get('original_supervisor_live'),phase=(result.get('health') or {}).get('phase'))


def accept(launch_ref,capture_ref,output):
    L=read(launch_ref);c=read(capture_ref);m=c.get('manifest') or {};r=c.get('result') or {}
    require(c.get('mode')=='terminal' and c.get('observed_unix',0)>=L['final_not_before_unix'],'Actual original terminal required')
    recipe=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+str(RECIPE)]))
    require(all(m.get(k)==v for k,v in recipe.items()),'Original published CPU recipe required')
    for name,ref in PAYLOADS.items():
        require(digest(subprocess.check_output(['git','show',L['source_revision']+':'+ref]))==L['payload_sha256'][name],'Published original payload differs')
    metadata=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+METADATA]))
    spec=importlib.util.spec_from_file_location('published_adapter_cpu_probe',Path(PAYLOADS['worker.py']))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    expected_probe=digest(worker.probe_source(Path(L['job'])).encode())
    probe=r.get('execution_adapter_CPU') or {};command=r.get('commands') or [];controls=probe.get('controls') or {}
    args=c.get('container_command') or []
    checks=dict(original_launch=c.get('launch')==L,
        original_source_manifest=r.get('source_revision')==m.get('source_revision')==L['source_revision'] and c.get('manifest_sha256')==L['manifest_sha256'],
        all_payloads=c.get('payload_sha256')==m.get('payload_sha256')==L['payload_sha256'],
        actual_terminal_success=r.get('status')==ADAPTER_STATUS and (c.get('supervisor_result') or {}).get('exit_code')==0,
        supervisor_and_container_exited=c.get('original_supervisor_live') is False and c.get('own_container_running') is False,
        own_resource_lock_released=c.get('own_resource_lock_free') is True,
        unchanged_original1789=c.get('independent_full_closure_sha256')==metadata['original_payload_sha256'],
        extra29_original_source_metadata=c.get('independent_extra_metadata_sha256')==metadata['additional_metadata_sha256'],
        exact_probe_and_exit=len(command)==1 and command[0]['exit_code']==0 and command[0]['exact_marker'] is True
            and command[0]['probe_source_sha256']==c.get('independent_probe_source_sha256')==expected_probe,
        exact_real_execution_inputs=probe.get('real_inputs')==recipe['expected_real_inputs'],
        original_full24_denominator=(probe.get('real_inputs') or {}).get('scope_counts')==L['scope_counts'],
        all3_generated_sources=probe.get('generated_sha256')==c.get('independent_generated_sha256')==recipe['expected_generated_sha256'],
        exact_reversible_SM89_binding=probe.get('binding')==recipe['expected_adaptation_binding'],
        all21_finance_controls=len(controls.get('checks',{}))==21 and all(controls.get('checks',{}).values()),
        finance_only_in_memory=controls.get('actual_GPU_ledger_opened') is False and controls.get('filesystem_transactions_executed')==0
            and controls.get('actual_reservations')==0 and controls.get('ledger_written') is False,
        unchanged_environment=r.get('environment_metadata_before')==r.get('environment_metadata_after')==m.get('environment_metadata_sha256') and r.get('runtime_critical_sources_unchanged') is True,
        readonly_network_none_GPU_hidden='--read-only' in args and args[args.index('--network')+1]=='none' and '--gpus' not in args
            and 'CUDA_VISIBLE_DEVICES=' in args and 'NVIDIA_VISIBLE_DEVICES=void' in args,
        owned_identity_cache=(r.get('process_identity_and_cache') or {}).get('write_probe_pass') is True
            and (r.get('process_identity_and_cache') or {}).get('numeric_uid')==1000
            and (r.get('process_identity_and_cache') or {}).get('system_passwd_modified') is False,
        remaining_gates_explicit=probe.get('remaining')==recipe['remaining']==REMAINING,
        no_false_full_production_or_GPU=probe.get('full_new_host_scope_production_CPU_accepted') is False
            and probe.get('actual_CUDA_compatibility_accepted') is False and probe.get('whole_card_new_host_quote_accepted') is False
            and probe.get('GPU_dispatch_ready') is False and probe.get('Cosmos_weights_loaded')==0 and probe.get('CUDA_initialized') is False)
    ok=all(checks.values())
    result=dict(status='BANK24_SM89_EXECUTION_ADAPTER_CPU_INDEPENDENTLY_ACCEPTED' if ok else 'BANK24_SM89_EXECUTION_ADAPTER_CPU_NOT_ACCEPTED',
        checks=checks,execution_adapter_CPU_accepted=ok,full_new_host_scope_production_CPU_accepted=False,
        actual_CUDA_compatibility_accepted=False,whole_card_new_host_quote_accepted=False,GPU_dispatch_ready=False,
        remaining=REMAINING,launch_ref=str(launch_ref),launch_sha256=sha(launch_ref),capture_ref=str(capture_ref),capture_sha256=sha(capture_ref),GPU_submissions=0,ledger_written=False)
    write(output,result);return dict(output=str(output),status=result['status'],execution_adapter_CPU_accepted=ok,GPU_dispatch_ready=False)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True);sub.add_parser('freeze')
    q=sub.add_parser('launch');q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('capture');q.add_argument('--kind',choices=['admission','halfway','terminal'],required=True)
    q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('accept');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--capture',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.mode=='freeze':v=freeze()
    elif a.mode=='launch':v=launch(a.output)
    elif a.mode=='capture':v=capture(a.kind,a.launch_ref,a.output)
    else:v=accept(a.launch_ref,a.capture,a.output)
    print(json.dumps(v))


if __name__=='__main__':main()
