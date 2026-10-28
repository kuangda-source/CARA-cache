"""No Torch, GPU mode or Docker calls: real CPU-child allocation controls."""
import argparse
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def main():
    p=argparse.ArgumentParser()
    for name in ('assets','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile','scope','manifest-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original allocation CPU proof')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('Allocation CPU tests must hide all GPUs')
    os.nice(10);started,cpu=time.monotonic(),time.process_time()
    original_run,original_popen=subprocess.run,subprocess.Popen
    commands=[]
    def cpu_child(command,*a,**kw):
        if (not isinstance(command,list) or Path(command[0]).resolve()!=Path(sys.executable).resolve()
                or kw.get('shell') or '--gpus' in command):
            raise ValueError('Only the declared CPU Python child may start')
        commands.append(list(command))
        return original_popen(command,*a,**kw)
    def no_hardware(*a,**kw):raise RuntimeError('CPU allocation proof forbids real hardware/Docker commands')
    subprocess.Popen,subprocess.run=cpu_child,no_hardware
    log=io.StringIO()
    try:
        import test_sq_gpu_allocation_r1 as units
        tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(units))
    finally:subprocess.Popen,subprocess.run=original_popen,original_run
    scope=json.loads((ROOT/args.scope).read_text())
    if not tests.wasSuccessful() or tests.testsRun!=12 or tests.skipped:
        raise ValueError('Actual Linux allocation controls failed: '+log.getvalue())
    if len(commands)!=7 or any(e['process'].poll() is None for e in units.EVENTS):
        raise ValueError('Exact seven CPU children must all be terminal')
    if 'torch' in sys.modules:raise ValueError('This allocation proof may not import Torch')
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    result=dict(status='SQ_FULL_ALLOCATION_CPU_PASS_STUB_HARDWARE_NOT_GPU_READY',profile=args.profile,scope=scope,
        unit_controls=dict(tests=tests.testsRun,skipped=len(tests.skipped),log=log.getvalue()),
        actual_Linux_CPU_children_started=len(commands),all_CPU_children_exited=True,
        CPU_child_exit_codes=[e['process'].returncode for e in units.EVENTS],
        actual_platform=dict(system=platform.system(),machine=platform.machine()),
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=child.ru_utime+child.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        hardware_modes_and_container_observations='EXPLICIT_SYNTHETIC_CPU_STUBS',
        all_bill_times_in_tests_are_synthetic=True,Torch_imported=False,real_hardware_calls=False,
        Q1_correction_integrated=False,S_GPU_entry_integrated=False,
        original_Q1_f3_launch_readiness_withdrawn=True,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
