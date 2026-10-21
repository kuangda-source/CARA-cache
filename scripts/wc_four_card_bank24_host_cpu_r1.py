#!/usr/bin/env python3
"""Freeze, deploy and independently collect one new-host BANK24 CPU boundary."""
import argparse
import base64
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time

from four_card_bank24_host_contract_r1 import (
    COUNTS, ENTRY_SOURCE, LIFECYCLE_SOURCE, archive_members, digest, read, require)
from wc_four_card_resource_cpu_r4 import ssh, write

ROOT='/data20t/gaokuangda/worldcache_workspace'
RUN='wc-fourcard-bank24-host-cpu-r1-20261022'
RECIPE=Path('manifests/wc_four_card_bank24_host_cpu_boundary_r1_20261022.json')
RECOVERY=Path('manifests/wc_four_card_bank24_dependency_recovery_r1_20261022.json')
LOCAL=Path('.sync/four-card-bank24-host-cpu-r1-20261022')
ARCHIVE=LOCAL/'frozen-closure.tgz'
OLD_CAPTURE='reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_collection_20261019.json.gz'
OLD_ACCEPTED='reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json'
RESOURCE_LAUNCH='reports/wc_four_card_offline_resources_CPU_R4_3_launch_20261022.json'
RESOURCE_CAPTURE='reports/wc_four_card_offline_resources_CPU_R4_3_terminal_20261022.json'
RESOURCE_ACCEPTED='reports/wc_four_card_offline_resources_CPU_R4_3_independent_acceptance_20261022.json'
PAYLOADS={'worker.py':'scripts/check_wc_four_card_bank24_host_cpu_r1.py',
    'supervisor.py':'scripts/supervise_wc_four_card_resource_cpu_r4.py',
    'resource_worker.py':'scripts/finish_wc_four_card_resources_cpu_r4.py',
    'repair_support.py':'scripts/repair_wc_four_card_environment_r2.py',
    'four_card_bank24_host_contract_r1.py':'scripts/four_card_bank24_host_contract_r1.py',
    'legacy-CPU-capture.json.gz':OLD_CAPTURE,'legacy-CPU-accepted.json':OLD_ACCEPTED,
    'resource-accepted.json':RESOURCE_ACCEPTED,
    'frozen-gate.json':'reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json'}


def sha(path):return digest(Path(path).read_bytes())


def freeze():
    """Recover missing bytes from captured originals; never fabricate a proof."""
    require(not RECIPE.exists() and not RECOVERY.exists(), 'Frozen recipe already exists')
    cap=read(OLD_CAPTURE);reg=cap['registration'];require(len(reg['payload_sha256'])==1789,'Full closure required')
    tracked=set(subprocess.check_output(['git','ls-tree','-r','--name-only',LIFECYCLE_SOURCE],text=True).splitlines())
    wanted=[n for n in reg['payload_sha256'] if n in tracked]
    raw=subprocess.check_output(['git','archive','--format=tar',LIFECYCLE_SOURCE,'--']+wanted)
    with tarfile.open(fileobj=io.BytesIO(raw)) as source:
        data={m.name:source.extractfile(m).read() for m in source.getmembers() if m.isfile()}
    provenance={}
    for target in reg['payload_sha256']:
        if target in data:continue
        if target.startswith('vendor/WorldCache/'):
            ref='research/sources/wc_w3_expl_dev8_prompts_20261015/'+Path(target).name
            body=subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+ref])
            provenance[target]=dict(source_revision=LIFECYCLE_SOURCE,ref=ref,
                                    source_file_sha256=digest(body),derivation='exact_bytes')
        else:
            specs={'simple26d-sampling-CPU-result.json':('reports/wc_simple26d_full96_CPU_collection_20261015_1616.json.gz','sampling'),
                'simple26d-memory-sampling-CPU-result.json':('reports/wc_simple26d_memory_full144_CPU_collection_20261015_2352.json.gz','numeric')}
            require(target in specs, 'Unregistered recovery target')
            ref,key=specs[target]
            source_bytes=subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+ref])
            body=(json.dumps(json.loads(gzip.decompress(source_bytes))[key],indent=2)+'\n').encode()
            provenance[target]=dict(source_revision=LIFECYCLE_SOURCE,ref=ref,
                source_file_sha256=digest(source_bytes),json_key=key,
                derivation='captured_original_JSON_indent2_newline_exact_target_SHA')
        require(digest(body)==reg['payload_sha256'][target], 'Recovered bytes differ from original CPU registration')
        data[target]=body
    require(len(data)==1789 and {n:digest(b) for n,b in data.items()}==reg['payload_sha256'], 'All original bytes required')
    archive=io.BytesIO()
    with tarfile.open(fileobj=archive,mode='w') as out:
        for name,body in sorted(data.items()):
            info=tarfile.TarInfo(name);info.size=len(body);info.mode=0o600;info.mtime=0
            out.addfile(info,io.BytesIO(body))
    encoded=gzip.compress(archive.getvalue(),mtime=0)
    archive_members(encoded,reg['payload_sha256'])
    LOCAL.mkdir(parents=True,exist_ok=True)
    with ARCHIVE.open('xb') as stream:stream.write(encoded)
    recovery=dict(status='BANK24_FULL1789_ORIGINAL_CLOSURE_RECOVERED_LOCALLY_NOT_NEW_HOST_CPU',
        lifecycle_source=LIFECYCLE_SOURCE,original_registration_sha256=cap['registration_sha256'],
        frozen_files=1789,Git_archive_exact_files=1779,recovered_exact_files=10,recovery=provenance,
        archive_sha256=digest(encoded),archive_bytes=len(encoded),archive_local_ref=str(ARCHIVE),
        frozen_payload_sha256=reg['payload_sha256'],GPU_submissions=0,ledger_written=False)
    write(RECOVERY,recovery)
    resource=read(RESOURCE_CAPTURE);accepted=read(RESOURCE_ACCEPTED)
    require(accepted['offline_environment_resources_accepted'] and all(accepted['checks'].values()),'Actual resource CPU acceptance required')
    require(accepted['capture_sha256']==sha(RESOURCE_CAPTURE),'Resource acceptance binding differs')
    recipe=dict(version='BANK24_FOUR_CARD_FROZEN_FRONTEND_HOST_CPU_BOUNDARY_R1',workspace=ROOT,run_id=RUN,
        CPU_scope='FULL1789_DEPENDENCY_AND_SIX_REQUEST_FRONTEND_NEW_HOST_BOUNDARY_ONLY',
        scope_counts=COUNTS,resource_launch_ref=RESOURCE_LAUNCH,resource_capture_ref=RESOURCE_CAPTURE,
        resource_acceptance_ref=RESOURCE_ACCEPTED,recovery_ref=str(RECOVERY),
        recovery_sha256=sha(RECOVERY),archive_sha256=digest(encoded),archive_bytes=len(encoded),
        archive_local_ref=str(ARCHIVE),legacy_capture_ref=OLD_CAPTURE,legacy_acceptance_ref=OLD_ACCEPTED,
        frozen_scientific_lifecycle_source=LIFECYCLE_SOURCE,
        frozen_scientific_entry_source=ENTRY_SOURCE,
        original_lifecycle_files=1789,original_entry_files=1772,
        original_numerical_CPU_reexecution=False,original_entry_CPU_reexecution=False,
        full_new_host_scope_production_CPU_accepted=False,full_GPU_lifecycle_ported=False,
        original_runner_SM86_constraint_requires_explicit_SM89_port=True,
        resource_CPU_reexecution=False,model_downloads=0,Cosmos_weights_loaded=0,
        CUDA_initialized=False,GPU_submissions=0,ledger_written=False,GPU_dispatch_ready=False,
        CPU_limit=2,memory_limit_GiB=16,network='none',workspace_readonly=True,
        offline_only=True,torch_cache_readonly=True,
        resume_completed_resolver=True,explicit_process_identity_cache=True,
        container_process_user_name='gaokuangda',planning_seconds=600,maximum_wall_seconds=1200,
        halfway_after_start_seconds=240,terminal_after_start_seconds=900,
        upstream_resource_job=resource['launch']['job'],
        upstream_resource_result_sha256=digest((json.dumps(resource['result'],indent=2)+'\n').encode()),
        upstream_resource_manifest_sha256=resource['manifest_sha256'],
        environment_metadata_sha256=resource['manifest']['environment_metadata_sha256'],
        runtime_source_sha256=resource['manifest']['runtime_source_sha256'],
        container_image_id=resource['manifest']['container_image_id'])
    write(RECIPE,recipe)
    return dict(status='BANK24_HOST_BOUNDARY_RECIPE_FROZEN_NOT_DISPATCHED',recipe_ref=str(RECIPE),
                recovered_files=1789,archive_bytes=len(encoded),GPU_submissions=0)


SETUP=r'''
import base64,fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);m=d['manifest'];root=Path(m['workspace']);job=root/'bootstrap'/m['run_id']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if job.exists():
 print(json.dumps(dict(status='EXISTING_STAGE_RESTORE_ONLY',job=str(job),
  launch=json.loads((job/'launch.json').read_text()) if (job/'launch.json').is_file() else None)));sys.exit(0)
assert job.parent.resolve()==(root/'bootstrap').resolve() and job.name=='wc-fourcard-bank24-host-cpu-r1-20261022'
free=shutil.disk_usage(root).free
memory=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert free>=128*(1<<30) and memory>=18*(1<<30)
previous=Path(m['upstream_resource_job'])
assert sha(previous/'result.json')==m['upstream_resource_result_sha256'] and sha(previous/'manifest.json')==m['upstream_resource_manifest_sha256']
assert json.loads((previous/'result.json').read_text())['status']=='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_COMPLETE_NOT_PRODUCTION_OR_GPU'
old=subprocess.run(['docker','inspect',previous.name,'--format','{{.State.Running}}'],capture_output=True,text=True,timeout=20)
assert old.returncode!=0 or old.stdout.strip()=='false'
image=subprocess.run(['docker','image','inspect',m['container_image_id'],'--format','{{.Id}}'],capture_output=True,text=True,timeout=20)
assert image.returncode==0 and image.stdout.strip()==m['container_image_id']
lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files={n:base64.b64decode(b) for n,b in d['files'].items()}
assert {n:hashlib.sha256(b).hexdigest() for n,b in files.items()}==m['payload_sha256']
assert all(Path(n).name==n for n in files)
namespace={};exec(compile(files['four_card_bank24_host_contract_r1.py'],'<published-archive-contract>','exec'),namespace)
import gzip
reg=json.loads(gzip.decompress(files['legacy-CPU-capture.json.gz']))['registration']
assert len(reg['payload_sha256'])==1789
raw=base64.b64decode(d['closure_archive']);assert hashlib.sha256(raw).hexdigest()==m['archive_sha256'] and len(raw)==m['archive_bytes']
closure=namespace['archive_members'](raw,reg['payload_sha256'])
job.mkdir(mode=0o700)
for name,body in files.items():(job/name).write_bytes(body)
for name,body in closure.items():
 target=job/'closure'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
manifest=job/'manifest.json';manifest.write_text(json.dumps(m,indent=2)+'\n');digest=sha(manifest)
(job/'dispatch-fence.json').write_text(json.dumps(dict(source_revision=m['source_revision'],manifest_sha256=digest,created_unix=time.time()))+'\n')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close();started=time.time()
with (job/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(job/'supervisor.py'),'--manifest',str(manifest)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=job)
stat=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
launch=dict(status='FOUR_CARD_BANK24_HOST_CPU_BOUNDARY_SINGLE_DISPATCHED',source_revision=m['source_revision'],job=str(job),
 identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=started,manifest_sha256=digest,
 payload_sha256=m['payload_sha256'],archive_sha256=m['archive_sha256'],scope_counts=m['scope_counts'],
 halfway_not_before_unix=started+m['halfway_after_start_seconds'],final_not_before_unix=started+m['terminal_after_start_seconds'],
 maximum_wall_seconds=m['maximum_wall_seconds'],planning_seconds=m['planning_seconds'],
 preflight=dict(data_disk_free_bytes=free,MemAvailable_bytes=memory,upstream_resource_CPU_exited=True),
 GPU_submissions=0,ledger_written=False,full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False)
(job/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''


CAPTURE=r'''
import fcntl,hashlib,json,subprocess,time
from pathlib import Path
job=Path(L['job']);m=json.loads((job/'manifest.json').read_text());root=Path(m['workspace'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):return json.loads((job/n).read_text()) if (job/n).is_file() else None
try:s=Path('/proc/%d/stat'%L['identity']['pid']).read_text().rsplit(')',1)[1].split();live=int(s[19])==L['identity']['start_ticks'] and s[0]!='Z'
except FileNotFoundError:live=False
call=subprocess.run(['docker','inspect',m['run_id']],capture_output=True,text=True,timeout=20)
docker=json.loads(call.stdout)[0] if call.returncode==0 else None
v=dict(status='ORIGINAL_BANK24_HOST_CPU_BOUNDARY_CAPTURE',mode=MODE,observed_unix=time.time(),launch=read('launch.json'),
 original_supervisor_live=live,own_container_running=bool(docker and docker['State']['Running']),
 manifest=m,manifest_sha256=sha(job/'manifest.json'),payload_sha256={n:sha(job/n) for n in m['payload_sha256']},
 health=read('health.json'),result_exists=(job/'result.json').is_file(),GPU_submissions=0,ledger_written=False)
if MODE=='admission':
 v.update(container_manifest_label=docker['Config']['Labels'].get('wcomr.manifest') if docker else None,
  readonly_root=docker['HostConfig']['ReadonlyRootfs'] if docker else None,
  devices=(docker['HostConfig'].get('Devices') or []) if docker else None,
  device_requests=(docker['HostConfig'].get('DeviceRequests') or []) if docker else None)
if MODE=='terminal':
 v.update(result=read('result.json'),supervisor_result=read('supervisor-result.json'),container_command=read('container-command.json'))
 v['logs']={p.name:p.read_text(errors='replace')[-8000:] for p in job.glob('*.log')}
 cap=json.loads(__import__('gzip').decompress((job/'legacy-CPU-capture.json.gz').read_bytes()))
 v['independent_full_closure_sha256']={n:sha(job/'closure'/n) for n in cap['registration']['payload_sha256']}
 v['independent_probe_source_sha256']=sha(job/'bank24-host-frontend-probe.py') if (job/'bank24-host-frontend-probe.py').is_file() else None
 lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_resource_lock_free']=True
 except BlockingIOError:v['own_resource_lock_free']=False
 lock.close()
print(json.dumps(v))
'''


def launch(output):
    require(not output.exists(), 'Never overwrite a dispatch receipt')
    recipe=read(RECIPE);recovery=read(RECOVERY)
    require(sha(RECOVERY)==recipe['recovery_sha256'] and sha(ARCHIVE)==recipe['archive_sha256'], 'Frozen archive or recovery changed')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]==source,'Publish exact source first')
    for ref in list(PAYLOADS.values())+[str(RECIPE),str(RECOVERY),__file__]:
        rel=str(Path(ref).resolve().relative_to(Path.cwd()))
        require(subprocess.check_output(['git','show',source+':'+rel])==Path(ref).read_bytes(), 'Published source differs')
    files={n:Path(p).read_bytes() for n,p in PAYLOADS.items()}
    manifest=dict(recipe,source_revision=source,recipe_ref=str(RECIPE),
        payload_sha256={n:digest(b) for n,b in files.items()},worker_sha256=digest(files['worker.py']),
        supervisor_sha256=digest(files['supervisor.py']))
    intent=LOCAL/'dispatch-intent.json'
    write(intent,dict(source_revision=source,job=ROOT+'/bootstrap/'+RUN,created_unix=time.time(),no_replay=True))
    result=ssh(SETUP,dict(manifest=manifest,files={n:base64.b64encode(b).decode() for n,b in files.items()},
                          closure_archive=base64.b64encode(ARCHIVE.read_bytes()).decode()),timeout=180)
    write(output,result)
    return dict(output=str(output),status=result['status'],job=result.get('job'),identity=result.get('identity'),GPU_submissions=0)


def capture(mode, launch_ref, output):
    require(not output.exists(),'Existing collection must be read offline')
    L=read(launch_ref);require(L['status']=='FOUR_CARD_BANK24_HOST_CPU_BOUNDARY_SINGLE_DISPATCHED','Recover actual original handle')
    if mode!='admission':require(time.time()>=L['halfway_not_before_unix' if mode=='halfway' else 'final_not_before_unix'],'Before actual once-only check')
    value=ssh('L='+repr(L)+'\nMODE='+repr(mode)+'\n'+CAPTURE,timeout=180)
    value.update(launch_ref=str(launch_ref),launch_sha256=sha(launch_ref));write(output,value)
    return dict(output=str(output),status=value['status'],original_supervisor_live=value.get('original_supervisor_live'),phase=(value.get('health') or {}).get('phase'))


def accept(launch_ref, capture_ref, output):
    L=read(launch_ref);c=read(capture_ref);r=c.get('result') or {};m=c.get('manifest') or {}
    require(c.get('mode')=='terminal' and c.get('observed_unix',0)>=L['final_not_before_unix'],'Actual final collection required')
    code=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+str(RECIPE)]))
    require(code['run_id']==RUN and all(m.get(k)==v for k,v in code.items()),'Original published CPU recipe required')
    for name in ('worker.py','resource_worker.py','repair_support.py','four_card_bank24_host_contract_r1.py'):
        require(sha(PAYLOADS[name])==L['payload_sha256'][name], 'Use original published CPU probe dependencies')
    expected=read(OLD_CAPTURE)['registration']['payload_sha256']
    probe_result=r.get('actual_frontend_CPU') or {};command=r.get('commands') or []
    args=c.get('container_command') or []
    native=Path(ROOT)/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages/nvidia/cuda_nvrtc'
    spec=importlib.util.spec_from_file_location('published_bank24_frontend_worker',Path(PAYLOADS['worker.py']))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    rspec=importlib.util.spec_from_file_location('published_resource_guard_generator',Path(PAYLOADS['resource_worker.py']))
    resource=importlib.util.module_from_spec(rspec);rspec.loader.exec_module(resource)
    probe=worker.integration_source(Path(L['job']),resource.guarded_source(Path(PAYLOADS['repair_support.py']).read_text()))
    checks=dict(original_launch=c.get('launch')==L,
        source_and_manifest=r.get('source_revision')==L['source_revision']==m.get('source_revision') and c.get('manifest_sha256')==L['manifest_sha256'],
        all_original_payloads=c.get('payload_sha256')==L['payload_sha256']==m.get('payload_sha256'),
        full1789_dependencies=c.get('independent_full_closure_sha256')==expected,
        original_process_and_container_exited=c.get('original_supervisor_live') is False and c.get('own_container_running') is False,
        supervisor_exit_zero=(c.get('supervisor_result') or {}).get('exit_code')==0,
        own_resource_lock_released=c.get('own_resource_lock_free') is True,
        actual_frontend_probe=len(command)==1 and command[0]['exit_code']==0 and command[0]['exact_marker'] is True,
        exact_registered_probe_source=len(command)==1 and command[0].get('probe_source_sha256')==c.get('independent_probe_source_sha256')==digest(probe.encode()),
        six_real_requests_and24_guards=probe_result.get('real_Cosmos_requests')==6 and probe_result.get('full_matrix_positions')==24 and len(probe_result.get('guard_refusals',[]))==24,
        twelve_scope_refusals=len(probe_result.get('scope_mutations_refused',[]))==12,
        no_historical_CPU_reexecution=r.get('numerical_CPU_paths_reexecuted')==0 and r.get('legacy_production_CPU_reexecuted') is False,
        actual_owned_cache_and_identity=(r.get('process_identity_and_cache') or {}).get('write_probe_pass') is True
            and (r.get('process_identity_and_cache') or {}).get('resolved_user')=='gaokuangda'
            and (r.get('process_identity_and_cache') or {}).get('numeric_uid')==1000
            and (r.get('process_identity_and_cache') or {}).get('system_passwd_modified') is False
            and all(k+'='+v in args for k,v in (r.get('process_identity_and_cache') or {}).get('variables',{}).items()),
        unchanged_environment_and_runtime=r.get('environment_metadata_before')==r.get('environment_metadata_after')==m.get('environment_metadata_sha256') and r.get('runtime_critical_sources_unchanged') is True,
        GPU_hidden_readonly_network_none='--read-only' in args and args[args.index('--network')+1]=='none' and '--gpus' not in args and '-e' in args and 'CUDA_VISIBLE_DEVICES=' in args and 'NVIDIA_VISIBLE_DEVICES=void' in args,
        existing_native_loader_process_environment='CUDA_HOME='+str(native) in args and 'CUDA_PATH='+str(native) in args,
        complete_price_inventory_kept_pending=(r.get('whole_quote_inventory') or {}).get('quote_complete') is False,
        frontend_only_no_full_production_or_GPU_claim=r.get('new_host_scope_production_CPU_accepted') is False and r.get('GPU_dispatch_ready') is False,
        actual_success_status=r.get('status')=='BANK24_NEW_HOST_FRONTEND_CPU_BOUNDARY_PASS_REMAINING_LIFECYCLE_AND_PRICE_GATES')
    ok=all(checks.values())
    value=dict(status='BANK24_FOUR_CARD_FRONTEND_CPU_BOUNDARY_INDEPENDENTLY_ACCEPTED' if ok else 'BANK24_FOUR_CARD_FRONTEND_CPU_BOUNDARY_NOT_ACCEPTED',checks=checks,
        host_boundary_CPU_accepted=ok,new_host_scope_production_CPU_accepted=False,actual_CUDA_compatibility_accepted=False,
        whole_card_new_host_quote_accepted=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,
        launch_ref=str(launch_ref),launch_sha256=sha(launch_ref),capture_ref=str(capture_ref),capture_sha256=sha(capture_ref))
    write(output,value);return dict(output=str(output),**{k:value[k] for k in ('status','host_boundary_CPU_accepted','new_host_scope_production_CPU_accepted','GPU_dispatch_ready')})


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    sub.add_parser('freeze')
    q=sub.add_parser('launch');q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('capture');q.add_argument('--kind',choices=['admission','halfway','terminal'],required=True)
    q.add_argument('--launch-ref',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('accept');q.add_argument('--launch-ref',type=Path,required=True)
    q.add_argument('--capture',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='freeze':v=freeze()
    elif a.mode=='launch':v=launch(a.output)
    elif a.mode=='capture':v=capture(a.kind,a.launch_ref,a.output)
    else:v=accept(a.launch_ref,a.capture,a.output)
    print(json.dumps(v))


if __name__=='__main__':main()
