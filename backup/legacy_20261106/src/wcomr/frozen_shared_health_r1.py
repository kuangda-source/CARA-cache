"""N07's one midpoint technical snapshot, without scientific result fields."""
import collections
import inspect
import json

RUN='wc-paper-n07-frozen-shared180-r1'
CONFIG='configs/wc_paper_N07_frozen_shared_production_r1_20261016.json'


def bind(launch,admission,admitted,schedule):
    keys=('source_revision','launch_id','gpu_uuid')
    if (launch['run_id']!=RUN or schedule['original_run_id']!=RUN
            or any(admission[k]!=launch[k] for k in keys)
            or any(schedule[k]!=launch[k] for k in ('source_revision','launch_id'))
            or schedule['original_gpu_uuid']!=launch['gpu_uuid']
            or admitted['launch']!=launch or not admission['GPU_admitted']
            or schedule['original_final_earliest_unix']!=launch['next_check_not_before_unix']
            or launch['scope_counts']['total_paths']!=180
            or launch['scope_counts']['full_warmup_paths']!=20
            or launch['scope_counts']['scientific_paths']!=160):
        raise ValueError('Bind the original approved N07 launch and unchanged two collection times')
    processes=admitted['original_processes']
    expected={name:dict(pid=processes[key]['pid'],start_ticks=processes[key]['start_ticks'])
        for name,key in (('supervisor','supervisor_pid'),('runner','child_pid'),('CPU_post','post_watcher_pid'))}
    if (expected['supervisor']['pid']!=admission['supervisor_pid']
            or expected['runner']['pid']!=admission['runner_pid']
            or expected['CPU_post']['pid']!=admission['post_watcher_pid']
            or any(type(v[k]) is not int or v[k]<=0 for v in expected.values() for k in ('pid','start_ticks'))):
        raise ValueError('Every original process needs its accepted PID and start ticks')
    check=next(r for r in schedule['scheduled_checks'] if r['kind']=='READONLY_MIDPOINT_HEALTH')
    return dict(project=launch['project'],stage=launch['stage'],run_id=RUN,
        source_revision=launch['source_revision'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],
        config_sha256=launch['config_sha256'],registration_sha256=launch['registration_sha256'],
        scope_counts=launch['scope_counts'],processes=expected,
        health_not_before_unix=check['unix'],final_not_before_unix=launch['next_check_not_before_unix'])


def check_window(expected,now):
    if now<expected['health_not_before_unix']:
        raise ValueError('Before original midpoint time; no SSH')
    if now>=expected['final_not_before_unix']:
        raise ValueError('Original final ETA reached; use the unchanged terminal collector')


def technical_progress(data):
    rows=data.get('runs',[])
    finished={'COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'}
    known=finished|{'RUNNING','TECH_FAILED','NOT_REACHED'}
    counts=dict(collections.Counter(r.get('status') if r.get('status') in known else 'UNKNOWN' for r in rows))
    sections={}
    for section,total in (('WARMUP',20),('TIMED',160)):
        selected=[r for r in rows if r.get('section')==section]
        sections[section]=dict(registered=total,observed=len(selected),
            terminal_request_outcomes=sum(r.get('status') in finished for r in selected),
            running=sum(r.get('status')=='RUNNING' for r in selected),
            technical_failures=sum(r.get('status')=='TECH_FAILED' for r in selected),
            not_reached=max(0,total-len(selected)))
    allowed={'N07_SHARED180_INITIALIZING_ONE_RESIDENT_MODEL','N07_SHARED180_RUNNING',
        'N07_SHARED180_GPU_COMPLETE_CPU_AUDIT_PENDING','N07_SHARED180_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'}
    return dict(status=data.get('status') if data.get('status') in allowed else 'UNKNOWN_STATUS',
        registered_total=180,observed_positions=len(rows),
        terminal_request_outcomes=sum(r.get('status') in finished for r in rows),
        not_reached=max(0,180-len(rows)),generation_status_counts=counts,sections=sections,
        excess_positions=max(0,len(rows)-180),no_per_method_quality_or_timing_readout=True)


def process_match(actual,expected):
    if actual.get('read_error'):return 'UNKNOWN_READ_ERROR'
    if actual.get('state') is None:return 'ORIGINAL_HANDLE_MISSING'
    if actual.get('start_ticks')!=expected['start_ticks']:return 'PID_REUSED_ORIGINAL_HANDLE_MISSING'
    return 'ORIGINAL_PROCESS_NOT_LIVE' if actual['state'] in ('Z','X') else 'ORIGINAL_PROCESS_LIVE'


def error_labels(text):
    lower=text.lower()
    labels=('out of memory','traceback (most recent call last)','runtimeerror','assertionerror',
        'attributeerror','keyerror','filenotfounderror','no space left','segmentation fault')
    return {label:lower.count(label) for label in labels if label in lower}


def classify(value):
    processes=value['original_processes'];sup=value.get('supervisor',{})
    labels=[tag for record in value.get('bounded_technical_logs',{}).values()
        for tag in record.get('error_labels',{})]
    mismatches=value.get('identity_mismatches',[])
    unknown=any(p['match']=='UNKNOWN_READ_ERROR' for p in processes.values())
    reused=any(p['match']=='PID_REUSED_ORIGINAL_HANDLE_MISSING' for p in processes.values())
    progress=value.get('technical_progress',{})
    if (labels or mismatches or sup.get('child_exit_code') not in (None,0)
            or value.get('CPU_post_exit',{}).get('exit_code') not in (None,0)
            or progress.get('excess_positions',0)>0
            or progress.get('generation_status_counts',{}).get('TECH_FAILED',0)>0):
        return 'TECHNICAL_SIGNAL_NEEDS_DIAGNOSIS'
    live={k:p['match']=='ORIGINAL_PROCESS_LIVE' for k,p in processes.items()}
    settled=value.get('own_budget_job',{}).get('status')=='SETTLED'
    if value.get('CPU_post_exit',{}).get('exit_code')==0 and settled and not any(live.values()):
        return 'ORIGINAL_TECHNICAL_PIPELINE_FINISHED_AWAITING_FINAL_AUDIT'
    if reused:return 'ORIGINAL_PROCESS_IDENTITY_CHANGED_NEEDS_DIAGNOSIS'
    if unknown or value.get('read_errors'):return 'TECHNICAL_STATE_PARTLY_UNKNOWN'
    if live['runner'] and live['supervisor']:return 'ORIGINAL_GPU_JOB_ACTIVE'
    if live['CPU_post'] and settled:
        return 'ORIGINAL_GPU_STAGE_FINISHED_CPU_POST_ACTIVE'
    return 'ORIGINAL_HANDLES_NOT_ACTIVE_TERMINAL_STATE_NOT_YET_CONFIRMED'


def remote_code(expected):
    helpers='\n\n'.join(inspect.getsource(f) for f in
        (technical_progress,process_match,error_labels,classify))
    return 'EXPECTED='+repr(expected)+'\n'+r'''
import collections,fcntl,hashlib,json,pathlib,shutil,subprocess,sys,time
'''+helpers+r'''
now=time.time()
if not EXPECTED['health_not_before_unix']<=now<EXPECTED['final_not_before_unix']:
 raise RuntimeError('Remote midpoint time gate refused; no original files read')
root=pathlib.Path(EXPECTED['project']).resolve();stage=pathlib.Path(EXPECTED['stage']).resolve()
assert root==pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve() and stage.parent==root/'.sync'
assert EXPECTED['run_id']=='wc-paper-n07-frozen-shared180-r1'
out=root/'outputs'/EXPECTED['run_id']
v=dict(status='N07_MIDPOINT_READONLY_TECHNICAL_HEALTH',observed_unix=now,expected=EXPECTED,
 original_processes={},identity_mismatches=[],read_errors=[],files={},bounded_technical_logs={},
 final_scientific_results_read=False,no_quality_or_method_latency_readout=True,
 server_stage_modified=False,ledger_written=False,GPU_submissions=0)
def meta(path):
 if not path.is_file():return dict(path=str(path),exists=False)
 s=path.stat();return dict(path=str(path),exists=True,bytes=s.st_size,modified_unix=s.st_mtime)
def read(role,path):
 info=meta(path);v['files'][role]=info
 if not info['exists']:return {}
 try:
  raw=path.read_bytes();info['sha256']=hashlib.sha256(raw).hexdigest();return json.loads(raw)
 except Exception as error:
  v['read_errors'].append(dict(role=role,error_type=type(error).__name__));return {}
reg=read('registration',stage/'registration.json')
if reg.get('source_revision')!=EXPECTED['source_revision'] or v['files']['registration'].get('sha256')!=EXPECTED['registration_sha256']:
 v['identity_mismatches'].append('registration')
config=read('config',stage/'configs/wc_paper_N07_frozen_shared_production_r1_20261016.json')
if v['files']['config'].get('sha256')!=EXPECTED['config_sha256']:v['identity_mismatches'].append('config')
raw=read('supervisor',out/'supervisor.json')
v['supervisor']={k:raw.get(k) for k in ('status','pid','start_ticks','child_pid','child_exit_code',
 'source_revision','run_id','launch_id','gpu_uuid','config_sha256')}
for name in ('source_revision','run_id','launch_id','gpu_uuid','config_sha256'):
 if raw and raw.get(name)!=EXPECTED[name]:v['identity_mismatches'].append('supervisor_'+name)
for name,wanted in (('pid',EXPECTED['processes']['supervisor']['pid']),
 ('start_ticks',EXPECTED['processes']['supervisor']['start_ticks']),('child_pid',EXPECTED['processes']['runner']['pid'])):
 if raw and raw.get(name)!=wanted:v['identity_mismatches'].append('supervisor_'+name)
runner=read('runner',out/'runner.json')
for role in ('supervisor','runner'):
 if not v['files'][role]['exists']:v['read_errors'].append(dict(role=role,error_type='OriginalFileNotYetAvailable'))
if runner:
 for name in ('source_revision','config_sha256'):
  if runner.get(name)!=EXPECTED[name]:v['identity_mismatches'].append('runner_'+name)
 if runner.get('scope_counts')!=EXPECTED['scope_counts']:v['identity_mismatches'].append('runner_scope')
 v['technical_progress']=technical_progress(runner)
exit=read('CPU_post_exit',stage/'post-CPU-exit.json')
v['CPU_post_exit']={k:exit.get(k) for k in ('status','exit_code')} if exit else {}
if exit and exit.get('original_supervisor')!=EXPECTED['processes']['supervisor']:
 v['identity_mismatches'].append('CPU_post_original_supervisor')
# The scientific final file is only stat'ed. Its contents are never opened.
v['files']['CPU_final_metadata_only']=meta(stage/'CPU-final-results.json')
for name,identity in EXPECTED['processes'].items():
 try:
  p=pathlib.Path('/proc')/str(identity['pid']);f=(p/'stat').read_text().split(') ',1)[1].split()
  actual=dict(pid=identity['pid'],state=f[0],start_ticks=int(f[19]),
   command=(p/'cmdline').read_bytes().replace(bytes([0]),b' ').decode(errors='replace'))
 except FileNotFoundError:actual=dict(pid=identity['pid'],state=None,start_ticks=None,command=None)
 except Exception as error:actual=dict(pid=identity['pid'],read_error=type(error).__name__)
 actual['match']=process_match(actual,identity);v['original_processes'][name]=actual
pool=read('budget_pool',root/'reports/gpu-budget-v2.json')
job=pool.get('jobs',{}).get(EXPECTED['run_id'],{})
if not job:v['read_errors'].append(dict(role='own_budget_job',error_type='OriginalJobNotAvailable'))
v['own_budget_job']={k:job.get(k) for k in ('status','source_revision','launch_id','gpu_uuid',
 'config_sha256','billed_limit_GPUh','actual_GPUh')}
for name in ('source_revision','launch_id','gpu_uuid','config_sha256'):
 if job and job.get(name)!=EXPECTED[name]:v['identity_mismatches'].append('budget_job_'+name)
lock=root/'.sync/gpu-locks'/(EXPECTED['gpu_uuid']+'.lock')
v['own_UUID_lock_exists']=lock.is_file();v['own_UUID_lock_free']=None
if lock.is_file():
 try:
  with lock.open('r') as h:
   try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_UUID_lock_free']=True;fcntl.flock(h,fcntl.LOCK_UN)
   except BlockingIOError:v['own_UUID_lock_free']=False
 except Exception as error:v['read_errors'].append(dict(role='own_UUID_lock',error_type=type(error).__name__))
v['disk_free_bytes']=shutil.disk_usage(root).free
try:
 v['own_GPU']=subprocess.check_output(['nvidia-smi','-i',EXPECTED['gpu_uuid'],
  '--query-gpu=uuid,name,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
  '--format=csv,noheader,nounits'],text=True,timeout=10)
 v['own_GPU_compute_processes']=[line for line in apps.splitlines() if line.split(',')[0].strip()==EXPECTED['gpu_uuid']]
except Exception as error:v['read_errors'].append(dict(role='GPU_telemetry',error_type=type(error).__name__))
for role,path in (('GPU',out/'GPU.log'),('CPU_post',stage/'post-CPU.log')):
 info=meta(path)
 if info['exists']:
  with path.open('rb') as h:h.seek(max(0,info['bytes']-65536));tail=h.read(65536).decode(errors='replace')
  info.update(maximum_bytes_read=65536,error_labels=error_labels(tail))
 v['bounded_technical_logs'][role]=info
v['technical_classification']=classify(v)
sys.stdout.write(json.dumps(v,allow_nan=False))
'''
