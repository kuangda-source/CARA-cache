"""Exercise the actual supervisor with CPU child processes and fixture-only ledger.

No CUDA call, nvidia-smi command, sudo command or authoritative ledger is used.
The original production module is imported from the frozen price stage.
"""
import argparse
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch


def run(stage, output_root):
    sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
    import torch
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and not torch.cuda.is_initialized()
    import wcomr.policy_generator_r1.cost112_card as contract
    import wcomr.policy_generator_r1.production_exclusive as exclusive
    from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,atomic_json,sha,process_identity
    import wc_cara_cost112_worker_r1 as worker
    checks=[]
    for scenario in ('success','runner_failure','foreign_context','telemetry_failure_on_release'):
        root=output_root/scenario;fixture=root/'.sync/fixture-stage';fixture.mkdir(parents=True)
        (root/'reports').mkdir();(root/'outputs').mkdir();(fixture/'scripts').mkdir()
        (root/'runtime').mkdir()
        source='CPU_FIXTURE_ONLY_NOT_AN_EXPERIMENT'
        config=dict(forecast_complete_GPUh=.1,billed_limit_GPUh=.2)
        reg=dict(source_revision=source)
        atomic_json(fixture/'registration.json',reg);atomic_json(fixture/contract.CONFIG,config)
        atomic_json(fixture/contract.CPU_PROOF,dict(CPU_fixture_only=True))
        atomic_json(fixture/'pg-independent-CPU-acceptance.json',dict(production_CPU_accepted=True,CPU_fixture_only=True))
        auth=dict(source_revision=source,registration_sha256=sha(fixture/'registration.json'),
            production_CPU_sha256=sha(fixture/contract.CPU_PROOF),scope_counts=contract.COUNTS,
            billed_limit_GPUh=.2,gpu_uuid='GPU-CPU-fixture',launch_id=scenario)
        atomic_json(fixture/'pg-GPU-authorization.json',auth)
        pool=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=1.,
            origin_gpu_jobs_launched=0,jobs={},events=[],CPU_FIXTURE_ONLY_NOT_AUTHORITY=True)
        pool.update(BudgetPool.accounting(pool));atomic_json(root/'reports/gpu-budget-v2.json',pool)
        # Real child, inherited FD, readiness handshake and own-session exit.
        runner='''import json,os,pathlib,sys,time
args=dict(zip(sys.argv[1::2],sys.argv[2::2]));stage=pathlib.Path(args['--stage'])
sys.path.insert(0, SOURCE_SRC)
from wcomr.gpu_budget_pool_v2 import process_identity,atomic_json
assert os.getppid()==int(os.environ['WC_SUPERVISOR_PID'])
fd=int(os.environ['WC_LOCK_FD']);assert os.fstat(fd).st_ino==(pathlib.Path(args['--project'])/'.sync/gpu-locks/GPU-CPU-fixture.lock').stat().st_ino
identity={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
atomic_json(stage/'pg-runner-context-ready.json',dict(identity=identity))
deadline=time.monotonic()+15
while not (stage/'pg-runner-context-granted.json').exists():
 assert time.monotonic()<deadline
 time.sleep(.02)
time.sleep(3)
raise SystemExit(EXIT_CODE)
'''.replace('SOURCE_SRC',repr(str(stage/'src'))).replace('EXIT_CODE','1' if scenario=='runner_failure' else '0')
        (fixture/'scripts/run_cara_cost112_r1.py').write_text(runner)
        post="import json,pathlib,sys\na=dict(zip(sys.argv[1::2],sys.argv[2::2]));p=pathlib.Path(a['--project'])/'outputs'/"+repr(contract.RUN)+"\n(p/'post-results.json').write_text(json.dumps(dict(CPU_fixture_only=True)))\n"
        (fixture/'scripts/postprocess_cara_cost112_r1.py').write_text(post)
        observations=[]
        def observe(uuid):
            assert uuid=='GPU-CPU-fixture'
            ready=fixture/'pg-runner-context-ready.json';apps=[]
            if ready.exists():
                ident=contract.read(ready)['identity'];actual=process_identity(ident['pid'])
                live=actual['start_ticks']==ident['start_ticks'] and actual['state'] not in (None,'Z','X')
                if live:apps=[ident]
                elif scenario=='telemetry_failure_on_release':raise RuntimeError('CPU_FIXTURE_TELEMETRY_LOST')
                if scenario=='foreign_context' and (fixture/'pg-runner-context-granted.json').exists():
                    apps.append(dict(pid=99999999,uid=9999,start_ticks=1))
            s=dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,mps_processes=[],observed_unix=time.time())
            observations.append(s);return s
        def smi(args,**kw):
            assert args[0]=='/usr/bin/nvidia-smi' and '--query-gpu=uuid,name,memory.used,compute_cap' in args
            # The accepted Ada base contains the separately recorded host port.
            return 'GPU-CPU-fixture, NVIDIA RTX 6000 Ada Generation, 0, 8.9\n'
        original_handler=__import__('signal').getsignal(__import__('signal').SIGTERM)
        error=None
        try:
            with patch.object(contract,'validate',lambda *a:(config,reg)),patch.object(exclusive,'observe',observe),patch.object(subprocess,'check_output',smi):
                try:worker.supervise(SimpleNamespace(project=root,stage=fixture))
                except (RuntimeError,ValueError) as e:error=str(e)
        finally:__import__('signal').signal(__import__('signal').SIGTERM,original_handler)
        out=root/'outputs'/contract.RUN;bill=contract.read(out/'billing.json');after=BudgetPool(root).read()
        assert after['jobs'][contract.RUN]['status']=='SETTLED'
        assert after['used_gpu_hours']==1+bill['actual_GPUh'] and after['reserved_gpu_hours']==0
        assert after['jobs'][contract.RUN]['billing_sha256']==sha(out/'billing.json')
        with DeviceLease(root,'GPU-CPU-fixture'):pass
        state=contract.read(out/'supervisor.json');monitor=contract.read(out/'exclusive-monitor-final.json')
        if scenario=='success':assert error is None and monitor['accepted'] and state['post_exit_code']==0
        else:
            assert not monitor['accepted']
            if scenario!='telemetry_failure_on_release':assert error is not None
        if (fixture/'pg-runner-context-ready.json').exists():
            i=contract.read(fixture/'pg-runner-context-ready.json')['identity'];actual=process_identity(i['pid'])
            assert actual['state'] in (None,'Z','X') or actual['start_ticks']!=i['start_ticks']
        checks.append(dict(scenario=scenario,status='PASS',real_child_exited=True,original_FD_verified=True,
            exact_context_handshake_exercised=True,actual_CPU_elapsed_fixture_settlement_preserved=True,
            authoritative_ledger_touched=False,original_lease_released=True,actual_nvidia_smi_calls=0,
            actual_sudo_calls=0,GPU_submissions=0))
    # Exercise the actual host guardian orchestration with fake administrative
    # commands, never using credentials or changing real hardware.
    import wc_cara_cost112_host_guardian_r1 as host
    import types
    for scenario in ('host_clean_restore','host_foreign_arrival_defer_restore'):
        root=output_root/scenario;fixture=root/'.sync/fixture-stage';fixture.mkdir(parents=True)
        atomic_json(fixture/'registration.json',dict(source_revision='CPU_HOST_FIXTURE'))
        atomic_json(fixture/'pg-GPU-authorization.json',dict(gpu_uuid='GPU-CPU-fixture'))
        snapshot=dict(gpu_uuid='GPU-CPU-fixture',compute_mode='Default',compute_apps=[],mps_processes=[],observed_unix=time.time())
        commands=[]
        def query(uuid):
            assert uuid=='GPU-CPU-fixture';return dict(snapshot,observed_unix=time.time())
        def admin(args,**kw):
            assert args[:4]==['sudo','-S','-p',''] and args[4:7]==['/usr/bin/nvidia-smi','-i','GPU-CPU-fixture']
            assert args[7]=='-c' and kw['input']=='CPU_FAKE_SECRET\n'
            commands.append(args)
            snapshot['compute_mode']={'EXCLUSIVE_PROCESS':'Exclusive_Process','DEFAULT':'Default'}[args[-1]]
            return SimpleNamespace(returncode=0)
        class ContainerCLI:
            pid=99999998
            def wait(self,**kw):
                if scenario=='host_foreign_arrival_defer_restore':snapshot['compute_apps']=[dict(pid=99999999)]
                return 0
            def poll(self):return 0
        def popen(command,**kw):
            assert command[0]=='docker' and command.count('--gpus')==1
            assert 'device=GPU-CPU-fixture' in command
            assert str(fixture/'scripts/wc_cara_cost112_worker_r1.py') in command
            assert '--authorization' not in command
            return ContainerCLI()
        helper=types.ModuleType('four_card_bank24_execution_tools_r1')
        helper.process_environment=lambda *a:dict(PATH=os.environ['PATH'])
        with patch.object(contract,'validate',lambda *a:({},dict(source_revision='CPU_HOST_FIXTURE'))), \
             patch.object(exclusive,'observe',query),patch.object(subprocess,'run',admin), \
             patch.object(subprocess,'Popen',popen),patch.dict(sys.modules,{'four_card_bank24_execution_tools_r1':helper}), \
             patch.object(sys,'argv',['guardian','--project',str(root),'--stage',str(fixture)]), \
             patch.object(sys,'stdin',io.StringIO(json.dumps(dict(sudo_password='CPU_FAKE_SECRET')))):
            original_handler=__import__('signal').getsignal(__import__('signal').SIGTERM)
            try:host.main()
            finally:__import__('signal').signal(__import__('signal').SIGTERM,original_handler)
        state=contract.read(fixture/'pg-host-guardian.json')
        assert state['mode_restoration']['restored']==(scenario=='host_clean_restore')
        assert len(commands)==(2 if scenario=='host_clean_restore' else 1)
        assert all('CPU_FAKE_SECRET' not in f.read_text() for f in fixture.rglob('*') if f.is_file())
        checks.append(dict(scenario=scenario,status='PASS',actual_selected_UUID_command_construction=True,
            credential_not_persisted=True,busy_foreign_process_not_touched=True,actual_sudo_calls=0,
            actual_nvidia_smi_calls=0,GPU_submissions=0))
    assert not torch.cuda.is_initialized()
    return dict(status='COST112_SUPERVISOR_REAL_CPU_CHILD_LIFECYCLE_PASS',checks=checks,
        production_supervisor_sha256=sha(stage/'scripts/wc_cara_cost112_worker_r1.py'),
        stage_registration_sha256=sha(stage/'registration.json'),
        production_host_guardian_sha256=sha(stage/'scripts/wc_cara_cost112_host_guardian_r1.py'),CUDA_initialized=False,
        hardware_exclusive_support_verified=False,CPU_fixture_only=True,GPU_submissions=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.stage,a.output_root)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
