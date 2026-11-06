#!/usr/bin/env python3
"""Read-only capture of the original completed paired CFG GPU/CPU evidence."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE=r'''
import base64,fcntl,gzip,hashlib,json,math,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/G['stage'];post=root/P['stage'];out=root/'outputs'/G['run_id']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'.sync/f1.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sup=json.loads((out/'supervisor.json').read_text());r=json.loads((out/'diagnostic/receipt.json').read_text())
    cpu=json.loads((post/'receipt.json').read_text());score=json.loads((post/'score.json').read_text());budget=json.loads((root/'reports/budget.json').read_text())
    assert sup['exit_code']==0 and cpu['exit_code']==0
    assert sup['status']=='EXITED_REQUIRES_RESULT_AUDIT'
    assert r['status']=='PAIRED_CFG_GPU_CORE_AND_HISTORY_COMPLETE_AUDIT_SCORE_PENDING'
    assert cpu['status']=='PAIRED_CFG_GPU_EXIT0_FULL_CPU_AUDIT_AND_SCORE_EXIT0'
    assert score['status']=='PAIRED_CFG_COMPLETE_FULL93_AUDIT_THREE_LOSSES_TWO_SIGNED_PAIRS_NOT_CONF'
    assert sup['source_revision']==r['source_revision']==cpu['source_revision']==G['source_revision']==P['source_revision']
    assert sup['run_id']==r['run_id']==G['run_id']==C['execution_run_id']
    assert sup['pid']==G['supervisor_pid'] and cpu['pid']==P['pid']
    assert [sup['pid'],sup['child_pid']]==P['bound_GPU_PIDs']==cpu['bound_GPU_PIDs']
    pids=[sup['pid'],sup['child_pid'],cpu['pid'],cpu['score_pid']]
    assert len(set(pids))==4 and all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
    assert cpu['GPU_submissions']==score['GPU_submissions']==0 and cpu['CUDA_initialized'] is False and score['CUDA_initialized'] is False
    assert r['planned_scope']==score['planned_scope']==C['preregistration']['scope_counts']
    assert len(r['cases'])==1 and r['cases'][0]['seed']==2
    row=r['cases'][0]['WC']['requests'][0]
    assert len(row['children'])==8 and len(row['decoded_children'])==4 and len(score['videos'])==6
    assert set(score['losses'])=={'BASE','SINGLE','PAIRED'} and [x['comparison'] for x in score['signed_pairs']]==['PAIRED_vs_BASE','PAIRED_vs_SINGLE']
    assert score['runner_sha256']==sha(out/'diagnostic/receipt.json') and cpu['score_sha256']==sha(post/'score.json')
    assert sup['config_sha256']==score['config_sha256']==G['config_sha256']==sha(stage/'paired-config.json')
    assert json.loads((stage/'paired-config.json').read_text())==C
    assert cpu['payload_after_sha256']==C['payload_sha256']=={n:sha(stage/n) for n in C['payload_sha256']}
    for name,h in C['project_input_sha256'].items():assert sha(root/name)==h,name
    assert budget==sup['budget_after']==score['budget']==cpu['budget_at_end'] and not any('inflight' in k for k in budget)
    assert budget['cap_gpu_hours']==24 and budget['gpu_jobs_launched']==sup['budget_before']['gpu_jobs_launched']+1
    assert math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
    new=[]
    for v in score['videos']:
        path=pathlib.Path(v['path']);assert v['full93_decode'] and path.stat().st_size==v['bytes'] and sha(path)==v['sha256']
        if v['path']!=C['preregistration']['existing_Native']['path']:
            assert (out/'diagnostic').resolve() in path.resolve().parents;new.append(path.resolve())
        else:assert all(v[k]==C['preregistration']['existing_Native'][k] for k in ('path','bytes','sha256'))
    assert len(new)==5 and set(new)=={p.resolve() for p in (out/'diagnostic').glob('**/*.mp4')}
    gpu=subprocess.check_output(['nvidia-smi','-i',sup['gpu_uuid'],'--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
    files={'supervisor_json':out/'supervisor.json','runner_json':out/'diagnostic/receipt.json','run_log':out/'run.log','gpu_monitor_jsonl':out/'gpu-monitor.jsonl',
        'CPU_receipt_json':post/'receipt.json','CPU_binding_json':post/'binding.json','CPU_driver_log':post/'driver.log','CPU_score_json':post/'score.json','CPU_score_log':post/'score.log','budget_after_json':root/'reports/budget.json'}
    archives={}
    for label,path in files.items():
        raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
        archives[label]={'bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_b64':base64.b64encode(compressed).decode()}
    assert all(sha(files[label])==v['raw_sha256'] for label,v in archives.items())
    print(json.dumps({'status':'PAIRED_CFG_ORIGINAL_GPU_CPU_TERMINAL_SOURCE_COST_RELEASE_BYTES_CAPTURE_PASS_NOT_RESEARCH_VERDICT',
        'observed_unix':time.time(),'source_revision':G['source_revision'],'run_id':G['run_id'],'pids_absent':pids,'budget':budget,'supervisor':sup,
        'GPU':gpu,'apps':apps,'lock_available':True,'planned_scope':r['planned_scope'],'new_videos':5,'audited_full93_videos':6,'source_files_checked':len(C['payload_sha256']),'archives':archives}))
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','gpu-launch','cpu-launch','prefix'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--ssh-target',required=True);a=p.parse_args()
    c,g,post=[json.loads(path.read_text()) for path in (a.config,a.gpu_launch,a.cpu_launch)]
    assert g['run_id']==c['preregistration']['run_id']=='wc-w3-paired-cfg-r1'
    labels=['supervisor_json','runner_json','run_log','gpu_monitor_jsonl','CPU_receipt_json','CPU_binding_json','CPU_driver_log','CPU_score_json','CPU_score_log','budget_after_json']
    outputs={n:Path(str(a.prefix)+'_'+n+'_native.gz') for n in labels};result=Path(str(a.prefix)+'_terminal_capture.json')
    assert a.prefix.parent.is_dir() and all(not path.exists() for path in [*outputs.values(),result])
    cmd='C='+repr(c)+'\nG='+repr(g)+'\nP='+repr(post)+'\n'+REMOTE
    response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',a.ssh_target,'python3 -'],input=cmd,text=True,capture_output=True,timeout=60)
    if response.returncode:raise RuntimeError(response.stderr[-4000:])
    value=json.loads(response.stdout);archives=value.pop('archives');assert set(archives)==set(outputs);decoded={}
    for label,item in archives.items():
        compressed=base64.b64decode(item.pop('gzip_b64'));raw=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==item['gzip_sha256'] and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256']
        decoded[label]=(compressed,raw)
    value['archives']={str(outputs[label]):item for label,item in archives.items()}
    value['local_input_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.config,a.gpu_launch,a.cpu_launch)}
    for label,(compressed,_) in decoded.items():
        with outputs[label].open('xb') as f:f.write(compressed)
    (a.prefix.parent/'budget.json').write_bytes(decoded['budget_after_json'][1])
    with result.open('x') as f:f.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','run_id','new_videos','audited_full93_videos','pids_absent')}))

if __name__=='__main__':main()
