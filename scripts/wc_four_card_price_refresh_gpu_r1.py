#!/usr/bin/env python3
"""Once-only GPU controller for the immutable, separately accepted price stage."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from wc_four_card_policy_assets_r1 import ssh,write,read,sha,REPO,RUNTIME_REF
from wc_four_card_price_refresh_r1 import CAPTURE as OLD_CAPTURE,ACCEPTED as OLD_ACCEPTED
from audit_wc_policy_price_refresh_cpu_r1 import accept as accept_cpu
sys.path.insert(0,str(REPO/'src'))
from wcomr.policy_price_refresh_production_r1 import COUNTS,RUN
from wcomr.policy_price_terminal_r1 import accept as accept_terminal


def published_controller():
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    from wcomr.immutable_stage_payload_r1 import local_python_closure
    names=local_python_closure(REPO,['scripts/wc_four_card_price_refresh_gpu_r1.py',
        'scripts/audit_wc_policy_price_refresh_cpu_r1.py','scripts/wc_four_card_price_refresh_r1.py',
        'scripts/wc_four_card_policy_assets_r1.py','tests/test_policy_price_terminal_r1.py'])
    values={}
    for name in names:
        raw=subprocess.check_output(['git','show',revision+':'+name],cwd=REPO)
        if raw!=(REPO/name).read_bytes():raise ValueError('Publish exact controller/acceptor before GPU dispatch')
        values[name]=hashlib.sha256(raw).hexdigest()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=REPO,text=True).split()[0]
    if remote!=revision:raise ValueError('Frozen controller revision is not published at remote main')
    return revision,values


def verified_CPU(a):
    cap=read(a.cpu_capture);life=read(a.lifecycle_capture);accepted=read(a.cpu_acceptance)
    recomputed=accept_cpu(cap,life)
    recomputed.update(capture_ref=str(a.cpu_capture),capture_sha256=sha(a.cpu_capture),
        lifecycle_capture_ref=str(a.lifecycle_capture),lifecycle_capture_sha256=sha(a.lifecycle_capture))
    if accepted!=recomputed or not accepted['production_CPU_accepted']:
        raise ValueError('Exact full CPU numerical, real entry and lifecycle acceptance required')
    return cap,accepted


def saved_secret():
    # Reuse the already authorized four-card credential reader. Never log it.
    p=REPO/'.sync/four-card-bootstrap-transfer-20261020/transfer_and_launch.py'
    namespace={};source=p.read_text().split('accepted_ref=',1)[0]
    exec(compile(source,'existing-authorized-four-card-credential-reader','exec'),namespace)
    return namespace['password']()


PREFLIGHT=r'''
import json,pathlib,os,sys,subprocess,time,shutil,hashlib,fcntl
p=json.load(sys.stdin);L=p['CPU_launch'];stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project'])
sys.path[:0]=[str(stage/'scripts'),str(stage/'src')]
from wcomr.policy_price_refresh_production_r1 import validate,read,sha,RUN,COUNTS,CPU_PROOF,CPU_BUNDLE,CONFIG
from wcomr.gpu_budget_pool_v2 import BudgetPool
from wcomr.policy_price_exclusive_r1 import observe
assert sha(stage/'registration.json')==L['registration_sha256']
c,reg,*_=validate(root,stage)
assert reg['source_revision']==L['source_revision'] and c['scope_counts']==COUNTS
assert sha(stage/CPU_PROOF)==p['CPU_files']['production'] and sha(stage/CPU_BUNDLE)==p['CPU_files']['bundle']
assert sha(stage/'price-numerical-CPU.json')==p['CPU_files']['numerical']
assert read(stage/CPU_BUNDLE)['exit_code']==0
pool=BudgetPool(root).read();active=[k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False]
assert pool['cap_gpu_hours']==226 and pool['origin_used_gpu_hours']==79.99637737158223
snap=observe(p['gpu_uuid'])
gpu=subprocess.check_output(['/usr/bin/nvidia-smi','-i',p['gpu_uuid'],'--query-gpu=uuid,name,compute_cap,memory.used','--format=csv,noheader,nounits'],text=True).strip().split(',')
assert gpu[0].strip()==p['gpu_uuid'] and 'RTX 6000 Ada' in gpu[1] and gpu[2].strip()=='8.9'
free=shutil.disk_usage(root).free
mem=int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
reasons=[]
if active:reasons.append('OWN_CONFIRMED_GPU_JOB_ACTIVE')
if snap['compute_apps'] or int(gpu[3])>1024:reasons.append('GPU_BUSY')
if snap['mps_processes']!=[]:reasons.append('MPS_PRESENT_OR_UNKNOWN')
if snap['compute_mode'] not in ('Default','Exclusive_Process'):reasons.append('UNSUPPORTED_PRIOR_MODE')
if pool['available_gpu_hours']<c['billed_limit_GPUh']:reasons.append('INSUFFICIENT_WHOLE_BUDGET')
if free<30*2**30:reasons.append('DISK_BELOW_FULL_CARD_RESERVE')
if mem<50*2**30:reasons.append('MEMORY_BELOW_FULL_CARD_RESERVE')
value=dict(status='PRICE_ADMISSION_OBSERVATION_PASS' if not reasons else 'PRICE_RESOURCE_WAIT_NO_DISPATCH',
 admissible=not reasons,reasons=reasons,snapshot=snap,observed_unix=time.time(),disk_free_bytes=free,MemAvailable_bytes=mem,
 pool={k:pool[k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours','cap_gpu_hours')},GPU_submissions=0,ledger_written=False)
'''


def preflight(a):
    cap,accepted=verified_CPU(a)
    data=dict(CPU_launch=cap['launch'],gpu_uuid=a.gpu_uuid,
        CPU_files={k:cap['files'][k]['sha256'] for k in ('production','numerical','bundle')})
    result=ssh(PREFLIGHT+'\nprint(json.dumps(value))',data)
    write(a.output,result);return result


def launch_gpu(a):
    cap,accepted=verified_CPU(a);L=cap['launch'];c=cap['files']['config']['data']
    revision,bindings=published_controller()
    auth=dict(kind='AUTONOMOUS_COMPLETE_UNDER12_PRICE_CARD',run_id=RUN,launch_id=str(uuid.uuid4()),
        source_revision=L['source_revision'],entry_stage=L['stage'],registration_sha256=L['registration_sha256'],
        config_sha256=cap['files']['config']['sha256'],production_CPU_sha256=cap['files']['production']['sha256'],
        independent_CPU_acceptance_sha256=sha(a.cpu_acceptance),gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,
        forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
        cumulative_cap_GPUh=226,direct_user_authorization=True,
        direct_user_instruction='先完成1624验收并解决动作价格的可信度问题，再推进PG-P1/P2；以后实验单卡硬独占。',
        autonomy_exclusive_upper_GPUh=12,controller_source_revision=revision,controller_payload_sha256=bindings,
        original_asset_capture_sha256=sha(REPO/OLD_CAPTURE),original_asset_acceptance_sha256=sha(REPO/OLD_ACCEPTED))
    data=dict(CPU_launch=L,gpu_uuid=a.gpu_uuid,auth=auth,
        control_runtime=read(REPO/RUNTIME_REF),
        CPU_files={k:cap['files'][k]['sha256'] for k in ('production','numerical','bundle')},
        accepted_base64=base64.b64encode(a.cpu_acceptance.read_bytes()).decode())
    # No credential lookup or durable intent until the selected UUID is idle.
    observed=ssh(PREFLIGHT+'\nprint(json.dumps(value))',data)
    if not observed['admissible']:
        write(a.output,observed);return observed
    data['sudo_password']=saved_secret()
    try:
        result=ssh(LAUNCH_PREFIX+PREFLIGHT.replace('p=json.load(sys.stdin);','')+LAUNCH_SUFFIX,data)
    except Exception as e:
        result=dict(status='PRICE_DISPATCH_UNKNOWN_RECOVER_ORIGINAL_ONLY',stage=L['stage'],project=L['project'],
            original_CPU_launch=L,intended_launch_id=auth['launch_id'],error_type=type(e).__name__,
            no_replay=True,recovery_names=['price-GPU-intent.json','price-GPU-launch.json','price-host-guardian.json'])
    finally:data.pop('sudo_password',None)
    write(a.output,result);return result


LAUNCH_PREFIX=r'''
import json,pathlib,fcntl,sys
p=json.load(sys.stdin);stage=pathlib.Path(p['CPU_launch']['stage'])
lock=(stage/'price-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for name in ('price-GPU-launch.json','price-GPU-intent.json'):
 if (stage/name).exists():
  print(json.dumps(dict(status='EXISTING_PRICE_GPU_HANDLE_RECOVER_ONLY',original=json.loads((stage/name).read_text()))));raise SystemExit(0)
'''
RUNTIME_WRAPPER=r'''
runtime=p['control_runtime'];runtime_root=pathlib.Path(runtime['job'])
assert runtime['status']=='NATIVE_CONTROL_PYTHON_CPU_PASS' and runtime['exit_code']==0
for name,key in [('bin/python3','wrapper_sha256'),('usr-local/bin/python3.10','python_sha256'),('lib/ld-linux-x86-64.so.2','loader_sha256'),('manifest.json','manifest_sha256')]:
 assert sha(runtime_root/name)==runtime[key]
assert read(runtime_root/'result.json')['status']=='NATIVE_CONTROL_PYTHON_CPU_PASS'
host_python=str(runtime_root/'bin/python3')
'''

LAUNCH_SUFFIX=RUNTIME_WRAPPER+r'''
import base64
from wcomr.gpu_budget_pool_v2 import process_identity,atomic_json
if not value['admissible']:
 print(json.dumps(value));raise SystemExit(0)
auth=p['auth'];assert not (root/'outputs'/RUN).exists()
assert auth['source_revision']==reg['source_revision'] and auth['registration_sha256']==L['registration_sha256']
assert auth['config_sha256']==sha(stage/CONFIG) and auth['production_CPU_sha256']==sha(stage/CPU_PROOF)
assert auth['scope_counts']==COUNTS and 0<c['forecast_complete_GPUh']<=c['billed_limit_GPUh']==auth['billed_limit_GPUh']<12
raw=base64.b64decode(p['accepted_base64']);assert hashlib.sha256(raw).hexdigest()==auth['independent_CPU_acceptance_sha256']
accepted=json.loads(raw);assert accepted['production_CPU_accepted'] and accepted['full_GPU_lifecycle_CPU_accepted']
for name in ('price-independent-CPU-acceptance.json','price-GPU-authorization.json','price-runner-context-ready.json','price-runner-context-granted.json'):
 assert not (stage/name).exists(),'Existing outcome: recover only'
(stage/'price-independent-CPU-acceptance.json').write_bytes(raw)
with (stage/'price-GPU-authorization.json').open('x') as f:json.dump(auth,f,indent=2);f.write(chr(10));f.flush();os.fsync(f.fileno())
intent=dict(status='PRICE_ONCE_ONLY_GPU_INTENT',launch_id=auth['launch_id'],source_revision=reg['source_revision'],
 registration_sha256=L['registration_sha256'],gpu_uuid=auth['gpu_uuid'],created_unix=time.time(),no_replay=True)
with (stage/'price-GPU-intent.json').open('x') as f:json.dump(intent,f,indent=2);f.flush();os.fsync(f.fileno())
command=[host_python,'-u',str(stage/'scripts/wc_policy_price_host_guardian_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'price-host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
now=time.time();identity=process_identity(child.pid);assert identity['start_ticks'] is not None
result=dict(status='PRICE_GPU_SINGLE_DISPATCHED_HARDWARE_ADMISSION_PENDING',project=str(root),stage=str(stage),
 run_id=RUN,launch_id=auth['launch_id'],source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],
 config_sha256=auth['config_sha256'],production_CPU_sha256=auth['production_CPU_sha256'],
 authorization_sha256=sha(stage/'price-GPU-authorization.json'),gpu_uuid=auth['gpu_uuid'],scope_counts=COUNTS,
 guardian_identity=identity,container=stage.name+'-gpu',started_unix=now,forecast_GPUh=auth['forecast_GPUh'],
 billed_limit_GPUh=auth['billed_limit_GPUh'],controller_source_revision=auth['controller_source_revision'],
 halfway_check_not_before_unix=now+auth['forecast_GPUh']*1800,next_check_not_before_unix=now+auth['forecast_GPUh']*3600+900)
with (stage/'price-GPU-launch.json').open('x') as f:json.dump(result,f,indent=2);f.write(chr(10));f.flush();os.fsync(f.fileno())
print(json.dumps(result))
'''


def recover(a):
    L=read(a.cpu_launch)
    result=ssh(r'''
import json,pathlib,subprocess,sys,time
p=json.load(sys.stdin);stage=pathlib.Path(p['stage']);v=dict(status='PRICE_ORIGINAL_HANDLE_RECOVERY_ONLY',stage=str(stage),observed_unix=time.time(),handles={},GPU_submissions=0)
for name in ('price-GPU-intent.json','price-GPU-launch.json','price-host-guardian.json','price-admission-failure.json','price-entry-recovery-intent.json','price-entry-recovery-launch.json'):
 if (stage/name).exists():v['handles'][name]=json.loads((stage/name).read_text())
q=subprocess.run(['docker','inspect',stage.name+'-gpu'],capture_output=True,text=True,timeout=15)
v['container_state']=json.loads(q.stdout)[0]['State'] if q.returncode==0 else None
print(json.dumps(v))
''',L);write(a.output,result);return result


ENTRY_RECOVERY_PREFIX=r'''
import json,pathlib,fcntl,sys
p=json.load(sys.stdin);stage=pathlib.Path(p['CPU_launch']['stage'])
lock=(stage/'price-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for name in ('price-entry-recovery-intent.json','price-entry-recovery-launch.json'):
 if (stage/name).exists():
  print(json.dumps(dict(status='EXISTING_ENTRY_RECOVERY_HANDLE_RECOVER_ONLY',original=json.loads((stage/name).read_text()))));raise SystemExit(0)
'''

ENTRY_RECOVERY_CHECK=r'''
from wcomr.gpu_budget_pool_v2 import process_identity
original=p['original_launch'];assert read(stage/'price-GPU-launch.json')==original
assert sha(stage/'price-GPU-launch.json')==p['original_launch_sha256']
assert original['run_id']==RUN and original['stage']==str(stage)
assert original['source_revision']==reg['source_revision'] and original['registration_sha256']==L['registration_sha256']
assert original['gpu_uuid']==p['gpu_uuid'] and original['scope_counts']==COUNTS
assert sha(stage/'price-GPU-authorization.json')==original['authorization_sha256']
auth=read(stage/'price-GPU-authorization.json');intent=read(stage/'price-GPU-intent.json')
assert intent['launch_id']==auth['launch_id']==original['launch_id']
ident=original['guardian_identity'];actual=process_identity(ident['pid'])
assert actual.get('start_ticks')!=ident['start_ticks'] or actual.get('state') in (None,'Z','X'),'Original guardian remains live'
assert RUN not in pool['jobs'] and not (root/'outputs'/RUN).exists(),'GPU reservation or output already exists; recover only'
for name in ('price-host-guardian.json','price-container.log','price-runner-context-ready.json','price-runner-context-granted.json'):
 assert not (stage/name).exists(),'Host entry progressed; no entry replay'
q=subprocess.run(['docker','inspect',original['container']],capture_output=True,text=True,timeout=20)
assert q.returncode!=0 and 'No such' in q.stderr,'Container exists or inspect is unknown; recover only'
failure=(stage/'price-host-guardian.log').read_text()
assert 'GLIBC_2.34' in failure and 'not found' in failure and 'Traceback' not in failure,'Not the known pre-interpreter loader failure'
assert sha(stage/'price-host-guardian.log')==p['failure_log_sha256']
assert value['snapshot']['compute_mode']=='Default','Mode changed after pre-interpreter failure'
if not value['admissible']:
 print(json.dumps(value));raise SystemExit(0)
'''

ENTRY_RECOVERY_START=RUNTIME_WRAPPER+r'''
if not p['execute']:
 print(json.dumps(dict(value,status='PRICE_ENTRY_RECOVERY_PRECONDITIONS_PASS',original_launch_id=original['launch_id'],
   confirmed_GPU_submissions=0,actual_GPUh=0,original_failure_log_sha256=p['failure_log_sha256'])));raise SystemExit(0)
recovery=dict(status='PRICE_ENTRY_RECOVERY_INTENT',launch_id=original['launch_id'],created_unix=time.time(),
 original_launch_sha256=p['original_launch_sha256'],failure_log_sha256=p['failure_log_sha256'],
 controller_source_revision=p['controller_source_revision'],controller_payload_sha256=p['controller_payload_sha256'],
 control_runtime=p['control_runtime'],entry_CPU_proof_sha256=p['entry_CPU_proof_sha256'],
 GPU_replay=False,pre_interpreter_failure_confirmed=True,confirmed_prior_GPU_submissions=0,prior_actual_GPUh=0)
with (stage/'price-entry-recovery-intent.json').open('x') as f:json.dump(recovery,f,indent=2);f.flush();os.fsync(f.fileno())
command=[host_python,'-u',str(stage/'scripts/wc_policy_price_host_guardian_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'price-host-guardian-entry-recovery.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
now=time.time();identity=process_identity(child.pid);assert identity['start_ticks'] is not None
result=dict(original,status='PRICE_ORIGINAL_INTENT_ENTRY_RESUMED_HARDWARE_ADMISSION_PENDING',guardian_identity=identity,
 original_guardian_identity=original['guardian_identity'],original_started_unix=original['started_unix'],
 original_launch_sha256=p['original_launch_sha256'],entry_recovery_intent_sha256=sha(stage/'price-entry-recovery-intent.json'),
 entry_recovery_controller_revision=p['controller_source_revision'],started_unix=now,
 halfway_check_not_before_unix=now+original['forecast_GPUh']*1800,
 next_check_not_before_unix=now+original['forecast_GPUh']*3600+900)
with (stage/'price-entry-recovery-launch.json').open('x') as f:json.dump(result,f,indent=2);f.write(chr(10));f.flush();os.fsync(f.fileno())
print(json.dumps(result))
'''


def resume_host_entry(a):
    cap,_=verified_CPU(a);original=read(a.launch_ref)
    proof=read(a.entry_cpu_proof);probe=json.loads(proof['stdout'])
    if (proof['exit_code']!=0 or proof['runtime']!=read(REPO/RUNTIME_REF)
            or probe['status']!='ACTUAL_FROZEN_HOST_ENTRY_WRAPPER_CPU_PASS'
            or probe['source_revision']!=original['source_revision'] or probe['scope_counts']!=COUNTS
            or probe['CUDA_initialized'] or probe['mode_changes'] or probe['GPU_submissions']):
        raise ValueError('Actual frozen host entry child-wrapper CPU proof required')
    revision,bindings=published_controller()
    data=dict(CPU_launch=cap['launch'],gpu_uuid=a.gpu_uuid,original_launch=original,
        original_launch_sha256=sha(a.launch_ref),failure_log_sha256=a.failure_log_sha256,
        CPU_files={k:cap['files'][k]['sha256'] for k in ('production','numerical','bundle')},
        controller_source_revision=revision,controller_payload_sha256=bindings,
        control_runtime=read(REPO/RUNTIME_REF),entry_CPU_proof_sha256=sha(a.entry_cpu_proof),execute=False)
    code=ENTRY_RECOVERY_PREFIX+PREFLIGHT.replace('p=json.load(sys.stdin);','')+ENTRY_RECOVERY_CHECK+ENTRY_RECOVERY_START
    checked=ssh(code,data)
    if checked.get('status')!='PRICE_ENTRY_RECOVERY_PRECONDITIONS_PASS':
        write(a.output,checked);return checked
    data.update(execute=True,sudo_password=saved_secret())
    try:result=ssh(code,data)
    except Exception as e:
        result=dict(status='PRICE_ENTRY_RECOVERY_UNKNOWN_RECOVER_ONLY',original_launch=original,error_type=type(e).__name__,no_replay=True)
    finally:data.pop('sudo_password',None)
    write(a.output,result);return result


def capture(a):
    L=read(a.launch_ref)
    if a.mode=='halfway' and time.time()<L['halfway_check_not_before_unix']:
        raise ValueError('Before actual-start midpoint')
    v=ssh(CAPTURE_GPU,dict(launch=L,terminal=a.mode=='terminal'))
    write(a.output,v);return {k:v.get(k) for k in ('status','original_live_handles','health','error_lines')}


CAPTURE_GPU=r'''
import json,pathlib,subprocess,sys,time,fcntl,hashlib,os
p=json.load(sys.stdin);L=p['launch'];terminal=p['terminal'];stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project'])
sys.path[:0]=[str(stage/'scripts'),str(stage/'src')]
from wcomr.policy_price_refresh_production_r1 import RUN,ORIGINAL_RUN,read,sha
from wcomr.gpu_budget_pool_v2 import process_identity
from wcomr.policy_price_exclusive_r1 import observe
assert sha(stage/'registration.json')==L['registration_sha256']
out=root/'outputs'/RUN
v=dict(status='PRICE_ORIGINAL_GPU_CAPTURE',launch=L,observed_unix=time.time(),files={},GPU_submissions=0,ledger_written=False)
v['current_GPU']=observe(L['gpu_uuid'])
v['pool']=read(root/'reports/gpu-budget-v2.json')
def keep(key,path):
 v['files'][key]=dict(exists=path.exists())
 if path.exists():
  raw=path.read_bytes();v['files'][key].update(raw_utf8=raw.decode(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def same(i):
 r=process_identity(i['pid']);return r.get('start_ticks')==i['start_ticks'] and r.get('state') not in (None,'Z','X')
sup=read(out/'supervisor.json') if (out/'supervisor.json').exists() else {}
identities=dict(guardian=L['guardian_identity'])
for k,n in [('supervisor','supervisor_identity'),('runner','child_identity'),('post','post_identity')]:
 if n in sup:identities[k]=sup[n]
v['original_live_handles']={k:same(i) for k,i in identities.items()}
q=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20)
if q.returncode==0:
 c=json.loads(q.stdout)[0];assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
 v['container']=dict(state=c['State'],image=c['Image'],readonly_root=c['HostConfig']['ReadonlyRootfs'],
  pid_mode=c['HostConfig']['PidMode'],manifest_sha256=c['Config']['Labels']['wcomr.manifest'],device_requests=c['HostConfig'].get('DeviceRequests') or [])
 v['original_live_handles']['container']=c['State']['Running']
else:v['container']=None
v['own_UUID_lock_free']=None
lock=root/'.sync/gpu-locks'/(L['gpu_uuid']+'.lock')
if lock.exists():
 with lock.open('rb') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_UUID_lock_free']=True;fcntl.flock(handle,fcntl.LOCK_UN)
  except BlockingIOError:v['own_UUID_lock_free']=False
for key,name in [('guardian','price-host-guardian.json'),('authorization','price-GPU-authorization.json'),
 ('ready','price-runner-context-ready.json'),('grant','price-runner-context-granted.json')]:keep(key,stage/name)
if L.get('entry_recovery_intent_sha256'):
 for key,name in [('entry_recovery','price-entry-recovery-intent.json'),('original_launch','price-GPU-launch.json')]:keep(key,stage/name)
v['health']=read(out/'runner-health.json') if (out/'runner-health.json').exists() else None
v['error_lines']=[]
host_log='price-host-guardian-entry-recovery.log' if L.get('entry_recovery_intent_sha256') else 'price-host-guardian.log'
for log in (stage/host_log,stage/'price-container.log',out/'GPU.log',out/'post-CPU.log'):
 if log.exists():
  with log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-16384));tail=f.read().decode(errors='replace')
  v['error_lines'] += [x for x in tail.splitlines() if any(k in x for k in ('Traceback','RuntimeError','AssertionError','OutOfMemory','No space left'))][-8:]
if terminal:
 for key,name in [('registration','registration.json'),('config','price-refresh-config.json'),('quote','price-whole-quote.json'),
  ('CPU_acceptance','price-independent-CPU-acceptance.json')]:keep(key,stage/name)
 for key,name in [('supervisor','supervisor.json'),('runner','runner.json'),('post','post-results.json'),('post_exit','post-exit.json'),
  ('billing','billing.json'),('bundle','generator-input-bundle.json'),('monitor_final','exclusive-monitor-final.json')]:keep(key,out/name)
 reg=read(stage/'registration.json');v['payload_actual_sha256']={n:sha(stage/n) for n in reg['payload_sha256']}
 v['runtime_actual_sha256']={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
 v['monitor_raw_utf8']=(out/'exclusive-monitor.jsonl').read_text() if (out/'exclusive-monitor.jsonl').exists() else ''
 v['pool']=read(root/'reports/gpu-budget-v2.json')
 old=root/'outputs'/ORIGINAL_RUN;c=read(stage/'price-refresh-config.json')
 v['original_files_actual_sha256']={n:sha(old/n) for n in c['accepted_original_files']}
 v['artifact_checks']=[]
 if not any(v['original_live_handles'].values()) and (out/'runner.json').exists():
  from postprocess_wc_policy_interval_assets_r1 import RGB
  import cv2
  cv2.setNumThreads(2)
  originals=read(old/'runner.json')['runs'];native={r['scene']:r for r in originals if r['mode']=='NATIVE'};pixels={}
  for row in read(out/'runner.json')['runs']:
   r=dict(id=row['id'])
   try:
    for key in ('guided','final_latent'):
     ref=row[key+'_artifact'];path=pathlib.Path(ref['path'])
     assert not path.is_symlink() and path.resolve().is_relative_to(out.resolve()) and path.stat().st_size==ref['bytes']
     # Stream multi-GB tensors without loading model/GPU or duplicating RAM.
     h=hashlib.sha256()
     with path.open('rb') as f:
      for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
     r[key+'_sha256']=h.hexdigest()
    video=pathlib.Path(row['video_path']);assert video.resolve().is_relative_to(out.resolve())
    if row['scene'] not in pixels:pixels[row['scene']]=RGB(native[row['scene']]['video_path'])
    frames=RGB(video);r.update(RGB_frame_count=len(frames),all93_old_Native_equal=frames==pixels[row['scene']])
   except Exception as e:r.update(error_type=type(e).__name__,error=str(e),all93_old_Native_equal=False)
   v['artifact_checks'].append(r)
print(json.dumps(v,allow_nan=False))
'''


def accept_gpu(a):
    v=read(a.capture);old=read(REPO/OLD_CAPTURE);accepted=read(REPO/OLD_ACCEPTED)
    if sha(REPO/OLD_CAPTURE)!=accepted['capture_sha256']:raise ValueError('Old accepted capture differs')
    from wcomr.policy_price_terminal_r1 import record
    auth=record(v,'authorization')
    if (auth['original_asset_capture_sha256']!=sha(REPO/OLD_CAPTURE)
            or auth['original_asset_acceptance_sha256']!=sha(REPO/OLD_ACCEPTED)):
        raise ValueError('Original labels differ from launch-bound accepted originals')
    result=accept_terminal(v,old,accepted)
    result.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    write(a.output,result);return result


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    for mode in ('preflight','launch-gpu','resume-host-entry'):
        q=s.add_parser(mode)
        for n in ('cpu-capture','cpu-acceptance','lifecycle-capture','output'):q.add_argument('--'+n,type=Path,required=True)
        q.add_argument('--gpu-uuid',required=True)
        if mode=='resume-host-entry':
            q.add_argument('--launch-ref',required=True,type=Path)
            q.add_argument('--failure-log-sha256',required=True)
            q.add_argument('--entry-cpu-proof',required=True,type=Path)
    q=s.add_parser('recover');q.add_argument('--cpu-launch',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('capture');q.add_argument('--launch-ref',type=Path,required=True);q.add_argument('--mode',choices=['admission','halfway','terminal'],required=True);q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('accept-gpu');q.add_argument('--capture',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Preserve originals; never overwrite or replay')
    result=globals()[a.command.replace('-','_')](a)
    print(json.dumps({k:result.get(k) for k in ('status','admissible','full_protocol_accepted','actual_GPUh','GPU_submissions') if k in result}))

if __name__=='__main__':main()
