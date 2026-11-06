"""Read original two CPU stages, handles and immutable previous GPU payload only."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

read = lambda p: json.loads(Path(p).read_text())
manifests = [read('manifests/wc_w1_own_state_core_cpu_r'+str(i)+'_20261006.json') for i in [1,2]]
receipts = [read('reports/wc_w1_own_state_core_actual_cpu_r'+str(i)+'_20261006.json') for i in [1,2]]
originals = [{k:v for k,v in r.items() if k not in ['original_receipt_sha256','executed_transfer_wrapper_sha256']}
             for r in receipts]
old = read('manifests/wc_w1_native_reference_execution_20261006.json')
tree = ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh = ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
remote = ('MS='+repr(manifests)+'\nRS='+repr(originals)+'\nSHAS='+repr([r['original_receipt_sha256'] for r in receipts])
    +'\nOLD='+repr(old)+'\nBUDGET='+repr(read('reports/budget.json'))+'\n'+r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');checked=[];logs=[];pids=[]
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def check(path,value):
 assert sha(path)==value,str(path);checked.append({'path':str(path),'sha256':value})
for m,r,digest in zip(MS,RS,SHAS):
 stage=root/m['stage']
 for name,value in m['payload_sha256'].items():check(stage/name,value)
 check(stage/'receipt.json',digest);assert json.loads((stage/'receipt.json').read_text())==r
 assert json.loads((stage/'manifest.json').read_text())==m
 pids.extend([r['CPU_supervisor_PID'],r['CPU_child_PID']])
 handle=json.loads((stage/'core-handle.json').read_text())
 assert handle['PID']==r['CPU_child_PID'] and handle['CPU_only'] and handle['limit_seconds']==180
 for name in ['start.json','core-handle.json','core.log','core.err','manifest.json']:
  path=stage/name;logs.append({'path':str(path),'sha256':sha(path)})
 assert r['budget_unchanged'] and r['GPU_submissions']==r['actual_model_runs']==r['scientific_labels']==0
 if r['exit_code']==0:assert json.loads((stage/'core.log').read_text().strip().splitlines()[-1])==r['result']
assert RS[0]['exit_code']==1 and 'view size is not compatible' in RS[0]['error_tail']
assert RS[1]['exit_code']==0 and len(RS[1]['result']['checks'])==8
result=RS[1]['result'];assert result['CPU_only'] and result['CUDA_initialized'] is False
assert result['mismatched_actual_CFG_input_refused'] and result['teacher_exception_restores_RNG_buffer_marker_without_label']
assert len(result['malformed_or_non_skip_pair_refusals'])==5
assert all(c['calls']==[45,46,67,68] and c['72_outputs_trace_full_anchors_cache_RNG_unchanged']
 and c['both_CFG_actual_input_pairs_equal'] for c in result['checks'])
assert len(set(pids))==4 and all(not pathlib.Path('/proc/'+str(p)).exists() for p in pids)
assert MS[0]['payload_sha256']['src/wcomr/own_state_shadow.py']==MS[1]['payload_sha256']['src/wcomr/own_state_shadow.py']
assert {k for k in MS[0]['payload_sha256'] if MS[0]['payload_sha256'][k]!=MS[1]['payload_sha256'][k]}=={'scripts/check_w1_own_state_core_cpu.py'}
for name,digest in OLD['payload_sha256'].items():check(root/OLD['stage']/name,digest)
runtime=root/'runtime/cosmos_predict2/_src/predict2/inference/worldcache_utils.py';check(runtime,result['source_sha256'])
budget=json.loads((root/'reports/budget.json').read_text());assert budget==BUDGET
assert not any(k.endswith('_inflight') for k in budget)
assert not (root/'manifests/wc_w3_placement_gpu_authorization_20261005.json').exists()
assert not (root/'outputs/wc-w3-placement-swap-r1').exists()
r={'status':'OWN_STATE_CORE_CPU_ORIGINAL_HASH_LOG_HANDLE_AUDIT_PASS_NOT_GPU_OR_SCIENTIFIC_LABELS',
 'observed_unix':time.time(),'checked_native_SHA256_count':len(checked),'checked_native_SHA256':checked,
 'logs_and_handles_sha256':logs,'original_CPU_handles_exited':pids,'CPU_source_revision':RS[1]['CPU_source_revision'],
 'original_R1_failure_retained':True,'only_fixture_contiguity_fixed_core_unchanged':True,
 'previous_160_GPU_payload_unchanged':True,'budget':budget,'budget_sha256':sha(root/'reports/budget.json'),
 'GPU_submissions':0,'no_Torch_import_or_GPU_query_in_auditor':True,'actual_model_runs':0,
 'new_scientific_teacher_labels':0,'production_entry_or_actual_generator_parity_established':False}
print(json.dumps(r))
''')
ast.parse(remote)
p = subprocess.run(ssh+['python3 -u -'],input=remote,text=True,capture_output=True,timeout=45)
assert p.returncode==0,p.stderr[-5000:]
r=json.loads(p.stdout)
r['executed_audit_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target=Path('reports/wc_w1_own_state_core_actual_cpu_audit_r2_20261006.json')
assert not target.exists()
target.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','checked_native_SHA256_count','original_CPU_handles_exited','budget_sha256']}))
