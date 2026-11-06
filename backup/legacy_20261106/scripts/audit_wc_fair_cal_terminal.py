#!/usr/bin/env python3
"""Read-only post-terminal source, conservative full cost and original-resource audit.

This independently checks the frozen single wc-fair-cal-r1 card. It never
launches generation, imports Torch/CUDA, changes the ledger, or accepts quality.
The live ledger must still match this run's settled supervisor receipt.
"""
import pathlib,json,time,hashlib,subprocess,fcntl,math,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=pathlib.Path,required=True)
parser.add_argument('--stage',type=pathlib.Path,required=True)
parser.add_argument('--python',required=True)
parser.add_argument('--expected-source',required=True)
args=parser.parse_args()
root=args.project;out=root/'outputs/wc-fair-cal-r1';stage=args.stage
s=json.loads((out/'supervisor.json').read_text());r=json.loads((out/'diagnostic/receipt.json').read_text());launch=json.loads((stage/'launch-r1.json').read_text());deploy=json.loads((stage/'deploy-r1.json').read_text());c=json.loads((stage/'mid-config.json').read_text())
assert s['status'] not in ['START_PENDING_INSPECT_SAME_OUTPUT','GPU_FAIR_CAL_RUNNING'],'still running; follow original handle'
assert launch['source_revision']==deploy['source_revision']==args.expected_source
assert s['run_id']==launch['run_id']==c['run_id']=='wc-fair-cal-r1'
assert r['run_card']==c['card']=='WC-FAIR-CAL-R1-20261004-A'
pids=[s['pid'],s['child_pid'],r['pid']]
assert len(set(pids))==3 and not any(pathlib.Path('/proc/'+str(p)).exists() for p in pids),'original PID still present'
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
budget=json.loads((root/'reports/budget.json').read_text());before=s['budget_before']
assert budget==s['budget_after'] and not any(k.endswith('_inflight') for k in budget)
assert budget['cap_gpu_hours']==12 and budget['gpu_jobs_launched']==before['gpu_jobs_launched']+1==44
assert math.isclose(budget['used_gpu_hours'],before['used_gpu_hours']+s['wall_seconds']/3600,abs_tol=1e-10)
assert s['reserved_seconds']==6300 and 0<s['wall_seconds']<=6300 and budget['used_gpu_hours']<=12
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'mid-config.json')==deploy['validation']['config_sha256']
for n,digest in deploy['payload_sha256'].items():assert sha(stage/n)==digest,n
assert c==r['scope']
assert deploy['cpu_checks']['cuda_initialized'] is False
python=args.python
validation=subprocess.run([python,str(stage/'scripts/run_wc_fair_cal.py'),'--project',str(root),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(out/'diagnostic'),'--validate-only'],capture_output=True,text=True,timeout=120)
assert validation.returncode==0,validation.stderr[-2000:]
validator=json.loads(validation.stdout.strip().splitlines()[-1]);assert validator['status']=='NEW_SCOPE_ASSETS_SOURCE_PACKAGE_PASS_NO_TORCH_OR_CUDA'
monitors=[json.loads(v) for v in (out/'gpu-monitor.jsonl').read_text().splitlines()]
assert monitors and all(v['uuid']==launch['gpu_uuid'] for v in monitors)
assert all(set(v['pids']).issubset({s['child_pid'],r['pid']}) for v in monitors)
assert not s['release']['pids'] and s['release']['uuid']==launch['gpu_uuid']
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
gpu=subprocess.check_output(['nvidia-smi','-i',launch['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
assert not any(v.split(',')[0].strip()==launch['gpu_uuid'] for v in apps.splitlines())
assert int(gpu.split(',')[2].strip())<=1024
result={'status':'FAIR_CAL_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_FOURTEEN_OUTPUT_AUDIT','source_revision':launch['source_revision'],'observed_unix':time.time(),'original_pids_absent':pids,'global_lock_free':True,'source_payload_sha256':deploy['payload_sha256'],'config_sha256':sha(stage/'mid-config.json'),'postrun_validator':validator,'supervisor':s,'budget':budget,'gpu_wall_seconds':s['wall_seconds'],'gpu_monitor_rows':len(monitors),'gpu_peak_memory_mib':max(v['memory_used_mib'] for v in monitors),'compute_after':apps,'gpu_after':gpu,'receipt_sha256':sha(out/'diagnostic/receipt.json'),'runner_status':r['status'],'planned_phases':14,'planned_outputs':14,'existing_mp4_files':sorted(str(p) for p in (out/'diagnostic').glob('**/*.mp4')),'quality_acceptance':False,'clean_E2E_speed_claim':False}
result['terminal_analysis_code_sha256']=sha(pathlib.Path(__file__))
print(json.dumps(result))
