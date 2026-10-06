import ast,base64,hashlib,io,json,subprocess,tarfile
from pathlib import Path
m=json.loads(Path('manifests/wc_w1_own_state_execution_20261006.json').read_text())
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as archive:
 for name,source in m['source_path_by_stage_path'].items():
  p=Path(source);assert hashlib.sha256(p.read_bytes()).hexdigest()==m['payload_sha256'][name]
  archive.add(p,arcname=name)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
remote='M='+repr(m)+'\nSOURCE='+repr(source)+'\nPAYLOAD='+repr(base64.b64encode(buf.getvalue()).decode())+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage'];base=root/M['base_stage']
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not stage.exists(),'Existing selected stage: inspect original handles; never resubmit'
assert not (root/'outputs/wc-w1-own-state-shadow-r1').exists(),'Original run already exists'
assert sha(root/'reports/budget.json')==M['budget_before_sha256'],'Budget changed; fresh admission required'
assert sha(base/'receipt.json')==M['base_original_receipt_sha256']
for n,d in M['base_payload_sha256'].items():assert sha(base/n)==d,n
stage.mkdir()
for n,d in M['base_payload_sha256'].items():
 if n=='own-state-config.json':continue
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/n,target)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(PAYLOAD)),mode='r:gz') as archive:
 assert all(i.isfile() and not pathlib.Path(i.name).is_absolute() and '..' not in pathlib.Path(i.name).parts for i in archive.getmembers())
 archive.extractall(stage)
for n,d in M['payload_sha256'].items():assert sha(stage/n)==d,n
approval='manifests/wc_w1_own_state_gpu_authorization_20261006.json';target=root/approval
if target.exists():assert sha(target)==M['payload_sha256'][approval]
else:
 with target.open('xb') as file:file.write((stage/approval).read_bytes())
(stage/'manifest.json').write_text(json.dumps(M,indent=2)+chr(10))
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python';runtime=root/'runtime'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(root/'hfhub'),PYTHONPATH=str(stage/'src'))
config=json.loads((stage/'own-state-config.json').read_text());output=root/'outputs'/config['run_id']
command=[python,'-u',str(stage/'scripts/run_w1_own_state.py'),'--project',str(root),'--stage',str(stage),
 '--runtime',str(runtime),'--output',str(output/'diagnostic'),'--gpu-uuid',M['gpu_uuid'],'--source-revision',SOURCE,'--validate-only']
started=time.time()
with (stage/'selected-preflight.log').open('w') as out,(stage/'selected-preflight.err').open('w') as err:
 child=subprocess.Popen(command,cwd=runtime,env=env,stdout=out,stderr=err)
 (stage/'selected-preflight-handle.json').write_text(json.dumps({'PID':child.pid,'CPU_only':True,'started_unix':started})+chr(10))
 try:code=child.wait(timeout=120)
 except subprocess.TimeoutExpired:child.kill();child.wait();code=124
proof={'status':'APPROVED_SELECTED_CPU_PREFLIGHT_PASS_NOT_GPU' if code==0 else 'APPROVED_SELECTED_CPU_PREFLIGHT_FAILED',
 'exit_code':code,'CPU_wall_seconds':time.time()-started,'source_revision':SOURCE,'payload_sha256':M['payload_sha256'],
 'budget_sha256':sha(root/'reports/budget.json'),'GPU_submissions':0}
(stage/'selected-preflight.json').write_text(json.dumps(proof,indent=2)+chr(10))
assert code==0,(stage/'selected-preflight.err').read_text()[-5000:]
assert sha(root/'reports/budget.json')==M['budget_before_sha256']
# Exclusive durable submission marker; after unknown transport outcome inspect this exact stage/handle.
marker=stage/'submission.json'
with marker.open('x') as file:file.write(json.dumps({'status':'APPROVED_SINGLE_SUBMISSION_START_PENDING','source_revision':SOURCE,'started_unix':time.time(),'GPU_submission_attempts':1})+chr(10))
command=[python,'-u',str(stage/'scripts/supervise_w1_own_state.py'),'--project',str(root),'--stage',str(stage),
 '--output',str(output),'--gpu-uuid',M['gpu_uuid'],'--source-revision',SOURCE]
env=dict(env,CUDA_VISIBLE_DEVICES=M['gpu_uuid'])
with (stage/'supervisor-launch.log').open('w') as log:
 supervisor=subprocess.Popen(command,cwd=runtime,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
handle={'status':'SUPERVISOR_DISPATCHED_NOT_EXPERIMENT_ACCEPTANCE','supervisor_pid':supervisor.pid,'source_revision':SOURCE,
 'stage':str(stage),'output':str(output),'gpu_uuid':M['gpu_uuid'],'dispatched_unix':time.time(),'CPU_preflight':proof,
 'selected_preflight_sha256':sha(stage/'selected-preflight.json'),'submission_marker':str(marker),'GPU_submission_attempts':1}
(stage/'supervisor-handle.json').write_text(json.dumps(handle,indent=2)+chr(10))
print(json.dumps(handle))
'''
ast.parse(remote)
p=subprocess.run(ssh+['timeout 180s python3 -u -'],input=remote,text=True,capture_output=True,timeout=210)
Path('.sync/w1-own-state-approved-launch-transport-20261006.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
assert p.returncode==0,p.stderr[-5000:]
r=json.loads(p.stdout);r['executed_deploy_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
Path('reports/wc_w1_own_state_dispatch_20261006.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','supervisor_pid','source_revision','dispatched_unix']}));print(json.dumps(r['CPU_preflight']))
