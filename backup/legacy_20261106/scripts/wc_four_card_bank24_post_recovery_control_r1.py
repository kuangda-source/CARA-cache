"""Once-only launch and collection of the separate BANK24 CPU post recovery."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

from wc_four_card_policy_assets_r1 import ssh
from wc_four_card_resource_cpu_r4 import write
from wc_four_card_bank24_advance_terminal_r1 import authority, read, sha, require

LAUNCH='reports/wc_four_card_BANK24_full24_GPU_retry2_actual_launch_20261022.json'
SOURCE='scripts/wc_four_card_bank24_post_recovery_r1.py'


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['launch','status','collect']);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();require(not a.output.exists(),'Keep every original receipt')
    L=read(Path(LAUNCH))['dispatch'];A=authority(L)
    job=L['stage']+'/post-recovery-r1-20261022'
    prefix='stage_name='+repr(L['stage'])+'\njob_name='+repr(job)+'\n'
    prefix+='''import json,pathlib,sys,hashlib,subprocess,os,time,base64
stage=pathlib.Path(stage_name);job=pathlib.Path(job_name);sys.path.insert(0,str(stage))
from four_card_bank24_container_transport_r1 import identity,alive
'''
    if a.mode=='launch':
        revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        blob=subprocess.check_output(['git','show',revision+':'+SOURCE]);require(blob==Path(SOURCE).read_bytes(),'Publish exact CPU recovery code first')
        from wc_four_card_bank24_native_transport_r4 import RUNTIME_REF
        runtime=read(Path(RUNTIME_REF));wrapper=str(Path(runtime['job'])/'bin/python3')
        code=prefix+'source='+repr(base64.b64encode(blob).decode())+'\nrevision='+repr(revision)+'\nwrapper='+repr(wrapper)+'\n'+'''
from four_card_bank24_execution_tools_r1 import verify_registration,post_conditions,read
verify_registration(stage);L=read(stage/'scout-GPU-launch.json')
post_conditions(pathlib.Path(L['project']),stage,L,'ABSENT')
if job.exists():
 print(json.dumps(dict(status='EXISTING_CPU_RECOVERY_RESTORE_ONLY',job=str(job))));sys.exit(0)
job.mkdir();raw=base64.b64decode(source);(job/'recovery.py').write_bytes(raw)
with (job/'supervisor.log').open('x') as log:
 child=subprocess.Popen([wrapper,str(job/'recovery.py'),'supervise','--stage',str(stage),'--job',str(job)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
v=dict(status='BANK24_SEPARATE_CPU_RECOVERY_DISPATCHED',job=str(job),launch_id=L['launch_id'],identity=identity(child.pid),source_revision=revision,source_sha256=hashlib.sha256(raw).hexdigest(),started_unix=time.time(),GPU_submissions=0)
(job/'launch.json').write_text(json.dumps(v,indent=2)+'\\n');print(json.dumps(v))
'''
    else:
        code=prefix+'''
L=json.loads((job/'launch.json').read_text());v=dict(status='BANK24_CPU_RECOVERY_STATUS',launch=L,supervisor_alive=alive(L['identity']))
for n in ['supervisor-result.json','host-release.json']:
 if (job/n).is_file():v[n]=json.loads((job/n).read_text())
if (job/'failure.log').is_file():v['failure_log']=(job/'failure.log').read_text()[-10000:]
if (job/'supervisor-failure.log').is_file():v['supervisor_failure_log']=(job/'supervisor-failure.log').read_text()[-10000:]
'''
        if a.mode=='collect':
            code+='''
assert not v['supervisor_alive'],'Keep original recovery handle; still running'
if v.get('supervisor-result.json',{}).get('status')=='COMPLETE_CPU_RECOVERY_COLLECTED':
 raw=(job/'complete-capture.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==v['supervisor-result.json']['capture_sha256'];v=json.loads(raw)
'''
        code+='print(json.dumps(v))\n'
    value=ssh(code)
    if a.mode=='collect' and value.get('mode')=='terminal':value['advanced_terminal_authority']=A
    write(a.output,value)
    print(json.dumps({k:value.get(k) for k in ('status','job','identity','started_unix','supervisor_alive','GPU_submissions')}))


if __name__=='__main__':main()
