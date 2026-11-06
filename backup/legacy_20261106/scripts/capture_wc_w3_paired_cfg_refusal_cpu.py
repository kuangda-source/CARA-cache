#!/usr/bin/env python3
"""Capture unchanged original terminal refusal, full generated scope and all fees."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import base64,fcntl,gzip,hashlib,json,math,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/G['stage'];post=root/P['stage'];out=root/'outputs'/G['run_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'.sync/f1.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 sup=json.loads((out/'supervisor.json').read_text());r=json.loads((out/'diagnostic/receipt.json').read_text());cpu=json.loads((post/'receipt.json').read_text());budget=json.loads((root/'reports/budget.json').read_text())
 assert sup['exit_code']!=0 and cpu['exit_code']!=0 and cpu['scored_videos']==0 and 'score_pid' not in cpu and not (post/'score.json').exists()
 assert sup['status']=='EXITED_REQUIRES_RESULT_AUDIT' and sup['source_revision']==r['source_revision']==cpu['source_revision']==G['source_revision']==P['source_revision']
 assert sup['run_id']==r['run_id']==G['run_id']==C['execution_run_id'] and sup['pid']==G['supervisor_pid'] and cpu['pid']==P['pid']
 assert [sup['pid'],sup['child_pid']]==P['bound_GPU_PIDs']==cpu['bound_GPU_PIDs']
 pids=[sup['pid'],sup['child_pid'],cpu['pid']];assert len(set(pids))==3 and all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
 assert cpu['GPU_submissions']==0 and cpu['payload_after_sha256']==C['payload_sha256']=={n:sha(stage/n) for n in C['payload_sha256']}
 assert sup['config_sha256']==G['config_sha256']==sha(stage/'paired-config.json') and json.loads((stage/'paired-config.json').read_text())==C
 assert sha(post/'binding.json')==P['binding_sha256'] and sha(post/'driver.py')==P['driver_sha256']
 for n,h in C['project_input_sha256'].items():assert sha(root/n)==h,n
 assert budget==sup['budget_after']==cpu['budget_at_end'] and not any('inflight' in k for k in budget)
 assert budget['cap_gpu_hours']==24 and budget['gpu_jobs_launched']==sup['budget_before']['gpu_jobs_launched']+1
 assert math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
 assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True);assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
 row=r['cases'][0]['WC']['requests'][0];items=([row['artifact']] if row.get('artifact') else [])+[x['artifact'] for x in row.get('decoded_children',[]) if x.get('artifact')];videos=[]
 for item in items:
  path=pathlib.Path(item['path']);assert (out/'diagnostic').resolve() in path.resolve().parents and path.stat().st_size==item['bytes'] and sha(path)==item['sha256'];videos.append(item)
 assert {x['path'] for x in videos}=={str(x) for x in (out/'diagnostic').glob('**/*.mp4')}
 files={'supervisor_json':out/'supervisor.json','runner_json':out/'diagnostic/receipt.json','run_log':out/'run.log','gpu_monitor_jsonl':out/'gpu-monitor.jsonl','original_CPU_receipt_json':post/'receipt.json','original_CPU_binding_json':post/'binding.json','original_CPU_driver_log':post/'driver.log','budget_after_json':root/'reports/budget.json'}
 archives={}
 for label,path in files.items():
  raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0);archives[label]={'bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_b64':base64.b64encode(compressed).decode()}
 assert all(sha(files[n])==v['raw_sha256'] for n,v in archives.items())
 print(json.dumps({'status':'ORIGINAL_PAIRED_CFG_REFUSAL_GENERATED_ARTIFACTS_AND_ALL_COSTS_CAPTURED_NOT_ACCEPTANCE','source_revision':G['source_revision'],'run_id':G['run_id'],'observed_unix':time.time(),'pids_absent':pids,'GPU_released':True,'lock_available':True,'budget':budget,'GPU_wall_seconds':sup['wall_seconds'],'original_GPU_exit_code':sup['exit_code'],'original_CPU_exit_code':cpu['exit_code'],'original_error':r.get('error'),'planned_scope':r['planned_scope'],'completed_suffixes':sum(x.get('status')=='COMPLETE_SUFFIX_NOT_RV_LABEL' for x in row['children']),'new_video_files':videos,'original_strict_GPU_acceptance':False,'archives':archives}))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('config','gpu-launch','cpu-launch','prefix'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--ssh-target',required=True);a=p.parse_args()
    c,g,post=[json.loads(path.read_text()) for path in (a.config,a.gpu_launch,a.cpu_launch)]
    labels=['supervisor_json','runner_json','run_log','gpu_monitor_jsonl','original_CPU_receipt_json','original_CPU_binding_json','original_CPU_driver_log','budget_after_json']
    paths={n:Path(str(a.prefix)+'_'+n+'_native.gz') for n in labels};result=Path(str(a.prefix)+'_terminal_capture.json')
    assert all(not path.exists() for path in [*paths.values(),result])
    cmd='C='+repr(c)+'\nG='+repr(g)+'\nP='+repr(post)+'\n'+REMOTE
    response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',a.ssh_target,'python3 -'],input=cmd,text=True,capture_output=True,timeout=60)
    if response.returncode:raise RuntimeError(response.stderr[-4000:])
    value=json.loads(response.stdout);archives=value.pop('archives');assert set(archives)==set(paths);raws={}
    for name,item in archives.items():
        data=base64.b64decode(item.pop('gzip_b64'));raw=gzip.decompress(data)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256'] and hashlib.sha256(data).hexdigest()==item['gzip_sha256']
        raws[name]=raw
        with paths[name].open('xb') as f:f.write(data)
    value['archives']={str(paths[n]):item for n,item in archives.items()}
    (a.prefix.parent/'budget.json').write_bytes(raws['budget_after_json'])
    with result.open('x') as f:f.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','original_error','completed_suffixes','GPU_wall_seconds','budget')}))


if __name__=='__main__':main()
