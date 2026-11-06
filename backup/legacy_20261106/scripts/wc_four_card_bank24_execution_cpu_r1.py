#!/usr/bin/env python3
"""Freeze, run and independently accept the last BANK24 execution-tools CPU."""
import argparse
import ast
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from four_card_bank24_execution_tools_r1 import PRODUCTION_SCRIPTS,ROOT,TARGET_STAGE,build_template
from four_card_bank24_execution_adapter_r1 import LIFECYCLE_SOURCE,read,digest,require
from four_card_bank24_gpu_port_r1 import generate,sha,FULL_CPU_STATUS
from wc_four_card_resource_cpu_r4 import ssh,write

RUN='wc-fourcard-bank24-full-execution-cpu-r1-20261022'
LOCAL=Path('.sync/four-card-bank24-full-execution-cpu-r1-20261022')
RECIPE=Path('manifests/wc_four_card_bank24_full_execution_cpu_r1_20261022.json')
UP='reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_'
METADATA='manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json'
PAYLOADS={name:'scripts/'+name for name in PRODUCTION_SCRIPTS}
PAYLOADS.update({'worker.py':'scripts/check_wc_four_card_bank24_execution_cpu_r1.py',
    'repair_support.py':'scripts/repair_wc_four_card_environment_r2.py',
    'container-accepted.json':UP+'independent_acceptance_20261022.json',
    'execution-metadata-registration.json':METADATA})


def freeze():
    require(not RECIPE.exists(),'Frozen complete CPU recipe is never overwritten')
    cap=read(UP+'terminal_20261022.json');accepted=read(UP+'independent_acceptance_20261022.json')
    require(accepted['container_lifecycle_CPU_accepted'] and all(accepted['checks'].values())
        and accepted['capture_sha256']==sha(UP+'terminal_20261022.json'),'Real cross-container acceptance required')
    # Only source generation is local. Do not rerun old numerical/frontend work.
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)
        for name in ['scripts/run_wc_drop1_full18_r1.py','scripts/postprocess_wc_scout_gpu_r1.py',
                     'src/wcomr/scout_gpu_lifecycle_r1.py','src/wcomr/gpu_budget_pool_v2.py']:
            p=path/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+name]))
        sys.path.insert(0,str(Path('src').resolve()));sources,binding=generate(path)
    m=cap['manifest']
    recipe=dict(version='BANK24_FULL_EXECUTION_TOOLS_ACTUAL_CPU_R1',workspace=ROOT,run_id=RUN,
        CPU_scope='ONE_DISPATCH_RESTORE_SETTLED_ONLY_REAL_POST_AND_HOST_BOUND_CPU_TERMINAL_COLLECTOR',
        CPU_only=True,CPU_limit=2,memory_limit_GiB=16,planning_seconds=300,maximum_wall_seconds=1200,
        halfway_after_start_seconds=120,terminal_after_start_seconds=420,
        upstream_container_job=cap['launch']['job'],upstream_container_source=cap['launch']['source_revision'],
        upstream_manifest_sha256=cap['manifest_sha256'],upstream_result_sha256=digest((json.dumps(cap['result'],indent=2)+'\n').encode()),
        upstream_acceptance_ref=UP+'independent_acceptance_20261022.json',upstream_acceptance_sha256=sha(UP+'independent_acceptance_20261022.json'),
        execution_metadata=read(METADATA),environment_metadata_sha256=m['environment_metadata_sha256'],runtime_source_sha256=m['runtime_source_sha256'],
        container_image_id=m['container_image_id'],scope_counts=m['scope_counts'],
        expected_generated_sha256={n:digest(b.encode()) for n,b in sources.items()},expected_port_binding=binding,
        target_stage=ROOT+'/.sync/'+TARGET_STAGE,original_numerical_or_frontend_reexecutions=0,
        GPU_boundary_fixture_only=True,actual_nvidia_smi_queries=0,actual_authoritative_budget_opened=False,
        GPU_submissions=0,ledger_written=False,Cosmos_weights_loaded=0,CUDA_initialized=False,
        full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False,
        remaining_after_CPU=['unique_authoritative_v2_full_history_and_single_writer_handoff',
            'fresh_GPU_UUID_disk_host_memory_and_budget_admission','charged_actual_CUDA_compatibility_and_complete24_GPU_execution',
            'actual_Ada_time_and_action_price_measurements'])
    write(RECIPE,recipe)
    return dict(status='FULL_EXECUTION_TOOLS_CPU_RECIPE_FROZEN_NOT_DISPATCHED',recipe_ref=str(RECIPE),GPU_submissions=0)


SETUP=r'''
import base64,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);m=d['manifest'];root=Path(m['workspace']);job=root/'bootstrap'/m['run_id']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if job.exists():
 print(json.dumps(dict(status='EXISTING_STAGE_RESTORE_ONLY',job=str(job),launch=json.loads((job/'launch.json').read_text()) if (job/'launch.json').is_file() else None)));sys.exit(0)
assert job.name=='wc-fourcard-bank24-full-execution-cpu-r1-20261022' and job.parent.resolve()==(root/'bootstrap').resolve()
free=shutil.disk_usage(root).free
memory=int(next(v.split()[1] for v in Path('/proc/meminfo').read_text().splitlines() if v.startswith('MemAvailable:')))*1024
assert free>=128*(1<<30) and memory>=18*(1<<30)
previous=Path(m['upstream_container_job'])
assert previous.parent.resolve()==(root/'bootstrap').resolve() and previous.name=='wc-fourcard-bank24-container-lifecycle-cpu-r1-20261022'
assert sha(previous/'manifest.json')==m['upstream_manifest_sha256'] and sha(previous/'result.json')==m['upstream_result_sha256']
assert json.loads((previous/'result.json').read_text())['container_lifecycle_CPU_passed'] is True
old=subprocess.run(['docker','inspect',previous.name,'--format','{{.State.Running}}'],capture_output=True,text=True,timeout=20)
assert old.returncode!=0 or old.stdout.strip()=='false'
lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files={n:base64.b64decode(v) for n,v in d['files'].items()}
assert all(Path(n).name==n for n in files) and {n:hashlib.sha256(b).hexdigest() for n,b in files.items()}==m['payload_sha256']
metadata=m['execution_metadata'];bindings=dict(metadata['original_payload_sha256'],**metadata['additional_metadata_sha256'])
assert len(metadata['original_payload_sha256'])==1789 and len(metadata['additional_metadata_sha256'])==29
inputs={}
for name,expected in bindings.items():
 path=previous/'inputs'/name
 assert not path.is_symlink() and (previous/'inputs').resolve() in path.resolve().parents
 body=path.read_bytes();assert hashlib.sha256(body).hexdigest()==expected;inputs[name]=body
job.mkdir(mode=0o700)
for name,body in files.items():(job/name).write_bytes(body)
for name,body in inputs.items():
 target=job/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
manifest=job/'manifest.json';manifest.write_text(json.dumps(m,indent=2)+'\n');fingerprint=sha(manifest)
(job/'dispatch-fence.json').write_text(json.dumps(dict(source_revision=m['source_revision'],manifest_sha256=fingerprint,created_unix=time.time()))+'\n')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close();started=time.time()
with (job/'worker.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(job/'worker.py'),'--manifest',str(manifest)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=job,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1'))
stat=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()
launch=dict(status='BANK24_FULL_EXECUTION_TOOLS_CPU_SINGLE_DISPATCHED',source_revision=m['source_revision'],job=str(job),
 identity=dict(pid=child.pid,start_ticks=int(stat[19])),started_unix=started,manifest_sha256=fingerprint,payload_sha256=m['payload_sha256'],scope_counts=m['scope_counts'],
 halfway_not_before_unix=started+m['halfway_after_start_seconds'],final_not_before_unix=started+m['terminal_after_start_seconds'],
 planning_seconds=m['planning_seconds'],maximum_wall_seconds=m['maximum_wall_seconds'],target_stage=m['target_stage'],
 preflight=dict(data_disk_free_bytes=free,MemAvailable_bytes=memory,original_container_CPU_exited_and_accepted=True,
 original1789_plus29_reused_from_server=True),GPU_submissions=0,ledger_written=False,actual_GPUh_charged=0,
 full_new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False)
(job/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''

CAPTURE=r'''
import fcntl,hashlib,json,subprocess,time
from pathlib import Path
job=Path(L['job']);m=json.loads((job/'manifest.json').read_text());root=Path(m['workspace'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((job/name).read_text()) if (job/name).is_file() else None
def alive(who):
 if not who:return False
 try:
  stat=Path('/proc/%d/stat'%who['pid']).read_text().rsplit(')',1)[1].split()
  return int(stat[19])==who['start_ticks'] and stat[0] not in ('Z','X')
 except FileNotFoundError:return False
health=read('health.json') or {}
v=dict(status='BANK24_FULL_EXECUTION_TOOLS_CPU_ORIGINAL_CAPTURE',mode=MODE,observed_unix=time.time(),launch=read('launch.json'),manifest=m,
 manifest_sha256=sha(job/'manifest.json'),payload_sha256={n:sha(job/n) for n in m['payload_sha256']},
 original_worker_live=alive(L['identity']),health=health,result_exists=(job/'result.json').is_file(),GPU_submissions=0,ledger_written=False)
if MODE=='terminal':
 meta=m['execution_metadata'];fixture=job/'TEST_ONLY/project/.sync/wc-bank24-fourcard-full-execution-r1-20261022'
 v.update(result=read('result.json'),independent_original1789_sha256={n:sha(job/'inputs'/n) for n in meta['original_payload_sha256']},
  independent_extra29_sha256={n:sha(job/'inputs'/n) for n in meta['additional_metadata_sha256']},
  target_registration=json.loads((fixture/'registration.json').read_text()) if (fixture/'registration.json').is_file() else None,
  target_registration_sha256=sha(fixture/'registration.json') if (fixture/'registration.json').is_file() else None,
  independent_fixture_controller_sha256=sha(fixture/'CPU-controller.py') if (fixture/'CPU-controller.py').is_file() else None,
  fixture_terminal=read('CPU-fixture-terminal-capture.json'),fixture_offline_function_input=read('CPU-offline-acceptance-function-input.json'))
 v['target_payload_sha256']={n:sha(fixture/n) for n in v['target_registration']['payload_sha256']} if v['target_registration'] else None
 fixture_launch=health.get('dispatch_fixture_launch') or {}
 v['fixture_handles_exited']=all(not alive(fixture_launch.get(k)) for k in ['supervisor_identity','post_watcher_identity'])
 v['own_CPU_containers']={}
 for name in ['post-CPU-observation','terminal-CPU-observation']:
  p=fixture/name/'cpu-manifest.json'
  if p.is_file():
   cm=json.loads(p.read_text());check=subprocess.run(['docker','inspect',cm['container']],capture_output=True,text=True,timeout=15)
   current=json.loads(check.stdout)[0] if check.returncode==0 else None
   release=json.loads((p.parent/'host-release.json').read_text()) if (p.parent/'host-release.json').is_file() else None
   v['own_CPU_containers'][name]=dict(manifest_sha256=sha(p),present=bool(current),running=bool(current and current['State']['Running']),host_release=release,
    original_label=(current['Config']['Labels'].get('wcomr.manifest')==sha(p)) if current else None)
 v['logs']={str(p.relative_to(job)):p.read_text(errors='replace')[-16000:] for p in [job/'worker.log',job/'failure.log',fixture/'post-watcher.log',fixture/'post-watcher-failure.log',fixture/'post-CPU-observation/failure.log',fixture/'terminal-CPU-observation/failure.log'] if p.is_file()}
 with (root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('r') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);v['resource_CPU_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
  except BlockingIOError:v['resource_CPU_lock_free']=False
print(json.dumps(v))
'''


def launch(output):
    require(not output.exists(),'Never overwrite actual dispatch')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]==source,'Publish exact complete CPU source first')
    for ref in list(PAYLOADS.values())+[str(RECIPE),'scripts/wc_four_card_bank24_execution_cpu_r1.py','scripts/wc_four_card_bank24_execution_r1.py']:
        require(Path(ref).read_bytes()==subprocess.check_output(['git','show',source+':'+ref]),'Published CPU input differs: '+ref)
    files={n:Path(p).read_bytes() for n,p in PAYLOADS.items()}
    m=dict(read(RECIPE),source_revision=source,recipe_ref=str(RECIPE),payload_sha256={n:digest(b) for n,b in files.items()},worker_sha256=digest(files['worker.py']))
    LOCAL.mkdir(parents=True,exist_ok=True);write(LOCAL/'dispatch-intent.json',dict(job=ROOT+'/bootstrap/'+RUN,source_revision=source,no_replay=True,created_unix=time.time()))
    value=ssh(SETUP,dict(manifest=m,files={n:base64.b64encode(b).decode() for n,b in files.items()}),timeout=180)
    write(output,value);return dict(output=str(output),status=value['status'],identity=value.get('identity'),GPU_submissions=0)


def capture(kind,launch_ref,output):
    require(not output.exists(),'Existing original must be read offline')
    L=read(launch_ref);require(L['status']=='BANK24_FULL_EXECUTION_TOOLS_CPU_SINGLE_DISPATCHED','Actual new CPU launch required')
    if kind!='admission':require(time.time()>=L['halfway_not_before_unix' if kind=='halfway' else 'final_not_before_unix'],'Before original not-before')
    value=ssh('L='+repr(L)+'\nMODE='+repr(kind)+'\n'+CAPTURE,timeout=180)
    value.update(launch_ref=str(launch_ref),launch_sha256=sha(launch_ref));write(output,value)
    return dict(output=str(output),status=value['status'],original_worker_live=value.get('original_worker_live'),phase=(value.get('health') or {}).get('phase'))


def accept(launch_ref,capture_ref,output):
    L=read(launch_ref);c=read(capture_ref);m=c.get('manifest') or {};r=c.get('result') or {}
    require(c.get('mode')=='terminal' and c.get('observed_unix',0)>=L['final_not_before_unix'],'Original terminal collection required')
    recipe=json.loads(subprocess.check_output(['git','show',L['source_revision']+':'+str(RECIPE)]))
    require(all(m.get(k)==v for k,v in recipe.items()),'Original complete CPU recipe differs')
    for name,ref in PAYLOADS.items():require(digest(subprocess.check_output(['git','show',L['source_revision']+':'+ref]))==L['payload_sha256'][name],'Original published payload differs')
    reg=c.get('target_registration') or {};fixture=r.get('fixture_terminal_control') or {};post=r.get('actual_post_binding') or {};cap=c.get('fixture_terminal') or {}
    worker_source=subprocess.check_output(['git','show',L['source_revision']+':'+PAYLOADS['worker.py']],text=True)
    tree=ast.parse(worker_source);probe_def=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixture_controller_source')
    ns={};exec(compile(ast.Module(body=[probe_def],type_ignores=[]),'<published-CPU-fixture-probe>','exec'),ns)
    final=cap.get('final') or {};bill=cap.get('billing') or {};pool=cap.get('pool') or {};jobs=pool.get('jobs') or {}
    fixture_job=jobs.get((cap.get('launch') or {}).get('run_id'),{})
    checks=dict(original_launch=c.get('launch')==L,source_manifest=r.get('source_revision')==m.get('source_revision')==L['source_revision'] and c.get('manifest_sha256')==L['manifest_sha256'],
        payloads=c.get('payload_sha256')==m.get('payload_sha256')==L['payload_sha256'],
        original1789=c.get('independent_original1789_sha256')==recipe['execution_metadata']['original_payload_sha256'],
        extra29=c.get('independent_extra29_sha256')==recipe['execution_metadata']['additional_metadata_sha256'],
        actual_complete_CPU=r.get('status')=='BANK24_FULL_EXECUTION_TOOLS_CPU_PASS_NOT_NEURAL_OR_GPU' and r.get('full_execution_tools_CPU_passed') is True,
        production_registration=c.get('target_registration_sha256')==r.get('target_registration_sha256') and reg.get('source_revision')==L['source_revision']
            and c.get('target_payload_sha256')==reg.get('payload_sha256') and len(reg.get('payload_sha256',{}))>1818,
        canonical_target=r.get('target_stage')==recipe['target_stage'],
        exact_generated_five=(r.get('production_template') or {}).get('generated_sha256')==recipe['expected_generated_sha256'],
        published_reversible_adapter=(r.get('production_template') or {}).get('port_binding')==recipe['expected_port_binding'],
        actual_once_restore=r.get('same_handle_restored_without_second_Popen') is True,
        exact_fixture_controller=c.get('independent_fixture_controller_sha256')==r.get('fixture_controller_sha256')==digest(ns['fixture_controller_source']().encode()),
        actual_production_CLI_schema=(r.get('actual_production_CLI_schema') or {}).get('help_exit0') is True
            and (r.get('actual_production_CLI_schema') or {}).get('incomplete_GPU_launch_exit2') is True,
        actual_post_after_settlement=post.get('exit_code')==0 and post.get('original_GPU_settled_before_post') is True,
        actual_post_peer=post.get('CPU_container_exit_verified') is True and (post.get('CPU_container_peer_binding') or {}).get('socket_peer_PID_matches_actual_Docker_PID') is True,
        four_actual_post_refusals=r.get('actual_post_refusals')==['live_original_parent','unknown_GPU_container','unreleased_original_UUID','unsettled_whole_reservation'],
        collector_Docker_peer=(fixture.get('actual_Docker_collector_peer') or {}).get('socket_peer_PID_matches_actual_Docker_PID') is True and fixture.get('actual_CPU_collector_exit') is True,
        original_observation_time_preserved=fixture.get('actual_observation_time_preserved') is True and cap.get('observed_unix',0)<c['observed_unix'],
        complete24_no_fabrication=fixture.get('complete24_retained') is True and fixture.get('zero_fabricated_scores') is True and fixture.get('full_neural_protocol_accepted') is False,
        independently_retained_all24=len(final.get('rows',[]))==24 and all(row.get('status')=='NOT_REACHED_RETAINED' and 'LPIPS' not in row and 'final_latent_sha256' not in row for row in final.get('rows',[]))
            and final.get('scored_formal_paths')==0 and (cap.get('runner') or {}).get('runs')==[],
        independent_fixture_wall_formula=fixture_job.get('status')=='SETTLED' and fixture_job.get('billing_sha256')==cap.get('billing_sha256')
            and type(bill.get('wall_seconds')) in (int,float) and math.isfinite(bill['wall_seconds']) and bill['wall_seconds']>0
            and math.isclose(bill['wall_seconds']/3600,bill['actual_GPUh'],rel_tol=1e-12) and fixture_job.get('actual_GPUh')==bill['actual_GPUh']
            and math.isclose(pool['used_gpu_hours'],79.99637737158223+bill['actual_GPUh'],abs_tol=1e-12,rel_tol=1e-12)
            and pool.get('reserved_gpu_hours')==0 and bill.get('actual_real_GPUh_charged')==0,
        actual_CPU_containers_GPU_hidden=all((peer or {}).get('container_devices')==[] and (peer or {}).get('container_device_requests')==[] and (peer or {}).get('container_actual_readonly_root') is True
            and (peer or {}).get('container_actual_pid_mode')=='host' for peer in [post.get('CPU_container_peer_binding'),fixture.get('actual_Docker_collector_peer')]),
        full_quote_not_measured=((r.get('production_template') or {}).get('planning_quote') or {}).get('billed_limit_GPUh')==8.75
            and all(v is None for v in ((r.get('production_template') or {}).get('planning_quote') or {}).get('actual_new_host_terms_seconds',{}).values()),
        explicit_fixture_not_authority=r.get('actual_authoritative_budget_opened') is False and r.get('actual_GPU_UUID_leased') is False and fixture.get('actual_GPUh_charged')==0,
        zero_CUDA_models_GPU=r.get('GPU_submissions')==0 and r.get('ledger_written') is False and r.get('Cosmos_weights_loaded')==0 and r.get('CUDA_initialized') is False and r.get('actual_nvidia_smi_queries')==0,
        actual_fixture_GPU_namespace_refused=r.get('actual_GPU_namespace_refused_CPU_fixture') is True,
        no_old_numerical_rerun=r.get('original_scientific_numerical_paths_reexecuted')==0,
        original_environment_runtime=r.get('environment_metadata_before')==r.get('environment_metadata_after')==recipe['environment_metadata_sha256'] and r.get('runtime_critical_sources_unchanged') is True,
        worker_and_fixture_handles_exited=c.get('original_worker_live') is False and c.get('fixture_handles_exited') is True,
        CPU_containers_exited=len(c.get('own_CPU_containers',{}))==2 and all(v.get('running') is False for v in c.get('own_CPU_containers',{}).values()),
        CPU_observation_locks_and_IPC_released=len(c.get('own_CPU_containers',{}))==2 and all((v.get('host_release') or {}).get('original_CPU_container_exit_verified') is True
            and (v.get('host_release') or {}).get('original_observation_FD_closed') is True and (v.get('host_release') or {}).get('original_IPC_directory_removed') is True
            and (v.get('host_release') or {}).get('actual_authoritative_UUID_lock_opened') is False for v in c.get('own_CPU_containers',{}).values()),
        resource_lock_released=c.get('resource_CPU_lock_free') is True)
    ok=all(checks.values());proofsha=digest((json.dumps(r,indent=2)+'\n').encode())
    value=dict(status=FULL_CPU_STATUS if ok else 'BANK24_FULL_EXECUTION_TOOLS_CPU_NOT_ACCEPTED',checks=checks,
        full_new_host_scope_production_CPU_accepted=ok,container_supervisor_and_terminal_lifecycle_accepted=ok,
        source_revision=L['source_revision'],target_stage=recipe['target_stage'],registration_sha256=c.get('target_registration_sha256'),proof_sha256=proofsha,
        launch_ref=str(launch_ref),launch_sha256=sha(launch_ref),capture_ref=str(capture_ref),capture_sha256=sha(capture_ref),
        actual_CUDA_compatibility_accepted=False,actual_new_host_measured_quote_accepted=False,unique_v2_handoff_accepted=False,
        GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,remaining=recipe['remaining_after_CPU'])
    write(output,value);return dict(output=str(output),status=value['status'],full_new_host_scope_production_CPU_accepted=ok,GPU_dispatch_ready=False)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True);sub.add_parser('freeze')
    q=sub.add_parser('launch');q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('capture');q.add_argument('--kind',choices=['admission','halfway','terminal'],required=True);q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('accept');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--capture',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.mode=='freeze':v=freeze()
    elif a.mode=='launch':v=launch(a.output)
    elif a.mode=='capture':v=capture(a.kind,a.launch_ref,a.output)
    else:v=accept(a.launch_ref,a.capture,a.output)
    print(json.dumps(v))


if __name__=='__main__':main()
