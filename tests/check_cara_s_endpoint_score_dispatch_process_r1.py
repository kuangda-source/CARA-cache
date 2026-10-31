"""Actual Linux once-dispatch processes; Docker and metric values are simulated."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from unittest.mock import patch

from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatch
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.gpu_budget_pool_v2 import atomic_json,sha


def inspect(stage,cid):
    path=stage/'CPU-container.json'
    if not path.exists():return dict(status='UNKNOWN',reason='CPU_CONTAINER_NOT_CREATED')
    container=read_record(path)
    if read_record(stage/'CPU-scenario.json')['scenario']=='wrong_container':container['Id']='f'*64
    return dict(status='OBSERVED',container=container)


def supervisor(stage):
    scenario=read_record(stage/'CPU-scenario.json')['scenario']
    dispatch.capture.inspect_original=lambda cid:inspect(stage,cid)
    def stop(command,**kwargs):
        assert command==['docker','stop','--time','10','a'*64]
        handle=read_record(stage/'CPU-worker-start.json')['identity']
        if observe_original_process(handle)['original_live'] is True:os.kill(handle['pid'],signal.SIGTERM)
        deadline=time.monotonic()+5
        while read_record(stage/'CPU-container.json')['State']['Running']:
            if time.monotonic()>deadline:raise TimeoutError('CPU container stop fixture')
            time.sleep(.01)
        return subprocess.CompletedProcess(command,0,'','')
    dispatch.subprocess.run=stop
    if scenario=='bootstrap_failure':
        popen=dispatch.subprocess.Popen
        dispatch.subprocess.Popen=lambda command,**kwargs:popen([sys.executable,'-c','raise SystemExit(7)'],**kwargs)
    dispatch.supervise(stage)


def cli(stage):
    scenario=read_record(stage/'CPU-scenario.json')['scenario']
    create_record(stage/'CPU-cli-once.json',dict(identity=bind_original_process(os.getpid())))
    control=stage/'endpoint-score-control';intent,_,config=dispatch.read_intent(stage)
    container=read_record(stage/'CPU-container-template.json')
    (control/'container.cid').write_text(container['Id']+'\n')
    container['State'].update(StartedAt=timestamp(time.time()),FinishedAt=timestamp(time.time()),ExitCode=7)
    if scenario=='preworker_failure':atomic_json(stage/'CPU-container.json',container);raise SystemExit(7)
    child=subprocess.Popen([sys.executable,str(stage/'CPU-fixture.py'),'worker',str(stage)],start_new_session=True)
    handle=bind_original_process(child.pid)
    container['State'].update(Status='running',Running=True,Pid=child.pid,ExitCode=0)
    atomic_json(stage/'CPU-container.json',container)
    def interrupted(signum,frame):raise InterruptedError('Owned CPU CLI stopped')
    signal.signal(signal.SIGTERM,interrupted)
    code=143
    try:code=child.wait(timeout=25)
    except InterruptedError:pass
    finally:
        stop_original(child,handle);child.wait(timeout=5)
        container['State'].update(Status='exited',Running=False,Pid=0,ExitCode=code,FinishedAt=timestamp(time.time()))
        atomic_json(stage/'CPU-container.json',container)
    raise SystemExit(code)


def timestamp(value):
    import datetime
    return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat().replace('+00:00','Z')


def worker(stage):
    intent,_,config=dispatch.read_intent(stage);_,out=dispatch.paths(stage,config)
    identity=bind_original_process(os.getpid());create_record(stage/'CPU-worker-start.json',dict(identity=identity))
    result=read_record(stage/'CPU-result-template.json');result.update(original_identity=identity,started_unix=time.time())
    create_record(out/'scores-intent.json',dict(manifest_sha256=intent['manifest_sha256'],no_replay=True,
        CPU_fixture_only=True,registered_pairs=[p['id'] for p in config['pairs']],
        worker_sha256=config['scorer_source_sha256'][dispatch.WORKER],original_identity=identity))
    scenario=read_record(stage/'CPU-scenario.json')['scenario']
    if scenario in ('timeout','wrong_container'):time.sleep(20)
    if scenario=='worker_failure':result.update(status='FAILED_DENOMINATOR_RETAINED',rows=[])
    result['ended_unix']=time.time();atomic_json(out/'scores.json',result)
    if scenario=='worker_failure':raise SystemExit(7)


def run(root):
    from test_cara_s_endpoint_score_dispatch_r1 import fixture,ROOT,save
    cases=[];root=Path(root)
    foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)'],start_new_session=True)
    foreign_handle=bind_original_process(foreign.pid)
    try:
        for scenario in ('complete','worker_failure','preworker_failure','timeout','unknown_capture','wrong_container','bootstrap_failure'):
            args,container,out,result=fixture(root/scenario);stage=args['stage']
            shutil.copytree(ROOT/'src',stage/'src',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ROOT/'scripts',stage/'scripts',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
            protocol='plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'
            (stage/protocol).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/protocol,stage/protocol)
            shutil.copyfile(ROOT/'tests/check_cara_s_endpoint_score_dispatch_process_r1.py',stage/'CPU-fixture.py')
            registration=read_record(stage/'registration.json');registration['payload_sha256'][protocol]=sha(stage/protocol)
            save(stage/'registration.json',registration);args['registration_sha256']=sha(stage/'registration.json')
            save(stage/'CPU-scenario.json',dict(scenario=scenario,CPU_fixture_only=True))
            save(stage/'CPU-container-template.json',container);save(stage/'CPU-result-template.json',result)
            args['work_seconds']=.8 if scenario in ('timeout','wrong_container') else 10.
            original_popen=subprocess.Popen;children=[]
            def spawn(command,**kwargs):
                assert command[1:3]==[str(stage/dispatch.BOOTSTRAP),'supervise']
                environment=dict(kwargs['env'],PYTHONPATH=str(stage/'src')+':'+str(stage/'scripts'))
                child=original_popen([sys.executable,str(stage/'CPU-fixture.py'),'supervise',str(stage)],
                    **dict(kwargs,env=environment));children.append(child);return child
            command=[sys.executable,str(stage/'CPU-fixture.py'),'cli',str(stage)]
            with patch.object(dispatch,'require_absent'),patch.object(dispatch,'resource_admission',return_value=dict(CPU_fixture=True)), \
                 patch.object(dispatch,'score_command',return_value=command),patch.object(dispatch.subprocess,'Popen',side_effect=spawn):
                launched=dispatch.dispatch(**args)
                # Discarding the returned launch fields simulates a lost SSH response.
                assert launched['status']=='ORIGINAL_SCORE_INTENT_CREATED'
                repeated=dispatch.dispatch(**args)
                assert repeated['status'] in ('ORIGINAL_SCORE_DISPATCH_ACTIVE','ORIGINAL_SCORE_DISPATCH_UNKNOWN')
                assert len(children)==1
            child=children[0]
            try:code=child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                handle=bind_original_process(child.pid);stop_original(child,handle);raise
            control=stage/'endpoint-score-control';terminal=read_record(control/'supervisor-terminal.json')
            log=(out/'supervisor.log').read_text()[-3000:]
            assert (code==0)==(scenario in ('complete','unknown_capture')),(scenario,terminal,log)
            with patch.object(dispatch.capture,'inspect_original',side_effect=lambda cid:inspect(stage,cid)):
                if scenario=='wrong_container':
                    try:dispatch.recover(stage)
                    except ValueError as error:assert 'ID/name' in str(error)
                    else:raise AssertionError('Foreign container accepted')
                    status='FOREIGN_CONTAINER_REFUSED'
                else:
                    recovered=dispatch.recover(stage);status=recovered['status']
                    expected='ORIGINAL_COMPLETE24_SCORE_ACCEPTED' if code==0 else (
                        'ORIGINAL_SCORE_DISPATCH_UNKNOWN' if scenario=='bootstrap_failure' else 'ORIGINAL_SCORE_FAILED')
                    assert status==expected,(scenario,status,terminal,log)
                    if code==0:
                        assert recovered['score_capture']['accepted']['formal_logical_positions']==24
                        assert recovered['score_capture']['accepted']['new_scored_pairs']==12
                    if scenario=='unknown_capture':
                        with patch.object(dispatch.capture,'inspect_original',return_value=dict(status='UNKNOWN',reason='CPU transport')):
                            assert dispatch.recover(stage)['status']=='ORIGINAL_SCORE_UNKNOWN'
                        assert dispatch.recover(stage)['status']=='ORIGINAL_COMPLETE24_SCORE_ACCEPTED'
                with patch.object(dispatch.subprocess,'Popen',side_effect=AssertionError('No second process')):
                    if scenario=='wrong_container':
                        try:dispatch.dispatch(**args)
                        except ValueError:pass
                    else:assert dispatch.dispatch(**args)['status']==status
            if scenario=='complete':
                before=sha(stage/'CPU-cli-once.json')
                duplicate=subprocess.run([sys.executable,str(stage/dispatch.BOOTSTRAP),'container-cli','--stage',str(stage)],
                    capture_output=True,text=True,timeout=10,env=dict(os.environ,PYTHONPATH=str(stage/'src')+':'+str(stage/'scripts')))
                assert duplicate.returncode!=0 and sha(stage/'CPU-cli-once.json')==before
            assert observe_original_process(foreign_handle)['original_live'] is True
            handles={}
            for role,path in (('cli',control/'container-cli-start.json'),('worker',stage/'CPU-worker-start.json')):
                if path.exists():
                    handle=read_record(path)['identity'];observed=observe_original_process(handle)
                    assert observed['original_live'] is False,(scenario,role,observed)
                    handles[role]=dict(identity=handle,observation=observed)
            cases.append(dict(scenario=scenario,status=status,exit_code=code,supervisor_terminal=terminal,
                supervisor_observation=observe_original_process(terminal['identity']),one_supervisor_spawn=True,
                original_handles=handles,repeated_dispatch_spawned=False,foreign_process_preserved=True))
        return dict(status='ACTUAL_LINUX_ONCE_SCORE_DISPATCH_CPU_PASS',cases=cases,scenarios=7,
            full24_acceptances=2,new_pairs_per_acceptance=12,metric_computations=0,Docker_simulated=True,
            score_values_synthetic=True,original_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False)
    finally:stop_original(foreign,foreign_handle);foreign.wait(timeout=10)


if __name__=='__main__':
    stage=Path(sys.argv[2]);assert read_record(stage/'CPU-scenario.json')['CPU_fixture_only'] is True
    {'supervise':supervisor,'cli':cli,'worker':worker}[sys.argv[1]](stage)
