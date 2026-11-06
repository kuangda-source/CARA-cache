"""Actual original CPU process chain; simulated GPU/container and host service."""
import os
from pathlib import Path
import subprocess
import sys
import time

import check_cara_s_endpoint_allocation_fixture_r1 as original
from wcomr import cara_s_endpoint_host_guardian_r1 as guardian
from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record, read_record, OriginalQueryUnknown
from wcomr.cara_budget_supervisor_r1 import stop_original


class CPUService:
    def __init__(self, stage):
        self.stage, self.child, self.identity = stage, None, None
        self.scenario = read_record(stage/'CPU-fit-scenario.json')['scenario']

    def start(self, state):
        assert state['CPU_fixture_only'] is True
        create_record(self.stage/'CPU-FIT-intent.json',dict(guardian_epoch=state['started_monotonic'],no_replay=True))
        if self.scenario=='start_failure':
            raise RuntimeError('CPU fixture FIT start refusal')
        self.child = subprocess.Popen([sys.executable,str(self.stage/'CPU-fixture.py'),'FIT_service',str(self.stage)],
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        self.identity = bind_original_process(self.child.pid)
        create_record(self.stage/'CPU-FIT-child.json',dict(identity=self.identity))
        deadline = time.monotonic()+5
        while not (self.stage/'CPU-FIT-start.json').exists():
            assert self.child.poll() is None
            assert time.monotonic()<deadline
            time.sleep(.005)
        return dict(identity=self.identity,clock_owner='HOST_GUARDIAN',new_GPU_bill=False)

    def check(self):
        if self.scenario=='service_failure':
            self.child.wait(timeout=5)
        if self.child.poll() is not None:
            raise RuntimeError('CPU fixture original FIT service failure')
        assert observe_original_process(self.identity)['original_live'] is True

    def close(self):
        if self.child is None:
            return dict(complete=True,kind='SERVICE_NOT_STARTED',new_GPU_bill=False)
        create_record(self.stage/'CPU-FIT-stop.json',dict(identity=self.identity))
        try:
            self.child.wait(timeout=5)
        finally:
            stop_original(self.child,self.identity)
        assert observe_original_process(self.identity)['original_live'] is False
        if self.scenario=='cleanup_unknown':
            raise OriginalQueryUnknown('CPU fixture FIT cleanup witness unavailable')
        closed = dict(complete=True,kind='CPU_ORIGINAL_SERVICE_TERMINAL',identity=self.identity,
            exit_code=self.child.returncode,ended_monotonic=time.monotonic(),new_GPU_bill=False)
        create_record(self.stage/'CPU-FIT-closed.json',closed)
        return closed


def run_service(stage):
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    create_record(stage/'CPU-FIT-start.json',dict(identity=bind_original_process(os.getpid()),CPU_fixture_only=True))
    if read_record(stage/'CPU-fit-scenario.json')['scenario']=='service_failure':
        time.sleep(.03)
        raise SystemExit(7)
    deadline=time.monotonic()+20
    while not (stage/'CPU-FIT-stop.json').exists():
        assert time.monotonic()<deadline
        time.sleep(.01)


if __name__=='__main__':
    role,stage=sys.argv[1],Path(sys.argv[2])
    assert read_record(stage/'CPU-scenario.json')['CPU_fixture_only'] is True
    if role=='FIT_service':
        run_service(stage)
    elif role=='guardian':
        allocate=guardian.allocate
        def with_fit(*args,**kwargs):
            return allocate(*args,**kwargs,fit_service=CPUService(stage))
        guardian.allocate=with_fit
        original.guardian(stage)
    else:
        {'cli':original.cli,'supervisor':original.supervise,'runner':original.runner}[role](stage)
