"""Run the frozen CPU terminal audit once, after the original GPU handles exit."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


read = lambda path: json.loads(Path(path).read_text())
manifest = read('manifests/wc_w1_own_state_execution_20261006.json')
dispatch = read('reports/wc_w1_own_state_dispatch_20261006.json')
tree = ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'ssh' for t in n.targets)))
remote = 'M=' + repr(manifest) + '\nSOURCE=' + repr(dispatch['source_revision']) + '\n' + r'''
import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage']
output=root/'outputs/wc-w1-own-state-shadow-r1'
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
sup=json.loads((output/'supervisor.json').read_text());rec=json.loads((output/'diagnostic/receipt.json').read_text())
assert sup['status'] not in ['START_PENDING_INSPECT_SAME_OUTPUT','GPU_W1_THREE_OWN_STATE_SCENES_RUNNING'],'Original GPU task not terminal'
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in [sup['pid'],sup['child_pid'],rec['pid']]),'Original GPU handles still live'
assert sup['source_revision']==rec['source_revision']==SOURCE,'Original GPU source differs'
before=(root/'reports/budget.json').read_bytes()
started=time.time()
with (stage/'terminal-and-summary-cpu-start.json').open('x') as file:
 file.write(json.dumps({'PID':os.getpid(),'started_unix':started,'GPU_source_revision':SOURCE,'CPU_only':True})+chr(10))
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(root/'hfhub'),PYTHONPATH=str(stage/'src'))
command=[python,'-u',str(stage/'scripts/summarize_w1_own_state.py'),'--project',str(root),'--stage',str(stage),'--output',str(output)]
log=stage/'terminal-and-summary-cpu.log';err=stage/'terminal-and-summary-cpu.err'
with log.open('x') as out,err.open('x') as error:
 child=subprocess.Popen(command,env=env,cwd=root/'runtime',stdout=out,stderr=error)
 with (stage/'terminal-and-summary-cpu-handle.json').open('x') as file:
  file.write(json.dumps({'PID':child.pid,'supervisor_PID':os.getpid(),'CPU_only':True,'started_unix':time.time(),'limit_seconds':300})+chr(10))
 try:code=child.wait(timeout=300)
 except subprocess.TimeoutExpired:child.kill();child.wait();code=124
result=json.loads(log.read_text().strip().splitlines()[-1]) if code==0 else None
assert before==(root/'reports/budget.json').read_bytes(),'CPU audit changed budget'
receipt={'status':'OWN_STATE_ORIGINAL_TERMINAL_AND_SIGNED_CPU_SUMMARY_PASS' if code==0 else 'OWN_STATE_TERMINAL_CPU_TECH_FAILURE_RETAINED',
 'exit_code':code,'GPU_source_revision':SOURCE,'CPU_supervisor_PID':os.getpid(),'CPU_child_PID':child.pid,
 'CPU_wall_seconds':time.time()-started,'budget_unchanged_during_CPU':True,'GPU_submissions':0,'no_GPU_source_modified':True,
 'runner_receipt_sha256':sha(output/'diagnostic/receipt.json'),'supervisor_receipt_sha256':sha(output/'supervisor.json'),
 'result_log_sha256':sha(log),'error_log_sha256':sha(err),'result':result,'error_tail':err.read_text()[-6000:] if code else None}
raw=(json.dumps(receipt,indent=2)+chr(10)).encode()
with (stage/'terminal-and-summary-cpu-receipt.json').open('xb') as file:file.write(raw)
print(json.dumps({'receipt':receipt,'CPU_receipt_original_sha256':hashlib.sha256(raw).hexdigest(),
 'supervisor':sup,'runner':rec,'budget':json.loads(before)}))
'''
ast.parse(remote)
p = subprocess.run(ssh + ['timeout 330s python3 -u -'], input=remote,
    text=True, capture_output=True, timeout=360)
Path('.sync/w1-own-state-terminal-summary-transport-20261006.json').write_text(
    json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
assert p.returncode == 0, p.stderr[-5000:]
value = json.loads(p.stdout)
for key, name in [('supervisor','wc_w1_own_state_supervisor_20261006.json'),
    ('runner','wc_w1_own_state_runner_20261006.json'),('budget','budget.json')]:
    target=Path('reports')/name
    if name != 'budget.json': assert not target.exists(), 'Preserve original '+name
    target.write_text(json.dumps(value[key],indent=2)+'\n')
receipt=value['receipt']
receipt['CPU_receipt_original_sha256']=value['CPU_receipt_original_sha256']
receipt['executed_CPU_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target=Path('reports/wc_w1_own_state_terminal_and_summary_cpu_r1_20261006.json')
assert not target.exists(), 'Preserve original CPU receipt'
target.write_text(json.dumps(receipt,indent=2)+'\n')
if receipt['result'] is not None:
    target=Path('reports/wc_w1_own_state_signed_summary_cpu_r1_20261006.json')
    assert not target.exists(), 'Preserve original signed summary'
    target.write_text(json.dumps(receipt['result'],indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['status','exit_code','CPU_wall_seconds','CPU_receipt_original_sha256']}))
if receipt['exit_code']: print(receipt['error_tail'])
elif receipt['result']: print(json.dumps(receipt['result']['rows']))
