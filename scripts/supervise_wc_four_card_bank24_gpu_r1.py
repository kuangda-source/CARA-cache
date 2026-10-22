#!/usr/bin/env python3
"""Actual whole BANK24 GPU controller; requires a real external v2 handoff.

No CPU/debug switch can grant GPU permission. CPU tests exercise its separate
transport and arithmetic, while this entry stays closed until real acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import signal
import shutil
import subprocess
import time

from four_card_bank24_container_transport_r1 import LeaseBroker,atomic,identity,alive,socket_path
from four_card_bank24_gpu_port_r1 import ROOT,SCIENCE_RUN,require_full_CPU,validate_handoff,sha,read,require


def module(path):
    spec=importlib.util.spec_from_file_location('registered_SM89_budget',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def observe(uuid):
    values=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap',
        '--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
    return dict(uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),
        compute_cap=values[3].strip(),pids=[int(v.split(',')[1]) for v in apps.splitlines() if v.split(',')[0].strip()==uuid])


def owned_container_state(name,label):
    check=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=20)
    if check.returncode:
        if 'No such object' in check.stderr or 'No such container' in check.stderr:return 'ABSENT'
        return 'UNKNOWN'
    value=json.loads(check.stdout)[0]
    require(value['Config']['Labels'].get('wcomr.manifest')==label,'Never stop an unowned container')
    return 'RUNNING' if value['State']['Running'] else 'EXITED'


def container_command(project,stage,out,m,image,environment):
    args=['docker','run','--rm','--read-only','--network','none','--pid','host','--name',m['container'],
        '--label','wcomr.manifest='+sha(stage/'gpu-container-manifest.json'),
        '--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--memory','48g','--pids-limit','512',
        '--gpus','device='+m['gpu_uuid'],'--tmpfs','/tmp:rw,size=2g',
        '-v',str(project)+':'+str(project)+':ro','-v',str(stage)+':'+str(stage)+':rw',
        '-v',str(out)+':'+str(out)+':rw',
        '-v',str(socket_path(stage).parent)+':'+str(socket_path(stage).parent)+':ro','-w',str(project/'runtime')]
    for key,value in environment.items():args+=['-e',key+'='+value]
    args+=['--entrypoint',str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python'),image,
        str(stage/'run_wc_four_card_bank24_inner_r1.py'),'--manifest',str(stage/'gpu-container-manifest.json')]
    return args


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True,type=Path)
    p.add_argument('--authorization',required=True,type=Path);a=p.parse_args()
    project=Path(ROOT);stage=a.stage.resolve();out=project/'outputs'/SCIENCE_RUN
    from four_card_bank24_execution_tools_r1 import validate_authorization,verify_nltk_resources
    validate_authorization(project,stage,read(a.authorization))
    nltk_resources=verify_nltk_resources(project)
    env=read(stage/'GPU-process-environment.json')
    require(env.get('NLTK_DATA')==nltk_resources['root'],'Materialized NLTK path missing from GPU environment')
    require(project.resolve() in stage.parents and stage.parent==project/'.sync','Wrong independent host namespace')
    reg=read(stage/'registration.json');meta=read(stage/'host-lifecycle-dependency.json');auth=read(a.authorization)
    require_full_CPU(stage,reg['source_revision'])
    require(auth['source_revision']==reg['source_revision'] and auth['registration_sha256']==sha(stage/'registration.json')
        and auth['config_sha256']==meta['config_sha256'] and auth['scope_counts']==meta['scope_counts'], 'Authorized source or whole scope differs')
    require(auth['production_CPU_sha256']==sha(stage/'scout-lifecycle-CPU-proof.json')
        and auth['independent_CPU_acceptance_sha256']==sha(stage/'scout-lifecycle-CPU-independent-acceptance.json'), 'Actual CPU binding differs')
    require(sha(stage/'unique-v2-handoff.json')==auth['unique_handoff_sha256'],'Actual handoff binding differs')
    validate_handoff(project,read(stage/'unique-v2-handoff.json'))
    for name,expected in reg['payload_sha256'].items():require(sha(stage/name)==expected,'Host immutable payload changed')
    quote=read(stage/'whole24-planning-quote.json')
    require(auth['planning_quote_sha256']==sha(stage/'whole24-planning-quote.json')
        and auth['forecast_GPUh']==quote['forecast_complete_GPUh'] and auth['billed_limit_GPUh']==quote['billed_limit_GPUh']
        and 0<auth['forecast_GPUh']<=auth['billed_limit_GPUh']<12,'Complete new-host planning quote required')
    runtimes=json.loads(subprocess.check_output(['docker','info','--format','{{json .Runtimes}}'],text=True,timeout=20))
    require('nvidia' in runtimes,'NVIDIA container runtime not available; no GPU dispatch')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    require(shutil.disk_usage(project).free>=128*(1<<30) and available>=50*(1<<30),'Full GPU disk/host-memory gate failed')
    poolmod=module(stage/'bank24_sm89_budget_pool.py');pool=poolmod.BudgetPool(project);lease=poolmod.DeviceLease(project,auth['gpu_uuid'])
    reserved=False;known_off=False;broker=None;child=None;state={};start=None
    def interrupted(number,frame):raise InterruptedError('Own GPU supervisor interrupted: '+str(number))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:
        lease.acquire();require(not out.exists(),'Original whole BANK24 output exists; restore only')
        with (stage/'GPU-dispatch-fence.json').open('x') as stream:json.dump(dict(source_revision=reg['source_revision'],launch_id=auth['launch_id'],created_unix=time.time()),stream)
        before=pool.read();require(before['cap_gpu_hours']==226 and before['origin_used_gpu_hours']==79.99637737158223,'Historical budget differs')
        gpu=observe(auth['gpu_uuid']);who=identity(os.getpid())
        job=dict(job_id=SCIENCE_RUN,run_id=SCIENCE_RUN,launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],source_revision=reg['source_revision'],
            config_sha256=meta['config_sha256'],registration_sha256=sha(stage/'registration.json'),
            production_CPU_sha256=auth['production_CPU_sha256'],authorization_sha256=sha(a.authorization),
            independent_CPU_acceptance_sha256=auth['independent_CPU_acceptance_sha256'],scope_counts=meta['scope_counts'],
            supervisor_pid=os.getpid(),supervisor_start_ticks=who['start_ticks'],forecast_GPUh=auth['forecast_GPUh'],billed_limit_GPUh=auth['billed_limit_GPUh'])
        after=pool.reserve(job,gpu);reserved=True;known_off=True;start=time.monotonic();out.mkdir(parents=True)
        m=dict(namespace='BANK24_FOURCARD_GPU_PORT_R1',source_revision=reg['source_revision'],project=str(project),output=str(out),
            gpu_uuid=auth['gpu_uuid'],handoff_nonce=secrets.token_hex(24),container='wc-bank24-gpu-'+auth['launch_id'],
            host_start_monotonic=start,billed_limit_GPUh=auth['billed_limit_GPUh'])
        atomic(stage/'gpu-container-manifest.json',m);label=sha(stage/'gpu-container-manifest.json')
        state=dict(status='BANK24_HOST_GPU_CONTAINER_RUNNING',source_revision=reg['source_revision'],scope_counts=meta['scope_counts'],
            supervisor_identity=who,started_unix=time.time(),pool_before=before,pool_after_reservation=after,
            launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],container=m['container'],container_manifest_sha256=label)
        atomic(out/'supervisor.json',state)
        broker=LeaseBroker(stage,lease.handle.fileno(),lease.path,m['handoff_nonce'],label,m['container']);broker.start()
        command=container_command(project,stage,out,m,meta['container_image_id'],env)
        atomic(stage/'GPU-container-command.json',command)
        with (stage/'GPU-container.log').open('x') as log:
            known_off=False
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:child.wait(timeout=max(1,auth['billed_limit_GPUh']*3600-15))
            except subprocess.TimeoutExpired:
                state['own_billed_limit_stop']=True
                if owned_container_state(m['container'],label)=='RUNNING':subprocess.run(['docker','stop','--time','5',m['container']],check=True,timeout=25,stdout=log,stderr=subprocess.STDOUT)
                child.wait(timeout=15)
        status=owned_container_state(m['container'],label);known_off=status in ('ABSENT','EXITED')
        state['owned_container_exit_verified']=known_off
        if not known_off:raise RuntimeError('Owned GPU container state unknown; preserve reservation and handle')
        inner=read(stage/'inner-supervisor.json') if (stage/'inner-supervisor.json').is_file() else {}
        state.update(child_pid=(inner.get('child_identity') or {}).get('pid'),child_identity=inner.get('child_identity'),
            inner_identity=inner.get('identity'),child_exit_code=inner.get('exit_code',child.returncode),
            original_FD_handoff_sha256=sha(stage/'host-FD-handoff.json') if (stage/'host-FD-handoff.json').is_file() else None)
        known_off=known_off and not alive(inner.get('identity')) and not alive(inner.get('child_identity'))
        require(known_off,'Original inner/runner process still live; retain reservation and restore only')
    except BaseException as error:
        state.update(error_type=type(error).__name__,error=str(error))
        if reserved and 'm' in locals():
            try:
                current=owned_container_state(m['container'],label)
                if current=='RUNNING':subprocess.run(['docker','stop','--time','5',m['container']],timeout=25,check=True,capture_output=True)
                known_off=owned_container_state(m['container'],label) in ('ABSENT','EXITED')
            except Exception:known_off=False
        raise
    finally:
        if broker:broker.close()
        if reserved and known_off:
            last_inner=read(stage/'inner-supervisor.json') if (stage/'inner-supervisor.json').is_file() else {}
            known_off=not alive(last_inner.get('identity')) and not alive(last_inner.get('child_identity'))
            state['owned_container_exit_verified']=known_off
        if reserved and known_off:
            # Container creation, import, inference, failures and container exit
            # are all inside this wall. No free GPU compatibility probe.
            wall=time.monotonic()-start
            bill=dict(status='SCOUT_ACTUAL_GPU_BILL',run_id=SCIENCE_RUN,launch_id=auth['launch_id'],source_revision=reg['source_revision'],
                gpu_uuid=auth['gpu_uuid'],scope_counts=meta['scope_counts'],wall_seconds=wall,actual_GPUh=wall/3600,
                billed_limit_GPUh=auth['billed_limit_GPUh'],ended_unix=time.time())
            atomic(out/'billing.json',bill);settled=pool.settle(SCIENCE_RUN,wall/3600,sha(out/'billing.json'))
            runner=out/'runner.json'
            state.update(status='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',billing_sha256=sha(out/'billing.json'),
                pool_after=settled,actual_GPUh=wall/3600,wall_seconds=wall,ended_unix=time.time(),
                runner_sha256=sha(runner) if runner.is_file() else None)
            lease.close();state['original_UUID_FD_closed_after_settlement']=True
            atomic(out/'supervisor.json',state)
        elif reserved:
            state.update(status='GPU_CONTAINER_UNKNOWN_RESERVATION_RETAINED_RESTORE_ONLY',settlement_unknown=True,
                own_UUID_release_verified=False,do_not_replay=True)
            atomic(out/'supervisor.json',state)
        else:
            lease.close()
            atomic(stage/'scout-admission-failure.json',dict(status='GPU_ADMISSION_FAILED_NO_RESERVATION',
                error_type=state.get('error_type'),error=state.get('error'),GPU_submissions=0,ledger_written=False))


if __name__=='__main__':main()
