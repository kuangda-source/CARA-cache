#!/usr/bin/env python3
"""Dispatch the exact full24 once after independent real production CPU."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
STANDING_QUOTE = '批准，以后少于 12gpuh 时的都不用问了，直接启动'


def authority_for(capture, accepted, gpu_uuid, launch_id, *, accepted_sha256, specific=None):
    from wcomr.drop1_window24_cpu_acceptance_r1 import accept
    from wcomr.drop1_window24_execution_envelope_r1 import input_fingerprint, validate_authority
    from wcomr.drop1_window24_production_r1 import RUN, COUNTS
    computed = accept(capture)
    if not computed['CPU_accepted'] or any(accepted.get(k) != v for k, v in computed.items()):
        raise ValueError('Whole real24 CPU acceptance cannot be inherited from a partial or different card')
    c = capture['files']['config']['data']; source = capture['registration']['source_revision']
    auth = dict(kind='EXISTING_PLAN_UNDER12_AUTONOMY', direct_user_authorization=True,
        user_reply_quote=STANDING_QUOTE, source_revision=source, launch_id=launch_id,
        whole_card_run=RUN, gpu_uuid=gpu_uuid, registration_sha256=capture['registration_sha256'],
        config_sha256=capture['files']['config']['sha256'], production_CPU_sha256=capture['files']['proof']['sha256'],
        independent_CPU_acceptance_sha256=accepted_sha256, bound_input_fingerprint=input_fingerprint(c),
        scope_counts=COUNTS, forecast_complete_GPUh=c['forecast_complete_GPUh'], billed_limit_GPUh=c['billed_limit_GPUh'],
        cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223, autonomy_exclusive_upper_GPUh=12)
    if c['billed_limit_GPUh'] >= 12:
        if specific is None: raise ValueError('Complete >=12GPUh card needs specific direct human approval')
        auth = dict(specific)
    validate_authority(c, capture['registration'], capture['files']['proof']['data'], accepted, auth,
        source_revision=source, gpu_uuid=gpu_uuid, registration_sha256=capture['registration_sha256'],
        config_sha256=auth['config_sha256'], proof_sha256=auth['production_CPU_sha256'],
        accepted_sha256=accepted_sha256)
    return auth


REMOTE = r'''
import hashlib,json,math,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
p=pathlib.PurePosixPath(STAGE);assert not p.is_absolute() and '..' not in p.parts and len(p.parts)==2 and p.parts[0]=='.sync'
stage=root/STAGE;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==AUTH['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==AUTH['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.path.insert(0,str(stage/'src'))
from wcomr.drop1_window24_production_r1 import CONFIG,CPU_RESULT,RUN,COUNTS,validate,write
from wcomr.drop1_window24_cpu_acceptance_r1 import BUNDLE,validate_bundle
from wcomr.drop1_window24_execution_envelope_r1 import validate_authority
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process
c,reg,*_=validate(root,stage);proof=json.loads((stage/CPU_RESULT).read_text());accepted=json.loads(ACCEPTED_TEXT)
validate_bundle(json.loads((stage/BUNDLE).read_text()),proof,c,reg,
 registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),proof_sha256=sha(stage/CPU_RESULT))
cpu=json.loads((stage/'window24-CPU-launch.json').read_text());assert not same_live_process(cpu['identity'])
assert accepted['original_CPU_identity']==cpu['identity']
assert hashlib.sha256(ACCEPTED_TEXT.encode()).hexdigest()==AUTH['independent_CPU_acceptance_sha256']
validate_authority(c,reg,proof,accepted,AUTH,source_revision=AUTH['source_revision'],gpu_uuid=AUTH['gpu_uuid'],
 registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
 proof_sha256=sha(stage/CPU_RESULT),accepted_sha256=hashlib.sha256(ACCEPTED_TEXT.encode()).hexdigest())
assert not (root/'outputs'/RUN).exists()
with (stage/'window24-GPU-dispatch-fence.json').open('x') as h:
 json.dump(dict(launch_id=AUTH['launch_id'],source_revision=AUTH['source_revision'],created_unix=time.time()),h);h.flush();os.fsync(h.fileno())
authpath=stage/'window24-GPU-authorization.json';assert not authpath.exists();write(authpath,AUTH)
with (stage/'window24-production-CPU-independent-acceptance.json').open('x') as h:
 h.write(ACCEPTED_TEXT);h.flush();os.fsync(h.fileno())
command=[sys.executable,str(stage/'scripts/supervise_wc_drop1_window24_r1.py'),'--project',str(root),'--stage',str(stage),
 '--authorization',str(authpath),'--source-revision',AUTH['source_revision'],'--gpu-uuid',AUTH['gpu_uuid']]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
identity=process_identity(child.pid);assert identity['state'] not in (None,'Z','X')
assert 'supervise_wc_drop1_window24_r1.py' in identity['command']
now=time.time();receipt=dict(status='WINDOW24_COMPLETE24_DISPATCHED_ADMISSION_PENDING',source_revision=AUTH['source_revision'],
 launch_id=AUTH['launch_id'],stage=str(stage),project=str(root),run_id=RUN,gpu_uuid=AUTH['gpu_uuid'],
 registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),production_CPU_sha256=sha(stage/CPU_RESULT),
 authorization_sha256=sha(authpath),independent_CPU_acceptance_sha256=AUTH['independent_CPU_acceptance_sha256'],
 bound_input_fingerprint=AUTH['bound_input_fingerprint'],scope_counts=COUNTS,supervisor_pid=child.pid,supervisor_identity=identity,
 post_watcher_pid=None,post_watcher_identity=None,command=command,started_unix=now,
 forecast_complete_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
 halfway_check_not_before_unix=now+math.ceil(c['forecast_complete_GPUh']*1800),
 next_check_not_before_unix=now+math.ceil(c['forecast_complete_GPUh']*3600+900),
 actual_GPU_admission_accepted_by_dispatch=False,new_quality_or_speed_result=False)
write(stage/'window24-GPU-launch.json',receipt)
try:
 postcommand=[sys.executable,str(stage/'scripts/watch_wc_drop1_window24_post_cpu_r1.py'),'--project',str(root),'--stage',str(stage),
  '--supervisor-pid',str(child.pid),'--supervisor-start-ticks',str(identity['start_ticks'])]
 with (stage/'post-watcher.log').open('xb') as log:
  post=subprocess.Popen(postcommand,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
 receipt.update(post_watcher_pid=post.pid,post_watcher_identity=process_identity(post.pid),post_command=postcommand)
except BaseException as e:receipt.update(post_dispatch_error_type=type(e).__name__,post_dispatch_error=str(e));raise
finally:write(stage/'window24-GPU-launch.json',receipt);print(json.dumps(receipt,allow_nan=False))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('CPU-launch-ref','CPU-capture','CPU-acceptance','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--gpu-uuid',required=True);p.add_argument('--specific-authorization',type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Keep the original GPU dispatch and never replay it')
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.immutable_stage_payload_r1 import registered_base_reference
    from wcomr.drop1_window24_execution_envelope_r1 import validate_authority
    raw=a.CPU_capture.read_bytes();capture=json.loads(gzip.decompress(raw));launch=json.loads(a.CPU_launch_ref.read_text())['launch']
    text=a.CPU_acceptance.read_text();accepted=json.loads(text)
    if capture['launch']!=launch or accepted['capture_sha256']!=hashlib.sha256(raw).hexdigest():
        raise ValueError('The exact original complete CPU capture and handle required')
    specific=json.loads(a.specific_authorization.read_text()) if a.specific_authorization else None
    launch_id=specific['launch_id'] if specific else str(uuid.uuid4())
    auth=authority_for(capture,accepted,a.gpu_uuid,launch_id,accepted_sha256=hashlib.sha256(text.encode()).hexdigest(),specific=specific)
    validate_authority(capture['files']['config']['data'],capture['registration'],capture['files']['proof']['data'],accepted,auth,
        source_revision=launch['source_revision'],gpu_uuid=a.gpu_uuid,registration_sha256=launch['registration_sha256'],
        config_sha256=capture['files']['config']['sha256'],proof_sha256=capture['files']['proof']['sha256'],accepted_sha256=auth['independent_CPU_acceptance_sha256'])
    stage=registered_base_reference(capture['registration']['stage'],launch['stage'])['project_relative']
    code='STAGE='+repr(stage)+'\nAUTH='+repr(auth)+'\nACCEPTED_TEXT='+repr(text)+'\n'+REMOTE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],capture_output=True,timeout=180)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        dispatch=json.loads(call.stdout)
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        result=dict(status='WINDOW24_GPU_DISPATCH_OBSERVATION_UNKNOWN_NO_REPLAY',stage=stage,source_revision=launch['source_revision'],
            launch_id=launch_id,error_type=type(e).__name__,error=str(e),original_task_terminal=False,
            original_recovery_ref=stage+'/window24-GPU-launch.json',authorization=auth,no_GPU_relaunch_authority=True)
        with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
        raise
    result=dict(dispatch=dispatch,authorization=auth,transport_exit_code=0,source_revision=launch['source_revision'],
        launcher_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(dispatch))


if __name__=='__main__':main()
