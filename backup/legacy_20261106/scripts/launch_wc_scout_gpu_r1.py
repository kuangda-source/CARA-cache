#!/usr/bin/env python3
"""One scout launch, bound to its own CPU proof and accepted upstream originals."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
PY = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
REMOTE = r'''
import base64,hashlib,json,math,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
packet=json.loads(sys.stdin.buffer.read());auth=packet['auth'];stage=pathlib.Path(packet['stage'])
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
assert stage.parent==root/'.sync'
os.environ.update(CUDA_VISIBLE_DEVICES='',WC_SCOUT_KIND=auth['kind'],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(stage/'src'))
from wcomr.scout_gpu_lifecycle_r1 import (bound_dependency,accept_cpu,validate_authority,verify_upstream,read,sha,dependency_ref,CPU_PROOF,CPU_LAUNCH,RUNS)
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process,atomic_json,BudgetPool
from wcomr.immutable_stage_payload_r1 import digest
meta,c,reg,*_=bound_dependency(root,stage)
DEPENDENCY=dependency_ref(stage)
assert reg['source_revision']==auth['source_revision'] and sha(stage/'registration.json')==auth['registration_sha256']
texts={k:base64.b64decode(v) for k,v in packet['files'].items()}
for role,key in [('accepted','independent_CPU_acceptance_sha256'),('upstream','upstream_capture_sha256'),('upstream_accepted','upstream_acceptance_sha256')]:
 assert digest(texts[role])==auth[key]
import gzip
cap=json.loads(gzip.decompress(texts['CPU_capture']));accepted=json.loads(texts['accepted'])
calculated=accept_cpu(cap);assert all(accepted.get(k)==v for k,v in calculated.items())
assert accepted['capture_sha256']==digest(texts['CPU_capture'])
assert read(stage/CPU_LAUNCH)==cap['launch'] and not same_live_process(cap['launch']['identity'])
assert sha(stage/CPU_PROOF)==accepted['proof_sha256']
validate_authority(auth,c,sha(stage/'registration.json'),digest(texts['accepted']),sha(stage/CPU_PROOF),sha(stage/DEPENDENCY))
gate=json.loads(texts['gate']) if c['kind']=='BANK24' else None
if gate is not None:assert digest(texts['gate'])==auth['frozen_gate_sha256']
verify_upstream(c['kind'],json.loads(gzip.decompress(texts['upstream'])),json.loads(texts['upstream_accepted']),gate)
assert not (root/'outputs'/RUNS[c['kind']]).exists()
fence=stage/'scout-GPU-dispatch-fence.json';assert not fence.exists()
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('own_scout_supervisor',stage/'scripts/supervise_wc_scout_gpu_r1.py');module=module_from_spec(spec);spec.loader.exec_module(module)
gpu=module.observe(auth['gpu_uuid']);pool=BudgetPool(root).read()
assert pool['cap_gpu_hours']==226 and pool['origin_used_gpu_hours']==79.99637737158223
if gpu['memory_used_mib']>1024 or gpu['pids'] or any(j['status']=='RESERVED_OR_RUNNING' and j['gpu_uuid']==auth['gpu_uuid'] for j in pool['jobs'].values()):
 print(json.dumps(dict(status='SCOUT_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE',GPU_submissions=0,ledger_written=False,gpu=gpu)));sys.exit(0)
assert pool['available_gpu_hours']>=c['billed_limit_GPUh']
with fence.open('x') as f:json.dump(dict(launch_id=auth['launch_id'],source_revision=auth['source_revision'],created_unix=time.time()),f);f.flush();os.fsync(f.fileno())
for role,name in [('accepted','scout-lifecycle-CPU-independent-acceptance.json'),('upstream','scout-upstream-capture.json.gz'),('upstream_accepted','scout-upstream-acceptance.json')]:
 with (stage/name).open('xb') as f:f.write(texts[role]);f.flush();os.fsync(f.fileno())
if gate is not None:
 with (stage/'scout-frozen-CAL-gate.json').open('xb') as f:f.write(texts['gate']);f.flush();os.fsync(f.fileno())
authpath=stage/'scout-GPU-authorization.json';atomic_json(authpath,auth)
command=[sys.executable,str(stage/'scripts/supervise_wc_scout_gpu_r1.py'),'--project',str(root),'--stage',str(stage),'--authorization',str(authpath),'--source-revision',auth['source_revision'],'--gpu-uuid',auth['gpu_uuid']]
env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
identity=process_identity(child.pid);now=time.time()
L=dict(status='SCOUT_COMPLETE_CARD_DISPATCHED_ADMISSION_PENDING',kind=c['kind'],run_id=RUNS[c['kind']],stage=str(stage),project=str(root),
 source_revision=auth['source_revision'],entry_source_revision=meta['entry_source_revision'],entry_stage=meta['entry_stage'],
 entry_registration_sha256=meta['entry_registration_sha256'],registration_sha256=auth['registration_sha256'],
 config_sha256=sha(stage/meta['config_ref']),production_CPU_sha256=sha(stage/CPU_PROOF),dependency_sha256=sha(stage/DEPENDENCY),
 authorization_sha256=sha(authpath),independent_CPU_acceptance_sha256=auth['independent_CPU_acceptance_sha256'],
 launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],scope_counts=c['scope_counts'],forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
 started_unix=now,halfway_check_not_before_unix=now+math.ceil(c['forecast_complete_GPUh']*1800),
 next_check_not_before_unix=now+math.ceil(c['forecast_complete_GPUh']*3600+900),supervisor_pid=child.pid,supervisor_identity=identity,
 post_watcher_identity=None,post_watcher_pid=None,command=command,actual_admission_accepted=False,new_quality_or_speed_result=False)
atomic_json(stage/'scout-GPU-launch.json',L)
try:
 postcommand=[sys.executable,str(stage/'scripts/watch_wc_scout_post_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--supervisor-pid',str(child.pid),'--supervisor-start-ticks',str(identity['start_ticks'])]
 with (stage/'post-watcher.log').open('xb') as log:
  post=subprocess.Popen(postcommand,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
 L.update(post_watcher_pid=post.pid,post_watcher_identity=process_identity(post.pid),post_command=postcommand)
except BaseException as error:L.update(post_dispatch_error_type=type(error).__name__,post_dispatch_error=str(error));raise
finally:atomic_json(stage/'scout-GPU-launch.json',L);print(json.dumps(L))
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('CPU-launch-ref', 'CPU-capture', 'CPU-acceptance', 'upstream-capture', 'upstream-acceptance', 'output'):
        p.add_argument('--'+n, type=Path, required=True)
    p.add_argument('--gpu-uuid', required=True); p.add_argument('--frozen-gate', type=Path)
    a = p.parse_args(); assert not a.output.exists(), 'Original dispatch is never replayed'
    sys.path.insert(0, str(ROOT/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import accept_cpu, verify_upstream, read, sha, validate_authority
    cap = read(a.CPU_capture); accepted = read(a.CPU_acceptance); calculated = accept_cpu(cap)
    assert calculated.get('lifecycle_CPU_accepted') and all(accepted.get(k) == v for k, v in calculated.items()) and accepted['capture_sha256'] == sha(a.CPU_capture)
    assert read(a.CPU_launch_ref)['launch'] == cap['launch']
    dep = cap['files']['dependency']['data']; c = cap['files']['config']['data']; kind = c['kind']
    up = read(a.upstream_capture); upa = read(a.upstream_acceptance)
    assert upa['capture_sha256'] == sha(a.upstream_capture)
    gate = read(a.frozen_gate) if a.frozen_gate else None; verify_upstream(kind, up, upa, gate)
    auth = dict(kind=kind, direct_user_authorization=True, user_reply_quote='Existing user approval: whole cards strictly under12 GPUh execute directly',
        run_id=c['run_id'], source_revision=cap['launch']['source_revision'], launch_id=str(uuid.uuid4()), gpu_uuid=a.gpu_uuid,
        scope_counts=c['scope_counts'], registration_sha256=cap['registration_sha256'],
        config_sha256=cap['files']['config']['sha256'], bound_config_fingerprint=hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest(),
        production_CPU_sha256=accepted['proof_sha256'], independent_CPU_acceptance_sha256=sha(a.CPU_acceptance),
        dependency_sha256=accepted['dependency_sha256'], upstream_originals_verified=True,
        upstream_capture_sha256=sha(a.upstream_capture), upstream_acceptance_sha256=sha(a.upstream_acceptance),
        frozen_gate_sha256=sha(a.frozen_gate) if a.frozen_gate else None, forecast_GPUh=c['forecast_complete_GPUh'],
        billed_limit_GPUh=c['billed_limit_GPUh'], cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223,
        autonomy_exclusive_upper_GPUh=12)
    validate_authority(auth, c, cap['registration_sha256'], sha(a.CPU_acceptance), accepted['proof_sha256'], accepted['dependency_sha256'])
    files = dict(CPU_capture=a.CPU_capture, accepted=a.CPU_acceptance, upstream=a.upstream_capture, upstream_accepted=a.upstream_acceptance)
    if a.frozen_gate: files['gate'] = a.frozen_gate
    packet = dict(auth=auth, stage=cap['launch']['stage'], files={k: base64.b64encode(v.read_bytes()).decode() for k, v in files.items()})
    try:
        call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
            'gkd_minchen', PY+' -c '+shlex.quote(REMOTE)], input=json.dumps(packet).encode(), capture_output=True, timeout=180)
        if call.returncode: raise RuntimeError(call.stderr.decode(errors='replace'))
        dispatch = json.loads(call.stdout); value = dict(dispatch=dispatch, authorization=auth, transport_exit_code=0)
    except (OSError, subprocess.TimeoutExpired, ValueError, RuntimeError) as error:
        value = dict(status='SCOUT_DISPATCH_OBSERVATION_UNKNOWN_NO_REPLAY', source_revision=auth['source_revision'],
            launch_id=auth['launch_id'], stage=packet['stage'], error_type=type(error).__name__, error=str(error),
            original_recovery_ref=packet['stage']+'/scout-GPU-launch.json', no_GPU_relaunch_authority=True)
    with a.output.open('x') as f: json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(value.get('dispatch') or value))


if __name__ == '__main__': main()
