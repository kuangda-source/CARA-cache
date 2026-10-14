"""Server-side child completion hook; no model or GPU submission."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def paths(stage,project):
    return Path(project)/'outputs/wc-w3-label-expldev8-parent18-local64-full864-r1',[
        sys.executable,str(Path(stage)/'scripts/postprocess_wc_w3_label64_full864_cpu_r1.py'),
        '--project',str(project),'--stage',str(stage),'--output',str(Path(stage)/'CPU-final-results.json')]


def alive(pid):
    p=Path('/proc')/str(pid)/'stat'
    try:return p.read_text().split(') ',1)[1].split()[0] not in ('Z','X')
    except FileNotFoundError:return False


def main():
    p=argparse.ArgumentParser();p.add_argument('--supervisor-pid',type=int,required=True)
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    while alive(a.supervisor_pid):time.sleep(5)
    output,command=paths(a.stage,a.project);dest=a.stage/'post-CPU-exit.json';assert not dest.exists()
    if not (output/'supervisor.json').exists():
        dest.write_text(json.dumps({'status':'W3_ADMISSION_FAILED_NO_POST_OR_RESTART','GPU_submissions':0,'ended_unix':time.time()})+'\n');return
    sup=json.loads((output/'supervisor.json').read_text())
    assert sup['pid']==a.supervisor_pid and sup['status']=='W3_LABEL64_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT'
    assert not alive(sup['child_pid'])
    with (a.stage/'post-CPU.log').open('x') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'CUDA_VISIBLE_DEVICES':''})
    dest.write_text(json.dumps({'status':'W3_LABEL64_FULL_POST_CPU_TERMINAL','exit_code':result.returncode,
        'GPU_submissions':0,'ledger_written':False,'ended_unix':time.time()})+'\n')


if __name__=='__main__':main()
