#!/usr/bin/env python3
"""Single dispatch of an already frozen, CPU-accepted whole40 authority."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def remote_code(stage, authority):
    return 'STAGE=' + repr(stage) + '\nAUTHORITY=' + repr(authority) + '\n' + r'''
import json,math,os,pathlib,subprocess,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(STAGE)
assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0]=='.sync'
stage=root/STAGE;sys.path.insert(0,str(stage/'src'))
from wcomr.balanced_repeat_production_r1 import CONFIG,RUN,CPU_RESULT,validate,validate_launch_authority
from wcomr.balanced_repeat_cpu_acceptance_r1 import validate_bundle,validate_proof
from wcomr.frozen_shared_production_r1 import sha,write
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process
config,registration,_old,_inputs,_tables,_previous,bound,_shared=validate(root,stage)
proofpath=stage/CPU_RESULT;proof=json.loads(proofpath.read_text())
validate_bundle(json.loads((stage/'N08-CPU-bundle-result.json').read_text()),registration['source_revision'])
validate_proof(proof,config,bound,registration,registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG))
cpu=json.loads((stage/'N08-CPU-launch.json').read_text())
assert cpu['source_revision']==registration['source_revision'] and not same_live_process(cpu['identity'])
assert all(sha(stage/n)==h for n,h in registration['payload_sha256'].items())
validate_launch_authority(config,bound,registration,proof,AUTHORITY,
 revision=AUTHORITY['source_revision'],gpu_uuid=AUTHORITY['gpu_uuid'],
 config_sha256=sha(stage/CONFIG),proof_sha256=sha(proofpath),registration_sha256=sha(stage/'registration.json'))
assert not (root/'outputs'/RUN).exists()
delay=config['first_collection_delay_seconds']
assert isinstance(delay,(int,float)) and not isinstance(delay,bool) and math.isfinite(delay) and delay>=60
fence=stage/'N08-GPU-launch-request.json'
with fence.open('x') as handle:json.dump(dict(launch_id=AUTHORITY['launch_id'],source_revision=AUTHORITY['source_revision']),handle)
authoritypath=stage/'N08-launch-authorization.json'
assert not authoritypath.exists();write(authoritypath,AUTHORITY)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[sys.executable,str(stage/'scripts/supervise_wc_paper_N08_balanced_full40_r1.py'),
 '--project',str(root),'--stage',str(stage),'--source-revision',AUTHORITY['source_revision'],
 '--gpu-uuid',AUTHORITY['gpu_uuid'],'--authorization',str(authoritypath)]
with (stage/'N08-supervisor.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(job.pid)
assert identity['state'] not in (None,'Z','X') and 'supervise_wc_paper_N08_balanced_full40_r1.py' in identity['command']
now=time.time()
receipt=dict(status='N08_FULL40_DISPATCHED_FRESH_ADMISSION_PENDING',stage=str(stage),project=str(root),
 run_id=RUN,source_revision=AUTHORITY['source_revision'],launch_id=AUTHORITY['launch_id'],gpu_uuid=AUTHORITY['gpu_uuid'],
 scope_counts=config['scope_counts'],config_sha256=sha(stage/CONFIG),registration_sha256=sha(stage/'registration.json'),
 bound_timing_fingerprint=AUTHORITY['bound_timing_fingerprint'],bound_input_fingerprint=AUTHORITY['bound_input_fingerprint'],
 authorization_sha256=sha(authoritypath),production_CPU_sha256=sha(proofpath),
 supervisor_pid=job.pid,supervisor_identity=identity,post_watcher_pid=None,post_watcher_identity=None,
 command=command,started_unix=now,forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
 next_check_not_before_unix=now+delay,midpoint_health_not_before_unix=now+delay/2)
write(stage/'N08-GPU-launch.json',receipt)
postcommand=[sys.executable,str(stage/'scripts/watch_wc_paper_N08_post_cpu_r1.py'),
 '--project',str(root),'--stage',str(stage),'--supervisor-pid',str(job.pid),'--supervisor-start-ticks',str(identity['start_ticks'])]
try:
 with (stage/'N08-post-watcher.log').open('xb') as log:
  post=subprocess.Popen(postcommand,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 receipt.update(post_watcher_pid=post.pid,post_watcher_identity=process_identity(post.pid),post_command=postcommand)
except BaseException as error:
 receipt.update(post_dispatch_error_type=type(error).__name__,post_dispatch_error=str(error));raise
finally:
 write(stage/'N08-GPU-launch.json',receipt);print(json.dumps(receipt,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True)
    parser.add_argument('--authorization', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    authority = json.loads(args.authorization.read_text()); relative = Path(args.stage)
    assert not relative.is_absolute() and relative.parts[0] == '.sync' and '..' not in relative.parts
    try:
        call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
            'gkd_minchen', PYTHON + ' -c ' + shlex.quote(remote_code(args.stage, authority))], capture_output=True, timeout=180)
    except (subprocess.TimeoutExpired, OSError) as error:
        value = dict(status='N08_DISPATCH_TRANSPORT_UNKNOWN_READ_ORIGINAL_STAGE_NO_RETRY', stage=args.stage,
            source_revision=authority['source_revision'], launch_id=authority['launch_id'], gpu_uuid=authority['gpu_uuid'],
            error_type=type(error).__name__, error=str(error), GPU_retry_authorized=False, original_task_terminal=False,
            original_readonly_recovery_refs=[args.stage + '/' + n for n in (
                'N08-GPU-launch-request.json', 'N08-GPU-launch.json', 'N08-supervisor-admission-failure.json')])
        args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n'); print(json.dumps(value)); raise
    value = dict(transport_exit_code=call.returncode, stderr=call.stderr.decode(errors='replace'), GPU_retry_authorized=False)
    try: value['dispatch'] = json.loads(call.stdout)
    except (json.JSONDecodeError, UnicodeDecodeError):
        value.update(status='N08_DISPATCH_RESPONSE_UNKNOWN_READ_ORIGINAL_STAGE_NO_RETRY',
            stage=args.stage, launch_id=authority['launch_id'], source_revision=authority['source_revision'],
            stdout=call.stdout.decode(errors='replace'), original_task_terminal=False)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n'); print(json.dumps(value))
    raise SystemExit(call.returncode if 'dispatch' in value else (call.returncode or 1))


if __name__ == '__main__': main()
