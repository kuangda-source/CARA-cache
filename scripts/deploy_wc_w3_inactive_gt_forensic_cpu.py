#!/usr/bin/env python3
"""Freeze a CPU-only H-T39 supervisor; wait for unchanged original terminal receipts."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

DRIVER = r'''
import gzip,hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(__file__).parent;M=json.loads((stage/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();start=time.monotonic()
s={'status':'H_T39_CPU_WAITING_ORIGINAL_GPU_AND_POST_CPU_TERMINAL_ZERO_SCORES','pid':os.getpid(),'CPU_source_revision':M['source_revision'],'original_PIDs':M['original_PIDs'],'GPU_submissions':0,'scored_videos':0,'started_unix':time.time()}
def save():
 p=stage/'receipt.tmp';p.write_text(json.dumps(s,indent=2,allow_nan=False)+'\n');p.replace(stage/'receipt.json')
save()
try:
 assert {n:sha(stage/n) for n in M['payload_sha256']}==M['payload_sha256']
 files={n:root/f for n,f in M['original_files'].items()}
 while True:
  sup=json.loads(files['supervisor'].read_text());post=json.loads(files['original_post_CPU'].read_text())
  assert [sup['pid'],sup['child_pid'],post['pid']]==M['original_PIDs'] and sup['source_revision']==post['source_revision']==M['original_GPU_source_revision']
  if 'exit_code' in sup and 'exit_code' in post and all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in M['original_PIDs']):break
  if 'exit_code' not in sup and not pathlib.Path('/proc/'+str(sup['pid'])).exists():raise ValueError('Original GPU supervisor lost without terminal receipt')
  time.sleep(10)
 # No original code or receipt is overwritten; bind all settled originals once.
 terminal={'original_files':M['original_files'],'original_file_sha256':{n:sha(p) for n,p in files.items()},'original_PIDs':M['original_PIDs'],'original_terminal_ended_unix':sup['ended_unix'],'config_sha256':M['config_sha256']}
 with (stage/'terminal-binding.json').open('x') as f:f.write(json.dumps(terminal,indent=2)+'\n')
 for n,p in files.items():
  with (stage/(n+'_original_native.gz')).open('xb') as f:f.write(gzip.compress(p.read_bytes(),mtime=0))
 assert {n:sha(p) for n,p in files.items()}==terminal['original_file_sha256']
 python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python';cmd=[python,'-u',str(stage/'scripts/audit_score_wc_w3_inactive_gt_forensic_cpu.py'),'--project',str(root),'--selected-stage',str(root/M['original_GPU_stage']),'--forensic-stage',str(stage)]
 s.update(status='H_T39_ORIGINAL_TERMINAL_CAPTURED_CPU_CONDITIONAL_AUDIT_AND_SCORE',command=cmd,terminal_binding_sha256=sha(stage/'terminal-binding.json'),original_GPU_exit_code=sup['exit_code'],original_post_CPU_exit_code=post['exit_code']);save()
 with (stage/'score.log').open('x') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=root/'runtime',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_CACHE=str(root/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH=str(root/M['original_GPU_stage']/'src')+':.:packages/cosmos-oss:packages/cosmos-cuda'));s['child_pid']=child.pid;save();s['exit_code']=child.wait()
 if s['exit_code']!=0:raise ValueError('H-T39 conditional CPU refusal or scoring failure; original failure and costs retained')
 result=json.loads((stage/'score.json').read_text());assert result['status']=='INACTIVE_GT_CONDITIONAL_FULL93_THREE_LOSSES_TWO_PAIRS_NOT_ORIGINAL_ACCEPTANCE_NOT_CONF' and len(result['losses'])==3 and len(result['signed_pairs'])==2 and result['original_strict_GPU_acceptance'] is False and result['CUDA_initialized'] is False and result['GPU_submissions']==0
 s.update(status='H_T39_CONDITIONAL_CPU_AUDIT_SCORE_EXIT0_ORIGINAL_STRICT_GPU_FAILURE_RETAINED',scored_videos=3,score_sha256=sha(stage/'score.json'),audit_sha256=sha(stage/'audit.json'),CUDA_initialized=False,original_strict_GPU_acceptance=False)
except BaseException as error:
 s.update(status='H_T39_CPU_REFUSED_OR_FAILED_ORIGINALS_RETAINED_NOT_METHOD_DENIAL',exit_code=s.get('exit_code',1),error=str(error));raise
finally:
 s.update(wait_and_CPU_wall_seconds=time.monotonic()-start,ended_unix=time.time(),payload_after_sha256={n:sha(stage/n) for n in M['payload_sha256']});save()
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--ssh-target',required=True);a=p.parse_args()
    repo=a.repo.resolve();source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    files=['scripts/wc_w3_inactive_gt_forensic.py','scripts/audit_score_wc_w3_inactive_gt_forensic_cpu.py',
           'scripts/check_wc_w3_inactive_gt_forensic_cpu.py','reports/wc_w3_inactive_gt_forensic_new_gate_cpu_r1_20261008.json',
           'manifests/wc_w3_paired_inactive_gt_cpu_preregistration_20261008.json',
           'manifests/wc_w3_paired_cfg_preregistration_20261008.json',
           'reports/wc_w3_paired_cfg_parent_prefix_bridge_cpu_20261008.json',
           'reports/wc_w3_paired_cfg_parent_prefix_native_20261008.json.gz',
           'reports/wc_w3_inactive_gt_semantics_cpu_r1_20261008_result_json_native.gz',
           'reports/wc_w3_inactive_gt_semantics_cpu_r1_20261008_receipt_json_native.gz']
    for name in files:
        committed=subprocess.check_output(['git','show',source+':'+name],cwd=repo)
        assert committed==(repo/name).read_bytes(),'Uncommitted new CPU source: '+name
    g=json.loads((repo/'reports/wc_w3_paired_cfg_gpu_r1_launch_20261008.json').read_text());post=json.loads((repo/'reports/wc_w3_paired_cfg_post_cpu_r1_launch_20261008.json').read_text())
    out='outputs/'+g['run_id']
    original={'runner':out+'/diagnostic/receipt.json','supervisor':out+'/supervisor.json','run_log':out+'/run.log',
              'GPU_monitor':out+'/gpu-monitor.jsonl','original_post_CPU':post['stage']+'/receipt.json',
              'original_post_binding':post['stage']+'/binding.json','original_post_log':post['stage']+'/driver.log',
              'budget':'reports/budget.json'}
    m={'identity':'WC-W3-PAIRED-INACTIVE-GT-FORENSIC-CPU-R1-20261008','stage':'.sync/wc-w3-inactive-gt-forensic-cpu-r1-20261008',
       'source_revision':source,'original_GPU_source_revision':g['source_revision'],'original_GPU_stage':g['stage'],
       'original_PIDs':[*post['bound_GPU_PIDs'],post['pid']],'original_files':original,'config_sha256':g['config_sha256'],
       'semantic_result_raw_sha256':'207105fc65400b3cdf5cf33bfd2e06083d8d6e32dd30ff2e04c10674bd730530',
       'payload_sha256':{n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in files},'GPU_submissions':0,
       'original_strict_GPU_acceptance':False,'independent_CONF':False}
    new={n:base64.b64encode((repo/n).read_bytes()).decode() for n in files}
    remote='M='+repr(m)+'\nNEW='+repr(new)+'\nDRIVER='+repr(DRIVER)+'\n'+r'''
import base64,hashlib,json,os,pathlib,subprocess
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');selected=root/M['original_GPU_stage'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(selected/'paired-config.json')==M['config_sha256'];c=json.loads((selected/'paired-config.json').read_text());assert {n:sha(selected/n) for n in c['payload_sha256']}==c['payload_sha256']
stage=root/M['stage'];assert not stage.exists();stage.mkdir()
for n,b in NEW.items():
 path=stage/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(b));assert sha(path)==M['payload_sha256'][n]
(stage/'manifest.json').write_text(json.dumps(M,indent=2)+'\n');(stage/'driver.py').write_text(DRIVER)
launch={'status':'H_T39_CPU_SUPERVISOR_DISPATCHED_NOT_SCORE_NOT_GPU','stage':M['stage'],'source_revision':M['source_revision'],'manifest_sha256':sha(stage/'manifest.json'),'driver_sha256':sha(stage/'driver.py'),'original_PIDs':M['original_PIDs'],'GPU_submissions':0}
# Write immutable launch bindings before the scorer can read them.
(stage/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(['python3','-u',str(stage/'driver.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=root,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
launch['pid']=child.pid;print(json.dumps(launch))
'''
    path=repo/'reports/wc_w3_inactive_gt_forensic_cpu_r1_launch_20261008.json';assert not path.exists()
    response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',a.ssh_target,'python3 -'],input=remote,text=True,capture_output=True,timeout=60)
    if response.returncode:raise RuntimeError(response.stderr[-4000:])
    result=json.loads(response.stdout);assert result['driver_sha256']==hashlib.sha256(DRIVER.encode()).hexdigest()
    with path.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
