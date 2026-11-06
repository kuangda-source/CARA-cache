"""Independent original receipt/native SHA/handle audit, no Torch or GPU query."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
revisions=['r1','r2','r3']
stages=[]
for rev in revisions:
    m=read('manifests/wc_w1_own_state_production_cpu_'+rev+'_20261006.json')
    r=read('reports/wc_w1_own_state_production_actual_cpu_'+rev+'_20261006.json')
    wrapper='research/sources/w1_native_cpu_execution_20261006/run_w1_own_state_production_cpu_'+rev+'_20261006.py'
    assert sha(wrapper)==r['executed_transfer_wrapper_sha256']
    stages.append({'manifest':m,'receipt_sha256':r['original_receipt_sha256'],'source':r['CPU_source_revision']})
old=read('manifests/wc_w1_native_reference_execution_20261006.json')
core=read('manifests/wc_w1_own_state_core_cpu_r2_20261006.json')
coreproof=read('reports/wc_w1_own_state_core_actual_cpu_r2_20261006.json')
ssh=ast.literal_eval(next(n.value for n in ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text()).body
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
remote='STAGES='+repr(stages)+'\nOLD='+repr(old)+'\nCORE='+repr(core)+'\nCORE_SHA='+repr(coreproof['original_receipt_sha256'])+'\n'+r'''
import hashlib,json,pathlib
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');checked=[];pids=[];raw_receipts=[]
def check(path,digest):
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest,str(path);checked.append(str(path));return raw
for name,d in OLD['payload_sha256'].items():check(root/OLD['stage']/name,d)
check(root/CORE['stage']/'receipt.json',CORE_SHA)
for name,d in CORE['payload_sha256'].items():check(root/CORE['stage']/name,d)
for item in STAGES:
 m=item['manifest'];stage=root/m['stage'];r=json.loads(check(stage/'receipt.json',item['receipt_sha256']))
 assert r['CPU_source_revision']==item['source'] and r['payload_sha256']==m['payload_sha256']
 assert r['GPU_submissions']==0 and r['scientific_labels']==0 and not r['CUDA_initialized'] and r['budget_unchanged']
 for name,d in m['payload_sha256'].items():check(stage/name,d)
 pids.append(r['CPU_supervisor_PID'])
 logs=[]
 for c in r['checks']:
  handle=json.loads((stage/(c['name']+'-handle.json')).read_text());pids.append(handle['PID'])
  if c['exit_code']==0 and not c['result'].get('help_only'):
   data=json.loads((stage/(c['name']+'.log')).read_text().strip().splitlines()[-1]);assert data==c['result']
  for suffix in ['.log','.err','-handle.json']:
   path=stage/(c['name']+suffix);logs.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 raw_receipts.append({'stage':m['stage'],'source':r['CPU_source_revision'],'exit_code':r['exit_code'],'wall_seconds':r['CPU_wall_seconds'],'original_sha256':item['receipt_sha256'],'logs':logs})
 if item is STAGES[-1]:
  assert r['exit_code']==0 and len(r['checks'])==7 and r['passed_core_fixture_not_rerun']
  fixture=r['checks'][1]['result'];assert len(fixture['scope_and_cost_refusals'])==13
  assert fixture['pipeline']['complete_CPU_pipeline_scenes']==3 and fixture['pipeline']['teacher_observations']==12
  assert len(fixture['pipeline']['bridge_refusals'])==9 and len(fixture['supervised'])==3
  assert r['checks'][2]['result']['actual_original_typed_requests']==3
  assert r['checks'][2]['result']['changed_setup_keys']==['output_dir']
for pid in pids:assert type(pid) is int and pid>0 and not pathlib.Path('/proc/'+str(pid)).exists(),pid
budget_path=root/'reports/budget.json';budget=json.loads(check(budget_path,STAGES[-1]['manifest']['budget_sha256']))
assert budget['used_gpu_hours']==13.504302792026298 and budget['cap_gpu_hours']==24 and budget['gpu_jobs_launched']==48
assert not any(k.endswith('_inflight') for k in budget)
assert not (root/'outputs/wc-w1-own-state-shadow-r1').exists()
assert not (root/'manifests/wc_w1_own_state_gpu_authorization_20261006.json').exists()
print(json.dumps({'status':'OWN_STATE_PRODUCTION_CPU_ORIGINALS_AUDIT_PASS','native_SHA_checks':len(checked),
 'distinct_original_CPU_handles':len(set(pids)),'all_original_CPU_handles_gone':True,'original_runs':raw_receipts,
 'passed_core_and_old_160_GPU_files_unchanged':True,'budget_sha256':STAGES[-1]['manifest']['budget_sha256'],
 'budget':budget,'new_GPU_output_and_authority_absent':True,'GPU_submissions':0,'GPU_queried':False,'Torch_imported':False}))
'''
p=subprocess.run(ssh+['python3 -'],input=remote,text=True,capture_output=True,timeout=60)
assert p.returncode==0,p.stderr
r=json.loads(p.stdout);r['executed_audit_wrapper_sha256']=sha(__file__)
target=Path('reports/wc_w1_own_state_production_actual_cpu_audit_r3_20261006.json');assert not target.exists();target.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','native_SHA_checks','distinct_original_CPU_handles','new_GPU_output_and_authority_absent']}))
