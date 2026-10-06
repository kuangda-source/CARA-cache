"""Unique isolated CPU core transfer; existing workloads/payloads and ledger untouched."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

m = json.loads(Path('manifests/wc_w1_own_state_core_cpu_r2_20261006.json').read_text())
old = json.loads(Path('manifests/wc_w1_native_reference_execution_20261006.json').read_text())
budget_sha = hashlib.sha256(Path('reports/budget.json').read_bytes()).hexdigest()
tree = ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'ssh' for t in n.targets)))
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
    for name, digest in m['payload_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
        archive.add(name, arcname=name)
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
remote = ('M=' + repr(m) + '\nOLD=' + repr(old) + '\nBUDGET_SHA=' + repr(budget_sha)
    + '\nSOURCE=' + repr(source) + '\nPAYLOAD=' + repr(base64.b64encode(buffer.getvalue()).decode()) + '\n' + r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage'];runtime=root/'runtime'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not stage.exists(),'Existing CPU stage: inspect original handles, never restart'
before=(root/'reports/budget.json').read_bytes();assert hashlib.sha256(before).hexdigest()==BUDGET_SHA
for name,digest in OLD['payload_sha256'].items():assert sha(root/OLD['stage']/name)==digest
assert sha(root/M['failed_R1_stage']/'receipt.json')==M['failed_R1_original_receipt_sha256']
stage.mkdir()
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(PAYLOAD)),mode='r:gz') as archive:
 assert all(i.isfile() and not pathlib.Path(i.name).is_absolute() and '..' not in pathlib.Path(i.name).parts for i in archive.getmembers())
 archive.extractall(stage)
for name,digest in M['payload_sha256'].items():assert sha(stage/name)==digest
(stage/'manifest.json').write_text(json.dumps(M,indent=2)+chr(10))
started=time.time();handle={'CPU_supervisor_PID':os.getpid(),'started_unix':started,'CPU_source_revision':SOURCE,'CPU_only':True}
(stage/'start.json').write_text(json.dumps(handle)+chr(10))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 PYTHONPATH=str(stage/'src'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
 str(stage/'scripts/check_w1_own_state_core_cpu.py'),'--stage',str(stage),'--runtime',str(runtime)]
with (stage/'core.log').open('w') as out,(stage/'core.err').open('w') as err:
 child=subprocess.Popen(cmd,env=env,cwd=runtime,stdout=out,stderr=err)
 (stage/'core-handle.json').write_text(json.dumps({'PID':child.pid,'CPU_supervisor_PID':os.getpid(),'CPU_only':True,'limit_seconds':180})+chr(10))
 try:code=child.wait(timeout=180)
 except subprocess.TimeoutExpired:child.kill();child.wait();code=124
result=json.loads((stage/'core.log').read_text().strip().splitlines()[-1]) if code==0 else None
assert before==(root/'reports/budget.json').read_bytes()
for name,digest in OLD['payload_sha256'].items():assert sha(root/OLD['stage']/name)==digest
r={'status':'OWN_STATE_SHADOW_CORE_ACTUAL_CPU_PASS_NOT_GPU' if code==0 else 'OWN_STATE_SHADOW_CORE_ACTUAL_CPU_FAILURE',
 'exit_code':code,'CPU_source_revision':SOURCE,'CPU_supervisor_PID':os.getpid(),'CPU_child_PID':child.pid,
 'CPU_wall_seconds':time.time()-started,'result':result,'error_tail':(stage/'core.err').read_text()[-6000:] if code else None,
 'payload_sha256':M['payload_sha256'],'budget_before_sha256':BUDGET_SHA,'budget_unchanged':True,
 'original_160_GPU_source_files_unchanged':True,'GPU_submissions':0,'actual_model_runs':0,'scientific_labels':0}
raw=(json.dumps(r,indent=2)+chr(10)).encode();(stage/'receipt.json').write_bytes(raw)
print(json.dumps({'receipt':r,'original_receipt_sha256':hashlib.sha256(raw).hexdigest()}))
''')
ast.parse(remote)
p = subprocess.run(ssh + ['timeout 210s python3 -u -'], input=remote, text=True, capture_output=True, timeout=230)
Path('.sync/w1-own-state-core-cpu-r2-transport-20261006.json').write_text(
    json.dumps({'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}, indent=2) + '\n')
assert p.returncode == 0, p.stderr[-5000:]
value = json.loads(p.stdout)
r = value['receipt']
r['original_receipt_sha256'] = value['original_receipt_sha256']
r['executed_transfer_wrapper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target = Path('reports/wc_w1_own_state_core_actual_cpu_r2_20261006.json')
assert not target.exists()
target.write_text(json.dumps(r, indent=2) + '\n')
print(json.dumps({k: r[k] for k in ['status', 'exit_code', 'CPU_wall_seconds', 'original_receipt_sha256']}))
if r['exit_code']:print(r['error_tail'])
