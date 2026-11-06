
import hashlib,json,os,pathlib,subprocess,time
stage=pathlib.Path(__file__).parent;M=json.loads((stage/'manifest.json').read_text());root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');base=root/M['base_stage'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state={'status':'NATIVE_RESPONSE_ONSET_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':M['source_revision'],'started_unix':time.time(),'steps':[],'GPU_submissions':0,'payload_sha256':M['all_payload_sha256'],'upstream_sha256':M['upstream_source_sha256'],'budget_before_sha256':sha(root/'reports/budget.json'),'CUDA_initialized':'PENDING_ACTUAL_IMPORT'}
def save():
 p=stage/'receipt.tmp';p.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');p.replace(stage/'receipt.json')
save();started=time.monotonic()
try:
 assert json.loads((stage/'onset-config.json').read_text())['run_id']==M['run_id']
 python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
 runner=[python,'-u',str(stage/'scripts/run_wc_w3_native_response_onset.py'),'--project',str(root),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(root/'outputs'/M['run_id']/'diagnostic')]
 commands=[('draft',runner+['--draft-check']),('contract',[python,str(stage/'tests/check_rv0_native_onset_production_cpu.py'),'--stage',str(stage)]),('validate',runner+['--validate-only']),('import',runner+['--cpu-import-check'])]
 for label,command in commands:
  step={'label':label,'command':command,'status':'STARTED','started_unix':time.time()};state['steps'].append(step);save()
  with (stage/(label+'.log')).open('x') as log:
   child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=root/'runtime',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=str(stage/'src')))
   step['pid']=child.pid;save();step['exit_code']=child.wait()
  step.update(status='EXITED',wall_seconds=time.time()-step['started_unix']);save()
  assert step['exit_code']==0,label+' failed; retain original receipt and logs'
 assert json.loads((stage/'import.log').read_text().strip().splitlines()[-1])['cuda_initialized'] is False
 state.update(status='NATIVE_RESPONSE_ONSET_ACTUAL_PRODUCTION_CPU_SOURCE_ASSETS_IMPORT_PASS_NOT_GPU',exit_code=0,CUDA_initialized=False)
except BaseException as error:
 state.update(status='NATIVE_RESPONSE_ONSET_PRODUCTION_CPU_TECH_BLOCKED_NOT_METHOD_FAILURE',exit_code=1,error_type=type(error).__name__,error=str(error));raise
finally:
 state['CPU_wall_seconds']=time.monotonic()-started;state['ended_unix']=time.time()
 state['payload_after_sha256']={n:sha(stage/n) for n in M['all_payload_sha256']}
 state['base_payload_after_sha256']={n:sha(base/n) for n in M['base_payload_sha256']}
 state['upstream_after_sha256']={n:sha(root/'runtime'/n) for n in M['upstream_source_sha256']}
 state['budget_after_sha256']=sha(root/'reports/budget.json');state['budget_unchanged']=state['budget_before_sha256']==state['budget_after_sha256']
 save()
