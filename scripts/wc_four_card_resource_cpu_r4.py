#!/usr/bin/env python3
"""Single dispatch and once-only collection for fixed LPIPS/offline CPU resources."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

RECIPE=Path('manifests/wc_four_card_offline_resources_cpu_r4_20261022.json')
ROOT='/data20t/gaokuangda/worldcache_workspace'
PAYLOADS={'worker.py':'scripts/finish_wc_four_card_resources_cpu_r4.py',
    'supervisor.py':'scripts/supervise_wc_four_card_resource_cpu_r4.py',
    'resource_support.py':'scripts/prepare_wc_four_card_modelscope_hybrid_r3.py',
    'repair_support.py':'scripts/repair_wc_four_card_environment_r2.py'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')


def ssh(code,data=None,timeout=180):
    host=json.loads(Path('configs/hosts.local.json').read_text())['four_card']
    control=json.loads(Path('.sync/four-card-bootstrap-transfer-20261020/owned-model-proxy-r4.json').read_text())
    args=['ssh','-F','/dev/null','-S',control['control_socket'],'-o','BatchMode=yes','-o','ControlMaster=no',
        '-o','StrictHostKeyChecking=yes','-p',str(host['port']),host['user']+'@'+host['host'],'python3 -c '+shlex.quote(code)]
    try:r=subprocess.run(args,input=json.dumps(data).encode() if data is not None else None,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired:return dict(status='BOUNDED_COLLECTION_OR_DISPATCH_UNKNOWN_RESTORE_HANDLE_ONLY')
    if r.returncode:
        raw=Path('.sync/four-card-bootstrap-transfer-20261020')/('resource-r4-error-'+str(time.time_ns())+'.private.bin')
        raw.write_bytes(r.stderr);raw.chmod(0o600)
        return dict(status='CONNECTION_OR_REMOTE_CHECK_UNKNOWN_RESTORE_HANDLE_ONLY',SSH_exit_code=r.returncode,private_error_path=str(raw))
    try:return json.loads(r.stdout)
    except (ValueError,UnicodeDecodeError):
        raw=Path('.sync/four-card-bootstrap-transfer-20261020')/('resource-r4-raw-'+str(time.time_ns())+'.private.bin')
        raw.write_bytes(r.stdout);raw.chmod(0o600)
        return dict(status='SAVED_PARSE_UNKNOWN_OFFLINE_REPAIR_ONLY',private_raw_path=str(raw))


SETUP=r'''
import base64,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
d=json.load(sys.stdin);m=d['manifest'];root=Path(m['workspace']);job=root/'bootstrap'/m['run_id']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if job.exists():
 if (job/'launch.json').is_file():
  old=json.loads((job/'launch.json').read_text());print(json.dumps(dict(status='EXISTING_HANDLE_RESTORE_ONLY',launch=old)))
 else:print(json.dumps(dict(status='EXISTING_STAGE_NO_LAUNCH_UNKNOWN_RESTORE_ONLY',job=str(job))))
 sys.exit(0)
assert root.is_dir() and (root/'bootstrap').is_dir()
assert job.parent.resolve()==(root/'bootstrap').resolve()
assert not Path(m['previous_preflight_only_stage']).exists(),'Original R4 stage must be explicitly absent before the new version'
free=shutil.disk_usage(root).free
memory=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert free>=128*(1<<30) and memory>=18*(1<<30)
previous=Path(m['previous_validation_job']);assert sha(previous/'result.json')==m['previous_result_sha256']
assert sha(previous/'manifest.json')==m['previous_manifest_sha256']
old_resource=Path(m['accepted_model_server_job']);assert json.loads((old_resource/m['accepted_model_server_result_filename']).read_text())['status']=='FOUR_FIXED_REASON_SHARDS_FULL_HASH_PASS'
old_docker=subprocess.run(['docker','inspect',m['accepted_model_server_container'],'--format','{{.State.Running}}'],capture_output=True,text=True,timeout=20)
assert old_docker.returncode!=0 or old_docker.stdout.strip()=='false'
image=subprocess.run(['docker','image','inspect',m['container_image_id'],'--format','{{.Id}}'],capture_output=True,text=True,timeout=20)
assert image.returncode==0 and image.stdout.strip()==m['container_image_id']
lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
job.mkdir(mode=0o700);(root/'cache/torch').mkdir(parents=True,exist_ok=True)
for name,value in d['files'].items():
 assert Path(name).name==name
 data=base64.b64decode(value);assert hashlib.sha256(data).hexdigest()==d['file_sha256'][name]
 (job/name).write_bytes(data)
manifest=job/'manifest.json';manifest.write_text(json.dumps(m,indent=2)+'\n');digest=sha(manifest)
(job/'dispatch-fence.json').write_text(json.dumps(dict(source_revision=m['source_revision'],manifest_sha256=digest,created_unix=time.time()))+'\n')
fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
started=time.time()
with (job/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(job/'supervisor.py'),'--manifest',str(manifest)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=job)
stat=Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split();ticks=int(stat[19])
launch=dict(status='OFFLINE_RESOURCE_CPU_R4_SINGLE_DISPATCHED',started_unix=started,identity=dict(pid=child.pid,start_ticks=ticks),
 job=str(job),source_revision=m['source_revision'],manifest_sha256=digest,file_sha256=d['file_sha256'],
 worker_sha256=m['worker_sha256'],supervisor_sha256=m['supervisor_sha256'],
 halfway_not_before_unix=started+m['halfway_after_start_seconds'],final_not_before_unix=started+m['terminal_after_start_seconds'],
 maximum_wall_seconds=m['maximum_wall_seconds'],planning_seconds=m['planning_seconds'],
 preflight=dict(data_disk_free_bytes=free,MemAvailable_bytes=memory,accepted_R3_server_container_exited=True,cached_container_image_id=image.stdout.strip(),original_R4_preflight_only_stage_absent=True),
 GPU_submissions=0,ledger_written=False,CUDA_initialized=False,Cosmos_weights_loaded=0,
 new_host_production_CPU_accepted=False,GPU_dispatch_ready=False)
(job/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''


CAPTURE=r'''
import fcntl,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
job=Path(L['job']);m=json.loads((job/'manifest.json').read_text());root=Path(m['workspace'])
def read(name):return json.loads((job/name).read_text()) if (job/name).is_file() else None
pid=L['identity']['pid'];proc=Path('/proc/%d/stat'%pid)
try:stat=proc.read_text().rsplit(')',1)[1].split();live=int(stat[19])==L['identity']['start_ticks'] and stat[0]!='Z'
except FileNotFoundError:live=False
owned=subprocess.run(['docker','inspect',m['run_id']],capture_output=True,text=True,timeout=20)
docker=json.loads(owned.stdout)[0] if owned.returncode==0 else None
v=dict(status='ORIGINAL_OFFLINE_RESOURCE_CPU_R4_CAPTURE',mode=MODE,observed_unix=time.time(),launch=read('launch.json'),
 original_supervisor_live=live,manifest=m,manifest_sha256=sha(job/'manifest.json'),
 file_sha256={n:sha(job/n) for n in L['file_sha256']},health=read('health.json'),result_exists=(job/'result.json').is_file(),
 own_container_running=bool(docker and docker['State']['Running']),own_container_label=docker['Config']['Labels'].get('wcomr.manifest') if docker else None,
 own_container_devices=(docker['HostConfig'].get('Devices') or []) if docker else None,
 own_container_device_requests=(docker['HostConfig'].get('DeviceRequests') or []) if docker else None,
 own_container_readonly_root=docker['HostConfig']['ReadonlyRootfs'] if docker else None,GPU_submissions=0,ledger_written=False)
if MODE=='terminal':
 v.update(result=read('result.json'),supervisor_result=read('supervisor-result.json'),worker_once=read('worker-once.json'),container_command=read('container-command.json'))
 v['logs']={p.name:p.read_text(errors='replace')[-6500:] for p in job.glob('*.log')}
 spec=importlib.util.spec_from_file_location('repair_support',job/'repair_support.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 v['independent_environment_metadata_sha256']=helper.metadata_fingerprint(root/'envs/wc-cosmos-py310-cu128-r3')
 v['runtime_critical_sources_unchanged']=all(sha(root/'runtime'/k)==h for k,h in m['runtime_source_sha256'].items())
 v['old_validation_result_sha256']=sha(Path(m['previous_validation_job'])/'result.json')
 lock=(root/'bootstrap/.wc-fourcard-offline-resource-cpu.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_resource_lock_free']=True
 except BlockingIOError:v['own_resource_lock_free']=False
 lock.close()
 result=v.get('result') or {}
 if result.get('status')=='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_COMPLETE_NOT_PRODUCTION_OR_GPU' and not live and not v['own_container_running']:
  paths={'backbone':root/'cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth','linear':root/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages/lpips/weights/v0.1/alex.pth'}
  v['independent_LPIPS_hashes']={k:dict(sha256=sha(p),bytes=p.stat().st_size,is_symlink=p.is_symlink()) for k,p in paths.items()}
 v['probe_source_sha256']={p.name:sha(p) for p in job.glob('*.py') if p.name not in L['file_sha256']}
print(json.dumps(v))
'''


def launch(out):
    recipe=json.loads(RECIPE.read_text());source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]
    assert source==remote,'Publish exact source before dispatch'
    for p in list(PAYLOADS.values())+[str(RECIPE),__file__]:
        relative=str(Path(p).resolve().relative_to(Path.cwd()))
        assert subprocess.check_output(['git','show',source+':'+relative])==Path(p).read_bytes()
    assert not out.exists()
    refs={'upstream-assets-acceptance.json':recipe['model_assets_acceptance_ref'],
        'upstream-public14-acceptance.json':recipe['public14_acceptance_ref'],'frozen96.json':recipe['fixed96_manifest_ref']}
    full=json.loads(Path(refs['upstream-assets-acceptance.json']).read_text());public=json.loads(Path(refs['upstream-public14-acceptance.json']).read_text())
    assert full['frozen_production_model_files_accepted'] is True and all(full['checks'].values())
    assert public['public_auxiliary_assets_accepted'] is True and all(public['checks'].values())
    assert full['capture_sha256']==sha(full['capture_ref']) and public['capture_sha256']==sha(public['capture_ref'])
    fixed=json.loads(Path(refs['frozen96.json']).read_text())['assets']
    hashes=json.loads(Path(public['capture_ref']).read_text())['independent_file_hashes']
    assert len(fixed)==96 and len(hashes)==14 and all(x['status']=='PASS' for x in hashes)
    availability=fixed+[dict(repo_id=x['repo_id'],path=x['path'],digest=x['digest'],size=x['bytes'],target_revisions=[x['revision']]) for x in hashes]
    files={name:Path(p).read_bytes() for name,p in dict(PAYLOADS,**refs).items()}
    m=dict(recipe,source_revision=source,worker_sha256=sha(PAYLOADS['worker.py']),supervisor_sha256=sha(PAYLOADS['supervisor.py']),
        resource_support_sha256=sha(PAYLOADS['resource_support.py']),repair_support_sha256=sha(PAYLOADS['repair_support.py']),
        model_assets_acceptance_sha256=sha(refs['upstream-assets-acceptance.json']),public14_acceptance_sha256=sha(refs['upstream-public14-acceptance.json']),
        fixed96_manifest_sha256=sha(refs['frozen96.json']),availability_assets=availability,recipe_sha256=sha(RECIPE))
    intent=Path('.sync/four-card-bootstrap-transfer-20261020')/(recipe['run_id']+'-dispatch-intent.json')
    write(intent,dict(source_revision=source,job=ROOT+'/bootstrap/'+recipe['run_id'],created_unix=time.time(),output=str(out)))
    value=ssh(SETUP,dict(manifest=m,files={n:base64.b64encode(b).decode() for n,b in files.items()},file_sha256={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}))
    value['local_source_revision']=source
    write(out,value);return value


def accept(L,c):
    r=c.get('result') or {};m=c.get('manifest') or {};cmd=r.get('commands',[]);hashes=c.get('independent_LPIPS_hashes') or {}
    phases=['frozen110-offline-paths-tokenizer','unchanged-guarded-inference-import','official-LPIPS-pretrained-CPU']
    logs=c.get('logs') or {};resource=json.loads(RECIPE.read_text())
    import types
    bound=types.ModuleType('original_resource_r4_worker')
    original=subprocess.check_output(['git','show',L['source_revision']+':'+PAYLOADS['worker.py']])
    exec(compile(original,'<published-R4-worker>','exec'),bound.__dict__)
    original_repair=subprocess.check_output(['git','show',L['source_revision']+':'+PAYLOADS['repair_support.py']]).decode()
    sources=[bound.offline_assets_probe(m.get('availability_assets',[])),bound.guarded_source(original_repair),bound.LPIPS_PROBE]
    expected_probe_hashes={phase+'.py':hashlib.sha256(source.encode()).hexdigest() for phase,source in zip(phases,sources)}
    command=c.get('container_command') or []
    checks=dict(original_source=m.get('source_revision')==L['source_revision'] and r.get('source_revision')==L['source_revision'],
        original_manifest=c.get('manifest_sha256')==L['manifest_sha256'] and r.get('manifest_sha256')==L['manifest_sha256'],
        all_original_job_files=c.get('file_sha256')==L['file_sha256'],
        exact_published_probe_sources=c.get('probe_source_sha256')==expected_probe_hashes,
        original_worker_and_supervisor=r.get('worker_sha256')==L['worker_sha256'] and (c.get('supervisor_result') or {}).get('manifest_sha256')==L['manifest_sha256'],
        successful_worker=r.get('status')=='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_COMPLETE_NOT_PRODUCTION_OR_GPU',
        all_three_actual_commands=len(cmd)==3 and [x['phase'] for x in cmd]==phases and all(x['exit_code']==0 and x['exact_marker'] for x in cmd),
        original_supervisor_and_container_exited=c.get('original_supervisor_live') is False and c.get('own_container_running') is False and (c.get('supervisor_result') or {}).get('exit_code')==0,
        own_resource_lock_free=c.get('own_resource_lock_free') is True,
        registered_CPU_container_contract='--gpus' not in command and '--read-only' in command and '--cpus' in command and command[command.index('--cpus')+1]=='2' and '--memory' in command and command[command.index('--memory')+1]=='16g' and 'NVIDIA_VISIBLE_DEVICES=void' in command and 'HF_HUB_OFFLINE=1' in command and 'TRANSFORMERS_OFFLINE=1' in command,
        frozen110_scope=len(m.get('availability_assets',[]))==110 and sum(x['size'] for x in m.get('availability_assets',[]))==21358871258+5034332532,
        full96_and_public14_accepted=r.get('full_fixed96_already_accepted') is True and r.get('public14_already_accepted') is True,
        official_backbone_full_SHA=hashes.get('backbone',{}).get('sha256')==resource['LPIPS_backbone']['sha256'] and hashes.get('backbone',{}).get('bytes')==244408911 and hashes.get('backbone',{}).get('is_symlink') is False,
        official_linear_full_SHA=hashes.get('linear',{}).get('sha256')==resource['LPIPS_linear_sha256'],
        unchanged_environment=c.get('independent_environment_metadata_sha256')==resource['environment_metadata_sha256'] and r.get('environment_metadata_unchanged') is True and r.get('environment_metadata_before')==resource['environment_metadata_sha256'],
        unchanged_runtime_and_old_validation=c.get('runtime_critical_sources_unchanged') is True and r.get('runtime_critical_sources_unchanged') is True and c.get('old_validation_result_sha256')==resource['previous_result_sha256'],
        reused_successful_components_and_decode=r.get('original_components_acceptance_reused') is True and r.get('original_successful_decode_reused') is True,
        explicit_HF_cache_and_offline_flags='FROZEN110_OFFLINE_HF_PATHS_AND_REASON_TOKENIZER_CPU_OK' in logs.get('frozen110-offline-paths-tokenizer.log','').splitlines(),
        offline_guarded_original_inference_import='FROZEN_PRODUCTION_GUARDED_INFERENCE_IMPORT_CPU_ONLY_OK' in logs.get('unchanged-guarded-inference-import.log','').splitlines(),
        actual_pretrained_LPIPS_CPU='OFFICIAL_LPIPS_PRETRAINED_CPU_RESOURCE_ONLY_OK' in logs.get('official-LPIPS-pretrained-CPU.log','').splitlines() and r.get('LPIPS_CPU_pretrained_weight_files_loaded')==2,
        resource_only=r.get('Cosmos_weights_loaded')==0 and r.get('CUDA_initialized') is False and r.get('real_video_scores')==0 and r.get('GPU_submissions')==0 and r.get('ledger_written') is False and r.get('production_CPU_accepted') is False and r.get('GPU_dispatch_ready') is False)
    return dict(status='LPIPS_AND_OFFLINE_INFERENCE_CPU_RESOURCES_INDEPENDENTLY_ACCEPTED' if all(checks.values()) else 'CPU_RESOURCE_NOT_ACCEPTED_PRESERVE_ORIGINAL',checks=checks,
        offline_environment_resources_accepted=all(checks.values()),actual_CUDA_compatibility_accepted=False,new_host_scope_production_CPU_accepted=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['launch','admission','halfway','terminal','accept'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():
        v=json.loads(a.output.read_text());print(json.dumps(dict(output=str(a.output),status=v['status'],existing_receipt_reused_offline=True)));return
    if a.mode=='launch':v=launch(a.output)
    else:
        L=json.loads(a.launch_ref.read_text());L=L.get('launch',L)
        if a.mode=='accept':
            c=json.loads(a.capture.read_text());v=accept(L,c);v.update(launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref),capture_ref=str(a.capture),capture_sha256=sha(a.capture));write(a.output,v)
        else:
            threshold=L['halfway_not_before_unix'] if a.mode=='halfway' else L['final_not_before_unix'] if a.mode=='terminal' else 0
            assert time.time()>=threshold,'Do not query before actual not-before'
            v=ssh('L='+repr(L)+'\nMODE='+repr(a.mode)+'\n'+CAPTURE,timeout=180)
            v.update(launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref));write(a.output,v)
    print(json.dumps(dict(output=str(a.output),status=v['status'],source_revision=v.get('source_revision'),original_supervisor_live=v.get('original_supervisor_live'),phase=(v.get('health') or {}).get('phase'),offline_environment_resources_accepted=v.get('offline_environment_resources_accepted'))))


if __name__=='__main__':main()
