"""Observe only original E5 handles, receipts, bound bytes and current resources."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    root=Path(__file__).resolve().parents[1];assert not args.output.exists()
    code=r'''import hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
s=root/'.sync/wc-e5-head-complete24-selected-r1-20261011';out=root/'outputs/wc-e5-native-wrapped-head-full24-r1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):h.update(part)
 return h.hexdigest()
c=json.loads((s/'e5-head-complete24-config.json').read_text());sup=json.loads((out/'supervisor.json').read_text())
launch=json.loads((s/'GPU-launch.json').read_text());post=json.loads((s/'terminal-CPU-supervisor.json').read_text())
assert sha(s/'e5-head-complete24-config.json')==launch['selected_config_sha256']==sup['config_sha256']
assert sup['pid']==launch['GPU_supervisor_pid'] and post['pid']==launch['terminal_CPU_supervisor_pid']
assert post['original_GPU_supervisor_pid']==sup['pid'] and sup['source_revision']==launch['source_revision']==post['source_revision']
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256'] and len(c['payload_sha256'])==456
assert sha(s/'production-CPU-receipt.json')==c['production_CPU_receipt_sha256']==sup['production_CPU_receipt_sha256']
ids=[sup['pid'],post['pid']]+[a['pid'] for a in sup['arms'] if 'pid' in a];handles=[];arms=[]
for pid in ids:
 path=pathlib.Path('/proc/'+str(pid));cmd=(path/'cmdline').read_bytes().replace(b'\0',b' ').decode() if path.exists() else None
 if cmd:assert str(s) in cmd and sup['source_revision'] in cmd
 handles.append({'original_pid':pid,'present':cmd is not None,'actual_cmdline':cmd})
for a in sup['arms']:
 q=out/a['id']/'receipt.json';r=json.loads(q.read_text()) if q.exists() else None
 rows=(r['batch'].get('requests',[]) or [{'paths':[]}])[0]['paths'] if r else []
 arms.append({'arm':a['id'],'original_process_entry':a,'runner_status':r['status'] if r else None,
  'original_receipt_sha256':sha(q) if r else None,'load_seconds':r.get('load_seconds') if r else None,
  'paths':[{'method':p['collect'],'status':p['status'],'recorded_updates':len(p['guided_sha256'])} for p in rows]})
uuid=c['gpu_uuid'];gpu=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True)
target=[a for a in apps.splitlines() if a.split(',')[0].strip()==uuid]
b=json.loads((root/'reports/budget.json').read_text())
print(json.dumps({'status':'E5_ORIGINAL_HANDLE_RESOURCE_AND_PAYLOAD_OBSERVATION_NOT_TERMINAL_ACCEPTANCE',
 'observed_unix':time.time(),'source_revision':sup['source_revision'],'payload_files_unchanged':456,
 'GPU_supervisor_status':sup['status'],'original_handles':handles,'original_arms':arms,
 'GPU':gpu,'target_compute_apps':target,'original_terminal_CPU':post,
 'budget':b,'budget_sha256':sha(root/'reports/budget.json'),'prior_settled_used_GPUh':sup['budget_before']['used_gpu_hours'],
 'prior_settled_remaining_GPUh':sup['budget_before']['cap_gpu_hours']-sup['budget_before']['used_gpu_hours'],
 'inflight_reservation_not_actual_spent':any('inflight' in k for k in b),'new_GPU_submissions':0}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout);args.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k] for k in ('status','observed_unix','source_revision','payload_files_unchanged',
        'GPU_supervisor_status','GPU','target_compute_apps','inflight_reservation_not_actual_spent')}))
    print(json.dumps({'original_handles':[(p['original_pid'],p['present']) for p in value['original_handles']],
        'arms':[{k:a[k] for k in ('arm','runner_status','load_seconds','paths')} for a in value['original_arms']]}))


if __name__=='__main__':main()
