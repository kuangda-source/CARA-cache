"""Scoped preparation, admission and recovery for the user-approved CAL35."""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
from cara_f19_speed190_transport_r1 import ROOT,rpc
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_f19_speed190_identity_r1 import RUN,STAGE,MANIFEST,GPU,IMAGE
from wcomr.immutable_stage_payload_r1 import local_python_closure

PREFIX="""
import base64,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
stage=root/'.sync/cara-budget-calibration-GPU-F19-speed190-r1-20261103'
base=root/'.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(pathlib.Path(p).read_text())
def create(path,value):
 with pathlib.Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\\n');f.flush();os.fsync(f.fileno())
sys.dont_write_bytecode=True
"""
INSTALL=PREFIX+"""
assert not stage.exists(),'Existing/partial source retained; inspect before amendment'
reg=read(base/'registration.json')
assert sha(base/'GPU-launch.json')=='86f01c9cebe0d45770c42855f3094baa428c6ef837c5371cb9d4b1afad652fcd'
assert all(sha(base/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
stage.mkdir(mode=0o700)
import shutil
for n in reg['payload_sha256']:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target)
for n,b64 in p['files'].items():
 name=pathlib.Path(n);assert not name.is_absolute() and '..' not in name.parts
 raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
new={**reg,'host':'two_card','stage':str(stage),'source_revision':p['revision'],'container_image':p['image'],
 'payload_sha256':{**reg['payload_sha256'],**p['hashes']},'base_stage':str(base),
 'read_only_base_registration_sha256':sha(base/'registration.json'),'scope_sha256':p['authority']['scope_sha256']}
create(stage/'registration.json',new);create(stage/'GPU-authorization.json',p['authority'])
print(json.dumps(dict(status='CAL35_SOURCE_PREPARED_NO_GPU',registration_sha256=sha(stage/'registration.json'),
 source_revision=p['revision'],payload_files=len(new['payload_sha256']),runtime_source_sha256=new['runtime_source_sha256'])))
"""
CPU=PREFIX+"""
attempt=p.get('CPU_attempt',1);assert attempt in (1,2,3,4,5,6,7,8)
name=stage.name+'-cpu'+('' if attempt==1 else '-r'+str(attempt))
intent_name='CPU-intent.json' if attempt==1 else 'CPU-r'+str(attempt)+'-intent.json'
launch_name='CPU-launch.json' if attempt==1 else 'CPU-r'+str(attempt)+'-launch.json'
if attempt>1:
 old_cpu=json.loads(subprocess.check_output(['docker','inspect',stage.name+'-cpu'+('' if attempt==2 else '-r'+str(attempt-1))],text=True))[0]
 assert not old_cpu['State']['Running'] and old_cpu['State']['ExitCode']==1 and not (stage/'CPU-proof.json').exists()
q=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
if q.returncode==0:
 c=json.loads(q.stdout)[0];result=dict(status='CPU_RUNNING' if c['State']['Running'] else 'CPU_TERMINAL',state=c['State'])
 if not c['State']['Running']:
  logs=subprocess.run(['docker','logs','--tail','35',name],capture_output=True,text=True);result['logs']=(logs.stdout+logs.stderr)[-6500:]
 if (stage/'CPU-proof.json').exists():result['proof']=read(stage/'CPU-proof.json')
 print(json.dumps(result));raise SystemExit
assert 'No such object' in q.stderr and not (stage/intent_name).exists(),'Unknown original CPU; recover only'
launch=read(base/'GPU-launch.json');old=launch['commands']['container_cli'];env=[]
for i,v in enumerate(old[:-1]):
 if v=='-e' and old[i+1].split('=',1)[0] in ('PATH','LD_LIBRARY_PATH','CUDA_HOME','CUDA_PATH','NLTK_DATA'):env.extend(['-e',old[i+1]])
sys.path[:0]=[str(stage/'scripts'),str(stage/'src')]
from four_card_bank24_execution_tools_r1 import process_environment
full_environment=process_environment(root,stage/'CPU-caches')
full_environment['LD_LIBRARY_PATH']=next(v.split('=',1)[1] for v in old if v.startswith('LD_LIBRARY_PATH='))
env=[item for k,v in full_environment.items() for item in ('-e',k+'='+str(v))]
cmd=['docker','run','-d','--name',name,'--network','none','--read-only','--cpus','2','--cpuset-cpus','4,5',
 '--memory','8g','--memory-swap','8g','--pids-limit','256','--tmpfs','/tmp:rw,size=512m',
 '--user',str(os.getuid())+':'+str(os.getgid()),'-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void',
 '-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2',
 '-e','HF_HUB_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1',
 '-e','HF_HOME='+str(root/'cache/huggingface'),'-e','HF_HUB_CACHE='+str(root/'cache/huggingface/hub'),
 '-e','NLTK_DATA='+str(root/'runtime-resources/nltk-guardrail-d6d4bfa8-r1'),
 '-v',str(root)+':'+str(root)+':ro','-v',str(stage)+':'+str(stage)+':rw',
 '-v',str(stage/'src')+':'+str(stage/'src')+':ro','-v',str(stage/'scripts')+':'+str(stage/'scripts')+':ro',
 '-v',str(stage/'tests')+':'+str(stage/'tests')+':ro','-w',str(root/'runtime')]+env
cmd += [read(stage/'registration.json')['container_image'],'timeout','--signal=TERM','--kill-after=15s','900',
 launch['commands']['runner'][0],str(stage/'scripts/check_cara_f19_speed190_cpu_r1.py'),'--project',str(root),'--stage',str(stage)]
create(stage/intent_name,dict(command=cmd,registration_sha256=sha(stage/'registration.json'),started_unix=time.time(),GPU_submissions=0))
q=subprocess.run(cmd,capture_output=True,text=True);create(stage/launch_name,dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
print(json.dumps(dict(status='CPU_DISPATCHED' if q.returncode==0 else 'CPU_DISPATCH_FAILED_NO_RETRY',exit_code=q.returncode,stderr=q.stderr[-1000:])))
"""
PROVISION=PREFIX+"""
if (stage/'storage-launch.json').exists():
 print(json.dumps(dict(status='RECOVER_STORAGE_ONLY',state=read(stage/'storage-state.json') if (stage/'storage-state.json').exists() else None)));raise SystemExit
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_original_handles_r1 import bind_original_process
with (stage/'storage.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/'scripts/provision_cara_f19_speed190_storage_r1.py')],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 create(stage/'storage-launch.json',dict(identity=bind_original_process(child.pid),started_unix=time.time(),GPU_submissions=0))
 child.stdin.write(json.dumps(dict(sudo_password=packet['sudo_password'])).encode());child.stdin.close()
print(json.dumps(dict(status='PRIVATE16_GIB_STORAGE_DISPATCHED_NO_GPU',pid=child.pid)))
"""
ADMIT=PREFIX+"""
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from four_card_bank24_execution_tools_r1 import verify_nltk_resources
verify_nltk_resources(root)
from wcomr.cara_f19_speed190_execution_r1 import fresh,ASSETS,validate_stage
from wcomr.cara_fast_b36_dispatch_r2 import assets_check
from wcomr.gpu_budget_pool_v2 import atomic_json
if not (stage/'history104-storage.json').exists():
 proof=read(stage/'storage-state.json');assert proof['status']=='TWO_CARD_PRIVATE16_STORAGE_PROVISIONED_NO_GPU'
 create(stage/'history104-storage.json',proof['result']['storage_contract'])
validate_stage(root,stage)
if not (stage/'asset-admission.json').exists():
 from wcomr.cara_budget_original_handles_r1 import bind_original_process
 assert not (stage/'asset-check-intent.json').exists(),'Recover original content-check process before another read'
 create(stage/'asset-check-intent.json',dict(identity=bind_original_process(os.getpid()),started_unix=time.time(),GPU_submissions=0))
 create(stage/'asset-admission.json',dict(assets=assets_check(root,read(stage/ASSETS))))
a=fresh(root,stage);atomic_json(stage/'fresh-admission.json',a)
print(json.dumps(dict(status='CAL35_FRESH_ADMISSION_NO_GPU',admission=a)))
"""


def payload():
    seeds=['scripts/cara_f19_speed190_host_r1.py','scripts/run_cara_f19_speed190_r1.py',
        'scripts/check_cara_f19_speed190_cpu_r1.py','scripts/provision_cara_f19_speed190_storage_r1.py',
        'scripts/score_cara_f19_speed190_r1.py','scripts/cara_fast_host_guardian_r2.py',
        'scripts/four_card_bank24_execution_tools_r1.py','scripts/four_card_policy_assets_port_r1.py',
        'scripts/cara_budget_process_bootstrap_r1.py','scripts/run_cara_budget_calibration_r1.py',
        'tests/check_cara_f19_speed190_pipeline_cpu_r1.py','tests/test_cara_f19_speed190_sampling_r1.py',
        'tests/check_cara_pg_production_sampling_cpu_r1.py','tests/check_partial_mlp_guided_sampling_cpu_r1.py',
        'tests/check_full_sampling.py','tests/check_rv0_video_actions_cpu.py',
        'tests/test_cara_read_write_provenance_r1.py','tests/test_cara_read_write_transition_r1.py']
    files=local_python_closure(ROOT,seeds)
    for n in (MANIFEST,'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',
            'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json',
            'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json',
            'reports/cara_CAL66_quality_binding_20261025.json'):
        files[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for n,h in files.items():
        raw=subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)
        if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Uncommitted stage source: '+n)
    card=json.loads((ROOT/MANIFEST).read_text());remote='/data20t/gaokuangda/worldcache_workspace/.sync/'+STAGE
    auth=dict(run_id=RUN,launch_id=uuid.uuid4().hex,host='two_card',gpu_uuid=GPU,stage=remote,
        source_revision=revision,scope_sha256=card['scope_sha256'],billed_limit_GPUh=3.,execution_authorized=True,
        direct_user_authorization=True,user_quote=card['authority']['user_quote'],authorizes_replay=False,
        CPU_fixture_only=False,central_transaction_authorized=True,
        central_transaction_scope='Necessary reserve and actual settlement for this newly user-approved CAL35 only; no four-card GPU/probing/transfers',
        preserve_confirmation_planning_GPUh=10.)
    return dict(files={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in files},hashes=files,
        revision=revision,authority=auth,image=IMAGE)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('install','cpu','cpu-r2','cpu-r3','cpu-r4','cpu-r5','cpu-r6','cpu-r7','cpu-r8','provision','admit'))
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--route',choices=('ipv4','v6'),default='v6');a=p.parse_args()
    assert not a.receipt.exists()
    data=payload() if a.action=='install' else ({'CPU_attempt':int(a.action[-1])} if a.action.startswith('cpu-r') else {})
    if a.action=='install':
        comparison=rpc(PREFIX+"assert not stage.exists();print(json.dumps(dict(status='CAL35_BASE_COMPARE_ONLY',needed=[n for n,h in p['hashes'].items() if not (base/n).is_file() or sha(base/n)!=h])))",dict(hashes=data['hashes']),route=a.route)
        if comparison.get('status')!='CAL35_BASE_COMPARE_ONLY':
            result=comparison
        else:
            data['files']={n:v for n,v in data['files'].items() if n in comparison['needed']}
            result=rpc(INSTALL,data,route=a.route)
            result['compared_overlay_files']=len(data['files'])
    else:result=rpc({'cpu':CPU,'cpu-r2':CPU,'cpu-r3':CPU,'cpu-r4':CPU,'cpu-r5':CPU,'cpu-r6':CPU,'cpu-r7':CPU,'cpu-r8':CPU,'provision':PROVISION,'admit':ADMIT}[a.action],data,route=a.route,timeout=300 if a.action=='admit' else 90)
    with a.receipt.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result.get(k) for k in ('status','stderr','logs','state','source_revision','payload_files')}))


if __name__=='__main__':main()
