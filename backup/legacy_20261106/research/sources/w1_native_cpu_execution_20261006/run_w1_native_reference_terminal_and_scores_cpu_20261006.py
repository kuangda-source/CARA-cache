import ast,hashlib,json,subprocess
from pathlib import Path
m=json.loads(Path('manifests/wc_w1_native_reference_execution_20261006.json').read_text());dispatch=json.loads(Path('reports/wc_w1_native_reference_dispatch_20261006.json').read_text())
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text());ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
remote='M='+repr(m)+'\nSOURCE='+repr(dispatch['source_revision'])+'\n'+r'''
import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage'];output=root/'outputs/wc-w1-native-reference-cal8-r1'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
sup=json.loads((output/'supervisor.json').read_text());rec=json.loads((output/'diagnostic/receipt.json').read_text())
assert sup['status'] not in ['START_PENDING_INSPECT_SAME_OUTPUT','GPU_W1_FIVE_NATIVE_REFERENCES_RUNNING'],'Original task not terminal: monitor, never restart'
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in [sup['pid'],sup['child_pid'],rec['pid']]),'Original handles still live'
assert not (stage/'terminal-and-score-cpu-start.json').exists(),'Original CPU handles already registered: inspect, never restart'
before=(root/'reports/budget.json').read_bytes()
(stage/'terminal-and-score-cpu-start.json').write_text(json.dumps({'PID':os.getpid(),'started_unix':time.time(),'source_revision':SOURCE,'CPU_only':True})+chr(10))
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python';env=dict(os.environ,CUDA_VISIBLE_DEVICES='',
 PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 HF_HUB_CACHE=str(root/'hfhub'),PYTHONPATH=str(stage/'src'))
audit=stage/'terminal-audit.json';scores=stage/'full93-lpips.json'
commands=[('terminal-full93-source-cost-release-audit',[python,'-u',str(stage/'scripts/audit_w1_native_references_terminal.py'),
 '--project',str(root),'--stage',str(stage),'--output',str(audit),'--expected-source',SOURCE],300),
 ('full93-W1-WC-Native-LPIPS-scoring',[python,'-u',str(stage/'scripts/score_w1_native_references_cpu.py'),
 '--project',str(root),'--stage',str(stage),'--receipt',str(output/'diagnostic/receipt.json'),
 '--terminal-audit',str(audit),'--output',str(scores)],900)]
checks=[];started=time.time();code=0
for name,command,limit in commands:
 t=time.time()
 with (stage/(name+'.log')).open('w') as out,(stage/(name+'.err')).open('w') as err:
  child=subprocess.Popen(command,env=env,cwd=root/'runtime',stdout=out,stderr=err)
  (stage/(name+'-handle.json')).write_text(json.dumps({'PID':child.pid,'supervisor_PID':os.getpid(),'CPU_only':True,'started_unix':t,'limit_seconds':limit})+chr(10))
  try:code=child.wait(timeout=limit)
  except subprocess.TimeoutExpired:child.kill();child.wait();code=124
 item={'name':name,'exit_code':code,'CPU_wall_seconds':time.time()-t}
 if code==0:item['result']=json.loads((stage/(name+'.log')).read_text().strip().splitlines()[-1])
 else:item['error_tail']=(stage/(name+'.err')).read_text()[-6000:]
 checks.append(item)
 if code:break
assert before==(root/'reports/budget.json').read_bytes()
r={'status':'W1_APPROVED_TERMINAL_AND_FULL93_CPU_SCORES_PASS_NOT_INDEPENDENT_CONF' if code==0 else 'W1_APPROVED_TERMINAL_OR_CPU_SCORE_TECH_FAILURE',
 'exit_code':code,'source_revision':SOURCE,'CPU_supervisor_PID':os.getpid(),'CPU_wall_seconds':time.time()-started,'checks':checks,
 'budget_unchanged_during_CPU':True,'GPU_submissions':0,'no_GPU_source_modified':True,
 'runner_receipt_sha256':sha(output/'diagnostic/receipt.json'),'supervisor_receipt_sha256':sha(output/'supervisor.json'),
 'terminal_audit_sha256':sha(audit) if audit.exists() else None,'score_sha256':sha(scores) if scores.exists() else None}
raw=(json.dumps(r,indent=2)+chr(10)).encode();(stage/'terminal-and-score-cpu-receipt.json').write_bytes(raw)
result={'receipt':r,'CPU_receipt_original_sha256':hashlib.sha256(raw).hexdigest(),
 'supervisor':sup,'runner':rec,'budget':json.loads(before),
 'terminal_audit':json.loads(audit.read_text()) if audit.exists() else None,
 'scores':json.loads(scores.read_text()) if scores.exists() else None}
print(json.dumps(result))
'''
ast.parse(remote)
p=subprocess.run(ssh+['timeout 1230s python3 -u -'],input=remote,text=True,capture_output=True,timeout=1260)
Path('.sync/w1-native-terminal-score-transport-20261006.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
assert p.returncode==0,p.stderr[-5000:]
r=json.loads(p.stdout)
for key,name in [('supervisor','wc_w1_native_reference_supervisor_20261006.json'),('runner','wc_w1_native_reference_runner_20261006.json'),('budget','budget.json'),('terminal_audit','wc_w1_native_reference_terminal_cpu_r1_20261006.json'),('scores','wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json')]:
 if r[key] is not None:
  target=Path('reports')/name
  if name!='budget.json':assert not target.exists(),name
  target.write_text(json.dumps(r[key],indent=2)+'\n')
receipt=r['receipt'];receipt['CPU_receipt_original_sha256']=r['CPU_receipt_original_sha256'];receipt['executed_CPU_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
Path('reports/wc_w1_native_reference_terminal_and_score_cpu_r1_20261006.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['status','exit_code','CPU_wall_seconds','CPU_receipt_original_sha256']}))
if receipt['exit_code']:print(receipt['checks'][-1].get('error_tail'))
if r['scores'] is not None:print(json.dumps(r['scores'].get('summary',{'score_status':r['scores']['status']})))
