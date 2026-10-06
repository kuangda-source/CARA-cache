"""Unique three-scene production CPU stage, passed core reused without rerun."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

m=json.loads(Path('manifests/wc_w1_own_state_production_cpu_r2_20261006.json').read_text())
prior=json.loads(Path('reports/wc_w1_own_state_production_actual_cpu_r1_20261006.json').read_text())
old=json.loads(Path('manifests/wc_w1_native_reference_execution_20261006.json').read_text())
ssh=ast.literal_eval(next(n.value for n in ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text()).body
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
    for name,d in m['payload_sha256'].items():
        if m['base_payload_sha256'].get(name)==d or m['own_core_payload_sha256'].get(name)==d:continue
        path=Path(m['source_path_by_stage_path'].get(name,name))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==d,name
        archive.add(path,arcname=name)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
remote='PRIOR='+repr(prior)+'\nM='+repr(m)+'\nOLD='+repr(old)+'\nSOURCE='+repr(source)+'\nPAYLOAD='+repr(base64.b64encode(buffer.getvalue()).decode())+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');runtime=root/'runtime';stage=root/M['stage'];base=root/M['base_stage'];core=root/M['own_core_stage']
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not stage.exists(),'Never restart an existing CPU stage'
priorstage=root/'.sync/wc-w1-own-state-production-cpu-r1-20261006'
assert sha(priorstage/'receipt.json')==PRIOR['original_receipt_sha256']
assert PRIOR['checks'][0]['exit_code']==0
assert all(PRIOR['checks'][0]['result']['budget_snapshot'][k]==json.loads((root/'reports/budget.json').read_text())[k] for k in ['cap_gpu_hours','used_gpu_hours','gpu_jobs_launched'])
before=(root/'reports/budget.json').read_bytes();assert hashlib.sha256(before).hexdigest()==M['budget_sha256']
assert sha(base/'receipt.json')==M['base_original_receipt_sha256']
assert sha(core/'receipt.json')==M['own_core_original_receipt_sha256']
for name,d in OLD['payload_sha256'].items():assert sha(root/OLD['stage']/name)==d
for previous,files in [(base,M['base_payload_sha256']),(core,M['own_core_payload_sha256'])]:
 for name,d in files.items():assert sha(previous/name)==d,name
stage.mkdir()
for previous,files in [(base,M['base_payload_sha256']),(core,M['own_core_payload_sha256'])]:
 for name,d in files.items():
  if M['payload_sha256'].get(name)==d:
   target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(previous/name,target)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(PAYLOAD)),mode='r:gz') as archive:
 assert all(i.isfile() and not pathlib.Path(i.name).is_absolute() and '..' not in pathlib.Path(i.name).parts for i in archive.getmembers())
 archive.extractall(stage)
for name,d in M['payload_sha256'].items():assert sha(stage/name)==d,name
(stage/'manifest.json').write_text(json.dumps(M,indent=2)+chr(10))
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 PYTHONPATH=str(stage/'src'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(root/'hfhub'))
c=json.loads((stage/'own-state-config.json').read_text())
entry=[python,'-u',str(stage/'scripts/run_w1_own_state.py'),'--project',str(root),'--stage',str(stage),
 '--runtime',str(runtime),'--output',str(root/'outputs'/c['run_id']/'diagnostic')]
checker=[python,'-u',str(stage/'tests/check_w1_own_state_production_cpu.py'),'--stage',str(stage),'--runtime',str(runtime)]
commands=[('new-stage-source-and-reused-R1-assets',[python,'-c',"from pathlib import Path;import json;from wcomr.own_state_execution import validate_stage;print(json.dumps(validate_stage(Path("+repr(str(root))+"),Path("+repr(str(stage))+"),Path("+repr(str(runtime))+"),json.loads(Path("+repr(str(stage/'own-state-config.json'))+").read_text()))))"],120,True),
 ('new-full-pipeline-bridge-cost-and-supervision',checker,90,True),
 ('actual-original-typed-request-import',checker+['--actual-import'],120,True)]
for script in ['run_w1_own_state','supervise_w1_own_state','audit_w1_own_state_terminal','summarize_w1_own_state']:
 commands.append((script+'-help',[python,str(stage/'scripts'/(script+'.py')),'--help'],30,False))
started=time.time();checks=[];code=0
(stage/'CPU-start.json').write_text(json.dumps({'PID':os.getpid(),'source_revision':SOURCE,'started_unix':started,'CPU_only':True})+chr(10))
for name,command,limit,parse in commands:
 t=time.time()
 with (stage/(name+'.log')).open('w') as out,(stage/(name+'.err')).open('w') as err:
  child=subprocess.Popen(command,env=env,cwd=runtime,stdout=out,stderr=err)
  (stage/(name+'-handle.json')).write_text(json.dumps({'PID':child.pid,'CPU_supervisor_PID':os.getpid(),'limit_seconds':limit,'CPU_only':True})+chr(10))
  try:code=child.wait(timeout=limit)
  except subprocess.TimeoutExpired:child.kill();child.wait();code=124
 item={'name':name,'exit_code':code,'CPU_wall_seconds':time.time()-t}
 if code==0:item['result']=json.loads((stage/(name+'.log')).read_text().strip().splitlines()[-1]) if parse else {'help_only':True}
 else:item['error_tail']=(stage/(name+'.err')).read_text()[-8000:]
 checks.append(item)
 if code:break
assert before==(root/'reports/budget.json').read_bytes()
for previous,files in [(root/OLD['stage'],OLD['payload_sha256']),(base,M['base_payload_sha256']),(core,M['own_core_payload_sha256'])]:
 for name,d in files.items():assert sha(previous/name)==d
r={'status':'OWN_STATE_PRODUCTION_ACTUAL_CPU_PASS_NOT_GPU' if code==0 else 'OWN_STATE_PRODUCTION_ACTUAL_CPU_FAILURE',
 'exit_code':code,'CPU_source_revision':SOURCE,'CPU_supervisor_PID':os.getpid(),'CPU_wall_seconds':time.time()-started,
 'checks':checks,'payload_sha256':M['payload_sha256'],'budget_sha256':M['budget_sha256'],'budget_unchanged':True,
 'old_160_GPU_files_unchanged':True,'passed_core_original_unchanged':True,'passed_core_fixture_not_rerun':True,
 'CUDA_initialized':False,'GPU_submissions':0,'actual_new_videos':0,'scientific_labels':0,'planned_scientific_scenes':3,
 'planned_scientific_observations':12,'CPU_fixture_not_real_Cosmos_network_or_codec':True,'passed_R1_asset_gate_reused':True,'failed_R1_stage_preserved':True}
raw=(json.dumps(r,indent=2)+chr(10)).encode();(stage/'receipt.json').write_bytes(raw)
print(json.dumps({'receipt':r,'original_receipt_sha256':hashlib.sha256(raw).hexdigest()}))
'''
ast.parse(remote)
p=subprocess.run(ssh+['timeout 480s python3 -u -'],input=remote,text=True,capture_output=True,timeout=510)
Path('.sync/w1-own-state-production-cpu-r2-transport-20261006.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
assert p.returncode==0,p.stderr[-8000:]
value=json.loads(p.stdout);r=value['receipt'];r['original_receipt_sha256']=value['original_receipt_sha256']
r['executed_transfer_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target=Path('reports/wc_w1_own_state_production_actual_cpu_r1_20261006.json');assert not target.exists();target.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','exit_code','CPU_wall_seconds','original_receipt_sha256']}))
for check in r['checks']:print(json.dumps(check))
