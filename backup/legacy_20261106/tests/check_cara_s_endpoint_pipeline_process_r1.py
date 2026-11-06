"""CPU-only simulated Docker roles; worker execs the actual fixed scorer."""
import importlib.util
import os
import subprocess
import signal
import time
from pathlib import Path
import sys

from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatch
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record


def main():
    role=sys.argv[1];stage=Path(sys.argv[2])
    assert read_record(stage/'CPU-scenario.json')['CPU_fixture_only'] is True
    if role=='worker':
        create_record(stage/'CPU-worker-start.json',dict(identity=bind_original_process(os.getpid())))
        intent,_,config=dispatch.read_intent(stage);_,out=dispatch.paths(stage,config)
        command=[sys.executable,str(stage/dispatch.WORKER),'--manifest',str(out/'manifest.json'),
                 '--output',str(out/'scores.json'),'--cpu-validation']
        os.execvpe(command[0],command,dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
    specification=importlib.util.spec_from_file_location('original_CPU_process_fixture',stage/'CPU-process-base.py')
    module=importlib.util.module_from_spec(specification);specification.loader.exec_module(module)
    if role=='supervise':module.supervisor(stage);return
    assert role=='cli'
    create_record(stage/'CPU-cli-once.json',dict(identity=bind_original_process(os.getpid())))
    container=read_record(stage/'CPU-container-template.json')
    (stage/'endpoint-score-control/container.cid').write_text(container['Id']+'\n')
    child=subprocess.Popen([sys.executable,str(stage/'CPU-fixture.py'),'worker',str(stage)],start_new_session=True)
    handle=bind_original_process(child.pid)
    container['State'].update(Status='running',Running=True,Pid=child.pid,ExitCode=0,
                             StartedAt=module.timestamp(time.time()),FinishedAt=module.timestamp(time.time()))
    module.atomic_json(stage/'CPU-container.json',container)
    def interrupted(signum,frame):raise InterruptedError('Owned CPU CLI stopped')
    signal.signal(signal.SIGTERM,interrupted)
    code=143
    try:code=child.wait(timeout=180)
    except InterruptedError:pass
    finally:
        module.stop_original(child,handle);child.wait(timeout=5)
        container['State'].update(Status='exited',Running=False,Pid=0,ExitCode=code,FinishedAt=module.timestamp(time.time()))
        module.atomic_json(stage/'CPU-container.json',container)
    raise SystemExit(code)


if __name__=='__main__':main()
