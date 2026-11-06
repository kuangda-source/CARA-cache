#!/usr/bin/env python3
"""Single dispatch of the original full40 after independent CPU acceptance."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import shlex
import subprocess

PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def resource_ready_before_fence(gpu_uuid, gpu_text, apps_text):
    """Read-only hint; the original supervisor still owns final atomic admission."""
    fields = [x.strip() for x in gpu_text.strip().split(',')]
    if (len(fields) != 4 or fields[0] != gpu_uuid or 'A6000' not in fields[1]
            or fields[3] != '8.6'):
        raise ValueError('Observe the exact original A6000 UUID before dispatch')
    used = int(fields[2])
    if used < 0: raise ValueError('Unknown GPU memory usage cannot authorize dispatch')
    own_pids = []
    for line in apps_text.splitlines():
        if not line.strip(): continue
        values = [x.strip() for x in line.split(',')]
        if len(values) != 2 or int(values[1]) <= 0:
            raise ValueError('Unknown GPU process observation cannot authorize dispatch')
        if values[0] == gpu_uuid: own_pids.append(int(values[1]))
    return used <= 1024 and not own_pids


def remote_code(stage, authority, accepted_text):
    header = ('STAGE=' + repr(stage) + '\nAUTHORITY=' + repr(authority)
              + '\nCPU_ACCEPTED_TEXT=' + repr(accepted_text)
              + '\nCLIENT_SHA=' + repr(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()) + '\n')
    return header + inspect.getsource(resource_ready_before_fence) + r'''
import hashlib,json,math,os,pathlib,subprocess,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(STAGE)
assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2 and relative.parts[0]=='.sync'
stage=root/STAGE;sys.path.insert(0,str(stage/'src'))
from wcomr.runtime_profile40_production_r1 import CONFIG,RUN,CPU_RESULT,validate,validate_authority
from wcomr.runtime_profile40_cpu_acceptance_r1 import PATTERNS,ACCEPTED_STATUS,validate_bundle,validate_proof
from wcomr.frozen_shared_production_r1 import sha,write,fingerprint
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process
config,registration,_old,_inputs,_tables,_previous,bound,_shared=validate(root,stage)
assert all(sha(stage/n)==h for n,h in registration['payload_sha256'].items())
proofpath=stage/CPU_RESULT;proof=json.loads(proofpath.read_text())
bundlepath=stage/'N09-CPU-bundle-result.json'
validate_bundle(json.loads(bundlepath.read_text()),registration['source_revision'],
 registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
 proof_sha256=sha(proofpath),payload_sha256=registration['payload_sha256'])
validate_proof(proof,config,bound,registration,registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG))
cpu=json.loads((stage/'N09-production-CPU-launch.json').read_text())
exit=json.loads((stage/'N09-production-CPU-exit.json').read_text())
assert cpu['source_revision']==registration['source_revision'] and not same_live_process(cpu['identity'])
assert exit['exit_code']==0 and exit['source_revision']==registration['source_revision']
assert exit['registration_sha256']==sha(stage/'registration.json')
assert all(exit['original_CPU_identity'].get(k)==cpu['identity'].get(k) for k in ('pid','start_ticks'))
assert exit['production_CPU_sha256']==sha(proofpath) and exit['bundle_result_sha256']==sha(bundlepath)
accepted=json.loads(CPU_ACCEPTED_TEXT)
accepted_sha=hashlib.sha256(CPU_ACCEPTED_TEXT.encode()).hexdigest()
assert AUTHORITY['independent_CPU_acceptance_sha256']==accepted_sha
expected=dict(status=ACCEPTED_STATUS,CPU_accepted=True,source_revision=registration['source_revision'],
 registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
 production_CPU_sha256=sha(proofpath),production_CPU_bundle_sha256=sha(bundlepath),
 bound_profile_fingerprint=fingerprint(bound),scope_counts=config['scope_counts'],CPU_commands=len(PATTERNS)+1,
 actual_sample_argument_variants=10)
assert all(accepted.get(k)==v for k,v in expected.items())
assert all(accepted['original_CPU_identity'].get(k)==cpu['identity'].get(k) for k in ('pid','start_ticks'))
validate_authority(config,bound,registration,proof,AUTHORITY,revision=AUTHORITY['source_revision'],
 gpu_uuid=AUTHORITY['gpu_uuid'],config_sha256=sha(stage/CONFIG),proof_sha256=sha(proofpath),
 registration_sha256=sha(stage/'registration.json'))
assert not (root/'outputs'/RUN).exists()
delay=config['first_collection_delay_seconds'];half=config.get('midpoint_health_delay_seconds',delay/2)
assert all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (delay,half))
assert delay>=60 and 0<half<delay
gpu=subprocess.check_output(['nvidia-smi','-i',AUTHORITY['gpu_uuid'],
 '--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
 '--format=csv,noheader,nounits'],text=True,timeout=15).strip()
resource_check=dict(observed_unix=time.time(),gpu=gpu,compute_apps=apps,read_only=True,
 final_atomic_admission_is_original_supervisor=True)
if not resource_ready_before_fence(AUTHORITY['gpu_uuid'],gpu,apps):
 print(json.dumps(dict(status='N09_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE',source_revision=AUTHORITY['source_revision'],
  stage=str(stage),run_id=RUN,launch_id=AUTHORITY['launch_id'],gpu_uuid=AUTHORITY['gpu_uuid'],
  resource_check=resource_check,client_orchestrator_source_sha256=CLIENT_SHA,
  GPU_submissions=0,ledger_written=False,dispatch_fence_written=False,
  future_fresh_attempt_requires_new_resource_snapshot=True)));sys.exit(0)
with (stage/'N09-GPU-launch-request.json').open('x') as h:
 json.dump(dict(launch_id=AUTHORITY['launch_id'],source_revision=AUTHORITY['source_revision']),h);h.flush();os.fsync(h.fileno())
authoritypath=stage/'N09-launch-authorization.json';assert not authoritypath.exists();write(authoritypath,AUTHORITY)
acceptedpath=stage/'N09-production-CPU-independent-acceptance.json'
with acceptedpath.open('x') as h:h.write(CPU_ACCEPTED_TEXT);h.flush();os.fsync(h.fileno())
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[sys.executable,str(stage/'scripts/supervise_wc_paper_N09_runtime_profile40_r1.py'),
 '--project',str(root),'--stage',str(stage),'--source-revision',AUTHORITY['source_revision'],'--gpu-uuid',AUTHORITY['gpu_uuid']]
with (stage/'N09-supervisor.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(job.pid)
assert identity['state'] not in (None,'Z','X') and 'supervise_wc_paper_N09_runtime_profile40_r1.py' in identity['command']
now=time.time()
receipt=dict(status='N09_FULL40_DISPATCHED_FRESH_ADMISSION_PENDING',project=str(root),stage=str(stage),run_id=RUN,
 source_revision=AUTHORITY['source_revision'],launch_id=AUTHORITY['launch_id'],gpu_uuid=AUTHORITY['gpu_uuid'],
 scope_counts=config['scope_counts'],config_sha256=sha(stage/CONFIG),registration_sha256=sha(stage/'registration.json'),
 bound_profile_fingerprint=fingerprint(bound),bound_input_fingerprint=AUTHORITY['bound_input_fingerprint'],
 authorization_sha256=sha(authoritypath),production_CPU_sha256=sha(proofpath),
 independent_CPU_acceptance_sha256=sha(acceptedpath),supervisor_pid=job.pid,supervisor_identity=identity,
 post_watcher_pid=None,post_watcher_identity=None,command=command,started_unix=now,
 forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
 midpoint_health_not_before_unix=now+half,next_check_not_before_unix=now+delay,
 resource_check_before_fence=resource_check,client_orchestrator_source_sha256=CLIENT_SHA,
 actual_GPU_admission_accepted_by_dispatch=False,clean_repeated_latency_claim=False)
write(stage/'N09-GPU-launch.json',receipt)
postcommand=[sys.executable,str(stage/'scripts/watch_wc_paper_N09_post_cpu_r1.py'),
 '--project',str(root),'--stage',str(stage),'--supervisor-pid',str(job.pid),'--supervisor-start-ticks',str(identity['start_ticks'])]
try:
 with (stage/'N09-post-watcher.log').open('xb') as log:
  post=subprocess.Popen(postcommand,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 receipt.update(post_watcher_pid=post.pid,post_watcher_identity=process_identity(post.pid),post_command=postcommand)
except BaseException as error:
 receipt.update(post_dispatch_error_type=type(error).__name__,post_dispatch_error=str(error));raise
finally:
 write(stage/'N09-GPU-launch.json',receipt);print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True)
    for name in ('authorization', 'CPU-acceptance', 'output'):parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original whole40 dispatch receipt')
    relative = Path(args.stage)
    if relative.is_absolute() or relative.parts[0] != '.sync' or '..' in relative.parts or len(relative.parts) != 2:
        raise ValueError('Original independent stage must be one .sync child')
    authority = json.loads(args.authorization.read_text()); raw = args.CPU_acceptance.read_bytes()
    if authority.get('independent_CPU_acceptance_sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('Bind the original independent CPU acceptance before dispatch')
    try:
        call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON + ' -c ' + shlex.quote(remote_code(args.stage,authority,raw.decode()))],
            capture_output=True,timeout=180)
    except (subprocess.TimeoutExpired,OSError) as error:
        result = dict(status='N09_GPU_DISPATCH_TRANSPORT_UNKNOWN_ORIGINAL_HANDLE_NO_RETRY',stage=args.stage,
            source_revision=authority['source_revision'],launch_id=authority['launch_id'],gpu_uuid=authority['gpu_uuid'],
            error_type=type(error).__name__,error=str(error),GPU_retry_authorized=False,original_task_terminal=False,
            original_readonly_recovery_refs=[args.stage + '/' + n for n in (
                'N09-GPU-launch-request.json','N09-GPU-launch.json','N09-supervisor-admission-failure.json')])
        with args.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
        raise
    result = dict(transport_exit_code=call.returncode,stderr=call.stderr.decode(errors='replace'),GPU_retry_authorized=False)
    try:result['dispatch'] = json.loads(call.stdout)
    except (ValueError,UnicodeDecodeError):
        result.update(status='N09_GPU_DISPATCH_RESPONSE_UNKNOWN_ORIGINAL_HANDLE_NO_RETRY',stage=args.stage,
            source_revision=authority['source_revision'],launch_id=authority['launch_id'],
            stdout=call.stdout.decode(errors='replace'),original_task_terminal=False,
            original_readonly_recovery_refs=[args.stage + '/N09-GPU-launch.json'])
    with args.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(result))
    raise SystemExit(call.returncode if 'dispatch' in result else (call.returncode or 1))


if __name__ == '__main__':main()
