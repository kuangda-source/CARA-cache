import ast,hashlib,json,shlex,subprocess
from pathlib import Path
read=lambda n:json.loads(Path(n).read_text())
m=read('manifests/wc_w1_native_reference_production_cpu_r2_20261006.json')
r=read('reports/wc_w1_native_reference_production_actual_cpu_r2_20261006.json')
failed=read('manifests/wc_w1_native_reference_production_cpu_r1_20261006.json')
failed_receipt=read('reports/wc_w1_native_reference_production_actual_cpu_r1_20261006.json')
core=read('manifests/wc_w1_native_reference_core_cpu_r2_20261006.json')
b=read('manifests/wc_w3_placement_production_cpu_r2_20261005.json')
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
original={k:v for k,v in r.items() if k not in ['server_receipt_sha256','executed_transfer_wrapper_sha256']}
remote='M='+repr(m)+'\nR='+repr(original)+'\nEXPECT='+repr(r['server_receipt_sha256'])+'\nFAILED='+repr(failed)+'\nFAILED_SHA='+repr(failed_receipt['server_receipt_sha256'])+'\nCORE='+repr(core)+'\nB='+repr(b)+'\n'+r'''
import fcntl,hashlib,json,os,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage'];checked=[]
def sha(path):
 digest=hashlib.sha256()
 with pathlib.Path(path).open('rb') as file:
  for chunk in iter(lambda:file.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()
def check(path,value):
 assert sha(path)==value,str(path);checked.append({'path':str(path),'sha256':value})
for name,value in M['payload_sha256'].items():check(stage/name,value)
check(stage/'receipt.json',EXPECT);actual=json.loads((stage/'receipt.json').read_text());assert actual==R
for directory,files in [(root/M['base_stage'],M['base_payload_sha256']),
 (root/FAILED['stage'],FAILED['payload_sha256']), (root/B['stage'],B['payload_sha256']),
 (root/CORE['base_stage'],CORE['base_complete_payload_sha256'])]:
 for name,value in files.items():check(directory/name,value)
check(root/FAILED['stage']/'receipt.json',FAILED_SHA)
check(root/M['base_stage']/'receipt.json',M['base_original_receipt_sha256'])
for name,value in M['upstream_sha256'].items():check(root/'runtime'/name,value)
config=json.loads((stage/'native-prod-config.json').read_text())
for name,value in config['project_input_sha256'].items():check(root/name,value)
check(root/config['lpips_resource_stage']/'receipt.json',config['lpips_resource_receipt_sha256'])
assert config['GPU_execution_selected'] is False and config['gpu_uuid'] is None and config['execution_scope_authority'] is None
assert actual['exit_code']==0 and len(actual['checks'])==7 and actual['GPU_submissions']==0 and actual['CUDA_initialized'] is False
pids=[];logs=[]
for directory in [stage,root/FAILED['stage'],root/M['base_stage']]:
 receipt=json.loads((directory/'receipt.json').read_text());pids.append(receipt['CPU_supervisor_PID'])
 for item in receipt['checks']:
  name=item['name'];handle=json.loads((directory/(name+'-handle.json')).read_text());pids.append(handle['PID'])
  text=(directory/(name+'.log')).read_text()
  if item['exit_code']==0 and not item['result'].get('help_only'):assert json.loads(text.strip().splitlines()[-1])==item['result']
  for suffix in ['.log','.err','-handle.json']:
   path=directory/(name+suffix);logs.append({'path':str(path),'sha256':sha(path)})
assert all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
contract=next(i['result'] for i in actual['checks'] if i['name']=='scope-cost-failure-and-signed93-contracts')
assert contract['refusal_count']==21 and len(contract['supervisor_CPU_integration'])==3 and contract['partial_card_preserved']
assert all(i['child_reaped'] and i['GPU_submissions']==0 and i['charged_only_in_temporary_CPU_ledger'] for i in contract['supervisor_CPU_integration'])
assert next(i['result'] for i in actual['checks'] if i['name']=='actual-production-native-arguments-import')['selected_original_requests']==5
budget=json.loads((root/'reports/budget.json').read_text())
assert budget['used_gpu_hours']==12.99974633233337 and budget['cap_gpu_hours']==24 and budget['gpu_jobs_launched']==47
assert not any(n.endswith('_inflight') for n in budget)
absent=['manifests/wc_w1_native_reference_gpu_authorization_20261006.json','manifests/wc_w3_placement_gpu_authorization_20261005.json',
 'outputs/wc-w1-native-reference-cal8-r1','outputs/wc-w3-placement-swap-r1']
assert all(not (root/name).exists() for name in absent)
with (root/'.sync/f1.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result={'status':'FIVE_REFERENCE_PRODUCTION_ORIGINAL_NATIVE_HASH_HANDLES_BUDGET_CPU_AUDIT_PASS_NOT_GPU',
 'observed_unix':time.time(),'original_receipt_sha256':EXPECT,'CPU_source_revision':actual['CPU_source_revision'],
 'checked_native_SHA256_count':len(checked),'checked_native_SHA256':checked,'original_CPU_log_and_handle_SHA256':logs,
 'original_CPU_handles_exited':pids,'global_lock_free':True,'refusal_count':21,'CPU_supervisor_integration_cases':3,
 'original_five_scope_and_8_7_1_preserved':True,'failed_R1_original_retained':True,'core_and_B_and_R1_sources_unchanged':True,
 'budget':budget,'budget_sha256':sha(root/'reports/budget.json'),'GPU_authorizations_and_outputs_absent':absent,
 'GPU_submissions':0,'CUDA_initialized':False,'no_Torch_import_or_GPU_query_in_auditor':True}
print(json.dumps(result))
'''
ast.parse(remote)
p=subprocess.run(ssh+['python3 -u -'],input=remote,text=True,capture_output=True,timeout=60)
assert p.returncode==0,p.stderr[-5000:]
v=json.loads(p.stdout);v['executed_audit_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
Path('reports/wc_w1_native_reference_production_cpu_audit_r2_20261006.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({k:v[k] for k in ['status','checked_native_SHA256_count','original_receipt_sha256','original_CPU_handles_exited','budget_sha256']}))
