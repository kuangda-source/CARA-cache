#!/usr/bin/env python3
"""Deploy/collect one real cross-container CPU lifecycle check; never a GPU."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import time

from four_card_bank24_execution_adapter_r1 import read,digest,require
from four_card_bank24_gpu_port_r1 import generate,full_quote
from wc_four_card_resource_cpu_r4 import ssh,write

ROOT='/data20t/gaokuangda/worldcache_workspace'
RUN='wc-fourcard-bank24-container-lifecycle-cpu-r1-20261022'
LOCAL=Path('.sync/four-card-bank24-container-lifecycle-cpu-r1-20261022')
RECIPE=Path('manifests/wc_four_card_bank24_container_lifecycle_cpu_r1_20261022.json')
COMP='reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_'
METADATA='manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json'
PAYLOADS={'worker.py':'scripts/check_wc_four_card_bank24_container_cpu_r1.py',
    'supervisor.py':'scripts/supervise_wc_four_card_bank24_container_cpu_r1.py',
    'legacy-supervisor.py':'scripts/supervise_wc_four_card_resource_cpu_r4.py',
    'resource_worker.py':'scripts/finish_wc_four_card_resources_cpu_r4.py',
    'repair_support.py':'scripts/repair_wc_four_card_environment_r2.py',
    'four_card_bank24_container_transport_r1.py':'scripts/four_card_bank24_container_transport_r1.py',
    'four_card_bank24_gpu_port_r1.py':'scripts/four_card_bank24_gpu_port_r1.py',
    'four_card_bank24_execution_adapter_r1.py':'scripts/four_card_bank24_execution_adapter_r1.py',
    'supervise_wc_four_card_bank24_gpu_r1.py':'scripts/supervise_wc_four_card_bank24_gpu_r1.py',
    'run_wc_four_card_bank24_inner_r1.py':'scripts/run_wc_four_card_bank24_inner_r1.py',
    'component-accepted.json':COMP+'independent_acceptance_20261022.json',
    'execution-metadata-registration.json':METADATA}


def sha(p):return digest(Path(p).read_bytes())


def freeze():
    require(not RECIPE.exists(),'Never modify frozen CPU recipe')
    cap=read(COMP+'terminal_20261022.json');accepted=read(COMP+'independent_acceptance_20261022.json')
    require(accepted['execution_adapter_CPU_accepted'] and all(accepted['checks'].values())
        and accepted['capture_sha256']==sha(COMP+'terminal_20261022.json'),'Actual complete component acceptance required')
    inputs=Path('.sync/four-card-bank24-execution-adapter-r1-20261022/inputs')
    import sys
    sys.path.insert(0,str(inputs/'src'))
    sources,binding=generate(inputs);config=read(inputs/'configs/wc_scout_bank24_production_entry_r1_20261018.json')
    quote=full_quote(read(inputs/'reports/wc_scout_BANK24_whole_quote_R1_20261018.json'),config['scope_counts'])
    m=cap['manifest'];metadata=read(METADATA)
    value=dict(version='BANK24_REAL_HOST_TO_CONTAINER_FD_AND_FULL24_POST_CPU_R1',workspace=ROOT,run_id=RUN,
        CPU_scope='ACTUAL_CROSS_CONTAINER_FD_PID_SUCCESS_FAILURE_TIMEOUT_FIXTURE_AND_ORIGINAL_POST_NEGATIVE_PATH',
        CPU_only=True,CPU_limit=2,memory_limit_GiB=16,scope_counts=config['scope_counts'],
        metadata_registration_ref=METADATA,metadata_registration_sha256=sha(METADATA),
        original_files=1789,extra_metadata_files=29,upstream_component_job=cap['launch']['job'],
        upstream_component_source=cap['launch']['source_revision'],
        upstream_component_result_sha256=digest((json.dumps(cap['result'],indent=2)+'\n').encode()),
        upstream_component_manifest_sha256=cap['manifest_sha256'],
        component_acceptance_sha256=sha(COMP+'independent_acceptance_20261022.json'),
        expected_generated_sha256={n:digest(b.encode()) for n,b in sources.items()},expected_port_binding=binding,
        expected_complete_planning_quote=quote,
        environment_metadata_sha256=m['environment_metadata_sha256'],runtime_source_sha256=m['runtime_source_sha256'],
        container_image_id=m['container_image_id'],container_process_user_name='gaokuangda',
        offline_only=True,torch_cache_readonly=True,resume_completed_resolver=True,explicit_process_identity_cache=True,
        planning_seconds=300,maximum_wall_seconds=900,halfway_after_start_seconds=120,terminal_after_start_seconds=420,
        full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,
        actual_GPUh_charged=0,fixture_budget_is_not_authority=True,
        remaining=['portable_GPU_dispatch_and_post_watcher_cli_binding','actual_scientific_terminal_collector_container_binding',
            'full_new_host_scope_CPU_acceptance','actual_CUDA_compatibility','actual_new_host_measured_prices','single_authoritative_v2_handoff'])
    write(RECIPE,value)
    return dict(status='CONTAINER_CPU_RECIPE_FROZEN_NOT_DISPATCHED',recipe_ref=str(RECIPE),
        planning_forecast_GPUh_not_measured=quote['forecast_complete_GPUh'],planning_whole_limit_GPUh_not_reservation=quote['billed_limit_GPUh'],GPU_submissions=0)


SETUP=r'''
import base64,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);m=d['manifest'];root=Path(m['workspace']);job=root/'bootstrap'/m['run_id']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if job.exists():
 print(json.dumps(dict(status='EXISTING_STAGE_RESTORE_ONLY',job=str(job),launch=json.loads((job/'launch.json').read_text()) if (job/'launch.json').is_file() else None)));sys.exit(0)
assert job.name=='wc-fourcard-bank24-container-lifecycle-cpu-r1-20261022' and job.parent.resolve()==(root/'bootstrap').resolve()
free=shutil.disk_usage(root).free
memory=int(next(v.split()[1] for v in Path('/proc/meminfo').read_text().splitlines() if v.startswith('MemAvailable:')))*1024
assert free>=128*(1<<30) and memory>=18*(1<<30)
previous=Path(m['upstream_component_job'])
assert previous.parent.resolve()==(root/'bootstrap').resolve() and previous.name=='wc-fourcard-bank24-execution-adapter-cpu-r1-1-20261022'
assert sha(previous/'manifest.json')==m['upstream_component_manifest_sha256'] and sha(previous/'result.json')==m['upstream_component_result_sha256']
assert json.loads((previous/'result.json').read_text())['execution_adapter_CPU_passed'] is True
assert json.loads((previous/'supervisor-result.json').read_text())['exit_code']==0
old=subprocess.run(['docker','inspect',previous.name,'--format','{{.State.Running}}'],capture_output=True,text=True,timeout=20)
assert old.returncode!=0 or old.stdout.strip()=='false'
lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files={n:base64.b64decode(v) for n,v in d['files'].items()}
assert all(Path(n).name==n for n in files) and {n:hashlib.sha256(b).hexdigest() for n,b in files.items()}==m['payload_sha256']
metadata=json.loads(files['execution-metadata-registration.json'])
assert len(metadata['original_payload_sha256'])==1789 and len(metadata['additional_metadata_sha256'])==29
inputs={}
for name,expected in dict(metadata['original_payload_sha256'],**metadata['additional_metadata_sha256']).items():
 path=previous/'inputs'/name
 assert not path.is_symlink() and (previous/'inputs').resolve() in path.resolve().parents
 body=path.read_bytes();assert hashlib.sha256(body).hexdigest()==expected;inputs[name]=body
runtimes=subprocess.run(['docker','info','--format','{{json .Runtimes}}'],capture_output=True,text=True,timeout=20)
runtime_names=sorted(json.loads(runtimes.stdout)) if runtimes.returncode==0 else None
job.mkdir(mode=0o700)
for name,body in files.items():(job/name).write_bytes(body)
for name,body in inputs.items():
 target=job/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
manifest=job/'manifest.json';manifest.write_text(json.dumps(m,indent=2)+'\n');fingerprint=sha(manifest)
(job/'dispatch-fence.json').write_text(json.dumps(dict(source_revision=m['source_revision'],manifest_sha256=fingerprint,created_unix=time.time()))+'\n')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close();started=time.time()
with (job/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(job/'supervisor.py'),'--manifest',str(manifest)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=job)
stat=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
launch=dict(status='BANK24_CONTAINER_LIFECYCLE_CPU_SINGLE_DISPATCHED',source_revision=m['source_revision'],job=str(job),
 identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=started,manifest_sha256=fingerprint,
 payload_sha256=m['payload_sha256'],scope_counts=m['scope_counts'],
 halfway_not_before_unix=started+m['halfway_after_start_seconds'],final_not_before_unix=started+m['terminal_after_start_seconds'],
 planning_seconds=m['planning_seconds'],maximum_wall_seconds=m['maximum_wall_seconds'],
 preflight=dict(data_disk_free_bytes=free,MemAvailable_bytes=memory,original_component_exited_and_accepted=True,
 original1789_plus29_reused_from_server=True,Docker_runtime_names=runtime_names,NVIDIA_Docker_runtime_registered=bool(runtime_names and 'nvidia' in runtime_names)),
 GPU_submissions=0,ledger_written=False,actual_GPUh_charged=0,full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False)
(job/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''

CAPTURE=r'''
import fcntl,hashlib,json,subprocess,time
from pathlib import Path
job=Path(L['job']);m=json.loads((job/'manifest.json').read_text());root=Path(m['workspace'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((job/name).read_text()) if (job/name).is_file() else None
try:
 stat=Path('/proc/%d/stat'%L['identity']['pid']).read_text().rsplit(')',1)[1].split()
 live=int(stat[19])==L['identity']['start_ticks'] and stat[0] not in ('Z','X')
except FileNotFoundError:live=False
check=subprocess.run(['docker','inspect',m['run_id']],capture_output=True,text=True,timeout=20)
container=json.loads(check.stdout)[0] if check.returncode==0 else None
value=dict(status='BANK24_ORIGINAL_CONTAINER_CPU_CAPTURE',mode=MODE,observed_unix=time.time(),launch=read('launch.json'),
 manifest=m,manifest_sha256=sha(job/'manifest.json'),payload_sha256={n:sha(job/n) for n in m['payload_sha256']},
 original_supervisor_live=live,own_container_running=bool(container and container['State']['Running']),health=read('health.json'),
 host_FD_handoff=read('host-FD-handoff.json'),host_FD_failure=read('host-FD-handoff-failure.json'),
 result_exists=(job/'result.json').is_file(),GPU_submissions=0,ledger_written=False)
if MODE=='terminal':
 metadata=read('execution-metadata-registration.json')
 value.update(result=read('result.json'),supervisor_result=read('supervisor-result.json'),container_command=read('container-command.json'),host_FD_release=read('host-CPU-lease-release.json'),
  independent_original1789_sha256={n:sha(job/'inputs'/n) for n in metadata['original_payload_sha256']},
  independent_extra29_sha256={n:sha(job/'inputs'/n) for n in metadata['additional_metadata_sha256']},
  independent_generated_sha256={p.name:sha(p) for p in (job/'generated').glob('*.py')},
  planning_quote=read('whole24-planning-quote.json'),planning_quote_sha256=sha(job/'whole24-planning-quote.json') if (job/'whole24-planning-quote.json').is_file() else None,
  independent_child_probe_sha256=sha(job/'CPU-child.py') if (job/'CPU-child.py').is_file() else None,
  independent_post_probe_sha256=sha(job/'negative-post-probe.py') if (job/'negative-post-probe.py').is_file() else None,
  post_negative_final=read('post-failure-fixture/CPU-final-results.json'))
 value['logs']={p.name:p.read_text(errors='replace')[-10000:] for p in job.glob('*.log')}
 for key,path in [('own_resource_lock_free',root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock'),
                  ('own_CPU_fixture_lease_free',job/'TEST_ONLY/.sync/gpu-locks/GPU-CPU-LIFECYCLE-PROBE.lock')]:
  if not path.is_file():value[key]=None;continue
  with path.open('r') as lock:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);value[key]=True;fcntl.flock(lock,fcntl.LOCK_UN)
   except BlockingIOError:value[key]=False
print(json.dumps(value))
'''


def launch(output):
    require(not output.exists(),'Never overwrite original dispatch receipt')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]==source,'Publish exact new CPU source first')
    for ref in list(PAYLOADS.values())+[str(RECIPE),str(Path(__file__).resolve().relative_to(Path.cwd()))]:
        rel=str(Path(ref).resolve().relative_to(Path.cwd()))
        require(Path(ref).read_bytes()==subprocess.check_output(['git','show',source+':'+rel]),'Actual published input differs')
    files={n:Path(p).read_bytes() for n,p in PAYLOADS.items()}
    m=dict(read(RECIPE),source_revision=source,recipe_ref=str(RECIPE),CPU_transport_nonce=secrets.token_hex(24),
        payload_sha256={n:digest(b) for n,b in files.items()},worker_sha256=digest(files['worker.py']),
        supervisor_sha256=digest(files['supervisor.py']),legacy_supervisor_sha256=digest(files['legacy-supervisor.py']))
    LOCAL.mkdir(parents=True,exist_ok=True)
    write(LOCAL/'dispatch-intent.json',dict(source_revision=source,job=ROOT+'/bootstrap/'+RUN,created_unix=time.time(),no_replay=True))
    result=ssh(SETUP,dict(manifest=m,files={n:base64.b64encode(b).decode() for n,b in files.items()}),timeout=180)
    write(output,result);return dict(output=str(output),status=result['status'],identity=result.get('identity'),GPU_submissions=0)


def capture(kind,launch_ref,output):
    require(not output.exists(),'Read existing original offline')
    L=read(launch_ref);require(L['status']=='BANK24_CONTAINER_LIFECYCLE_CPU_SINGLE_DISPATCHED','Actual original launch required')
    if kind!='admission':require(time.time()>=L['halfway_not_before_unix' if kind=='halfway' else 'final_not_before_unix'],'Before original once-only check')
    value=ssh('L='+repr(L)+'\nMODE='+repr(kind)+'\n'+CAPTURE,timeout=180)
    value.update(launch_ref=str(launch_ref),launch_sha256=sha(launch_ref));write(output,value)
    return dict(output=str(output),status=value['status'],original_supervisor_live=value.get('original_supervisor_live'),phase=(value.get('health') or {}).get('phase'))


def accept(launch_ref,capture_ref,output):
    L=read(launch_ref);c=read(capture_ref);m=c.get('manifest') or {};r=c.get('result') or {}
    require(c.get('mode')=='terminal' and c.get('observed_unix',0)>=L['final_not_before_unix'],'Actual original final collection required')
    recipe=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+str(RECIPE)]))
    require(all(m.get(k)==v for k,v in recipe.items()),'Original source recipe differs')
    for name,ref in PAYLOADS.items():
        require(digest(subprocess.check_output(['git','show',L['source_revision']+':'+ref]))==L['payload_sha256'][name],'Original published payload differs')
    metadata=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+METADATA]))
    spec=importlib.util.spec_from_file_location('published_container_CPU_worker',Path(PAYLOADS['worker.py']))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    expected_post=digest(worker.negative_post_source(Path(L['job']),Path(L['job'])/'TEST_ONLY',Path(L['job'])/'post-failure-fixture').encode())
    handshake=c.get('host_FD_handoff') or {};release=c.get('host_FD_release') or {};scenarios=r.get('scenarios') or []
    post=r.get('post_negative_path') or {};final=c.get('post_negative_final') or {};args=c.get('container_command') or []
    checks=dict(original_launch=c.get('launch')==L,
        original_source_manifest=r.get('source_revision')==m.get('source_revision')==L['source_revision'] and c.get('manifest_sha256')==L['manifest_sha256'],
        all_payloads=c.get('payload_sha256')==m.get('payload_sha256')==L['payload_sha256'],
        exact_original1789=c.get('independent_original1789_sha256')==metadata['original_payload_sha256'],
        exact_extra29=c.get('independent_extra29_sha256')==metadata['additional_metadata_sha256'],
        actual_success=r.get('status')=='BANK24_CROSS_CONTAINER_LIFECYCLE_CPU_PASS_NOT_GPU_OR_FULL_DISPATCH_PORT' and (c.get('supervisor_result') or {}).get('exit_code')==0,
        original_process_and_container_exited=c.get('original_supervisor_live') is False and c.get('own_container_running') is False,
        real_host_PID_and_Docker_peer=handshake.get('socket_peer_PID_matches_actual_Docker_PID') is True
            and all((handshake.get('peer_identity') or {}).get(k)==(r.get('worker_identity') or {}).get(k) for k in ('pid','start_ticks'))
            and all((handshake.get('host_identity') or {}).get(k)==L['identity'][k] for k in ('pid','start_ticks')),
        actual_host_PID_namespace_and_hidden_GPU=handshake.get('container_actual_pid_mode')=='host' and handshake.get('container_actual_readonly_root') is True
            and handshake.get('container_devices')==[] and handshake.get('container_device_requests')==[],
        original_FD_receipt=r.get('actual_host_to_container_FD')==handshake and c.get('host_FD_failure') is None,
        success_failure_timeout_child_paths=len(scenarios)==3 and [v['kind'] for v in scenarios]==['normal','failure','timeout']
            and [v['visited_slots'] for v in scenarios]==[24,3,0] and [v['missing_slots'] for v in scenarios]==[0,21,24]
            and all(v['retained_slots']==24 and v['subprocess']['child_exited'] for v in scenarios)
            and scenarios[-1]['subprocess'].get('owned_timeout_stop') is True,
        exact_child_probe=c.get('independent_child_probe_sha256')==digest(worker.child_probe_source().encode()),
        original_fd_fully_released=release.get('handoff_success') is True and release.get('actual_authoritative_UUID_lock_opened') is False
            and c.get('own_CPU_fixture_lease_free') is True and c.get('own_resource_lock_free') is True,
        all_generated_sources=c.get('independent_generated_sha256')==r.get('generated_sha256')==recipe['expected_generated_sha256'],
        reversible_post_and_acceptance=r.get('port_binding')==recipe['expected_port_binding'],
        real_negative_post_full24=len(final.get('rows',[]))==24 and all(row['status']=='NOT_REACHED_RETAINED' for row in final.get('rows',[]))
            and post.get('registered_paths')==24 and post.get('exit_code')==0 and post.get('scored_formal_paths')==0,
        exact_negative_post_probe=c.get('independent_post_probe_sha256')==post.get('probe_sha256')==expected_post,
        no_fake_fidelity=all('LPIPS' not in row and 'final_latent_sha256' not in row for row in final.get('rows',[])) and post.get('quality_fields_fabricated') is False,
        complete_quote_separate_from_measurement=c.get('planning_quote')==r.get('whole24_planning_quote')==recipe['expected_complete_planning_quote']
            and recipe['expected_complete_planning_quote']['actual_new_host_measured_quote_accepted'] is False,
        actual_admission_requires_full_CPU_and_handoff=r.get('actual_admission_refusals')==['missing_full_CPU','missing_authoritative_handoff'],
        fixture_only_not_actual_ledger=r.get('actual_authoritative_ledger_opened') is False and r.get('actual_GPU_UUID_leased') is False
            and (r.get('fixture_budget_summary') or {}).get('actual_authoritative_budget_opened') is False
            and (r.get('fixture_budget_summary') or {}).get('actual_GPUh_charged')==0,
        actual_additive_fixture_and_released_reservations=(r.get('fixture_budget_summary') or {}).get('settled_fixture_jobs')==3
            and (r.get('fixture_budget_summary') or {}).get('additive_actual_wall_formula_verified') is True
            and (r.get('fixture_budget_summary') or {}).get('whole_reservations_released') is True,
        owned_process_caches=(r.get('process_identity_and_cache') or {}).get('write_probe_pass') is True,
        readonly_offline_hidden_GPU='--read-only' in args and args[args.index('--network')+1]=='none'
            and args[args.index('--pid')+1]=='host' and '--gpus' not in args and 'NVIDIA_VISIBLE_DEVICES=void' in args,
        unchanged_env_runtime=r.get('environment_metadata_before')==r.get('environment_metadata_after')==m.get('environment_metadata_sha256')
            and r.get('runtime_critical_sources_unchanged') is True,
        remaining_false_flags=r.get('full_new_host_scope_production_CPU_accepted') is False and r.get('GPU_dispatch_ready') is False)
    ok=all(checks.values());value=dict(status='BANK24_REAL_CROSS_CONTAINER_LIFECYCLE_CPU_INDEPENDENTLY_ACCEPTED' if ok else 'BANK24_REAL_CROSS_CONTAINER_LIFECYCLE_CPU_NOT_ACCEPTED',
        checks=checks,container_lifecycle_CPU_accepted=ok,full_new_host_scope_production_CPU_accepted=False,
        actual_CUDA_compatibility_accepted=False,actual_new_host_measured_quote_accepted=False,GPU_dispatch_ready=False,
        launch_ref=str(launch_ref),launch_sha256=sha(launch_ref),capture_ref=str(capture_ref),capture_sha256=sha(capture_ref),
        remaining=recipe['remaining'],GPU_submissions=0,ledger_written=False)
    write(output,value);return dict(output=str(output),status=value['status'],container_lifecycle_CPU_accepted=ok,GPU_dispatch_ready=False)


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
