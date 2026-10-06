"""Independent read-only native receipt, payload, cost and signed-score audit."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

read = lambda name: json.loads(Path(name).read_text())
m = read('manifests/wc_w1_native_reference_execution_20261006.json')
dispatch = read('reports/wc_w1_native_reference_dispatch_20261006.json')
cpu = read('reports/wc_w1_native_reference_terminal_and_score_cpu_r1_20261006.json')
original_cpu = {k: v for k, v in cpu.items() if k not in [
    'CPU_receipt_original_sha256', 'executed_CPU_wrapper_sha256']}
originals = {name: read('reports/' + name) for name in [
    'wc_w1_native_reference_supervisor_20261006.json',
    'wc_w1_native_reference_runner_20261006.json',
    'wc_w1_native_reference_terminal_cpu_r1_20261006.json',
    'wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json', 'budget.json']}
tree = ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'ssh' for t in n.targets)))
remote = ('M=' + repr(m) + '\nSOURCE=' + repr(dispatch['source_revision'])
          + '\nCPU=' + repr(original_cpu) + '\nCPU_SHA=' + repr(cpu['CPU_receipt_original_sha256'])
          + '\nORIGINALS=' + repr(originals) + '\n' + r'''
import fcntl, hashlib, json, math, pathlib, statistics, time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage']
output=root/'outputs/wc-w1-native-reference-cal8-r1';checked=[]
def sha(path):
 digest=hashlib.sha256()
 with pathlib.Path(path).open('rb') as file:
  for chunk in iter(lambda:file.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()
def check(path,digest):
 assert sha(path)==digest,str(path);checked.append({'path':str(path),'sha256':digest})
def original(path,name):
 actual=json.loads(path.read_text());assert actual==ORIGINALS[name],str(path)
 checked.append({'path':str(path),'sha256':sha(path)});return actual
for directory,files in [(stage,M['payload_sha256']),(root/M['base_stage'],M['base_payload_sha256'])]:
 for name,digest in files.items():check(directory/name,digest)
check(root/M['base_stage']/'receipt.json',M['base_original_receipt_sha256'])
check(stage/'terminal-and-score-cpu-receipt.json',CPU_SHA)
assert json.loads((stage/'terminal-and-score-cpu-receipt.json').read_text())==CPU
sup=original(output/'supervisor.json','wc_w1_native_reference_supervisor_20261006.json')
rec=original(output/'diagnostic/receipt.json','wc_w1_native_reference_runner_20261006.json')
audit=original(stage/'terminal-audit.json','wc_w1_native_reference_terminal_cpu_r1_20261006.json')
scores=original(stage/'full93-lpips.json','wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json')
budget=original(root/'reports/budget.json','budget.json')
check(output/'supervisor.json',CPU['supervisor_receipt_sha256'])
check(output/'diagnostic/receipt.json',CPU['runner_receipt_sha256'])
check(stage/'terminal-audit.json',CPU['terminal_audit_sha256'])
check(stage/'full93-lpips.json',CPU['score_sha256'])
config=json.loads((stage/'native-prod-config.json').read_text())
draft=json.loads((stage/'w1-reference-draft.json').read_text())
assert sup['source_revision']==rec['source_revision']==audit['source_revision']==SOURCE
assert sup['exit_code']==0 and CPU['exit_code']==0 and len(CPU['checks'])==2
assert sup['reserved_seconds']==3600 and 0<sup['wall_seconds']<=3600 and not sup['hard_wall_cap_exceeded']
assert sup['config']==rec['scope']==config and sup['budget_after']==audit['budget']==budget
assert sup['budget_before']['gpu_jobs_launched']==47 and budget['gpu_jobs_launched']==48
assert sup['budget_before']['used_gpu_hours']==12.99974633233337
assert budget['used_gpu_hours']==sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600
assert budget['cap_gpu_hours']==24 and not any(k.endswith('_inflight') for k in budget)
assert rec['original_denominator']==[8,7,1] and len(rec['cases'])==rec['planned_references']==5
assert not rec['original_rejected_sample_replaced'] and not rec['independent_confirmation'] and not rec['GPU_scoring']
assert rec['status']=='FIVE_REFERENCES_ATTEMPTED_REQUIRES_TERMINAL_AND_CPU_VIDEO_AUDIT'
pids=[sup['pid'],sup['child_pid'],rec['pid'],CPU['CPU_supervisor_PID']]
logs=[]
for item in CPU['checks']:
 name=item['name'];handle=stage/(name+'-handle.json');pids.append(json.loads(handle.read_text())['PID'])
 assert item['exit_code']==0
 assert json.loads((stage/(name+'.log')).read_text().strip().splitlines()[-1])==item['result']
 for suffix in ['.log','.err','-handle.json']:
  path=stage/(name+suffix);logs.append({'path':str(path),'sha256':sha(path)})
assert len(set(pids))==len(pids) and all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
with (root/'.sync/f1.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
indices=[0,3,4,5,7]
for case,index in zip(rec['cases'],indices):
 row=draft['rows'][index]
 assert case['original_CAL_index']==index and case['sample_name']==row['scene'] and case['request']==row['request']
 assert not case['worldcache_enabled'] and case['flags_before']==case['flags_after']==rec['backend_flags']
 if case['outcome']!='TEXT_REJECTED':
  assert (case['CFG_calls'],case['solver_steps'],case['prepare_calls'])==(72,36,1)
  assert case['block_counts']=={'denoiser_calls':72,'full_calls':72,'skipped_deep_calls':0}
  assert len(case['trace'])==72 and all(t['deep_executed'] for t in case['trace'])
 if case['outcome']=='ACCEPTED':check(case['artifact']['path'],case['artifact']['sha256'])
 else:assert case['artifact'] is None
assert audit['full_five_reference_card_completed'] and audit['original_pids_absent'] and audit['global_lock_free']
assert scores['reference_plan']==audit['reference_plan'] and scores['original_denominator']==[8,7,1]
assert scores['CUDA_initialized'] is False and scores['GPU_submissions']==0
assert scores['status']=='W1_AVAILABLE_FULL93_NATIVE_FIDELITY_SCORES_COMPLETE_NOT_INDEPENDENT_CONFIRMATION'
assert scores['metric_protocol']['expected_frames']==93 and scores['metric_protocol']['expected_HWC']==[432,768,3]
assert scores['metric_protocol']['device']=='cpu' and scores['metric_protocol']['precision']=='torch.float32'
assert scores['metric_protocol']['resize_crop_subsample'] is False
plan=scores['reference_plan'];assert len(plan['rows'])==8 and plan['original_denominator']==[8,7,1]
assert plan['rows'][6]['status']=='ORIGINAL_W1_REJECTED_NOT_REPLACED'
assert len(scores['pairs'])==len(plan['pairs'])==2*plan['matched_accepted_scene_count']
for video in audit['videos']:
 check(video['path'],video['sha256']);assert video['full93_decode']
summary=scores['summary'];derived=[]
for row in plan['rows']:
 if row['status']!='TWO_FULL93_LOSSES_PLANNED':continue
 pairs=[p for p in scores['pairs'] if p['scene']==row['scene']]
 assert [p['method'] for p in pairs]==['official_WC','W1_scalar']
 a,b=[p['score'] for p in pairs]
 for pair in pairs:
  score=pair['score'];values=score['frame_distances']
  assert score['frames']==len(values)==len(score['pts'])==93 and all(math.isfinite(v) for v in values)
  assert abs(score['mean_LPIPS']-sum(values)/93)<1e-12
  assert score['reference_sha256']==pair['reference']['sha256'] and score['candidate_sha256']==pair['candidate']['sha256']
 assert a['reference_sha256']==b['reference_sha256'] and a['pts']==b['pts']
 delta=a['mean_LPIPS']-b['mean_LPIPS'];frame=[x-y for x,y in zip(a['frame_distances'],b['frame_distances'])]
 derived.append({'scene':row['scene'],'WC_LPIPS':a['mean_LPIPS'],'W1_LPIPS':b['mean_LPIPS'],
  'WC_minus_W1':delta,'relative_improvement_percent':100*delta/a['mean_LPIPS'] if a['mean_LPIPS']>0 else None,
  'improved_frames':sum(v>0 for v in frame),'tied_frames':sum(v==0 for v in frame),
  'degraded_frames':sum(v<0 for v in frame),'frames_are_independent_samples':False})
assert summary['per_scene']==derived
delta=[r['WC_minus_W1'] for r in derived]
assert summary['scene_equal_mean_WC_minus_W1']==statistics.mean(delta)
assert summary['scene_median_WC_minus_W1']==statistics.median(delta)
assert summary['improved_scenes']==sum(v>0 for v in delta) and summary['degraded_scenes']==sum(v<0 for v in delta)
assert summary['tied_scenes']==sum(v==0 for v in delta) and summary['matched_accepted_scene_count']==len(delta)
assert summary['development_only_not_independent_CONF'] and summary['LPIPS_fidelity_not_physics_or_semantic_quality']
assert not summary['all_seven_must_improve'] and not summary['clean_speed_claim']
assert not (root/'manifests/wc_w3_placement_gpu_authorization_20261005.json').exists()
assert not (root/'outputs/wc-w3-placement-swap-r1').exists()
monitor=[json.loads(t) for t in (output/'gpu-monitor.jsonl').read_text().splitlines()]
assert len(monitor)==audit['monitor_rows']
assert all(r['uuid']==M['gpu_uuid'] and set(r['pids']).issubset(pids[:3]) for r in monitor)
assert not set(sup['release']['pids']).intersection(pids[:3])
for name in ['native-reference.log','gpu-monitor.jsonl','supervisor-launch.log']:
 path=(stage if name=='supervisor-launch.log' else output)/name
 logs.append({'path':str(path),'sha256':sha(path)})
result={'status':'W1_FIVE_NATIVE_REFERENCE_ORIGINAL_HASH_COST_HANDLES_SIGNED93_AUDIT_PASS_NOT_INDEPENDENT_CONF',
 'observed_unix':time.time(),'GPU_source_revision':SOURCE,'checked_native_SHA256_count':len(checked),
 'checked_native_SHA256':checked,'original_logs_and_handles_SHA256':logs,'original_handles_exited':pids,
 'global_lock_free':True,'budget':budget,'budget_sha256':sha(root/'reports/budget.json'),
 'GPU_wall_seconds':sup['wall_seconds'],'GPU_charge_hours':sup['wall_seconds']/3600,
 'CPU_original_receipt_sha256':CPU_SHA,'independent_recomputed_per_scene':derived,
 'descriptive_scene_equal_mean_WC_LPIPS':statistics.mean(r['WC_LPIPS'] for r in derived),
 'descriptive_scene_equal_mean_W1_LPIPS':statistics.mean(r['W1_LPIPS'] for r in derived),
 'original_8_7_1_and_five_scope_preserved':True,'all93_frames_not_independent_samples':True,
 'W3_B_not_automatically_authorized_or_launched':True,'new_GPU_submissions':0,
 'no_Torch_import_or_GPU_query_in_auditor':True}
print(json.dumps(result))
''')
ast.parse(remote)
p = subprocess.run(ssh + ['python3 -u -'], input=remote, text=True, capture_output=True, timeout=60)
assert p.returncode == 0, p.stderr[-5000:]
result = json.loads(p.stdout)
result['executed_audit_wrapper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target = Path('reports/wc_w1_native_reference_final_original_native_audit_20261006.json')
assert not target.exists(), 'Preserve original independent audit'
target.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'checked_native_SHA256_count',
    'original_handles_exited', 'GPU_wall_seconds', 'GPU_charge_hours', 'budget_sha256']}))
