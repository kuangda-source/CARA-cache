"""Original host handle: A -> release/settle -> CPU freeze -> fresh B -> CPU scores.

Credential stays in anonymous stdin/memory. No GPU retry, migration or new scope.
"""
import argparse,json,os,signal,subprocess,sys,time,shutil
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
 from wcomr.wc73_execution_r1 import validate,read,sha,RUN,Pool
 from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
 from wcomr.history104_storage_r2 import storage_for
 c,reg,auth=validate(a.project,a.stage);secret=json.load(sys.stdin);assert set(secret)=={'sudo_password'}
 assert auth['host']=='four_card','This controller binds the central Ada ledger; A6000 needs the central external-host bridge before dispatch'
 out=a.project/'outputs'/RUN;storage=storage_for(a.stage)
 state=dict(status='ADMITTING_A',identity=process_identity(os.getpid()),started_unix=time.time(),stage=str(a.stage),source_revision=reg['source_revision'],run_id=RUN,launch_id=auth['launch_id'])
 child=None
 def save():storage.persist('guardian',a.stage/'whole-controller.json',state,atomic_json)
 def stop(signum,frame):raise KeyboardInterrupt('Original whole controller interrupted')
 signal.signal(signal.SIGTERM,stop);save()
 def run(cmd,label,stdin=None,timeout=None):
  nonlocal child
  with (a.stage/(label+'.log')).open('x') as log:
   child=subprocess.Popen(cmd,stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   state.update(active_child=process_identity(child.pid),active_step=label);save()
   if stdin:child.stdin.write(json.dumps(stdin).encode());child.stdin.close()
   code=child.wait(timeout=timeout)
   if code:raise RuntimeError(label+' failed: '+str(code))
 def gpu(stage,phase):
  state['status']=phase+'_GPU_ADMISSION_OR_RUNNING';save()
  run([sys.executable,str(stage/'scripts/wc_wc73_host_guardian_r1.py'),'--project',str(a.project),'--stage',str(stage)],phase+'-guardian',stdin=secret,timeout=({'A':5,'B':7}[phase]*3600+120))
  receipt=read(stage/'pg-host-guardian.json')
  assert receipt.get('container_exit_code')==0 and receipt['mode_restoration']['restored'],'GPU guardian did not confirm success and restoration'
 def cpu(stage,phase):
  state['status']=phase+'_CPU_AFTER_GPU_RELEASE';save()
  from four_card_bank24_execution_tools_r1 import process_environment
  from four_card_policy_assets_port_r1 import container_command
  cmd=container_command(a.project,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(a.project,stage/'CPU-caches'),os.getuid(),os.getgid())
  cmd[cmd.index('--name')+1]=stage.name+'-post-cpu';cmd[cmd.index('--cpus')+1]='4';cmd[cmd.index('--memory')+1]='12g'
  at=cmd.index('--entrypoint');cmd[at:at]=['--cpuset-cpus',auth['CPU_score_cpuset'],'-v',str(out)+':'+str(out)+':rw','-v',str(storage.journal.path)+':'+str(storage.journal.path)+':rw']
  for i,x in enumerate(cmd):
   if x.startswith(('OMP_NUM_THREADS=','OPENBLAS_NUM_THREADS=')):cmd[i]=x.split('=')[0]+'=4'
  cmd=cmd[:cmd.index('--entrypoint')+3]+[str(stage/'scripts/postprocess_cara_wc73_r1.py'),'--project',str(a.project),'--stage',str(stage)]
  run(cmd,phase+'-CPU',timeout=(3600 if phase=='A' else 21600))
 try:
  gpu(a.stage,'A');cpu(a.stage,'A')
  freeze=read(out/'frozen-selection.json');assert freeze['phase_A_GPU_released'] and freeze['scope_sha256']==c['scope_sha256']
  bstage=a.stage.with_name(a.stage.name+'-B');bstage.mkdir()
  for n in reg['payload_sha256']:
   dest=bstage/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.stage/n,dest)
  breg={**reg,'stage':str(bstage),'phase':'B'};atomic_json(bstage/'registration.json',breg)
  for n in ('execution-CPU-proof.json','history104-storage.json'):shutil.copyfile(a.stage/n,bstage/n)
  bauth={**auth,'phase':'B','registration_sha256':sha(bstage/'registration.json'),'frozen_selection_sha256':sha(out/'frozen-selection.json')};atomic_json(bstage/'pg-GPU-authorization.json',bauth)
  state['B_stage']=str(bstage);save();gpu(bstage,'B');cpu(bstage,'B')
  state['status']='COMPLETE73_SCORES_PENDING_INDEPENDENT_ACCEPTANCE'
 except BaseException as e:
  state.update(status='STOPPED_NO_REPLAY',error_type=type(e).__name__,error=str(e))
  if child and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=60)
   except subprocess.TimeoutExpired:state['child_cleanup_unconfirmed']=True
  # CPU Docker CLI death does not stop container; stop only our exact named and label-bound CPU container.
  for stage in (a.stage,a.stage.with_name(a.stage.name+'-B')):
   name=stage.name+'-post-cpu';r=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
   if r.returncode==0:
    info=json.loads(r.stdout)[0]
    if info['Config']['Labels'].get('wcomr.manifest')==sha(stage/'registration.json') and info['State']['Running']:
     subprocess.run(['docker','stop','--time','15',name],capture_output=True,timeout=30)
  pool=Pool(a.project);v=pool.read();j=v['jobs'].get(RUN)
  # Remaining B reservation can be cancelled only when A is settled and B never acquired GPU.
  if j and j['status']=='RESERVED_OR_RUNNING' and j['billed_limit_GPUh']==7 and not (out/'B-supervisor.json').exists():
   receipt=dict(reason=state['status'],B_GPU_started=False,actual_GPUh=0,ended_unix=time.time());atomic_json(out/'B-not-started-billing.json',receipt);pool.settle(RUN,0,sha(out/'B-not-started-billing.json'))
  raise
 finally:secret.clear();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
