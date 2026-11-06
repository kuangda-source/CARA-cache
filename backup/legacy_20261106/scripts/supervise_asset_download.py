"""One bounded CPU-only public asset acquisition with durable process receipts."""
import argparse, fcntl, json, os, signal, subprocess, time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--python',required=True);p.add_argument('--range-download',action='store_true')
a=p.parse_args();project=a.project.resolve();manifest=a.manifest.resolve();output=a.output.resolve()
protocol=json.loads(manifest.read_text());seconds=protocol['cpu_download_seconds_cap']
if protocol['endpoint'] not in ['https://huggingface.co','https://hf-mirror.com'] or seconds not in [1200,3600]:raise ValueError('Unsupported public acquisition endpoint/cap')
if protocol['endpoint']=='https://hf-mirror.com' and protocol.get('intended_role')!='Small development VQA judge, not paper Qwen3-VL235B or final Joint confirmation':raise ValueError('Mirror permitted only for this hash-locked public development judge')
if a.range_download and (protocol.get('download_strategy')!='bounded_http_ranges' or protocol['endpoint']!='https://huggingface.co' or seconds!=3600):raise ValueError('Range downloader requires pinned official L0 CPU protocol')
lock_path=project/'.sync/judge-download.lock';lock_path.parent.mkdir(parents=True,exist_ok=True);lock=lock_path.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
output.mkdir(parents=True,exist_ok=False)
state={'pid':os.getpid(),'status':'PREPARING','started_unix':time.time(),'gpu_workload_started':False,'max_cpu_wall_seconds':seconds}
def save():
    tmp=output/'supervisor.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(output/'supervisor.json')
def stop(child):
    if child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
def terminate(*args):raise SystemExit('CPU acquisition supervisor SIGTERM')
signal.signal(signal.SIGTERM,terminate);save()
command=['timeout','--kill-after=10',str(seconds-10),a.python,str(project/('scripts/download_l0_adapter_ranges.py' if a.range_download else 'scripts/download_auxiliary.py')),'--manifest',str(manifest),'--cache',str(project/'hfhub'),'--receipt',str(output/'download.json')]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',HF_HUB_DISABLE_XET='1',PYTHONPATH=str(project/'src'))
child=None;started=time.time()
try:
    with (output/'download.log').open('x') as log:
        child=subprocess.Popen(command,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,pass_fds=(lock.fileno(),))
        state.update(status='RUNNING',child_pid=child.pid,command=command);save()
        while child.poll() is None:
            if time.time()-started>=seconds-10:stop(child);state['stop_reason']='CPU_DOWNLOAD_TIMEOUT';break
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
except BaseException as e:
    state.update(status='SUPERVISOR_ERROR',error=type(e).__name__+': '+str(e));raise
finally:
    if child is not None:stop(child);state['exit_code']=child.returncode
    state['ended_unix']=time.time();state['wall_seconds']=time.time()-started
    if state['status']!='SUPERVISOR_ERROR':state['status']='DOWNLOAD_EXITED_REQUIRES_INTEGRITY_CHECK' if child is not None and child.returncode==0 else 'DOWNLOAD_FAILED_OR_TIMEOUT'
    save()
