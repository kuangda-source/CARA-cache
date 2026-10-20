#!/usr/bin/env python3
"""Immutable CPU and once-only full interval-assets GPU lifecycle."""
import argparse
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
REMOTE_PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
REMOTE_ROOT='/home/gaokuangda/data/gkd/worldcache_omr'


def own_imports(stage):
    os.environ['WC_SCOUT_KIND']='CAL12';stage=Path(stage)
    sys.path.insert(0,str(stage/'src'))
    if stage.parent.name=='.sync':
        runtime=stage.parent.parent/'runtime'
        sys.path[1:1]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    from wcomr import policy_interval_assets_r1 as A
    return A


def dump(path,value):
    path=Path(path)
    with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')


def ssh(code,packet=None,timeout=120):
    return subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen',REMOTE_PY+' -c '+shlex.quote(code)],input=packet,capture_output=True,timeout=timeout)


def prepare(a):
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr import policy_interval_assets_r1 as A
    oldref='manifests/wc_drop1_window24_real_N09_whole_cost_r1_20261018.json'
    old=A.read(ROOT/oldref);source='configs/wc_scout_cal12_production_entry_r1_20261018.json'
    original=A.read(ROOT/source)
    quote=A.complete_quote(max_whole_request_seconds=old['positions'][0]['observed_old_whole_request_max_seconds'],
        load_seconds=old['original_load_seconds'],readout_inclusive_planning_seconds=old['per_extra_A_planning_proxy_seconds'],
        latent_elements=1990656,hidden_elements=63700992,prior_unattributed_seconds=old['original_unattributed_seconds'])
    quote['historical_planning_evidence']=dict(ref=oldref,sha256=A.sha(ROOT/oldref),
        interpretation='INCLUSIVE_PLANNING_ALLOWANCE_NOT_INDEPENDENT_ACTION_PRICE')
    quote_ref='manifests/wc_policy_interval_assets_full1624_whole_quote_r1_20261020.json'
    dump(ROOT/quote_ref,quote)
    c=dict(version=A.VERSION,run_id=A.RUN,profile=A.PROFILE,scope_counts=A.COUNTS,matrix=A.matrix(),
        requests=original['requests'],label_basis='TEACHER_CONDITIONED_PROPOSAL',
        guardrails_enabled=True,cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
        autonomy_exclusive_upper_GPUh=12,forecast_complete_GPUh=quote['forecast_complete_GPUh'],
        billed_limit_GPUh=quote['billed_limit_GPUh'],training=False,F_B_enabled=False,P_enabled=False,
        endpoint_selection=False,new_generated_policy=False,clean_speed_claim=False,
        references={'quote':dict(ref=quote_ref,sha256=A.sha(ROOT/quote_ref)),
            'original_CAL4_entry':dict(ref=source,sha256=A.sha(ROOT/source))})
    A.validate_contract(c);dump(ROOT/A.CONFIG,c)
    dump(a.output,dict(status='COMPLETE_INTERVAL1624_CARD_PREPARED_NOT_PRODUCTION_CPU',config_ref=A.CONFIG,
        config_sha256=A.sha(ROOT/A.CONFIG),quote_ref=quote_ref,quote_sha256=A.sha(ROOT/quote_ref),
        forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],
        GPU_submissions=0,production_CPU_accepted=False))
    print(json.dumps(quote,ensure_ascii=False))


def deploy_cpu(a):
    A=own_imports(ROOT)
    from wcomr.immutable_stage_payload_r1 import plan,git_archive
    base_ref=ROOT/'reports/wc_scout_CAL12_GPU_lifecycle_CPU_R2_collection_20261019.json.gz'
    base=A.read(base_ref);reg=base['registration']
    points=['scripts/wc_policy_interval_assets_lifecycle_r1.py','scripts/run_wc_policy_interval_assets_r1.py',
        'scripts/check_wc_policy_interval_assets_cpu_r1.py','scripts/postprocess_wc_policy_interval_assets_r1.py']
    extra=['tests/test_policy_interval_assets_r1.py','tests/check_policy_interval_assets_sampling_cpu_r1.py']
    packet=plan(ROOT,config_roots=[A.CONFIG],python_entrypoints=points,extra_files=extra,
        base_registration_sha256=base['registration_sha256'],base_source_revision=reg['source_revision'],numeric_sources={})
    changed=[n for n,h in packet['overlay_sha256'].items() if n in reg['payload_sha256'] and reg['payload_sha256'][n]!=h]
    if changed:raise ValueError('Unchanged accepted execution dependency changed: '+str(changed))
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=git_archive(ROOT,packet,revision)
    stage=Path(a.stage)
    assert not stage.is_absolute() and len(stage.parts)==2 and stage.parts[0]=='.sync'
    M=dict(root=REMOTE_ROOT,stage=str(stage),base=reg['stage'],base_sha=base['registration_sha256'],
        revision=revision,packet=packet)
    code='M='+repr(M)+'\n'+r'''
import hashlib,json,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path(M['root']).resolve();base=pathlib.Path(M['base']);stage=root/M['stage']
assert not stage.exists() and base.parent==stage.parent
raw=(base/'registration.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==M['base_sha']
reg=json.loads(raw);sys.path.insert(0,str(base/'src'))
from wcomr.immutable_stage_payload_r1 import overlay_bytes
from wcomr.gpu_budget_pool_v2 import process_identity
extra=overlay_bytes(sys.stdin.buffer.read(),M['packet'])
stage.mkdir()
for n,h in reg['payload_sha256'].items():
 data=(base/n).read_bytes();assert hashlib.sha256(data).hexdigest()==h
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for n,data in extra.items():
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
reg.update(source_revision=M['revision'],stage=str(stage),read_only_base_stage=str(base),
 read_only_base_registration_sha256=M['base_sha'],CPU_scope='POLICY_INTERVAL_ASSETS_FULL1624_NEW_SCOPE')
reg['payload_sha256'].update(M['packet']['overlay_sha256'])
raw=(json.dumps(reg,indent=2)+'\n').encode();(stage/'registration.json').write_bytes(raw)
command=[sys.executable,str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'),'cpu-worker','--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',WC_SCOUT_KIND='CAL12',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
 WC_POLICY_ASSETS_RUNTIME=str(root/'runtime'))
with (stage/'policy-assets-CPU.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
now=time.time();identity=process_identity(child.pid);assert identity and identity['pid']==child.pid
value=dict(status='POLICY_ASSETS_CPU_SINGLE_DISPATCHED',project=str(root),stage=str(stage),source_revision=M['revision'],
 registration_sha256=hashlib.sha256(raw).hexdigest(),payload_files=len(reg['payload_sha256']),identity=identity,
 command=command,started_unix=now,halfway_not_before_unix=now+450,final_not_before_unix=now+1080,
 GPU_submissions=0,ledger_written=False)
(stage/'policy-assets-CPU-launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    try:
        result=ssh(code,archive,180)
        value=dict(status='POLICY_ASSETS_CPU_DISPATCH_RESPONSE',exit_code=result.returncode,
            launch=json.loads(result.stdout) if result.returncode==0 else None,stderr=result.stderr.decode(),
            stage=str(stage),source_revision=revision,GPU_submissions=0)
    except Exception as e:value=dict(status='POLICY_ASSETS_CPU_DISPATCH_UNKNOWN_NO_REPLAY',stage=str(stage),
        source_revision=revision,error_type=type(e).__name__,error=str(e),GPU_submissions=0,
        recovery_ref=str(stage)+'/policy-assets-CPU-launch.json')
    dump(a.output,value);print(json.dumps(value.get('launch') or value))


def cpu_worker(a):
    A=own_imports(a.stage)
    from wcomr.gpu_budget_pool_v2 import atomic_json
    reg=A.read(a.stage/'registration.json')
    assert all(A.sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    commands=[[sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p','test_policy_interval_assets_r1.py','-v']]
    commands += [[sys.executable,str(a.stage/'scripts/check_wc_policy_interval_assets_cpu_r1.py'),
        '--mode',mode,'--project',str(a.project),'--stage',str(a.stage),'--output',str(a.stage/name)]
        for mode,name in [('numerical','policy-assets-numerical-CPU.json'),('production',A.CPU_PROOF)]]
    value=dict(status='POLICY_ASSETS_CPU_RUNNING',source_revision=reg['source_revision'],commands=[],
        CUDA_initialized=False,GPU_submissions=0,ledger_written=False,started_unix=time.time())
    try:
        for command in commands:
            call=subprocess.run(command,cwd=a.project/'runtime',env=dict(os.environ,PYTHONPATH=str(a.stage/'src')))
            value['commands'].append(dict(command=command,exit_code=call.returncode))
            if call.returncode:raise RuntimeError('New full-scope CPU command failed')
        value.update(status='POLICY_ASSETS_FULL_PRODUCTION_CPU_PASS',exit_code=0,
            proof_sha256=A.sha(a.stage/A.CPU_PROOF),numerical_sha256=A.sha(a.stage/'policy-assets-numerical-CPU.json'))
    except BaseException as e:
        value.update(status='POLICY_ASSETS_CPU_FAILURE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e));raise
    finally:
        value['CPU_wall_seconds']=time.time()-value['started_unix'];atomic_json(a.stage/A.CPU_BUNDLE,value)


def launch_gpu(a):
    A=own_imports(ROOT)
    from wcomr.policy_interval_assets_lifecycle_r1 import accept_cpu
    from wcomr.policy_interval_assets_production_r1 import require_BANK24
    cpu=A.read(a.CPU_capture);accepted=A.read(a.CPU_acceptance);recomputed=accept_cpu(cpu)
    assert all(accepted.get(k)==v for k,v in recomputed.items()) and accepted['production_CPU_accepted']
    assert accepted['capture_sha256']==A.sha(a.CPU_capture)
    L=A.read(a.CPU_launch_ref)['launch'];assert cpu['launch']==L
    c=cpu['files']['config']['data'];reg=cpu['registration']
    upstream=A.read(a.upstream_capture);upa=A.read(a.upstream_acceptance);require_BANK24(upstream,upa)
    assert upa['capture_sha256']==A.sha(a.upstream_capture)
    approval=A.read(a.specific_approval) if a.specific_approval else None
    if c['billed_limit_GPUh']>=12:
        assert approval and approval.get('approved') is True and approval.get('direct_human_quote')
        assert approval['config_sha256']==accepted['config_sha256'] and approval['billed_limit_GPUh']==c['billed_limit_GPUh']
    launch_id=str(uuid.uuid4())
    auth=dict(kind='SPECIFIC_WHOLE_CARD_APPROVAL' if approval else 'STANDING_STRICT_UNDER12',
        run_id=A.RUN,whole_card_run=A.RUN,launch_id=launch_id,gpu_uuid=a.gpu_uuid,
        source_revision=L['source_revision'],config_sha256=accepted['config_sha256'],
        registration_sha256=L['registration_sha256'],production_CPU_sha256=accepted['proof_sha256'],
        independent_CPU_acceptance_sha256=None,scope_counts=A.COUNTS,
        bound_input_fingerprint=hashlib.sha256(json.dumps(c['requests'],sort_keys=True).encode()).hexdigest(),
        forecast_GPUh=c['forecast_complete_GPUh'],forecast_complete_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
        cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,direct_user_authorization=True,
        specific_whole_card_approved=bool(approval),user_reply_quote=approval['direct_human_quote'] if approval else
        '生产CPU验证通过后直接推进，预算和少于12 GPUh不用确认的规则不变',
        upstream_capture_sha256=A.sha(a.upstream_capture),upstream_acceptance_sha256=A.sha(a.upstream_acceptance))
    # The accepted CPU bytes are frozen into the authority before any mutation.
    accepted_raw=json.dumps(accepted,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    auth['independent_CPU_acceptance_sha256']=hashlib.sha256(accepted_raw.encode()).hexdigest()
    meta=dict(project=L['project'],stage=L['stage'],regsha=L['registration_sha256'],auth=auth,
        accepted_raw=accepted_raw,upstream_capture=str(a.upstream_capture),upstream_accepted=str(a.upstream_acceptance))
    # Upstream is reverified locally from complete originals; only its SHA and
    # identity receipt are transported, never a new source or changed stage.
    code='M='+repr(meta)+'\n'+r'''
import hashlib,json,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path(M['project']);stage=pathlib.Path(M['stage']);sys.path.insert(0,str(stage/'src'))
from wcomr.policy_interval_assets_r1 import CONFIG,RUN,CPU_PROOF,read,sha
from wcomr.policy_interval_assets_lifecycle_r1 import validate_authority
from wcomr.gpu_budget_pool_v2 import process_identity,BudgetPool
assert sha(stage/'registration.json')==M['regsha']
c=read(stage/CONFIG);auth=M['auth']
validate_authority(auth,c,M['regsha'],sha(stage/CPU_PROOF),hashlib.sha256(M['accepted_raw'].encode()).hexdigest())
fence=stage/'policy-assets-GPU-dispatch-fence.json'
assert not fence.exists() and not (stage/'policy-assets-GPU-launch.json').exists() and not (root/'outputs'/RUN).exists()
gpu=subprocess.check_output(['nvidia-smi','-i',auth['gpu_uuid'],'--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True,timeout=12)
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=12)
busy=int(gpu.split(',')[1])>1024 or any(s.split(',')[0].strip()==auth['gpu_uuid'] for s in apps.splitlines() if s.strip())
pool=BudgetPool(root).read();assert pool['cap_gpu_hours']==226 and pool['origin_used_gpu_hours']==79.99637737158223
if busy:
 print(json.dumps(dict(status='POLICY_ASSETS_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE',GPU_submissions=0,ledger_written=False,observed_unix=time.time())));raise SystemExit(0)
assert pool['available_gpu_hours']>=auth['billed_limit_GPUh']
quote=read(stage/c['references']['quote']['ref']);fs=os.statvfs(root)
assert fs.f_bavail*fs.f_frsize>=quote['minimum_free_disk_bytes']
mem={line.split(':')[0]:int(line.split()[1])*1024 for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if ':' in line and line.split()[1].isdigit()}
assert mem['MemAvailable']>=quote['peak_CPU_anchor_bank_planning_bytes']*1.3+4*1024**3
with fence.open('x') as f:json.dump(dict(status='ORIGINAL_ONCE_ONLY_NO_REPLAY',launch_id=auth['launch_id'],source_revision=auth['source_revision']),f)
(stage/'policy-assets-independent-CPU-acceptance.json').write_text(M['accepted_raw'])
authorization=stage/'policy-assets-GPU-authorization.json';authorization.write_text(json.dumps(auth,indent=2,ensure_ascii=False)+'\n')
command=[sys.executable,str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'),'supervise','--project',str(root),'--stage',str(stage),'--authorization',str(authorization)]
with (stage/'policy-assets-supervisor.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',WC_SCOUT_KIND='CAL12',PYTHONDONTWRITEBYTECODE='1'))
now=time.time();identity=process_identity(child.pid);assert identity and identity['pid']==child.pid
value=dict(status='POLICY_ASSETS_GPU_SINGLE_DISPATCHED_PENDING_ATOMIC_ADMISSION',project=str(root),stage=str(stage),
 source_revision=auth['source_revision'],registration_sha256=M['regsha'],config_sha256=sha(stage/CONFIG),
 production_CPU_sha256=sha(stage/CPU_PROOF),authorization_sha256=sha(authorization),
 run_id=RUN,launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],scope_counts=c['scope_counts'],
 supervisor_pid=child.pid,supervisor_identity=identity,started_unix=now,
 halfway_check_not_before_unix=now+c['forecast_complete_GPUh']*1800,
 next_check_not_before_unix=now+c['forecast_complete_GPUh']*3600+900)
(stage/'policy-assets-GPU-launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    try:
        result=ssh(code,timeout=120)
        value=dict(status='POLICY_ASSETS_GPU_LAUNCH_RESPONSE',exit_code=result.returncode,
            launch=json.loads(result.stdout) if result.returncode==0 else None,stderr=result.stderr.decode(),original_stage=L['stage'])
    except Exception as e:value=dict(status='POLICY_ASSETS_GPU_DISPATCH_UNKNOWN_NO_REPLAY',original_stage=L['stage'],
        error_type=type(e).__name__,error=str(e),recovery_ref=L['stage']+'/policy-assets-GPU-launch.json')
    dump(a.output,value);print(json.dumps(value.get('launch') or value))


def observe(uuid_value):
    values=subprocess.check_output(['nvidia-smi','-i',uuid_value,'--query-gpu=uuid,name,memory.used,compute_cap',
        '--format=csv,noheader,nounits'],text=True,timeout=12).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=12)
    return dict(unix=time.time(),uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),
        compute_cap=values[3].strip(),pids=[int(r.split(',')[1]) for r in apps.splitlines() if r.split(',')[0].strip()==uuid_value])


def stop(child):
    if child is None or child.poll() is not None:return
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()


def supervise(a):
    A=own_imports(a.stage)
    from wcomr.policy_interval_assets_lifecycle_r1 import validate_authority
    from wcomr.policy_interval_assets_production_r1 import validate
    from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
    from wcomr.gpu_budget_pool_v2 import DeviceLease,process_identity,atomic_json
    os.environ['CUDA_VISIBLE_DEVICES']=''
    c,reg,*_=validate(a.project,a.stage);auth=A.read(a.authorization)
    accepted_path=a.stage/'policy-assets-independent-CPU-acceptance.json'
    validate_authority(auth,c,A.sha(a.stage/'registration.json'),A.sha(a.stage/A.CPU_PROOF),A.sha(accepted_path))
    out=a.project/'outputs'/A.RUN;pool=ApprovedCardBudgetPool(a.project);lease=DeviceLease(a.project,auth['gpu_uuid'])
    child=None;reserved=False;state=None;start=None
    try:
        lease.acquire();assert not out.exists()
        gpu=observe(auth['gpu_uuid']);ident=process_identity(os.getpid());before=pool.read()
        job=dict(job_id=A.RUN,run_id=A.RUN,launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],
            source_revision=reg['source_revision'],config_sha256=A.sha(a.stage/A.CONFIG),registration_sha256=A.sha(a.stage/'registration.json'),
            production_CPU_sha256=A.sha(a.stage/A.CPU_PROOF),authorization_sha256=A.sha(a.authorization),
            bound_input_fingerprint=auth['bound_input_fingerprint'],scope_counts=A.COUNTS,
            cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
            forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
            supervisor_pid=os.getpid(),supervisor_start_ticks=ident['start_ticks'],stage=str(a.stage))
        after=pool.reserve(job,gpu) if c['billed_limit_GPUh']<12 else pool.reserve_specific_whole_card(job,gpu,a.authorization)
        reserved=True;start=time.monotonic();out.mkdir(parents=True)
        state=dict(status='POLICY_ASSETS_GPU_RUNNING',supervisor_identity=ident,source_revision=reg['source_revision'],
            run_id=A.RUN,launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],scope_counts=A.COUNTS,
            config_sha256=job['config_sha256'],started_unix=time.time(),pool_before=before,pool_after_reservation=after)
        atomic_json(out/'supervisor.json',state)
        def interrupted(signum,frame):raise KeyboardInterrupt('Own assets supervisor interrupted')
        signal.signal(signal.SIGTERM,interrupted)
        command=[sys.executable,'-u',str(a.stage/'scripts/run_wc_policy_interval_assets_r1.py'),'--project',str(a.project),
            '--stage',str(a.stage),'--source-revision',reg['source_revision'],'--gpu-uuid',auth['gpu_uuid']]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=auth['gpu_uuid'],WC_LOCK_FD=str(lease.handle.fileno()),
            WC_SUPERVISOR_PID=str(os.getpid()),WC_SCOUT_KIND='CAL12',PYTHONPATH=str(a.stage/'src'),
            OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        with (out/'GPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime',
                env=env,pass_fds=(lease.handle.fileno(),),start_new_session=True)
            state.update(child_pid=child.pid,child_identity=process_identity(child.pid),command=command);atomic_json(out/'supervisor.json',state)
            while child.poll() is None:
                if time.monotonic()-start>=c['billed_limit_GPUh']*3600-30:
                    state['own_billed_limit_stop']=True;stop(child);break
                time.sleep(10)
            state['child_exit_code']=child.wait()
    except BaseException as e:
        if state is not None:state.update(error_type=type(e).__name__,error=str(e))
        else:atomic_json(a.stage/'policy-assets-admission-failure.json',dict(status='NO_GPU_CHILD_ADMISSION_FAILED_RETAINED',
            error_type=type(e).__name__,error=str(e),GPU_child_started=False,actual_GPUh=0))
        raise
    finally:
        try:
            stop(child)
            if reserved:
                wall=time.monotonic()-start
                bill=dict(status='POLICY_ASSETS_ACTUAL_FULL_GPU_WALL_BILL',run_id=A.RUN,launch_id=auth['launch_id'],
                    source_revision=reg['source_revision'],gpu_uuid=auth['gpu_uuid'],scope_counts=A.COUNTS,
                    wall_seconds=wall,actual_GPUh=wall/3600,billed_limit_GPUh=c['billed_limit_GPUh'],ended_unix=time.time())
                atomic_json(out/'billing.json',bill);settled=pool.settle(A.RUN,wall/3600,A.sha(out/'billing.json'))
                state.update(status='POLICY_ASSETS_GPU_RELEASED_CPU_POST_PENDING',billing_sha256=A.sha(out/'billing.json'),
                    actual_GPUh=wall/3600,ended_unix=time.time(),pool_after=settled)
                atomic_json(out/'supervisor.json',state)
        finally:lease.close()
    # Model process and UUID lease have actually ended before this CPU audit.
    # Its CPU time is not falsely billed as occupied GPU time.
    command=[sys.executable,str(a.stage/'scripts/postprocess_wc_policy_interval_assets_r1.py'),
        '--project',str(a.project),'--stage',str(a.stage)]
    with (out/'post-CPU.log').open('x') as log:
        post=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime',
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(a.stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
        state.update(post_pid=post.pid,post_identity=process_identity(post.pid));atomic_json(out/'supervisor.json',state)
        code=post.wait()
    result=out/'post-results.json'
    atomic_json(out/'post-exit.json',dict(exit_code=code,final_result_sha256=A.sha(result) if result.exists() else None,
        CPU_only_after_UUID_release=True,ended_unix=time.time()))
    state.update(status='POLICY_ASSETS_CPU_POST_EXITED',post_exit_code=code);atomic_json(out/'supervisor.json',state)


def capture(a):
    A=own_imports(ROOT);envelope=A.read(a.launch_ref);L=envelope['launch'];assert L
    cpu=a.mode.startswith('cpu-');terminal=a.mode.endswith('terminal')
    not_before=L['final_not_before_unix'] if cpu and terminal else L['halfway_not_before_unix'] if cpu else (
        L['next_check_not_before_unix'] if terminal else L['halfway_check_not_before_unix'] if a.mode=='gpu-halfway' else 0)
    assert time.time()>=not_before,'Before original not-before: no SSH'
    code='L='+repr(L)+'\nMODE='+repr(a.mode)+'\n'+CAPTURE_CODE
    try:
        result=ssh(code,timeout=150)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        raw=result.stdout;v=json.loads(gzip.decompress(raw))
    except Exception as e:
        v=dict(status='OBSERVATION_UNKNOWN_NOT_TASK_TERMINAL',error_type=type(e).__name__,error=str(e),launch=L)
        raw=gzip.compress(json.dumps(v).encode())
    with a.output.open('xb') as f:f.write(raw)
    print(json.dumps({k:v.get(k) for k in ('status','mode','process','health','original_live_handles','error_lines')}))


CAPTURE_CODE=r'''
import fcntl,gzip,hashlib,json,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage']);sys.path.insert(0,str(stage/'src'))
from wcomr.policy_interval_assets_r1 import CONFIG,RUN,CPU_BUNDLE,CPU_PROOF,read,sha
from wcomr.policy_interval_assets_lifecycle_r1 import live
from wcomr.gpu_budget_pool_v2 import process_identity
assert sha(stage/'registration.json')==L['registration_sha256']
cpu=MODE.startswith('cpu-');terminal=MODE.endswith('terminal')
v=dict(status='POLICY_ASSETS_ONCE_ORIGINAL_CAPTURE',mode=MODE,launch=L,observed_unix=time.time(),GPU_submissions=0,ledger_written=False)
if cpu:
 v['process']=process_identity(L['identity']['pid'])
 names={'bundle':CPU_BUNDLE,'proof':CPU_PROOF,'numerical':'policy-assets-numerical-CPU.json','config':CONFIG}
 if terminal:
  reg=read(stage/'registration.json');v.update(registration=reg,registration_sha256=sha(stage/'registration.json'),
   payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
  for k,n in names.items():
   p=stage/n;v['files'][k]=dict(exists=p.exists())
   if p.exists():v['files'][k].update(data=read(p),sha256=sha(p))
 else:v['result_files_present']={k:(stage/n).exists() for k,n in names.items()}
 log=stage/'policy-assets-CPU.log'
else:
 out=root/'outputs'/RUN
 sup=read(out/'supervisor.json') if (out/'supervisor.json').exists() else {}
 identities={'supervisor':L['supervisor_identity']}
 if sup.get('child_identity'):identities['runner']=sup['child_identity']
 if sup.get('post_identity'):identities['post']=sup['post_identity']
 v['original_processes']={k:process_identity(i['pid']) for k,i in identities.items()}
 v['original_live_handles']={k:live(i,v['original_processes'][k]) for k,i in identities.items()}
 v['supervisor']=sup;v['pool']=read(root/'reports/gpu-budget-v2.json')
 lock=root/'.sync/gpu-locks'/(L['gpu_uuid']+'.lock');v['own_UUID_lock_free']=None
 if lock.exists():
  with lock.open('rb') as f:
   try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_UUID_lock_free']=True;fcntl.flock(f.fileno(),fcntl.LOCK_UN)
   except BlockingIOError:v['own_UUID_lock_free']=False
 try:
  v['own_GPU']=subprocess.check_output(['nvidia-smi','-i',L['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=12)
  v['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=12)
 except Exception as e:v['GPU_telemetry_error']=str(e)
 if terminal:
  reg=read(stage/'registration.json');v.update(registration=reg,registration_sha256=sha(stage/'registration.json'),
   payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
  for k,n in {'post':'post-results.json','post_exit':'post-exit.json','bundle':'generator-input-bundle.json'}.items():
   p=out/n;v['files'][k]=dict(exists=p.exists())
   if p.exists():v['files'][k].update(data=read(p),sha256=sha(p))
  if (out/'runner.json').exists():v.update(runner=read(out/'runner.json'),runner_sha256=sha(out/'runner.json'))
  if (out/'billing.json').exists():v.update(billing=read(out/'billing.json'),billing_sha256=sha(out/'billing.json'))
  v['other_reservation_identities']={k:process_identity(j['supervisor_pid']) for k,j in v['pool']['jobs'].items() if j['status']=='RESERVED_OR_RUNNING'}
 else:
  p=out/'runner-health.json';v['health']=read(p) if p.exists() else {'phase':'PREVALIDATION_OR_NOT_STARTED'}
  active=v['health'].get('active_path')
  if active:
   p=out/active/'interval-raw'/'technical-progress.json'
   if p.exists():v['cell_technical_progress']=read(p)
 log=out/'GPU.log'
if log.exists():
 with log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-65536));tail=f.read().decode(errors='replace')
 v['error_lines']=[s for s in tail.splitlines() if any(k in s for k in ('Traceback','RuntimeError','AssertionError','OutOfMemory','No space left'))][-16:]
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def accept(a):
    A=own_imports(ROOT)
    from wcomr.policy_interval_assets_lifecycle_r1 import accept_cpu,accept_terminal
    v=A.read(a.capture)
    value=(accept_cpu if a.kind=='cpu' else accept_terminal)(v)
    value.update(capture_ref=str(a.capture),capture_sha256=A.sha(a.capture))
    dump(a.output,value);print(json.dumps(value,ensure_ascii=False))


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('prepare');q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('deploy-cpu');q.add_argument('--stage',required=True);q.add_argument('--output',type=Path,required=True)
    for name in ('cpu-worker','supervise'):
        q=s.add_parser(name)
        for key in ('project','stage'):q.add_argument('--'+key,type=Path,required=True)
        if name=='supervise':q.add_argument('--authorization',type=Path,required=True)
    q=s.add_parser('launch-gpu')
    for n in ('CPU-launch-ref','CPU-capture','CPU-acceptance','upstream-capture','upstream-acceptance','output'):
        q.add_argument('--'+n,type=Path,required=True)
    q.add_argument('--gpu-uuid',required=True);q.add_argument('--specific-approval',type=Path)
    q=s.add_parser('capture');q.add_argument('--mode',choices=['cpu-halfway','cpu-terminal','gpu-admission','gpu-halfway','gpu-terminal'],required=True)
    q.add_argument('--launch-ref',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('accept');q.add_argument('--kind',choices=['cpu','gpu'],required=True)
    q.add_argument('--capture',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if hasattr(a,'output') and a.output.exists():raise FileExistsError('Original receipt exists; offline only, never overwrite')
    {'prepare':prepare,'deploy-cpu':deploy_cpu,'cpu-worker':cpu_worker,'launch-gpu':launch_gpu,
        'supervise':supervise,'capture':capture,'accept':accept}[a.command](a)


if __name__=='__main__':main()
