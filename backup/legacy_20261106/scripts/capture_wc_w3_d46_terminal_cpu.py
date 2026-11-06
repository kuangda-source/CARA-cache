#!/usr/bin/env python3
"""Archive completed original D46 GPU/CPU evidence without another submission."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''
import base64,fcntl,gzip,hashlib,json,math,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/M['stage'];out=root/'outputs'/M['run_id'];post=root/POST
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'.sync/f1.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sup=json.loads((out/'supervisor.json').read_text())
    runner=json.loads((out/'diagnostic/receipt.json').read_text())
    cpu=json.loads((post/'continuation.json').read_text())
    score=json.loads((post/'audit-score.json').read_text())
    budget=json.loads((root/'reports/budget.json').read_text())
    assert sup['status']=='EXITED_REQUIRES_RESULT_AUDIT' and sup['exit_code']==0
    assert sup['source_revision']==runner['source_revision']==cpu['source_revision']==SOURCE
    assert sup['run_id']==runner['run_id']==cpu['run_id']==M['run_id']
    assert runner['status']=='D46_TWO_SEEDS_GPU_CORE_COMPLETE_AUDIT_AND_SCORE_PENDING'
    assert cpu['status']=='D46_ORIGINAL_GPU_AND_CPU_FULL93_SCORING_COMPLETE_RESEARCH_INTERPRETATION_PENDING'
    assert len(cpu['steps'])==1 and cpu['steps'][0]['exit_code']==0 and cpu['GPU_submissions']==0
    assert score['status']=='D46_TWO_REGISTERED_SEEDS_FULL_CPU_AUDIT_AND_AVAILABLE_LOSSES_COMPLETE_NOT_CONF'
    assert score['CUDA_initialized'] is False and score['GPU_submissions']==0
    assert runner['planned_scope']==score['planned_scope']==M['scope_counts']
    assert [c['seed'] for c in runner['cases']]==[c['seed'] for c in score['cases']]==[1,2]
    assert score['runner_sha256']==sha(out/'diagnostic/receipt.json')
    assert cpu['result_sha256']==sha(post/'audit-score.json')
    assert sup['config_sha256']==score['config_sha256']==M['payload_sha256']['seed-config.json']
    assert budget==sup['budget_after']==score['budget'] and not any('inflight' in k for k in budget)
    assert budget['cap_gpu_hours']==24
    assert math.isclose(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    pids=[sup['pid'],sup['child_pid'],cpu['pid'],cpu['steps'][0]['pid']]
    assert len(set(pids))==4 and all(not pathlib.Path('/proc/'+str(p)).exists() for p in pids)
    assert not sup['release']['pids'] and sup['release']['memory_used_mib']<=1024
    config=json.loads((stage/'seed-config.json').read_text());base=root/config['base_stage']
    for name,h in M['payload_sha256'].items():assert sha(stage/name)==h,name
    for name,h in M['base_payload_sha256'].items():
        assert sha(base/name)==h,name
        if name not in M['payload_sha256']:assert sha(stage/name)==h,name
    for name,h in config['project_input_sha256'].items():assert sha(root/name)==h,name
    accepted=sum(c['Native_outcome']=='ACCEPTED' for c in score['cases'])
    videos=score['videos'];assert len(videos)==8+accepted
    for v in videos:
        p=pathlib.Path(v['path']);assert (out/'diagnostic').resolve() in p.resolve().parents
        assert v['full93_decode'] and p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
    assert {p.resolve() for p in (out/'diagnostic').glob('**/*.mp4')}=={pathlib.Path(v['path']).resolve() for v in videos}
    gpu=subprocess.check_output(['nvidia-smi','-i',sup['gpu_uuid'],'--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
    files={'supervisor_json':out/'supervisor.json','runner_json':out/'diagnostic/receipt.json',
        'run_log':out/'run.log','gpu_monitor_jsonl':out/'gpu-monitor.jsonl',
        'CPU_continuation_json':post/'continuation.json','CPU_binding_json':post/'binding.json',
        'CPU_continuation_log':post/'continuation-launch.log','CPU_score_json':post/'audit-score.json',
        'CPU_score_log':post/'audit-score.log','budget_after_json':root/'reports/budget.json'}
    archives={}
    for label,p in files.items():
        raw=p.read_bytes();compressed=gzip.compress(raw,mtime=0)
        archives[label]={'bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_b64':base64.b64encode(compressed).decode(),'gzip_sha256':hashlib.sha256(compressed).hexdigest()}
    assert all(sha(files[k])==v['raw_sha256'] for k,v in archives.items())
    print(json.dumps({'archives':archives,'observed_unix':time.time(),'source_revision':SOURCE,
        'run_id':M['run_id'],'supervisor':sup,'budget':budget,'pids_absent':pids,
        'GPU':gpu,'apps':apps,'lock_available':True,'new_videos':len(videos),
        'registered_seed_denominator':2,'Native_accepted':accepted,'planned_scope':M['scope_counts'],
        'selected_source_files_checked':len(M['payload_sha256']),
        'base_source_files_checked':len(M['base_payload_sha256']),
        'CPU_complete_original_score_sha256':sha(post/'audit-score.json'),
        'status':'D46_ORIGINAL_GPU_CPU_TERMINAL_SOURCE_COST_RELEASE_BYTES_CAPTURE_PASS_NOT_RESEARCH_VERDICT'}))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','launch','prefix'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('ssh-target','postrun'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text());launch=json.loads(args.launch.read_text())
    assert launch['source_revision'] and manifest['run_id']=='wc-w3-d46-fresh-seeds-r3'
    labels=['supervisor_json','runner_json','run_log','gpu_monitor_jsonl','CPU_continuation_json',
        'CPU_binding_json','CPU_continuation_log','CPU_score_json','CPU_score_log','budget_after_json']
    outputs={label:Path(str(args.prefix)+'_'+label+'_native.gz') for label in labels}
    result_path=Path(str(args.prefix)+'_terminal_capture.json')
    assert args.prefix.parent.is_dir() and all(not x.exists() for x in [*outputs.values(),result_path])
    command='M='+repr(manifest)+'\nSOURCE='+repr(launch['source_revision'])+'\nPOST='+repr(args.postrun)+'\n'+REMOTE
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',args.ssh_target,'python3 -'],
        input=command,text=True,capture_output=True,timeout=60)
    if r.returncode:raise RuntimeError(r.stderr[-4000:])
    value=json.loads(r.stdout);archives=value.pop('archives');assert set(archives)==set(outputs)
    decoded={}
    for label,item in archives.items():
        compressed=base64.b64decode(item.pop('gzip_b64'));raw=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==item['gzip_sha256']
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256']
        decoded[label]=(compressed,raw)
    value['archives']={str(outputs[k]):v for k,v in archives.items()}
    value['local_inputs_sha256']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [args.manifest,args.launch]}
    for label,(compressed,raw) in decoded.items():
        with outputs[label].open('xb') as f:f.write(compressed)
    # This copies settled original bytes; a live reserve can never reach here.
    (args.prefix.parent/'budget.json').write_bytes(decoded['budget_after_json'][1])
    with result_path.open('x') as f:f.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','run_id','new_videos','Native_accepted','pids_absent')}))


if __name__=='__main__':main()
