#!/usr/bin/env python3
"""Dispatch exactly the selected complete card and its bound released-GPU CPU audit."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch=json.loads(Path('reports/wc_real_paired_interface_selected_cpu_r1_launch_20261009.json').read_text())
    proof=json.loads(Path('reports/wc_real_paired_interface_selected_cpu_r1_terminal_20261009_capture.json').read_text())
    assert proof['exit_code']==0 and proof['local_native_bytes_binding_scope_and_request_verified']
    assert proof['source_revision']==launch['source_revision'] and proof['payload_files']==launch['payload_files']
    driver=Path('scripts/supervise_wc_real_paired_interface_post_cpu.py').read_bytes()
    original=subprocess.check_output(['git','show',launch['source_revision']+':scripts/supervise_wc_real_paired_interface_post_cpu.py'])
    assert driver==original
    source='L='+repr(launch)+'\nP='+repr(proof)+'\nD='+repr(base64.b64encode(driver).decode())+'\n'+r'''
import base64,fcntl,hashlib,json,os,pathlib,shutil,subprocess,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text())
assert sha(stage/'receipt.json')==P['files']['receipt.json']['sha256'] and r['exit_code']==0
assert all(not pathlib.Path('/proc/'+str(r[k])).exists() for k in ('pid','child_pid'))
assert sha(stage/'teacher-config.json')==L['config_sha256']
sys.path.insert(0,str(stage/'src'))
from wcomr.cfg_real_paired_interface_production import validate,validate_selected
c,_=validate(root,stage);validate_selected(c,root,stage)
assert c['execution_run_id']=='wc-w3-real-paired-interface-r1' and len(c['payload_sha256'])==L['payload_files']
budget=root/'reports/budget.json';before=json.loads(budget.read_text())
assert sha(budget)==P['budget_sha256_unchanged'] and before['cap_gpu_hours']==50 and not any('inflight' in k for k in before)
assert c['preregistration']['forecast']['forecast_complete_GPUh']<=2
assert before['used_gpu_hours']+c['preregistration']['forecast']['forecast_complete_GPUh']<=50
assert not (root/'outputs'/c['execution_run_id']).exists()
assert shutil.disk_usage(root).free>50*(1<<30)
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
row=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
assert row[0].strip()==c['gpu_uuid'] and row[3].strip()=='8.6' and int(row[2])<=1024
assert not any(x.split(',')[0].strip()==c['gpu_uuid'] for x in apps.splitlines())
post=root/'.sync/wc-real-paired-interface-post-cpu-r1-20261009';assert not post.exists();post.mkdir()
(post/'driver.py').write_bytes(base64.b64decode(D))
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
command=['python3',str(stage/'scripts/supervise_wc_real_paired_interface.py'),'--project',str(root),'--stage',str(stage),'--source-revision',L['source_revision']]
with (post/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
post_command=['python3',str(post/'driver.py'),'--project',str(root),'--stage',str(stage),'--post',str(post),
              '--source-revision',L['source_revision'],'--supervisor-pid',str(child.pid)]
with (post/'driver.log').open('x') as log:
 audit=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,
            env=dict(env,CUDA_VISIBLE_DEVICES=''),start_new_session=True)
result={'run_id':c['execution_run_id'],'stage':str(stage),'post_CPU_stage':str(post),'source_revision':L['source_revision'],
 'supervisor_pid':child.pid,'post_CPU_pid':audit.pid,'config_sha256':sha(stage/'teacher-config.json'),'payload_files':len(c['payload_sha256']),
 'post_driver_sha256':sha(post/'driver.py'),'budget_before':before,'planned_scope':c['preregistration']['scope_counts'],
 'forecast_complete_GPUh':c['preregistration']['forecast']['forecast_complete_GPUh'],'gpu_uuid':c['gpu_uuid'],
 'command':command,'post_CPU_command':post_command,'selected_CPU_receipt_sha256':sha(stage/'receipt.json'),
 'fresh_target_memory_mib':int(row[2]),'observed_unix':time.time(),'GPU_submissions_by_launch':1}
(post/'launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                         input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-5000:])
    result=json.loads(call.stdout);dest=Path('reports/wc_real_paired_interface_r1_GPU_launch_20261009.json');assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('run_id','source_revision','supervisor_pid','post_CPU_pid','planned_scope','forecast_complete_GPUh','GPU_submissions_by_launch')}))


if __name__=='__main__':main()
