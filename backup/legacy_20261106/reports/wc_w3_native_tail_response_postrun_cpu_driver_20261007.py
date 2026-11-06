
import hashlib,json,os,pathlib,subprocess,time
post=pathlib.Path(__file__).parent;binding=json.loads((post/'binding.json').read_text())
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/binding['stage'];out=root/'outputs'/binding['run_id']
python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
state={'status':'WAITING_ORIGINAL_GPU_TERMINAL_NOT_CPU_AUDIT_OR_SCORE','pid':os.getpid(),'run_id':binding['run_id'],
 'source_revision':binding['source_revision'],'started_unix':time.time(),'original_gpu_pids':binding['pids'],
 'GPU_submissions':0,'formal_RV_labels':False,'steps':[],'driver_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
def save():
 p=post/'continuation.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(post/'continuation.json')
def check_sources():
 for rel,digest in binding['source_sha256'].items():
  assert hashlib.sha256((stage/rel).read_bytes()).hexdigest()==digest,rel
def original_handles():
 live=[]
 for pid,name in zip(binding['pids'],['supervise_wc_w3_native_tail_response.py','run_wc_w3_native_tail_response.py']):
  p=pathlib.Path('/proc/'+str(pid))
  if p.exists():
   cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
   if cmd:
    assert str(stage) in cmd and name in cmd and binding['source_revision'] in cmd,'Original PID identity changed'
   live.append(pid)
 return live
save()
try:
 check_sources()
 while True:
  s=json.loads((out/'supervisor.json').read_text())
  assert s['pid']==binding['pids'][0] and s['child_pid']==binding['pids'][1] and s['source_revision']==binding['source_revision'] and s['run_id']==binding['run_id']
  live=original_handles()
  if s['status']=='GPU_W3_NATIVE_TAIL_RUNNING':
   assert live,'Original handles absent with nonterminal receipt; preserve and inspect'
  elif s['status']=='EXITED_REQUIRES_RESULT_AUDIT':
   assert s['exit_code']==0 and 'settlement_error' not in s
   if not live:break
  else:
   raise RuntimeError('Original GPU terminal is not successful: '+s['status'])
  time.sleep(20)
 state.update(status='ORIGINAL_GPU_TERMINAL_CPU_AUDIT_PENDING',GPU_terminal_observed_unix=time.time());save()
 commands=[('terminal_audit',[python,'-u',str(stage/'scripts/audit_wc_w3_native_tail_response_terminal.py'),'--project',str(root),'--stage',str(stage),'--expected-source',binding['source_revision'],'--output',str(post/'terminal-audit.json')]),
 ('full93_lpips',[python,'-u',str(stage/'scripts/analyze_wc_w3_native_tail_response_lpips_cpu.py'),'--project',str(root),'--stage',str(stage),'--receipt',str(out/'diagnostic/receipt.json'),'--terminal-audit',str(post/'terminal-audit.json'),'--output',str(post/'lpips-score.json')])]
 for name,command in commands:
  check_sources();step={'name':name,'argv':command,'started_unix':time.time(),'status':'CPU_RUNNING'};state['steps'].append(step);state['status']='CPU_'+name.upper()+'_RUNNING';save()
  with (post/(name+'.log')).open('x') as log:
   child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=root/'runtime',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
   step['pid']=child.pid;save();code=child.wait()
  step.update(exit_code=code,ended_unix=time.time(),status='CPU_EXITED');step['wall_seconds']=step['ended_unix']-step['started_unix'];save()
  if code:raise RuntimeError(name+' failed; original receipt and log retained, no automatic retry')
 score=json.loads((post/'lpips-score.json').read_text());assert len(score['pairs'])==5 and len(score['signed_diagnostics'])==2 and score['reused_existing_loss_count']==3 and score['CUDA_initialized'] is False
 assert score['status']=='NATIVE_TAIL_FULL93_FIVE_LOSSES_THREE_REUSED_TWO_NEW_AND2_SIGNED_POLICY_EFFECTS_NOT_RV_LABELS'
 state.update(status='CPU_TERMINAL_AUDIT_AND_COMPLETE_FULL93_SCORES_DONE_REQUIRES_RESEARCH_INTERPRETATION',score_sha256=hashlib.sha256((post/'lpips-score.json').read_bytes()).hexdigest(),terminal_audit_sha256=hashlib.sha256((post/'terminal-audit.json').read_bytes()).hexdigest())
except BaseException as error:
 state.update(status='CPU_CONTINUATION_TECH_BLOCKED_ORIGINAL_ARTIFACTS_RETAINED',error_type=type(error).__name__,error=str(error));raise
finally:
 state['ended_unix']=time.time();save()
