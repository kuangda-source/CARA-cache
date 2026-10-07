"""Wait for the bound original GPU job, then audit/score it once on CPU."""
import hashlib,json,os,pathlib,subprocess,time
post=pathlib.Path(__file__).parent;binding=json.loads((post/'binding.json').read_text())
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/binding['stage'];out=root/'outputs'/binding['run_id']
state={'status':'WAITING_ORIGINAL_D46_GPU_NOT_SCIENTIFIC_RESULT','pid':os.getpid(),'run_id':binding['run_id'],'source_revision':binding['source_revision'],'original_gpu_pids':binding['pids'],'GPU_submissions':0,'steps':[],'started_unix':time.time(),'driver_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
def save():
    p=post/'continuation.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(post/'continuation.json')
def check_sources():
    for name,digest in binding['source_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest,name
def handles():
    live=[]
    for pid,name in zip(binding['pids'],['supervise_wc_w3_d46_fresh_seeds.py','run_wc_w3_d46_fresh_seeds.py']):
        p=pathlib.Path('/proc/'+str(pid))
        if p.exists():
            command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
            if command:assert str(stage) in command and name in command and binding['source_revision'] in command,'Original PID identity changed'
            live.append(pid)
    return live
save()
try:
    check_sources()
    while True:
        sup=json.loads((out/'supervisor.json').read_text());assert sup['pid']==binding['pids'][0] and sup['child_pid']==binding['pids'][1] and sup['source_revision']==binding['source_revision']
        live=handles()
        if sup['status']=='D46_GPU_RUNNING':assert live,'Missing original handles with nonterminal receipt'
        elif sup['status']=='EXITED_REQUIRES_RESULT_AUDIT':
            assert sup['exit_code']==0,'Original GPU failed; preserve original evidence and actual cost'
            if not live:break
        else:raise RuntimeError('Unexpected original GPU status: '+sup['status'])
        time.sleep(20)
    state.update(status='ORIGINAL_D46_GPU_TERMINAL_CPU_AUDIT_AND_SCORE_PENDING',GPU_terminal_observed_unix=time.time());save();check_sources()
    python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=[python,'-u',str(stage/'scripts/audit_score_wc_w3_d46_seeds_cpu.py'),'--project',str(root),'--stage',str(stage),'--output',str(post/'audit-score.json')]
    step={'name':'full_terminal_source_cost_state_video_and93frame_lpips','status':'CPU_RUNNING','argv':command,'started_unix':time.time()};state['steps'].append(step);state['status']='D46_CPU_AUDIT_AND_FULL93_SCORING_RUNNING';save()
    with (post/'audit-score.log').open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=root/'runtime',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
        step['pid']=child.pid;save();code=child.wait()
    step.update(status='CPU_EXITED',exit_code=code,ended_unix=time.time());step['wall_seconds']=step['ended_unix']-step['started_unix'];save()
    assert code==0,'CPU audit/scoring failed; original receipt/log retained, no automatic rerun'
    result=json.loads((post/'audit-score.json').read_text());assert result['status']=='D46_TWO_REGISTERED_SEEDS_FULL_CPU_AUDIT_AND_AVAILABLE_LOSSES_COMPLETE_NOT_CONF' and result['CUDA_initialized'] is False and [c['seed'] for c in result['cases']]==[1,2]
    state.update(status='D46_ORIGINAL_GPU_AND_CPU_FULL93_SCORING_COMPLETE_RESEARCH_INTERPRETATION_PENDING',result_sha256=hashlib.sha256((post/'audit-score.json').read_bytes()).hexdigest())
except BaseException as error:
    state.update(status='D46_POSTRUN_CPU_TECH_BLOCKED_ORIGINAL_EVIDENCE_RETAINED',error_type=type(error).__name__,error=str(error));raise
finally:
    state['ended_unix']=time.time();save()
