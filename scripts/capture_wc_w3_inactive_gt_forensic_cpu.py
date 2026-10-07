#!/usr/bin/env python3
"""Capture separate completed CPU forensics plus immutable original failure bytes."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import base64,fcntl,gzip,hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/L['stage'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'.sync/f1.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(stage/'manifest.json')==L['manifest_sha256'] and sha(stage/'driver.py')==L['driver_sha256']
 m=json.loads((stage/'manifest.json').read_text());r=json.loads((stage/'receipt.json').read_text());s=json.loads((stage/'score.json').read_text());audit=json.loads((stage/'audit.json').read_text());terminal=json.loads((stage/'terminal-binding.json').read_text())
 assert r['exit_code']==0 and r['status']=='H_T39_CONDITIONAL_CPU_AUDIT_SCORE_EXIT0_ORIGINAL_STRICT_GPU_FAILURE_RETAINED' and r['pid']==L['pid'] and r['CPU_source_revision']==L['source_revision']==m['source_revision']
 assert s['status']=='INACTIVE_GT_CONDITIONAL_FULL93_THREE_LOSSES_TWO_PAIRS_NOT_ORIGINAL_ACCEPTANCE_NOT_CONF' and r['score_sha256']==sha(stage/'score.json') and r['audit_sha256']==sha(stage/'audit.json')
 assert r['original_strict_GPU_acceptance'] is False and s['original_strict_GPU_acceptance'] is False and r['original_GPU_exit_code']==r['original_post_CPU_exit_code']==s['original_GPU_exit_code']==s['original_CPU_exit_code']==1
 assert s['GPU_submissions']==r['GPU_submissions']==0 and s['CUDA_initialized'] is False and r['CUDA_initialized'] is False
 assert len(s['videos'])==6 and set(s['losses'])=={'BASE','SINGLE','PAIRED'} and len(s['signed_pairs'])==2
 assert r['payload_after_sha256']==m['payload_sha256']=={n:sha(stage/n) for n in m['payload_sha256']}
 selected=root/m['original_GPU_stage'];c=json.loads((selected/'paired-config.json').read_text());assert sha(selected/'paired-config.json')==m['config_sha256'] and {n:sha(selected/n) for n in c['payload_sha256']}==c['payload_sha256']
 pids=m['original_PIDs']+[r['pid'],r['child_pid']];assert len(set(pids))==5 and all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
 assert terminal['original_files']==m['original_files'] and {n:sha(root/f) for n,f in m['original_files'].items()}==terminal['original_file_sha256']
 for n in m['original_files']:
  assert hashlib.sha256(gzip.decompress((stage/(n+'_original_native.gz')).read_bytes())).hexdigest()==terminal['original_file_sha256'][n]
 budget=json.loads((root/'reports/budget.json').read_text());assert budget==s['budget'] and not any('inflight' in k for k in budget)
 for v in s['videos']:
  path=pathlib.Path(v['path']);assert v['full93_decode'] and path.stat().st_size==v['bytes'] and sha(path)==v['sha256']
 sup=json.loads((root/m['original_files']['supervisor']).read_text());apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True);assert not any(x.split(',')[0].strip()==sup['gpu_uuid'] for x in apps.splitlines())
 files={n:stage/name for n,name in {'CPU_receipt_json':'receipt.json','CPU_audit_json':'audit.json','CPU_score_json':'score.json','CPU_score_log':'score.log','CPU_driver_log':'driver.log','CPU_manifest_json':'manifest.json','CPU_launch_json':'launch.json','CPU_terminal_binding_json':'terminal-binding.json'}.items()};files.update({'original_'+n:root/f for n,f in m['original_files'].items()})
 archives={}
 for n,path in files.items():
  raw=path.read_bytes();data=gzip.compress(raw,mtime=0);archives[n]={'bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(data).hexdigest(),'gzip_b64':base64.b64encode(data).decode()}
 assert all(sha(files[n])==v['raw_sha256'] for n,v in archives.items())
 print(json.dumps({'status':'H_T39_CONDITIONAL_CPU_ORIGINAL_FAILURE_SOURCE_BYTES_EXIT_COST_CAPTURE_PASS_NOT_ORIGINAL_GPU_ACCEPTANCE','observed_unix':time.time(),'CPU_source_revision':L['source_revision'],'original_GPU_source_revision':m['original_GPU_source_revision'],'pids_absent':pids,'GPU_released':True,'lock_available':True,'GPU_submissions':0,'original_strict_GPU_acceptance':False,'new_payload_files_checked':len(m['payload_sha256']),'original_payload_files_checked':len(c['payload_sha256']),'budget':budget,'CPU_score_seconds':s['CPU_wall_seconds'],'archives':archives}))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu-launch',type=Path,required=True);p.add_argument('--prefix',type=Path,required=True);p.add_argument('--ssh-target',required=True);a=p.parse_args()
    launch=json.loads(a.cpu_launch.read_text());target=Path(str(a.prefix)+'_terminal_capture.json');assert not target.exists()
    response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',a.ssh_target,'python3 -'],input='L='+repr(launch)+'\n'+REMOTE,text=True,capture_output=True,timeout=60)
    if response.returncode:raise RuntimeError(response.stderr[-4000:])
    value=json.loads(response.stdout);archives=value.pop('archives');paths={n:Path(str(a.prefix)+'_'+n+'_native.gz') for n in archives}
    assert all(not path.exists() for path in paths.values())
    for n,item in archives.items():
        data=base64.b64decode(item.pop('gzip_b64'));raw=gzip.decompress(data)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256'] and hashlib.sha256(data).hexdigest()==item['gzip_sha256']
        with paths[n].open('xb') as f:f.write(data)
    value['archives']={str(paths[n]):v for n,v in archives.items()}
    with target.open('x') as f:f.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','CPU_score_seconds','pids_absent','original_strict_GPU_acceptance')}))


if __name__=='__main__':main()
