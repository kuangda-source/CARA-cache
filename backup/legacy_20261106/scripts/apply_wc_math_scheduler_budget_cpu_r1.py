#!/usr/bin/env python3
"""Apply the human's remaining48/strict-over8 policy without launching a GPU."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = 'manifests/budget_authorization_20261012_wc_math_scheduler_new48gpuh.json'
REMOTE = r'''
import fcntl,hashlib,json,os,pathlib,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
request=json.load(sys.stdin); raw=request['authority_text'].encode(); a=json.loads(raw)
assert hashlib.sha256(raw).hexdigest()==request['authority_sha256']
assert request['ref']=='manifests/budget_authorization_20261012_wc_math_scheduler_new48gpuh.json'
assert a['direct_user_authorization'] and a['authorized_remaining_gpu_hours']==48
assert a['automatic_single_job_gpu_hours']==8 and not a['usage_reset']
lock=(root/'.sync/f1.lock').open('a+')
fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
p=root/'reports/budget.json'; before=p.read_bytes(); b=json.loads(before)
assert not any('inflight' in k for k in b)
if b.get('budget_authorization_ref')==request['ref']:
 assert b['cap_gpu_hours']==a['new_cumulative_cap_gpu_hours']
 print(json.dumps({'status':'AUTHORIZATION_ALREADY_APPLIED_NO_RESET','ledger':b,
  'ledger_sha256':hashlib.sha256(before).hexdigest(),'GPU_submissions':0}));sys.exit(0)
assert hashlib.sha256(before).hexdigest()==a['previous_budget_sha256']
assert b['used_gpu_hours']==a['window_start_used_gpu_hours']
assert b['gpu_jobs_launched']==a['gpu_jobs_launched_at_change']
assert b['cap_gpu_hours']==a['previous_cap_gpu_hours']
assert a['new_cumulative_cap_gpu_hours']==b['used_gpu_hours']+48
archive=root/'.sync/wc-math-scheduler-budget-new48-20261012'
archive.mkdir(exist_ok=True)
backup=archive/'budget-before.json'
if backup.exists():assert backup.read_bytes()==before
else:
 with backup.open('xb') as f:f.write(before)
target=root/request['ref']
target.parent.mkdir(parents=True,exist_ok=True)
if target.exists():assert target.read_bytes()==raw
else:
 with target.open('xb') as f:f.write(raw)
assert hashlib.sha256(target.read_bytes()).hexdigest()==request['authority_sha256']
entry={'authorized_on_local':a['authorized_on_local'],
 'user_instruction':a['source_user_instruction'],'authorization_ref':request['ref'],
 'previous_cap_gpu_hours':b['cap_gpu_hours'],'new_cumulative_cap_gpu_hours':a['new_cumulative_cap_gpu_hours'],
 'used_gpu_hours_at_change':b['used_gpu_hours'],'gpu_jobs_launched_at_change':b['gpu_jobs_launched'],
 'authorized_remaining_gpu_hours':48,'no_usage_reset_or_transfer':True}
b.setdefault('budget_authorization_history',[]).append(entry)
b.setdefault('execution_policy_authorization_history',[]).append({
 'authorized_on_local':a['authorized_on_local'],'source_user_instruction':a['source_user_instruction'],
 'previous_automatic_single_job_gpu_hours':b.get('automatic_single_job_gpu_hours'),
 'automatic_single_job_gpu_hours':8,'authorization_ref':request['ref'],
 'complete_single_job_strictly_over8_requires_confirmation':True})
b['budget_authorization_ref']=request['ref'];b['execution_policy_authorization_ref']=request['ref']
b['cap_gpu_hours']=a['new_cumulative_cap_gpu_hours'];b['automatic_single_job_gpu_hours']=8
b['budget_authorization_window']={'authorization_ref':request['ref'],
 'start_used_gpu_hours':b['used_gpu_hours'],'authorized_remaining_gpu_hours':48,
 'cumulative_cap_gpu_hours':b['cap_gpu_hours'],'recorded_unix':time.time()}
b['status']='MATH_SCHEDULER_REMAINING48_AUTHORIZED_NO_NEW_GPU'
after=(json.dumps(b,indent=2)+'\n').encode()
temp=p.with_name('budget-math-scheduler-new48.tmp')
if temp.exists():
 assert json.loads(temp.read_bytes())['budget_authorization_ref']==request['ref']
 temp.unlink()
with temp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
os.replace(temp,p)
assert b['used_gpu_hours']==json.loads(before)['used_gpu_hours']
assert b['gpu_jobs_launched']==json.loads(before)['gpu_jobs_launched']
receipt={'status':'MATH_SCHEDULER_REMAINING48_POLICY_APPLIED_NO_GPU',
 'authority_sha256':request['authority_sha256'],'before_sha256':hashlib.sha256(before).hexdigest(),
 'ledger_sha256':hashlib.sha256(after).hexdigest(),'ledger':b,'GPU_submissions':0,
 'historical_usage_preserved':True,'remaining_GPUh':b['cap_gpu_hours']-b['used_gpu_hours']}
with (archive/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''

def main():
    raw=(ROOT/REF).read_text()
    payload={'ref':REF,'authority_text':raw,'authority_sha256':hashlib.sha256(raw.encode()).hexdigest()}
    # Code and JSON share stdin through a single literal Python bootstrap.
    bootstrap='import json; request=json.loads('+repr(json.dumps(payload))+'); import io,sys; sys.stdin=io.StringIO(json.dumps(request)); exec('+repr(REMOTE)+')'
    value=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=bootstrap,text=True))
    (ROOT/'reports/wc_math_scheduler_new48_policy_receipt_20261012.json').write_text(json.dumps(value,indent=2)+'\n')
    (ROOT/'reports/budget.json').write_text(json.dumps(value['ledger'],indent=2)+'\n')
    print(json.dumps({k:value.get(k) for k in ('status','remaining_GPUh','GPU_submissions','ledger_sha256')}))

if __name__=='__main__':main()
