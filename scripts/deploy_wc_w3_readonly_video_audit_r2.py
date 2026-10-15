#!/usr/bin/env python3
"""One fresh CPU-only reader; original W3 and running same26D remain read-only."""
import argparse,hashlib,io,json,shlex,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
FILES=('src/wcomr/w3_video_failure_audit_r2.py','scripts/postprocess_wc_w3_fullscope_readonly_repair_r2.py','scripts/deploy_wc_w3_readonly_video_audit_r2.py','reports/wc_w3_video_failure_reader_local_CPU_controls_20261016.json')

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();payload={}
 for n in FILES:
  digest=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
  assert digest==hashlib.sha256(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)).hexdigest();payload[n]=digest
 original=json.loads((ROOT/'reports/wc_w3_label64_actual_production_CPU_r3_launch_20261015.json').read_text())['launch']
 stream=io.BytesIO()
 with tarfile.open(fileobj=stream,mode='w:gz') as archive:
  for n in FILES:archive.add(ROOT/n,arcname=n,recursive=False)
 code='REV='+repr(rev)+'\nPAYLOAD='+repr(payload)+'\nORIGINAL='+repr(original)+'\n'+r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
old=root/'.sync/wc-w3-label64-production-cpu-r3-20261015';stage=root/'.sync/wc-w3-readonly-video-audit-r2-20261016'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not stage.exists(),'Never overwrite old CPU/GPU directories'
assert sha(old/'registration.json')==ORIGINAL['registration_sha256']
reg0=json.loads((old/'registration.json').read_text());assert reg0['source_revision']=='047dcf181a3ab706002b2965e74b626e4648deea'
assert all(sha(old/n)==h for n,h in reg0['payload_sha256'].items())
post=old/'scripts/postprocess_wc_w3_label64_full864_cpu_r1.py'
original_post_failure=json.loads((old/'CPU-final-results.json').read_text());assert original_post_failure['error_type']=='CalledProcessError'
assert not pathlib.Path('/proc/876879').exists(),'Original GPU task must be terminal'
stage.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as archive:
 for member in archive:
  assert member.isfile() and member.name in PAYLOAD and '..' not in pathlib.PurePosixPath(member.name).parts
  path=stage/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read());assert sha(path)==PAYLOAD[member.name]
reg=dict(source_revision=REV,payload_sha256=PAYLOAD,original_GPU_source_revision=reg0['source_revision'],original_registration_sha256=ORIGINAL['registration_sha256'],original_post_source_sha256=sha(post),original_stage=str(old),GPU_submissions=0,original_stage_written=False)
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=[sys.executable,str(stage/'scripts/postprocess_wc_w3_fullscope_readonly_repair_r2.py'),'--project',str(root),'--original-stage',str(old),'--repair-stage',str(stage)]
with (stage/'CPU.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1'})
now=time.time();receipt=dict(status='W3_FRESH_VIDEO_EXCEPTION_READONLY_CPU_DISPATCHED',pid=job.pid,source_revision=REV,stage=str(stage),original_stage=str(old),original_GPU_source_revision=reg0['source_revision'],registration_sha256=sha(stage/'registration.json'),command=command,launched_unix=now,next_check_not_before_unix=now+540,GPU_submissions=0,original_stage_written=False)
(stage/'launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
 result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],input=stream.getvalue(),capture_output=True,timeout=120)
 value=dict(transport_exit_code=result.returncode,stderr=result.stderr.decode())
 try:value['launch']=json.loads(result.stdout)
 except json.JSONDecodeError:value['stdout']=result.stdout.decode()
 a.output.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value));raise SystemExit(result.returncode)
if __name__=='__main__':main()
