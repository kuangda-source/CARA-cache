#!/usr/bin/env python3
"""Queue one approved complete MF-00 card; no GPU reservation while waiting.

This is a single-run resource waiter, not a recurring scheduler. A stopped or
ambiguous admission must be inspected rather than relaunched. The actual frozen
dispatcher repeats all source, lock, GPU, budget and selected-CPU checks.
"""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

PINNED='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def main():
    old=Path('scripts/launch_wc_mf00_interface.py').read_text()
    tree=ast.parse(old)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    node=next(n for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets))
    launch=json.loads(Path('reports/wc_mf00_interface_selected_cpu_r1_launch_20261010.json').read_text())
    proof=json.loads(Path('reports/wc_mf00_interface_selected_cpu_r1_terminal_20261010_capture.json').read_text())
    assert proof['exit_code']==0 and proof['local_native_bytes_binding_scope_and_request_verified']
    assert old.encode()==subprocess.check_output(['git','show',launch['source_revision']+':scripts/launch_wc_mf00_interface.py'])
    driver=Path('scripts/supervise_wc_mf00_interface_post_cpu.py').read_bytes()
    assert driver==subprocess.check_output(['git','show',launch['source_revision']+':scripts/supervise_wc_mf00_interface_post_cpu.py'])
    source=eval(compile(ast.Expression(node.value),'<source-bound MF00 dispatch expression>','eval'),
                {'launch':launch,'proof':proof,'driver':driver,'base64':base64,'repr':repr})
    original="command=['python3',str(stage/'scripts/supervise_wc_mf00_interface.py')"
    replacement="command=["+repr(PINNED)+",str(stage/'scripts/supervise_wc_mf00_interface.py')"
    assert source.count(original)==1
    dispatch=source.replace(original,replacement)
    assert dispatch.replace(replacement,original)==source
    ast.parse(dispatch)
    packet={'source_revision':launch['source_revision'],
        'waiter_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'pinned_python':PINNED,'dispatch_source':dispatch,
        'dispatch_source_sha256':hashlib.sha256(dispatch.encode()).hexdigest(),
        'dispatcher_inverse_equal':True,'scope':json.loads(Path('configs/wc_mf00_interface_selected_r1_20261010.json').read_text())['preregistration']['scope_counts'],
        'forecast_complete_GPUh':1.707952636679945}
    # This self-contained worker reads resources and invokes one source-bound
    # admission. No torch import, shared-lock hold or budget mutation in waiting.
    worker=r'''
import fcntl,hashlib,json,os,pathlib,subprocess,time
P=json.loads(pathlib.Path(__file__).with_name('packet.json').read_text())
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=pathlib.Path(__file__).parent;receipt=stage/'receipt.json'
uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
out=root/'outputs/wc-mf00-interface-r1';post=root/'.sync/wc-mf00-interface-post-cpu-r1-20261010'
assert hashlib.sha256(P['dispatch_source'].encode()).hexdigest()==P['dispatch_source_sha256']
r={'status':'WAITING_OTHER_GPU_PROCESS_NO_GPU_RESERVATION','pid':os.getpid(),'started_unix':time.time(),
   'source_revision':P['source_revision'],'waiter_revision':P['waiter_revision'],
   'dispatch_source_sha256':P['dispatch_source_sha256'],'scope':P['scope'],
   'forecast_complete_GPUh':P['forecast_complete_GPUh'],'GPU_submissions_by_waiter':0,'ledger_written_by_waiter':False}
def save():
 tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(receipt)
save()
try:
 while True:
  b=json.loads((root/'reports/budget.json').read_text())
  assert b['cap_gpu_hours']==77.89524658965853 and b['automatic_single_job_gpu_hours']==4
  assert b['cap_gpu_hours']-b['used_gpu_hours']>=P['forecast_complete_GPUh']
  assert not out.exists() and not post.exists(), 'Run identity already exists; inspect, never replay'
  apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
  pids=[int(x.split(',')[1]) for x in apps.splitlines() if x.split(',')[0].strip()==uuid]
  row=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
  lock_free=False
  with (root/'.sync/f1.lock').open('a+') as lock:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);lock_free=True;fcntl.flock(lock,fcntl.LOCK_UN)
   except BlockingIOError:pass
  r.update(observed_unix=time.time(),actual_other_gpu_pids=pids,
       actual_other_gpu_pids_live=[pid for pid in pids if pathlib.Path('/proc/'+str(pid)).exists()],
       memory_used_mib=int(row[1]),shared_lock_available=lock_free,
       settled_used_gpu_hours=b['used_gpu_hours'],gpu_jobs_launched=b['gpu_jobs_launched']);save()
  if pids or int(row[1])>1024 or not lock_free or any('inflight' in k for k in b):time.sleep(15);continue
  assert row[0].strip()==uuid and row[2].strip()=='8.6'
  r['status']='FRESH_COMPLETE_SOURCE_BOUND_ADMISSION_RUNNING';save()
  child=subprocess.Popen([P['pinned_python'],'-'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
       text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  r['admission_child_pid']=child.pid;save()
  stdout,stderr=child.communicate(P['dispatch_source'])
  (stage/'admission.stdout').write_text(stdout);(stage/'admission.stderr').write_text(stderr)
  r['admission_exit_code']=child.returncode
  if child.returncode:
   # No retry after any attempted admission. Read authoritative handles first.
   r.update(status='ADMISSION_FAILED_OR_AMBIGUOUS_NEEDS_HANDLE_INSPECTION',error=stderr[-3000:],exit_code=1);save();break
  actual=json.loads(stdout)
  assert actual['run_id']=='wc-mf00-interface-r1' and actual['planned_scope']==P['scope']
  (stage/'GPU-launch.json').write_text(json.dumps(actual,indent=2)+'\n')
  r.update(status='COMPLETE_GPU_CARD_DISPATCHED_ONCE_POST_CPU_BOUND',actual_launch=actual,
       GPU_submissions_by_waiter=1,exit_code=0);save();break
except BaseException as error:
 r.update(status='RESOURCE_WAITER_STOPPED_REQUIRES_INSPECTION',error=str(error),error_type=type(error).__name__,exit_code=1);save()
raise SystemExit(r['exit_code'])
'''
    ast.parse(worker)
    request={'packet':packet,'worker':worker,'worker_sha256':hashlib.sha256(worker.encode()).hexdigest()}
    remote='P='+repr(request)+'\n'+r'''
import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/'.sync/wc-mf00-interface-resource-wait-r1-20261010'
assert not stage.exists() and not (root/'outputs/wc-mf00-interface-r1').exists()
assert hashlib.sha256(P['worker'].encode()).hexdigest()==P['worker_sha256']
stage.mkdir();(stage/'worker.py').write_text(P['worker']);(stage/'packet.json').write_text(json.dumps(P['packet'],indent=2)+'\n')
with (stage/'worker.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/'worker.py')],stdout=log,stderr=subprocess.STDOUT,
      env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
launch={'stage':str(stage),'waiter_pid':child.pid,'worker_sha256':P['worker_sha256'],
 'source_revision':P['packet']['source_revision'],'waiter_revision':P['packet']['waiter_revision'],
 'dispatch_source_sha256':P['packet']['dispatch_source_sha256'],'GPU_submissions_by_queue':0,
 'ledger_written_by_queue':False,'created_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=remote,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    result=json.loads(call.stdout)
    target=Path('reports/wc_mf00_interface_resource_queue_launch_20261010.json');assert not target.exists()
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
