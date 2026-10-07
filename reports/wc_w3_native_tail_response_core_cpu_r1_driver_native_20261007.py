
import hashlib,json,os,pathlib,subprocess,time
stage=pathlib.Path(__file__).parent;binding=json.loads((stage/'manifest.json').read_text());root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');base=root/binding['base_stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state={'status':'NATIVE_TAIL_AFFECTED_CORE_CPU_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':binding['source_revision'],'started_unix':time.time(),'GPU_submissions':0,'CUDA_initialized':'PENDING_ACTUAL_CHECK','payload_sha256':binding['new_payload_sha256'],'base_payload_sha256':binding['base_payload_sha256'],'upstream_sha256':binding['upstream_source_sha256'],'budget_before_sha256':sha(root/'reports/budget.json')}
def save():
 p=stage/'receipt.tmp';p.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');p.replace(stage/'receipt.json')
save();started=time.monotonic()
try:
 for n,d in binding['base_payload_sha256'].items(): assert sha(base/n)==d,n
 for n,d in binding['new_payload_sha256'].items():assert sha(stage/n)==d,n
 for n,d in binding['upstream_source_sha256'].items():assert sha(root/'runtime'/n)==d,n
 python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
 command=[python,'-u',str(stage/'scripts/check_wc_w3_native_tail_core_cpu.py'),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'core-result.json')]
 state['command']=command;save()
 with (stage/'core.log').open('x') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=root/'runtime',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=str(stage/'src'),WC_NATIVE_TAIL_CPU_ATTEMPTS=str(stage/'attempts.json')))
  state['child_pid']=child.pid;save();state['exit_code']=child.wait()
 assert state['exit_code']==0,'Actual core fixture failed; retain log and partial attempts'
 result=json.loads((stage/'core-result.json').read_text());assert result['CUDA_initialized'] is False and result['GPU_submissions']==0
 state.update(status='NATIVE_TAIL_ACTUAL_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU',CUDA_initialized=False,result_sha256=sha(stage/'core-result.json'),attempts_sha256=sha(stage/'attempts.json'),counts=[result['complete_CPU_parents'],result['complete_CPU_suffixes'],result['mock_outputs_not_videos']],failure_cases=result['failures_retained'],mutation_refusals=result['raw_mutation_refusals'],tail_changes=result['deliberate_native_tail_action_changes'])
except BaseException as error:
 state.update(status='NATIVE_TAIL_AFFECTED_CORE_CPU_TECH_BLOCKED_NOT_METHOD_FAILURE',error_type=type(error).__name__,error=str(error))
 raise
finally:
 state['CPU_wall_seconds']=time.monotonic()-started;state['ended_unix']=time.time()
 state['budget_after_sha256']=sha(root/'reports/budget.json');state['budget_unchanged']=state['budget_after_sha256']==state['budget_before_sha256']
 state['new_payload_after_sha256']={n:sha(stage/n) for n in binding['new_payload_sha256']}
 state['base_payload_after_sha256']={n:sha(base/n) for n in binding['base_payload_sha256']}
 state['upstream_after_sha256']={n:sha(root/'runtime'/n) for n in binding['upstream_source_sha256']}
 if (stage/'attempts.json').exists():state['attempts_sha256']=sha(stage/'attempts.json')
 save()
