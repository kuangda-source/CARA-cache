#!/usr/bin/env python3
"""Dispatch the CPU-accepted immutable full960 once, after completed N09."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def authority_for(capture,accepted,*,accepted_sha256,gpu_uuid,launch_id,specific=None):
    from wcomr.automatic_quality_production_cpu_r1 import accept
    from wcomr.automatic_quality_production_r1 import validate_authority
    rebuilt=accept(capture)
    if not rebuilt.get('CPU_accepted') or any(accepted.get(k)!=v for k,v in rebuilt.items()):
        raise ValueError('The exact original complete real production CPU acceptance is required')
    c=capture['files']['config']['data'];reg=capture['registration'];p=capture['files']['proof']
    ref=c['references']['accepted_inputs'];raw=(ROOT/ref['ref']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref['sha256']:
        raise ValueError('The complete original scoring input bundle changed')
    inputs=json.loads(gzip.decompress(raw) if ref['ref'].endswith('.gz') else raw)['input_bundle']
    if c['billed_limit_GPUh']>=12:
        if specific is None:raise ValueError('A complete >=12GPUh card needs its specific human approval')
        auth=dict(specific)
    else:
        auth=dict(kind='STANDING_STRICT_UNDER12',direct_user_authorization=True,
            user_reply_quote='批准，以后少于 12gpuh 时的都不用问了，直接启动',
            source_revision=reg['source_revision'],launch_id=launch_id,gpu_uuid=gpu_uuid,
            config_sha256=capture['files']['config']['sha256'],production_CPU_sha256=p['sha256'],
            bound_input_fingerprint=c['input_bundle_fingerprint'],scope_counts=c['scope_counts'],
            whole_card_run=c['run_id'],forecast_complete_GPUh=c['forecast_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
            cumulative_cap_GPUh=c['cumulative_cap_GPUh'],budget_origin_used_GPUh=c['budget_origin_used_GPUh'])
    auth['independent_CPU_acceptance_sha256']=accepted_sha256
    validate_authority(c,reg,inputs,p['data'],auth,revision=reg['source_revision'],gpu_uuid=gpu_uuid,
        config_sha256=capture['files']['config']['sha256'],registration_sha256=capture['registration_sha256'],
        proof_sha256=p['sha256'],worker_sha256=reg['payload_sha256']['scripts/score_wc_paper_N10_full960_r1.py'])
    return auth


def prior_N09(capture,accepted,capture_sha256):
    runs=capture.get('runner',{}).get('runs',[])
    if (accepted.get('capture_sha256')!=capture_sha256
            or accepted.get('terminal_receipt_audit_accepted') is not True
            or accepted.get('original_finance_status')!='ORIGINAL_ACTUAL_BILL_AND_ADDITIVE_SETTLEMENT_MATCH'
            or accepted.get('own_GPU_finance_released') is not True
            or accepted.get('original_CPU_post_exit_code')!=0
            or accepted.get('original_runner_paths')!=40 or accepted.get('registered_total_paths')!=40
            or len(runs)!=40 or any(r.get('status') not in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED') for r in runs)
            or capture.get('supervisor',{}).get('child_exit_code')!=0):
        raise ValueError('Finish and audit original whole40 N09 first; legitimate refusals remain visible')
    return dict(run_id=capture['launch']['run_id'],source_revision=capture['launch']['source_revision'],
        billing_sha256=capture['billing_sha256'],actual_GPUh=accepted['actual_GPUh'],capture_sha256=capture_sha256)


REMOTE=r'''
import hashlib,json,math,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
M=json.loads(sys.stdin.buffer.read());root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
relative=pathlib.PurePosixPath(M['stage']);assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==2 and relative.parts[0]=='.sync'
stage=root/M['stage'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==M['CPU_capture']['registration_sha256']
sys.path.insert(0,str(stage/'src'))
from wcomr.automatic_quality_production_r1 import CONFIG,load,read,validate_authority
from wcomr.automatic_quality_production_cpu_r1 import accept
from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json,process_identity,same_live_process
c,reg,bundle,*_=load(stage);saved=json.loads(M['accepted_text']);computed=accept(M['CPU_capture'])
assert computed['CPU_accepted'] and all(saved.get(k)==v for k,v in computed.items())
assert M['CPU_capture']['registration']==reg
assert sha(stage/'CPU-scoring-entry-result.json')==saved['production_CPU_sha256']
assert sha(stage/'N10-production-CPU-bundle-result.json')==saved['bundle_sha256']
assert sha(stage/CONFIG)==saved['config_sha256']
cpu=read(stage/'N10-production-CPU-launch.json');exit=read(stage/'N10-production-CPU-exit.json')
assert not same_live_process(cpu['identity']) and all(cpu['identity'][k]==saved['original_CPU_identity'][k] for k in ('pid','start_ticks'))
assert exit['exit_code']==0 and exit['source_revision']==reg['source_revision'] and exit['bundle_sha256']==saved['bundle_sha256']
auth=M['authority'];assert hashlib.sha256(M['accepted_text'].encode()).hexdigest()==auth['independent_CPU_acceptance_sha256']
validate_authority(c,reg,bundle,read(stage/'CPU-scoring-entry-result.json'),auth,revision=reg['source_revision'],gpu_uuid=auth['gpu_uuid'],
 config_sha256=sha(stage/CONFIG),registration_sha256=sha(stage/'registration.json'),proof_sha256=sha(stage/'CPU-scoring-entry-result.json'),
 worker_sha256=sha(stage/'scripts/score_wc_paper_N10_full960_r1.py'))
pool=BudgetPool(root).read();prior=M['prior_N09'];job=pool['jobs'][prior['run_id']]
assert job['status']=='SETTLED' and all(job[k]==prior[k] for k in ('source_revision','billing_sha256','actual_GPUh'))
assert not any(j['status']=='RESERVED_OR_RUNNING' for j in pool['jobs'].values())
assert not (root/'outputs'/c['run_id']).exists() and not (stage/'N10-GPU-dispatch-fence.json').exists()
gpu=subprocess.check_output(['nvidia-smi','-i',auth['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
parts=[p.strip() for p in gpu.split(',')]
if int(parts[2])>1024 or any(x.split(',')[0].strip()==auth['gpu_uuid'] for x in apps.splitlines()):
 print(json.dumps(dict(status='N10_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE',GPU_submissions=0,ledger_written=False,gpu=gpu,compute_apps=apps)));sys.exit(0)
assert parts[0]==auth['gpu_uuid'] and 'A6000' in parts[1] and parts[3]=='8.6'
with (stage/'N10-GPU-dispatch-fence.json').open('x') as h:json.dump(dict(launch_id=auth['launch_id'],source_revision=reg['source_revision'],created_unix=time.time()),h);h.flush();os.fsync(h.fileno())
with (stage/'N10-launch-authorization.json').open('x') as h:json.dump(auth,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
with (stage/'N10-production-CPU-independent-acceptance.json').open('x') as h:h.write(M['accepted_text']);h.flush();os.fsync(h.fileno())
command=[sys.executable,str(stage/'scripts/supervise_wc_paper_N10_full960_r1.py'),'--project',str(root),'--stage',str(stage),
 '--source-revision',reg['source_revision'],'--gpu-uuid',auth['gpu_uuid']]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'N10-supervisor.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
identity=process_identity(child.pid);now=time.time()
receipt=dict(status='N10_FULL960_DISPATCHED_ADMISSION_PENDING',project=str(root),stage=str(stage),run_id=c['run_id'],
 source_revision=reg['source_revision'],launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],scope_counts=c['scope_counts'],
 config_sha256=sha(stage/CONFIG),registration_sha256=sha(stage/'registration.json'),production_CPU_sha256=saved['production_CPU_sha256'],
 independent_CPU_acceptance_sha256=sha(stage/'N10-production-CPU-independent-acceptance.json'),authorization_sha256=sha(stage/'N10-launch-authorization.json'),
 bound_input_fingerprint=c['input_bundle_fingerprint'],supervisor_pid=child.pid,supervisor_identity=identity,command=command,
 started_unix=now,forecast_GPUh=c['forecast_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
 midpoint_health_not_before_unix=now+math.ceil(c['forecast_GPUh']*1800),next_check_not_before_unix=now+math.ceil(c['forecast_GPUh']*3600+900),
 prior_N09=prior,orchestrator_source_sha256=M['orchestrator_source_sha256'],actual_GPU_admission_accepted_by_dispatch=False,new_quality_result=False)
atomic_json(stage/'N10-GPU-launch.json',receipt);print(json.dumps(receipt,allow_nan=False))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('CPU-launch-ref','CPU-capture','CPU-acceptance','prior-N09-capture','prior-N09-acceptance','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--gpu-uuid',required=True);p.add_argument('--specific-authorization',type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve the original dispatch; never replay an unknown launch')
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.immutable_stage_payload_r1 import registered_base_reference
    raw=a.CPU_capture.read_bytes();cap=json.loads(gzip.decompress(raw));old=json.loads(a.CPU_launch_ref.read_text())['launch']
    text=a.CPU_acceptance.read_text();accepted=json.loads(text)
    if cap['launch']!=old or accepted['capture_sha256']!=hashlib.sha256(raw).hexdigest():
        raise ValueError('The original actual production CPU capture and its file hash must agree')
    before=a.prior_N09_capture.read_bytes();previous=json.loads(gzip.decompress(before))
    prior=prior_N09(previous,json.loads(a.prior_N09_acceptance.read_text()),hashlib.sha256(before).hexdigest())
    specific=json.loads(a.specific_authorization.read_text()) if a.specific_authorization else None
    launch_id=specific['launch_id'] if specific else str(uuid.uuid4())
    auth=authority_for(cap,accepted,accepted_sha256=hashlib.sha256(text.encode()).hexdigest(),gpu_uuid=a.gpu_uuid,launch_id=launch_id,specific=specific)
    stage=registered_base_reference(cap['registration']['stage'],old['stage'])['project_relative']
    meta=dict(stage=stage,authority=auth,CPU_capture=cap,accepted_text=text,prior_N09=prior,
        orchestrator_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PYTHON+' -c '+shlex.quote(REMOTE)],input=json.dumps(meta,ensure_ascii=False,allow_nan=False).encode(),capture_output=True,timeout=180)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        dispatch=json.loads(call.stdout)
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        result=dict(status='N10_DISPATCH_OBSERVATION_UNKNOWN_NO_REPLAY',stage=stage,source_revision=auth['source_revision'],
            launch_id=launch_id,error_type=type(e).__name__,error=str(e),original_task_terminal=False,
            original_recovery_ref=stage+'/N10-GPU-launch.json',authorization=auth)
        with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
        raise
    result=dict(dispatch=dispatch,authorization=auth,CPU_capture_ref=str(a.CPU_capture),
        CPU_capture_sha256=hashlib.sha256(raw).hexdigest(),CPU_acceptance_ref=str(a.CPU_acceptance),
        CPU_acceptance_sha256=hashlib.sha256(text.encode()).hexdigest(),dispatcher_source_sha256=meta['orchestrator_source_sha256'])
    with a.output.open('x') as h:json.dump(result,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(dispatch))


if __name__=='__main__':main()
