import ast,base64,hashlib,io,json,subprocess,tarfile
from pathlib import Path
m=json.loads(Path('manifests/wc_w1_native_reference_core_cpu_r1_20261006.json').read_text())
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
# Old snapshots already exist on the server; send only the genuinely new small files.
root_sources={'reports/w1_replay_r1_runner.json','reports/w1d_cal8_r1_runner.json','configs/cal_w1d8.jsonl','configs/f1_setup.json'}
extra={k:v for k,v in m['payload_sha256'].items() if k not in m['base_payload_sha256']}
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as archive:
 for name,digest in extra.items():
  source=Path(m['source_path_by_stage_path'][name]);assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,name
  if name not in root_sources:archive.add(source,arcname=name)
source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
remote='MANIFEST='+repr(m)+'\nEXTRA='+repr(extra)+'\nROOT_SOURCES='+repr(list(root_sources))+'\nPAYLOAD='+repr(base64.b64encode(buf.getvalue()).decode())+'\nSOURCE='+repr(source_revision)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,shutil,subprocess,sys,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');runtime=root/'runtime';stage=root/MANIFEST['stage'];base=root/MANIFEST['base_stage']
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not stage.exists(), 'Existing stage: inspect its original handles/receipt; never restart'
before=(root/'reports/budget.json').read_bytes();assert hashlib.sha256(before).hexdigest()==MANIFEST['budget_sha256']
assert sha(base/'receipt.json')==MANIFEST['base_original_receipt_sha256']
stage.mkdir()
for name,digest in MANIFEST['base_payload_sha256'].items():
 assert sha(base/name)==digest,name
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/name,target)
for name in ROOT_SOURCES:
 if name in EXTRA:
  assert sha(root/name)==EXTRA[name],name
  target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(PAYLOAD)),mode='r:gz') as archive:
 assert all(i.isfile() and not pathlib.Path(i.name).is_absolute() and '..' not in pathlib.Path(i.name).parts for i in archive.getmembers())
 archive.extractall(stage)
(stage/'manifest.json').write_text(json.dumps(MANIFEST,indent=2)+chr(10))
for name,digest in MANIFEST['payload_sha256'].items():assert sha(stage/name)==digest,name
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 PYTHONPATH=str(stage/'src'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(root/'hfhub'))
entry=[python,'-u',str(stage/'scripts/check_w1_native_reference_core_cpu.py'),'--project',str(root),'--stage',str(stage),'--runtime',str(runtime)]
validator='import importlib.util,json;from pathlib import Path;from wcomr.w1_native_reference_scope import validate_core_stage;stage=Path('+repr(str(stage))+');root=Path('+repr(str(root))+');runtime=root/"runtime";c=json.loads((stage/"native-core-config.json").read_text());r=validate_core_stage(stage,root,runtime,c);s=importlib.util.spec_from_file_location("old_readonly_asset_gate",stage/"scripts/run_wc_s0_profile.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.validate(root,stage,runtime);print(json.dumps(dict(r,existing_asset_gate="REUSED_READ_ONLY_NOT_OLD_JOB")))'
commands=[('real-root-source-scope-assets',[python,'-c',validator],120),
 ('scope-16-refusals',entry+['--pure-only'],30),('two-complete-five-reference-torch-fixtures',entry,120),
 ('actual-native-class-original-arguments-import',entry+['--actual-import'],120)]
started=time.time();checks=[];code=0
(stage/'CPU-start.json').write_text(json.dumps({'PID':os.getpid(),'source_revision':SOURCE,'started_unix':started,'CPU_only':True,'CUDA_VISIBLE_DEVICES':''},indent=2)+chr(10))
for name,cmd,limit in commands:
 t=time.time()
 with (stage/(name+'.log')).open('w') as out,(stage/(name+'.err')).open('w') as err:
  child=subprocess.Popen(cmd,env=env,cwd=runtime,stdout=out,stderr=err)
  (stage/(name+'-handle.json')).write_text(json.dumps({'PID':child.pid,'supervisor_PID':os.getpid(),'started_unix':t,'limit_seconds':limit,'CPU_only':True},indent=2)+chr(10))
  try:code=child.wait(timeout=limit)
  except subprocess.TimeoutExpired:child.kill();child.wait();code=124
 item={'name':name,'exit_code':code,'CPU_wall_seconds':time.time()-t}
 if code==0:item['result']=json.loads((stage/(name+'.log')).read_text().strip().splitlines()[-1])
 else:item['error_tail']=(stage/(name+'.err')).read_text()[-6000:]
 checks.append(item)
 if code:break
assert before==(root/'reports/budget.json').read_bytes()
for name,digest in MANIFEST['base_payload_sha256'].items():assert sha(base/name)==digest,name
r={'status':'FIVE_NATIVE_REFERENCE_ACTUAL_CPU_CORE_AND_IMPORT_PASS_NOT_GPU' if code==0 else 'FIVE_NATIVE_REFERENCE_ACTUAL_CPU_CORE_FAILURE',
 'exit_code':code,'CPU_source_revision':SOURCE,'CPU_supervisor_PID':os.getpid(),'CPU_wall_seconds':time.time()-started,'checks':checks,
 'payload_sha256':MANIFEST['payload_sha256'],'upstream_sha256':MANIFEST['upstream_sha256'],'budget_unchanged':True,
 'old_B_stage_source_unchanged':True,'CUDA_initialized':False,'GPU_submissions':0,'actual_new_videos':0,'reference_phases':5,
 'original_denominator':[8,7,1],'production_supervisor_ready':False,'new_GPU_authorization':False}
raw=(json.dumps(r,indent=2)+chr(10)).encode();(stage/'receipt.json').write_bytes(raw)
print(json.dumps({'receipt':r,'server_receipt_sha256':hashlib.sha256(raw).hexdigest()}))
'''
ast.parse(remote)
p=subprocess.run(ssh+['timeout 480s python3 -u -'],input=remote,text=True,capture_output=True,timeout=510)
Path('.sync/w1-native-core-cpu-r1-attempt-20261006.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
assert p.returncode==0,p.stderr[-4000:]
value=json.loads(p.stdout);r=value['receipt'];r['server_receipt_sha256']=value['server_receipt_sha256'];r['executed_transfer_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
Path('reports/wc_w1_native_reference_core_actual_cpu_r1_20261006.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','exit_code','CPU_wall_seconds','server_receipt_sha256']}))
for c in r['checks']:print(json.dumps({k:c[k] for k in ['name','exit_code','CPU_wall_seconds']},ensure_ascii=False))
if r['exit_code']:print(r['checks'][-1].get('error_tail'))
