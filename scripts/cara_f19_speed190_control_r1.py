"""Operate/recover only the single user-approved CAL35 original allocation."""
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
from cara_f19_speed190_ops_r1 import PREFIX
from cara_f19_speed190_transport_r1 import ROOT,rpc
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_f19_speed190_identity_r1 import RUN,STAGE,MANIFEST
from wcomr.immutable_stage_payload_r1 import local_python_closure

BIND=PREFIX+"""
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_f19_speed190_execution_r1 import validate_stage,read,fresh,capture,RUN
from wcomr.gpu_budget_pool_v2 import atomic_json
"""
STATUS=BIND+"""
result=dict(status='ORIGINAL_CAL35_STATUS',authority=read(stage/'GPU-authorization.json'),registration_sha256=sha(stage/'registration.json'),observed_unix=time.time())
for n in ('CPU-launch.json','CPU-r2-launch.json','CPU-proof.json','storage-state.json','GPU-intent.json','GPU-dispatch.json','GPU-launch.json','pg-runner-context-ready.json','pg-runner-context-granted.json','runner-start.json','supervisor-start.json','guardian.json','supervisor.json','billing.json'):
 if (stage/n).exists():result[n]=read(stage/n)
if (stage/'GPU-launch.json').exists():
 result['launch_sha256']=sha(stage/'GPU-launch.json');result['lifecycle']=capture(root,stage)
monitor=stage/'exclusive-monitor.jsonl'
if monitor.exists():
 with monitor.open('rb') as stream:
  stream.seek(max(0,monitor.stat().st_size-65536));lines=stream.read().splitlines()
  if lines:result['last_exclusive_monitor']=json.loads(lines[-1])
output=root/'outputs'/RUN
if output.exists():
 result['output_free_bytes']=os.statvfs(output).f_bavail*os.statvfs(output).f_frsize
 if (output/'collection.json').exists():
  c=read(output/'collection.json');result['operational_progress']=dict(status=c['status'],complete=sum(r['status']=='COMPLETE' for r in c['rows']),denominator=35,running=[r['slot'] for r in c['rows'] if r['status']=='RUNNING'],scientific_scores_read=False)
if (stage/'host-guardian.log').exists():result['guardian_log_tail']=(stage/'host-guardian.log').read_text()[-3000:]
q=subprocess.run(['docker','inspect',stage.name+'-gpu'],capture_output=True,text=True)
if q.returncode==0:
 c=json.loads(q.stdout)[0];result['container_state']=c['State']
 if not c['State']['Running']:
  q=subprocess.run(['docker','logs','--tail','45',stage.name+'-gpu'],capture_output=True,text=True);result['container_logs']=(q.stdout+q.stderr)[-6500:]
print(json.dumps(result))
"""
DISPATCH=BIND+"""
validate_stage(root,stage)
assert not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','GPU-dispatch.json','guardian-intent.json')),'Original dispatch exists; recover only'
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_f19_speed190_execution_r1 import HOST_ENTRY
assert p['snapshot']['ledger']['jobs'][RUN]==p['envelope']['job']
if (stage/'central-reservation.json').exists():assert read(stage/'central-reservation.json')==p['envelope']
else:create(stage/'central-reservation.json',p['envelope'])
atomic_json(stage/'central-snapshot.json',p['snapshot'])
admission=fresh(root,stage);atomic_json(stage/'fresh-admission.json',admission)
assert 0<=time.time()-p['snapshot']['observed_unix']<=60
command=['python3',str(stage/HOST_ENTRY),'guardian','--project',str(root),'--stage',str(stage)]
create(stage/'GPU-intent.json',dict(launch_id=read(stage/'GPU-authorization.json')['launch_id'],command=command,observed_unix=time.time(),no_replay=True))
with (stage/'host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 result=dict(status='ORIGINAL_CAL35_GUARDIAN_DISPATCHED',guardian_identity=bind_original_process(child.pid),
  launch_id=read(stage/'GPU-authorization.json')['launch_id'],intent_sha256=sha(stage/'GPU-intent.json'))
 create(stage/'GPU-dispatch.json',result)
 child.stdin.write(json.dumps(dict(sudo_password=packet['sudo_password'])).encode());child.stdin.close()
print(json.dumps(result))
"""
CENTRAL="""
import base64,hashlib,json,pathlib,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
auth=p['authority'];source=pathlib.Path('/tmp')/('cara-F19-CAL35-central-'+auth['launch_id'])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
expected=p['hashes']
old=pathlib.Path('/tmp/source-lifecycle-P1-central-operator-498503f9cfd249f1aab929da18f04e10')
def previous(n):
 for base in (root,old):
  f=base/n
  if f.is_file() and not f.is_symlink() and sha(f)==expected[n]:return f
 return None
if p['action']=='compare':
 print(json.dumps(dict(status='CENTRAL_OPERATOR_COMPARE_ONLY',needed=[n for n in expected if previous(n) is None])));raise SystemExit
if not source.exists():
 assert p['action']=='prepare','Prepare exact original operator first'
 source.mkdir(mode=0o700)
 for n,h in expected.items():
  relative=pathlib.Path(n);assert not relative.is_absolute() and '..' not in relative.parts
  raw=base64.b64decode(p['files'][n]) if n in p['files'] else previous(n).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==h
  target=source/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
assert all(sha(source/n)==h for n,h in expected.items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(source/'src')]
from wcomr.cara_f19_speed190_execution_r1 import reserve,settle,RUN
from wcomr.wc73_execution_r1 import Pool
pool=Pool(root);envelope=None;settlement=None
if p['action']=='reserve':envelope=reserve(root,p['admission'])
if p['action']=='settle':settlement=settle(root,p['capture'],p['launch_sha256'])
ledger=pool.read()
print(json.dumps(dict(status='CAL35_CENTRAL_'+p['action'].upper(),ledger=ledger,envelope=envelope,settlement=settlement,observed_unix=time.time())))
"""
SCORE=BIND+"""
from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
from wcomr.cara_f19_speed190_identity_r1 import MANIFEST
validate_stage(root,stage)
release=released_lifecycle(p['capture'],sha(stage/'GPU-launch.json'),p['settlement'])
assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
control=stage/'released-score-control';name=stage.name+'-score'
q=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
if q.returncode==0:
 c=json.loads(q.stdout)[0]
 original=read(control/'launch.json');assert c['Id']==original['stdout'].strip()
 h=c['HostConfig'];assert c['Image']==read(stage/'registration.json')['container_image']
 assert not h.get('DeviceRequests') and h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==2000000000
 assert h['CpusetCpus']=='4,5' and h['NetworkMode']=='none' and h['ReadonlyRootfs']
 assert {'CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void'}<=set(c['Config']['Env'])
 result=dict(status='SCORE_RUNNING' if c['State']['Running'] else 'SCORE_TERMINAL',state=c['State'])
 if (control/'scores.json').exists():
  state=read(control/'scores.json');result['progress']=dict(status=state['status'],RGB=len(state['RGB']),LPIPS=len(state['LPIPS']),quality=len(state['quality_rows']))
  if not c['State']['Running']:result['scores']=state
 if not c['State']['Running']:
  q=subprocess.run(['docker','logs','--tail','35',name],capture_output=True,text=True);result['logs']=(q.stdout+q.stderr)[-5000:]
 print(json.dumps(result));raise SystemExit
assert 'No such object' in q.stderr and not control.exists(),'Recover original scorer, never relaunch'
control.mkdir();output=root/'outputs'/RUN
assert read(output/'collection.json')['status']=='COMPLETE35_PENDING_RELEASE_SCORING'
create(control/'release.json',release);create(control/'capture.json',p['capture']);create(control/'settlement.json',p['settlement'])
config=dict(manifest=MANIFEST,output=str(output),collection_sha256=sha(output/'collection.json'),launch_sha256=sha(stage/'GPU-launch.json'),
 release_sha256=sha(control/'release.json'),torch_home=str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/torch'),
 piq_site=str(root/'.sync/wc-time-score-CPU-two_card-r1-20261027/site'))
create(control/'score-config.json',config)
launch=read(base/'GPU-launch.json');old=launch['commands']['container_cli'];env=[]
for i,v in enumerate(old[:-1]):
 if v=='-e' and old[i+1].split('=',1)[0] in ('PATH','LD_LIBRARY_PATH'):env.extend(['-e',old[i+1]])
from four_card_bank24_execution_tools_r1 import process_environment
full_environment=process_environment(root,control/'caches')
full_environment['LD_LIBRARY_PATH']=next(v.split('=',1)[1] for v in old if v.startswith('LD_LIBRARY_PATH='))
env=[item for k,v in full_environment.items() for item in ('-e',k+'='+str(v))]
cmd=['docker','run','-d','--name',name,'--network','none','--read-only','--cpus','2','--cpuset-cpus','4,5',
 '--memory','8g','--memory-swap','8g','--pids-limit','256','--tmpfs','/tmp:rw,size=512m','--user',str(os.getuid())+':'+str(os.getgid()),
 '-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void','-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2',
 '-e','OPENBLAS_NUM_THREADS=2','-e','HF_HUB_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1',
 '-v',str(root)+':'+str(root)+':ro','-v',str(output)+':'+str(output)+':ro','-v',str(control)+':'+str(control)+':rw','-w',str(root/'runtime')]+env
cmd += [read(stage/'registration.json')['container_image'],'timeout','--signal=TERM','--kill-after=15s','21600',launch['commands']['runner'][0],
 str(stage/'scripts/score_cara_f19_speed190_r1.py'),'--stage',str(stage),'--control',str(control)]
create(control/'intent.json',dict(command=cmd,launch_sha256=sha(stage/'GPU-launch.json'),created_unix=time.time(),no_replay=True,GPU_submissions=0))
q=subprocess.run(cmd,capture_output=True,text=True);create(control/'launch.json',dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
print(json.dumps(dict(status='SCORE_DISPATCHED' if q.returncode==0 else 'SCORE_LAUNCH_FAILED_NO_RETRY',exit_code=q.returncode,stderr=q.stderr[-1000:])))
"""


def read(path):return json.loads(Path(path).read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('status','central-prepare','reserve','dispatch','settle','score','export'))
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--input',type=Path);p.add_argument('--route',default='v6',choices=('v6','ipv4'));a=p.parse_args()
    assert not a.receipt.exists()
    data=read(a.input) if a.input else {}
    if a.action=='status':v=rpc(STATUS,{},route=a.route)
    elif a.action=='dispatch':v=rpc(DISPATCH,data,route=a.route)
    elif a.action=='score':v=rpc(SCORE,data,route=a.route)
    elif a.action=='export':
        code=BIND+"""
from wcomr.cara_budget_lifecycle_r1 import released_lifecycle
release=released_lifecycle(p['capture'],sha(stage/'GPU-launch.json'),p['settlement'])
assert release['GPU_released'] and release['cost_settled'] and release['container_exit_success']
print(json.dumps(dict(status='RELEASED_CAL35_ARTIFACTS',collection=read(root/'outputs'/RUN/'collection.json'),release=release,
 scores=read(stage/'released-score-control/scores.json'))))
"""
        v=rpc(code,data,route=a.route)
    else:
        binding=read(ROOT/'.sync/cara-f19-CAL35-original-binding.json');auth=binding['authority']
        files=binding.get('central_source_sha256') or local_python_closure(ROOT,['src/wcomr/cara_f19_speed190_execution_r1.py'])
        args=dict(action={'central-prepare':'prepare','reserve':'reserve','settle':'settle'}[a.action],authority=auth,hashes=files,**data)
        if a.action=='central-prepare':
            compare=rpc(CENTRAL,{**args,'action':'compare'},host='four_card',route=a.route)
            if compare.get('status')!='CENTRAL_OPERATOR_COMPARE_ONLY':v=compare
            else:
                args['files']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in compare['needed']}
                v=rpc(CENTRAL,args,host='four_card',route=a.route)
        else:v=rpc(CENTRAL,args,host='four_card',route=a.route)
    with a.receipt.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v.get(k) for k in ('status','stderr','container_state','progress','operational_progress','logs')}))


if __name__=='__main__':main()
