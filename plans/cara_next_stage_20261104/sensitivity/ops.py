"""One-card preparation/dispatch and explicit recovery commands; no scheduled work."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.immutable_stage_payload_r1 import local_python_closure

selector=argparse.ArgumentParser(add_help=False)
selector.add_argument('--manifest',type=Path,default=HERE/'manifest.json')
CARD=selector.parse_known_args()[0].manifest.resolve()
CARD_REL=str(CARD.relative_to(ROOT))
CONFIG=json.loads(CARD.read_text())
RUN=CONFIG['run_id']
STAGE='cara-budget-calibration-GPU-'+RUN[5:]
LIMIT=CONFIG['quote']['hard_GPUh']
REQUESTS=len(CONFIG['matrix'])
REL='plans/cara_next_stage_20261104/sensitivity'
GPU='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
BINDING=ROOT/'.sync'/('cara-sensitivity-original-binding.json' if RUN=='cara-native-sensitivity8-confirm4-r1-20261104' else RUN+'-original-binding.json')

PREFIX=f'''
import base64,copy,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
stage=root/'.sync/{STAGE}';base=root/'.sync/cara-budget-calibration-GPU-F19-speed190-r1-20261103'
rel='{REL}';run='{RUN}';gpu_uuid='{GPU}';manifest_rel='{CARD_REL}';limit={LIMIT};request_count={REQUESTS}
card_path=stage/manifest_rel
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def create(path,value):
 with pathlib.Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\\n');f.flush();os.fsync(f.fileno())
sys.dont_write_bytecode=True
'''

PRECHECK=PREFIX+'''
q=lambda a:subprocess.check_output(a,text=True).strip()
print(json.dumps(dict(observed_unix=time.time(),hostname=q(['hostname']),
 GPUs=q(['nvidia-smi','--query-gpu=uuid,name,utilization.gpu,memory.used,memory.total,compute_mode,temperature.gpu','--format=csv,noheader,nounits']),
 compute_apps=q(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory','--format=csv,noheader,nounits']),
 stage_exists=stage.exists(),output_exists=(root/'outputs'/run).exists(),
 MemAvailable_kib=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))))))
'''

INSTALL=PREFIX+'''
assert not stage.exists(),'Recover the existing original stage'
reg=read(base/'registration.json');stage.mkdir(mode=0o700)
import shutil
for name,digest in reg['payload_sha256'].items():
 assert sha(base/name)==digest
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
for name,raw in p['files'].items():
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(base64.b64decode(raw))
reg.update(stage=str(stage),source_revision=p['revision'],scope_sha256=p['authority']['scope_sha256'],
 payload_sha256={**reg['payload_sha256'],**p['hashes']},base_stage=str(base))
create(stage/'registration.json',reg);create(stage/'GPU-authorization.json',p['authority'])
print(json.dumps(dict(status='SOURCE_PREPARED_NO_GPU',registration_sha256=sha(stage/'registration.json'))))
'''

CPU=PREFIX+'''
assert not (stage/'CPU-launch.json').exists(),'Recover original CPU process'
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from four_card_bank24_execution_tools_r1 import process_environment
old=read(base/'GPU-launch.json')['commands']['container_cli']
env=process_environment(root,stage/'CPU-caches')
env['LD_LIBRARY_PATH']=next(v.split('=',1)[1] for v in old if v.startswith('LD_LIBRARY_PATH='))
cmd=['docker','run','-d','--name',stage.name+'-cpu','--network','none','--read-only','--cpus','2',
 '--cpuset-cpus','4,5','--memory','8g','--memory-swap','8g','--pids-limit','256','--tmpfs','/tmp:rw,size=512m',
 '--user',str(os.getuid())+':'+str(os.getgid()),'-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void',
 '-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2',
 '-v',str(root)+':'+str(root)+':ro','-v',str(stage)+':'+str(stage)+':rw','-w',str(root/'runtime')]
cmd += [x for k,v in env.items() for x in ('-e',k+'='+str(v))]
card=read(card_path)
if 'reuse' in card:
 source=pathlib.Path(card['reuse']['output_root']).resolve();cmd += ['-v',str(source)+':'+str(source)+':ro']
if 'carryover' in card:
 source=pathlib.Path(card['carryover']['output_root']).resolve();cmd += ['-v',str(source)+':'+str(source)+':ro']
cmd += [read(stage/'registration.json')['container_image'],'timeout','--signal=TERM','--kill-after=15s','1800',
 str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python'),str(stage/rel/'linux_cpu.py'),'--manifest',str(card_path)]
create(stage/'CPU-intent.json',dict(command=cmd,GPU_submissions=0))
q=subprocess.run(cmd,capture_output=True,text=True);create(stage/'CPU-launch.json',dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
print(json.dumps(dict(status='CPU_DISPATCHED' if q.returncode==0 else 'CPU_FAILED',stderr=q.stderr)))
'''

CPU_STATUS=PREFIX+'''
q=subprocess.run(['docker','inspect','--format','{{json .State}}',stage.name+'-cpu'],capture_output=True,text=True)
v=dict(exit_code=q.returncode,stderr=q.stderr,state=json.loads(q.stdout) if q.returncode==0 else None)
if v['state'] and not v['state']['Running']:
 q=subprocess.run(['docker','logs','--tail','30',stage.name+'-cpu'],capture_output=True,text=True);v['logs']=(q.stdout+q.stderr)[-6000:]
 if (stage/'CPU-proof.json').exists():v['proof']=read(stage/'CPU-proof.json')
print(json.dumps(v))
'''

PROVISION=PREFIX+'''
assert not (stage/'storage-launch.json').exists(),'Recover original provisioning'
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_original_handles_r1 import bind_original_process
with (stage/'storage.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/rel/'provision.py'),'--manifest',str(card_path)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 create(stage/'storage-launch.json',dict(identity=bind_original_process(child.pid),started_unix=time.time()))
 child.stdin.write(json.dumps(dict(sudo_password=packet['sudo_password'])).encode());child.stdin.close()
print(json.dumps(dict(status='STORAGE_PROVISIONING_NO_GPU',pid=child.pid)))
'''

STORAGE_STATUS=PREFIX+'''
print(json.dumps(dict(state=read(stage/'storage-state.json') if (stage/'storage-state.json').exists() else None,
 log_tail=(stage/'storage.log').read_text()[-3000:] if (stage/'storage.log').exists() else '')))
'''

ADMIT=PREFIX+'''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_fast_b36_dispatch_r2 import assets_check,selected_gpu
from wcomr.cara_fast_b36_capture_r1 import lock_free
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.history104_storage_r2 import storage_for
from four_card_bank24_execution_tools_r1 import verify_nltk_resources
reg=read(stage/'registration.json');proof=read(stage/'CPU-proof.json');card=read(card_path)
assert proof['passed'] and proof['actual_production_entry_imported'] and not proof['CUDA_initialized']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
assert proof['source_sha256']==reg['payload_sha256'] and proof['scope_sha256']==card['scope_sha256']
verify_nltk_resources(root.resolve())
if not (stage/'asset-admission.json').exists():
 create(stage/'asset-admission.json',dict(assets=assets_check(root,read(stage/'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'))))
if not (stage/'history104-storage.json').exists():create(stage/'history104-storage.json',read(stage/'storage-state.json')['result']['storage_contract'])
storage=storage_for(stage);checked=storage.check();gpu=selected_gpu(gpu_uuid)
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert not gpu['pids'] and gpu['memory_used_mib']<=1024 and gpu['compute_mode']=='Default' and gpu['utilization_percent']==0
assert mem>=50*2**30 and gpu['temperature_C']<90
assert all(lock_free(root/'.sync/gpu-locks'/(gpu_uuid+s)) for s in ('.lock','.mode-owner.lock'))
assert card['quote']['forecast_GPUh']<=(11.0 if 'pipeline' in card else limit) and not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json'))
admission=dict(authorization=read(stage/'GPU-authorization.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
 registration_sha256=sha(stage/'registration.json'),gpu=gpu,MemAvailable_bytes=mem,storage=checked,
 forecast_GPUh=card['quote']['forecast_GPUh'],observed_unix=time.time())
atomic_json(stage/'fresh-admission.json',admission);print(json.dumps(admission))
'''

CENTRAL=PREFIX+'''
sys.path[:0]=['/tmp/cara-F19-CAL35-central-f17bfbf0d188491a8821bb65604cb679/src']
from wcomr.wc73_execution_r1 import Pool,admit_host
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.cara_budget_lifecycle_r1 import IDENTITY,financial_terminal
pool=Pool(root);path=root/'reports'/(run+'.central-'+p['action']+'.json')
if p['action']=='status':
 v=pool.read();print(json.dumps(dict(totals={k:v[k] for k in ('cap_gpu_hours','used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},
 CAL35=v['jobs']['cara-F19-speed190-CAL35-r1-20261103'],job=v['jobs'].get(run),observed_unix=time.time())));raise SystemExit
if p['action']=='reserve':
 a=p['admission'];auth=a['authorization']
 with pool.transaction() as value:
  if path.exists():
   receipt=read(path);assert receipt['job']['launch_id']==auth['launch_id']
   if value==receipt['central_before']:atomic_json(pool.path,receipt['central_after'])
   else:assert value['jobs'][run]==receipt['job']
  else:
   assert run not in value['jobs'] and value['jobs']['cara-F19-speed190-CAL35-r1-20261103']['status']=='SETTLED'
   assert value['cap_gpu_hours']==250 and pool.accounting(value)['available_gpu_hours']>=limit and not value.get('budget_overrun_recorded')
   assert auth['run_id']==run and auth['billed_limit_GPUh']==limit and auth['execution_authorized'] and 0<=time.time()-a['observed_unix']<=60
   admit_host(value,'two_card')
   before=copy.deepcopy(value);after=copy.deepcopy(value)
   job={k:auth[k] for k in IDENTITY};job.update(job_id=run,registration_sha256=a['registration_sha256'],
    authorization_sha256=a['authorization_sha256'],forecast_GPUh=a['forecast_GPUh'],status='RESERVED_OR_RUNNING',kind='V2',reserved_unix=time.time(),physical_paths=request_count)
   event=auth['reservation_event']
   after['jobs'][run]=job;after.update(pool.accounting(after));after['events'].append(dict(sequence=len(after['events'])+1,unix=time.time(),type=event,job_id=run))
   receipt=dict(central_ledger_host='four_card',new_reservation=True,job=job,central_before=before,central_after=after,observed_unix=time.time())
   create(path,receipt);atomic_json(pool.path,after)
elif p['action']=='settle':
 launch,billing=financial_terminal(p['capture'],p['launch_sha256']);bill_sha=p['capture']['files']['billing']['sha256']
 with pool.transaction() as value:
  if path.exists():
   receipt=read(path);assert receipt['launch_id']==launch['launch_id'] and receipt['billing_sha256']==bill_sha
   if value==receipt['central_before']:atomic_json(pool.path,receipt['central_after'])
   else:assert value['jobs'][run]==receipt['central_after']['jobs'][run]
  else:
   assert value['jobs'][run]['launch_id']==launch['launch_id'] and value['jobs'][run]['status']=='RESERVED_OR_RUNNING'
   before=copy.deepcopy(value);after=copy.deepcopy(value);after['jobs'][run].update(status='SETTLED',actual_GPUh=billing['actual_GPUh'],billing_sha256=bill_sha,settled_unix=time.time())
   if billing['actual_GPUh']>limit:after['budget_overrun_recorded']=True
   after.update(pool.accounting(after));after['events'].append(dict(sequence=len(after['events'])+1,unix=time.time(),type='SETTLE_ACTUAL_ADDITIVELY',job_id=run))
   receipt=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=bill_sha,central_before=before,central_after=after)
   create(path,receipt);atomic_json(pool.path,after)
print(json.dumps(receipt))
'''

DISPATCH=PREFIX+'''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.cara_budget_original_handles_r1 import bind_original_process
assert not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','GPU-dispatch.json'))
create(stage/'central-reservation.json',p['envelope']);atomic_json(stage/'central-snapshot.json',p['snapshot'])
command=['python3',str(stage/rel/'ops.py'),'launch-host','--project',str(root),'--stage',str(stage),'--manifest',str(card_path)]
create(stage/'GPU-intent.json',dict(command=command,launch_id=read(stage/'GPU-authorization.json')['launch_id']))
with (stage/'host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 create(stage/'GPU-dispatch.json',dict(guardian_identity=bind_original_process(child.pid),launch_id=read(stage/'GPU-authorization.json')['launch_id']))
 child.stdin.write(json.dumps(dict(sudo_password=packet['sudo_password'])).encode());child.stdin.close()
print(json.dumps(dict(status='ORIGINAL_GUARDIAN_DISPATCHED',pid=child.pid)))
'''

STATUS=PREFIX+'''
v=dict(observed_unix=time.time())
for name in ('GPU-launch.json','guardian.json','supervisor.json','billing.json'):
 if (stage/name).exists():v[name]=read(stage/name)
if (stage/'central-settlement.json').exists():
 s=read(stage/'central-settlement.json');v['billing.json']['central_settlement_pending']=False
 v['settlement']=dict(sequence=s['central_after']['events'][-1]['sequence'],cumulative_GPUh=s['central_after']['used_gpu_hours'],actual_GPUh=s['central_after']['jobs'][run]['actual_GPUh'])
q=subprocess.run(['docker','inspect','--format','{{json .State}}',stage.name+'-gpu'],capture_output=True,text=True)
v['container_state']=json.loads(q.stdout) if q.returncode==0 else None
v['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory','--format=csv,noheader,nounits'],text=True)
target=root/'outputs'/run/'collection.json'
if target.exists():
 c=read(target);v['progress']=dict(status=c['status'],completed=sum(r['status']=='COMPLETE' for r in c['rows']),denominator=request_count,first=c['rows'][0]['status'],running=[r['slot']['id'] for r in c['rows'] if r['status']=='RUNNING'])
memory=root/'outputs'/run/'host_memory.jsonl'
if memory.exists():v['host_memory']=[json.loads(line) for line in memory.read_text().splitlines()[-3:]]
v['log_tail']=(stage/'runner.log').read_text()[-1500:] if (stage/'runner.log').exists() else (stage/'host-guardian.log').read_text()[-1500:] if (stage/'host-guardian.log').exists() else ''
print(json.dumps(v))
'''

CAPTURE=PREFIX+'''
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_lifecycle_capture_r1 import capture_lifecycle
print(json.dumps(capture_lifecycle(root,stage,sha(stage/'GPU-launch.json'))))
'''


def launch_host(project,stage):
    sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    from wcomr.cara_fast_b36_dispatch_r2 import selected_gpu
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.history104_storage_r2 import storage_for
    from cara_fast_host_guardian_r2 import container_arguments
    read=lambda path:json.loads(path.read_text())
    create=lambda path,value:path.write_text(json.dumps(value,indent=2)+'\n')
    auth=read(stage/'GPU-authorization.json');reg=read(stage/'registration.json')
    dispatch=read(stage/'GPU-dispatch.json');identity=bind_original_process(__import__('os').getpid())
    assert identity==dispatch['guardian_identity']
    snapshot=read(stage/'central-snapshot.json')
    import time,os
    assert 0<=time.time()-snapshot['observed_unix']<=60
    gpu=selected_gpu(GPU);assert not gpu['pids'] and gpu['memory_used_mib']<=1024 and gpu['compute_mode']=='Default'
    storage=storage_for(stage);storage.check()
    command=container_arguments(project,stage,storage,sha(stage/'registration.json'),'24,25',os.getuid(),os.getgid(),GPU,40)
    i=command.index(str(stage/'scripts/cara_fast_worker_r2.py'));command[i:i+2]=[str(stage/REL/'host.py'),'supervise']
    j=command.index('--entrypoint');command[j:j]=['--cidfile',str(stage/'container.cid'),
        '-v',str(stage/REL)+':'+str(stage/REL)+':ro']
    card=read(stage/CARD_REL)
    if 'reuse' in card:
        source=Path(card['reuse']['output_root']).resolve()
        command[j:j]=['-v',str(source)+':'+str(source)+':ro']
    if 'carryover' in card:
        source=Path(card['carryover']['output_root']).resolve()
        command[j:j]=['-v',str(source)+':'+str(source)+':ro']
    from wcomr.cara_budget_lifecycle_r1 import IDENTITY
    launch={k:auth[k] for k in IDENTITY}
    launch.update(CPU_fixture_only=False,container=stage.name+'-gpu',guardian_identity=identity,
        registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json'),admission_sha256=sha(stage/'fresh-admission.json'),
        commands=dict(container_cli=command,runner=[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python'),
        str(stage/REL/'runner.py'),'--project',str(project),'--stage',str(stage),'--manifest',str(stage/CARD_REL),'--source-revision',auth['source_revision'],'--gpu-uuid',GPU]))
    assert not (stage/'GPU-launch.json').exists();create(stage/'GPU-launch.json',launch)
    from wcomr.cara_budget_host_guardian_r1 import allocate
    return allocate(project,stage,storage,json.load(sys.stdin)['sudo_password'])


def payload():
    seeds=[str(p.relative_to(ROOT)) for p in HERE.glob('*.py')]
    seeds+=['scripts/cara_fast_host_guardian_r2.py','scripts/run_cara_budget_calibration_r1.py',
        'scripts/four_card_bank24_execution_tools_r1.py','scripts/four_card_policy_assets_port_r1.py',
        'scripts/cara_budget_process_bootstrap_r1.py']
    files=local_python_closure(ROOT,seeds)
    for name in (REL+'/manifest.json',REL+'/PREREGISTRATION.md',CARD_REL):
        files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    if CARD!=HERE/'manifest.json':
        name=str((CARD.parent/('RUN_HANDOFF.md' if 'carryover' in CONFIG else 'PREREGISTRATION_ADDENDUM.md')).relative_to(ROOT))
        files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name,digest in files.items():
        assert hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest()==digest,name
    card=CONFIG
    auth=dict(run_id=RUN,launch_id=uuid.uuid4().hex,host='two_card',gpu_uuid=GPU,
        stage='/data20t/gaokuangda/worldcache_workspace/.sync/'+STAGE,source_revision=revision,
        scope_sha256=card['scope_sha256'],billed_limit_GPUh=LIMIT,execution_authorized=True,
        direct_user_authorization=True,user_quote=card['authority']['user_quote'],
        reservation_event=card.get('reservation_event','SENSITIVITY8_PIPELINE_R2_WHOLE11_5_RESERVE' if REQUESTS==122 else 'SENSITIVITY8_WHOLE9_5_RESERVE' if REQUESTS==143 else 'F17_CONFIRM4_WHOLE1_95_RESERVE'),
        authorizes_replay=False,CPU_fixture_only=False,central_transaction_authorized=True)
    return dict(files={name:base64.b64encode((ROOT/name).read_bytes()).decode() for name in files},
        hashes=files,revision=revision,authority=auth)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action')
    parser.add_argument('--receipt',type=Path);parser.add_argument('--input',type=Path)
    parser.add_argument('--project',type=Path);parser.add_argument('--stage',type=Path)
    parser.add_argument('--manifest',type=Path,default=CARD)
    parser.add_argument('--route',choices=('ipv4','v6','relay'),default='ipv4');args=parser.parse_args()
    if CONFIG['phase']=='FORMAL_QUOTE_AWAITING_APPROVAL' and args.action in ('prepare','reserve','dispatch','launch-host'):
        raise ValueError('Pipeline quote has no GPU or reservation authority')
    if args.action=='launch-host':launch_host(args.project,args.stage);return
    from cara_f19_speed190_transport_r1 import rpc
    if args.receipt.exists():raise ValueError('Preserve the original observation/transaction')
    data=json.loads(args.input.read_text()) if args.input else {}
    if args.action=='prepare':
        data=payload()
        if BINDING.exists():raise ValueError('Original binding already exists; recover it')
        BINDING.write_text(json.dumps({k:v for k,v in data.items() if k!='files'},indent=2)+'\n')
    if args.action in ('central-status','reserve','settle'):
        data.update(action={'central-status':'status','reserve':'reserve','settle':'settle'}[args.action])
        result=rpc(CENTRAL,data,host='four_card',route=args.route)
    elif args.action=='dispatch':
        result=rpc(DISPATCH,data,route=args.route)
    else:
        code={'precheck':PRECHECK,'prepare':INSTALL,'cpu':CPU,'cpu-status':CPU_STATUS,
              'provision':PROVISION,'storage-status':STORAGE_STATUS,'admit':ADMIT,'status':STATUS,'capture':CAPTURE}[args.action]
        result=rpc(code,data,route=args.route,timeout=300 if args.action=='admit' else 90)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','state','totals','progress','stderr','log_tail') if k in result}))


if __name__=='__main__':main()
