"""Failed-card technical receipts and explicitly reconstructed budget charges."""
import copy, datetime, hashlib, json, math, re
from pathlib import Path


def classify(container_state, live_handles):
    if any(v is None for v in live_handles.values()):
        return 'TERMINAL_HANDLE_IDENTITY_INCOMPLETE'
    if any(live_handles.values()) or container_state.get('Running'):
        return 'RUNNING_ORIGINAL_HANDLE_ONLY'
    if not isinstance(container_state.get('ExitCode'), int):
        return 'TERMINAL_STATE_UNAVAILABLE'
    return ('FAILED_ORIGINAL_TERMINAL' if container_state['ExitCode'] != 0
            or container_state.get('OOMKilled') else 'EXITED_ZERO_REQUIRES_FULL_ACCEPTANCE')


def reconstruction(capture):
    capture={k:v for k,v in capture.items() if k!='reconstruction'}
    L=capture['launch']; state=capture['container_state']
    if classify(state,capture['live_handles'])!='FAILED_ORIGINAL_TERMINAL':
        raise ValueError('Exited failed original handles required')
    if not capture['lock_free'] or capture['original_billing_exists']:
        raise ValueError('Original bill or active lease must be reconciled instead')
    if capture['registration_sha256']!=L['registration_sha256'] or capture['authorization_sha256']!=L['authorization_sha256']:
        raise ValueError('Original identity differs')
    samples=capture['monitor_summary']; elapsed=samples['last_monotonic_seconds']
    end=datetime.datetime.fromisoformat(re.sub(r'(\.\d{6})\d+', r'\1', state['FinishedAt']).replace('Z','+00:00')).timestamp()
    wall=end-L['started_unix']
    if not 0<elapsed<=wall<=L['billed_limit_GPUh']*3600 or samples['clock_offset_span_seconds']>2:
        raise ValueError('Inconsistent clock evidence; keep full reservation')
    # Charge an explicit conservative estimate; never fabricate the lost exact bill.
    charged=math.ceil((wall+60)/36)/100
    if charged>L['billed_limit_GPUh']:raise ValueError('Reconstruction exceeds original envelope')
    return dict(status='FAILED104_RECONSTRUCTED_CONSERVATIVE_BUDGET_CHARGE',
        launch_id=L['launch_id'],run_id=L['run_id'],source_revision=L['source_revision'],gpu_uuid=L['gpu_uuid'],
        original_billing_missing=True,exact_actual_GPUh=None,actual_is_exact=False,
        monotonic_lower_bound_GPUh=elapsed/3600,container_launch_wall_estimate_GPUh=wall/3600,
        charge_GPUh=charged,round_up_quantum_GPUh=.01,additional_wall_allowance_seconds=60,
        accounting_basis='Container finish minus earlier launch, plus60s, rounded UP to0.01GPUh; not exact monotonic billing',
        original_reservation_GPUh=L['billed_limit_GPUh'],original_failure_retained=True,
        full_protocol_accepted=False,GPU_submissions=0,
        evidence_sha256=hashlib.sha256(json.dumps(capture,sort_keys=True,allow_nan=False).encode()).hexdigest())


def settle_reconstructed(pool,receipt,billing_sha256):
    """Compatibility actual_GPUh holds the charged estimate, explicitly annotated.

    Keep SETTLED so already-frozen ledger readers can still account for all jobs.
    The basis and exact_actual_GPUh=null prevent claiming exact recovered cost.
    """
    if receipt['status']!='FAILED104_RECONSTRUCTED_CONSERVATIVE_BUDGET_CHARGE' or receipt['actual_is_exact'] is not False:
        raise ValueError('Explicit reconstruction receipt required')
    if len(billing_sha256)!=64 or any(c not in '0123456789abcdef' for c in billing_sha256):raise ValueError('Missing bill digest')
    with pool.transaction() as value:
        j=value['jobs'][receipt['run_id']]
        for k in ('launch_id','gpu_uuid','source_revision'):
            if j[k]!=receipt[k]:raise ValueError('Wrong original job '+k)
        charge=receipt['charge_GPUh']
        if not math.isfinite(charge) or not 0<charge<=j['billed_limit_GPUh'] or value['cap_gpu_hours']!=226:raise ValueError('Original budget boundary changed')
        if j['status']=='SETTLED':
            if j['billing_sha256']!=billing_sha256 or j['actual_GPUh']!=charge or j.get('actual_is_exact') is not False:raise ValueError('Conflicting old settlement')
            return copy.deepcopy(value)
        if j['status']!='RESERVED_OR_RUNNING':raise ValueError('Unknown original state')
        j.update(status='SETTLED',actual_GPUh=charge,actual_is_exact=False,exact_actual_GPUh=None,
                 charged_GPUh=charge,billing_sha256=billing_sha256,accounting_basis=receipt['accounting_basis'],
                 original_failure_retained=True,full_protocol_accepted=False)
        pool.commit(value,dict(type='SETTLE_FAILED_RECONSTRUCTED_CONSERVATIVE_NOT_EXACT',job_id=receipt['run_id'],charged_GPUh=charge))
        return copy.deepcopy(value)


REMOTE_CAPTURE = r'''
import json,sys,os,pathlib,subprocess,time,hashlib,fcntl
L=json.load(sys.stdin);root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage']);out=root/'outputs'/L['run_id']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=json.loads(subprocess.check_output(['docker','inspect',L['container']],universal_newlines=True))[0]
assert raw['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
auth=json.loads((stage/'pg-GPU-authorization.json').read_text());assert auth['launch_id']==L['launch_id']
files={}
for p in [stage/'pg-host-guardian.json',out/'supervisor.json',out/'runner-health.json',out/'billing.json',*out.glob('billing.json.*.tmp')]:
 files[str(p)]=dict(exists=p.exists())
 if p.exists():
  b=p.read_bytes();files[str(p)].update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),raw_utf8=b.decode(errors='replace'))
identities={'guardian':L['guardian_identity']}
for n in ('supervisor.json',):
 if (out/n).exists():
  s=json.loads((out/n).read_text());identities.update(supervisor=s.get('supervisor_identity'),runner=s.get('child_identity'))
g=json.loads((stage/'pg-host-guardian.json').read_text());identities['container_cli']=g.get('container_cli_identity')
live={}
for key,i in identities.items():
 if not i:live[key]=None;continue
 try:
  fields=(pathlib.Path('/proc')/str(i['pid'])/'stat').read_text().rsplit(')',1)[1].split();live[key]=fields[0] not in ('Z','X') and int(fields[19])==i['start_ticks']
 except FileNotFoundError:live[key]=False
lock=root/'.sync/gpu-locks'/(L['gpu_uuid']+'.lock');h=lock.open('r');free=False
try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);free=True
except BlockingIOError:pass
finally:h.close()
samples=[];bad=[];monitor=out/'exclusive-monitor.jsonl';b=monitor.read_bytes()
for i,line in enumerate(b.splitlines()):
 try:samples.append(json.loads(line))
 except ValueError:bad.append(i)
offsets=[s['snapshot']['observed_unix']-s['monotonic_elapsed'] for s in samples]
v=dict(observed_unix=time.time(),launch=L,container_state=raw['State'],container_image=raw['Image'],live_handles=live,
 lock_free=free,registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
 original_billing_exists=(out/'billing.json').exists(),files=files,monitor_sha256=hashlib.sha256(b).hexdigest(),
 monitor_summary=dict(valid_samples=len(samples),invalid_line_indices=bad,last_monotonic_seconds=samples[-1]['monotonic_elapsed'] if samples else None,clock_offset_span_seconds=max(offsets)-min(offsets) if offsets else None),
 pool=json.loads((root/'reports/gpu-budget-v2.json').read_text()),GPU_submissions=0,remote_mutations=0)
storage_ref=stage/'history104-storage.json'
if storage_ref.exists():
 try:
  reg=json.loads((stage/'registration.json').read_text());assert sha(storage_ref)==reg['payload_sha256']['history104-storage.json']
  storage=json.loads(storage_ref.read_text());assert storage['run_id']==L['run_id']
  sys.path.insert(0,str(stage/'src'))
  from wcomr.history104_storage_r2 import FixedJournal,KEYS
  journal=FixedJournal(storage['journal_path']);v['durable_control']={}
  for key in KEYS:
   try:v['durable_control'][key]=dict(valid=True,value=journal.read(key))
   except (ValueError,OSError) as e:v['durable_control'][key]=dict(valid=False,error=str(e))
 except Exception as e:v['durable_control_error']=dict(type=type(e).__name__,message=str(e))
s=os.statvfs(root);v['available_bytes']=s.f_bavail*s.f_frsize
print(json.dumps(v))
'''


def audit_durable_billing(capture):
    """Recover precise future bills only from a bound, checksum-valid journal.

    This accepts financial evidence only; failed/partial104 stays unaccepted.
    """
    if classify(capture['container_state'],capture['live_handles']) not in ('FAILED_ORIGINAL_TERMINAL','EXITED_ZERO_REQUIRES_FULL_ACCEPTANCE') or not capture['lock_free']:
        raise ValueError('Original processes and lease must be released')
    entry=capture.get('durable_control',{}).get('billing',{})
    if not entry.get('valid'):raise ValueError('No checksum-valid durable billing record')
    bill=entry['value'];L=capture['launch']
    for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):
        if bill.get(k)!=L[k]:raise ValueError('Durable bill identity differs '+k)
    seconds=bill['wall_seconds'];actual=bill['actual_GPUh']
    if not math.isfinite(seconds) or not 0<seconds/3600==actual<=L['billed_limit_GPUh']:raise ValueError('Invalid exact monotonic bill')
    return dict(status='DURABLE_MONOTONIC_FINANCIAL_EVIDENCE_ACCEPTED_ONLY',bill=bill,
                exact_actual_GPUh=actual,full_protocol_accepted=False,GPU_submissions=0)
