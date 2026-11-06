"""Single external-host CAL66 envelope, exclusive launch, capture and settlement.

The central ledger remains on the four-card server. The A6000 ledger is a
single-run subledger: its reservation is the same money as the central envelope.
"""
import argparse,base64,hashlib,json,subprocess,sys,time
from pathlib import Path
import cara_two_card_transport_r1 as transport
from cara_cal66_a6000_profile_r1 import RUN,VERSION,STAGE,QUOTE,adapt
from audit_cara_cal66_a6000_cpu_r1 import accept as accept_cpu
from wc_four_card_resource_cpu_r4 import write
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

# Install the same enumerated generated contract used by the remote stage.
# Scientific modules, original manifests and the source tree stay unchanged.
import wcomr.policy_generator_r1.shared66_card as contract
exec(compile(adapt('src/wcomr/policy_generator_r1/shared66_card.py',
                  (ROOT/'src/wcomr/policy_generator_r1/shared66_card.py').read_text())[0],
             contract.__file__,'exec'),contract.__dict__)
import wc_four_card_cara_shared66_gpu_r1 as proven
from wcomr.policy_generator_r1.shared66_terminal import accept as accept_terminal
from wcomr.gpu_budget_pool_v2 import atomic_json

PREFLIGHT=proven.PREFLIGHT.replace("'RTX 6000 Ada' in g[1] and g[2].strip()=='8.9'", "'RTX A6000' in g[1] and g[2].strip()=='8.6'")
ENVELOPE_ID=RUN+'-external-budget-envelope'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ssh(code,data=None):return transport.ssh(code,data,docker_group=True,timeout=420)


def published():
    from wcomr.immutable_stage_payload_r1 import local_python_closure
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=local_python_closure(ROOT,['scripts/wc_two_card_cara_cal66_gpu_r1.py'])
    for n,h in files.items():
        assert hashlib.sha256(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)).hexdigest()==h
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==rev
    return rev,files


def bind(a):
    cap=read(a.cpu_capture);cpu=accept_cpu(cap)
    supplied=read(a.cpu_acceptance)
    assert all(supplied[k]==v for k,v in cpu.items())
    L=cap['launch'];assert L['stage'].endswith('/'+STAGE)
    central=transport.four_ssh("import pathlib,json,hashlib; p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/reports/gpu-budget-v2.json');print(json.dumps(dict(pool=json.loads(p.read_text()),sha256=hashlib.sha256(p.read_bytes()).hexdigest())))")
    code=r'''
import pathlib,json,sys,hashlib,os,time
p=json.load(sys.stdin);L=p['launch'];stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project'])
assert not any((stage/n).exists() for n in ('pg-GPU-intent.json','pg-GPU-launch.json'))
assert hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()==L['registration_sha256']
assert hashlib.sha256((stage/'shared66-recovery-CPU.json').read_bytes()).hexdigest()==p['cpu']['proof_sha256']
target=stage/'pg-independent-CPU-acceptance.json';assert not target.exists()
target.write_text(json.dumps(p['cpu'],indent=2)+'\n')
sys.path.insert(0,str(stage/'src'));from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json
pool=p['central']['pool'];assert all(pool[k]==v for k,v in BudgetPool.accounting(pool).items())
assert not (root/'reports/gpu-budget-v2.json').exists()
atomic_json(root/'reports/gpu-budget-v2.json',pool)
v=dict(status='CAL66_A6000_CPU_BOUND_NO_GPU',project=str(root),stage=str(stage),run_id=p['run'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],CPU_proof_sha256=p['cpu']['proof_sha256'],central_snapshot_sha256=p['central']['sha256'],observed_unix=time.time(),GPU_submissions=0,central_ledger_written=False)
atomic_json(stage/'A6000-stage-ref.json',v);print(json.dumps(v))
'''
    return ssh(code,dict(launch=L,cpu=supplied,central=central,run=RUN))


def central_envelope(L,uuid):
    # Use the reviewed financial-aware accountant; old uncertainty rows remain
    # byte-for-byte in jobs and continue reserving16.5h. They are not GPU leases.
    budget=adapt('src/wcomr/gpu_budget_pool_v2.py',(ROOT/'src/wcomr/gpu_budget_pool_v2.py').read_text())[0]
    code=r'''
import pathlib,json,sys,hashlib,time,copy
p=json.load(sys.stdin);ns={'__name__':'cal66_scope_budget'};exec(p['budget_code'],ns)
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');pool=ns['BudgetPool'](root)
oldstage=root/'.sync/cara-shared66-full-ada-r2-20261025'
assert not any((oldstage/n).exists() for n in ('pg-GPU-intent.json','pg-GPU-launch.json'))
with pool.transaction() as v:
 assert v['cap_gpu_hours']==226
 eid=p['envelope_id'];old=copy.deepcopy(v)
 if eid in v['jobs']:
  job=v['jobs'][eid];assert job['stage']==p['stage']['stage'] and job['source_revision']==p['stage']['source_revision'] and job['gpu_uuid']==p['gpu_uuid']
  receipt=json.loads((root/'reports/cal66-a6000-envelope-original.json').read_text());print(json.dumps(receipt));raise SystemExit(0)
 assert not any(j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False for j in v['jobs'].values())
 assert pool.accounting(v)['available_gpu_hours']>=8
 job=dict(job_id=eid,kind='EXTERNAL_HOST_SCOPED_CAL66_ENVELOPE',status='RESERVED_OR_RUNNING',billed_limit_GPUh=8.,gpu_uuid=p['gpu_uuid'],confirmed_GPU_submission=False,actual_GPU_submission_known=False,run_id=p['run'],source_revision=p['stage']['source_revision'],stage=p['stage']['stage'],created_unix=time.time(),counts_as_additional_scientific_run=False)
 v['jobs'][eid]=job;v['financial_holds_are_not_device_leases']=True
 pool.commit(v,dict(type='RESERVE_EXTERNAL_HOST_CAL66_ONCE',job_id=eid))
 receipt=dict(version='CAL66_CENTRAL_ENVELOPE_R1',run_id=p['run'],envelope_id=eid,gpu_uuid=p['gpu_uuid'],limit_GPUh=8.,central_reservation_verified=True,stage_reference=p['stage'],prior_pool=old,central_pool_after=v,created_unix=time.time(),same_money_not_two_reservations=True)
 ns['atomic_json'](root/'reports/cal66-a6000-envelope-original.json',receipt)
 print(json.dumps(receipt))
'''
    return transport.four_ssh(code,dict(budget_code=budget,stage=L,gpu_uuid=uuid,run=RUN,envelope_id=ENVELOPE_ID))


def launch(a):
    L=read(a.stage_ref);permission=read(a.recovery_authorization)
    assert permission['new_run_id']==RUN and permission['explicit_GPU_dispatch_authorized'] is True
    assert permission['registration_sha256']==L['registration_sha256']
    observed=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=L,gpu_uuid=a.gpu_uuid))
    if not observed['admissible']:return observed
    published()
    prior=ssh("import pathlib,json,sys;p=json.load(sys.stdin);s=pathlib.Path(p['stage']);print(json.dumps({n:json.loads((s/n).read_text()) for n in ('pg-GPU-intent.json','pg-GPU-launch.json') if (s/n).exists()}))",L)
    if prior:return dict(status='EXISTING_CAL66_A6000_HANDLE_RECOVER_ONLY',original_files=prior)
    envelope=central_envelope(L,a.gpu_uuid)
    # Persist the same8h envelope before GPU admission. UNKNOWN retains it.
    ssh(r'''
import pathlib,json,sys
p=json.load(sys.stdin);s=pathlib.Path(p['stage']['stage']);root=pathlib.Path(p['stage']['project']);sys.path.insert(0,str(s/'src'))
from wcomr.gpu_budget_pool_v2 import atomic_json,BudgetPool
assert not (s/'pg-GPU-intent.json').exists()
pool=p['envelope']['prior_pool'];assert all(pool[k]==v for k,v in BudgetPool.accounting(pool).items())
with BudgetPool(root).transaction() as old:
 assert p['envelope']['run_id'] not in old['jobs']
 atomic_json(root/'reports/gpu-budget-v2.json',pool)
 atomic_json(root/'reports/cal66-migration-envelope.json',p['envelope'])
print(json.dumps({'envelope_bound':True}))
''',dict(stage=L,envelope=envelope))
    proven.RUN=RUN;proven.PREFLIGHT=PREFLIGHT;proven.ssh=ssh;proven.saved_secret=transport.password;proven.published=published
    return proven.launch(a)


def capture(a):
    L=read(a.launch_ref)
    if a.mode=='terminal':
        from wcomr.history104_failure_recovery_r1 import REMOTE_CAPTURE,classify
        technical=ssh(REMOTE_CAPTURE,L)
        if 'container_state' in technical and classify(technical['container_state'],technical['live_handles'])=='FAILED_ORIGINAL_TERMINAL':
            technical.update(status='FAILED_ORIGINAL_TERMINAL',full_protocol_accepted=False);return technical
    return ssh(proven.CAPTURE,dict(launch=L,terminal=a.mode=='terminal'))


def confirm(a):
    """Mark the parent envelope as a live lease only after actual admission."""
    L=read(a.launch_ref);v=read(a.capture);assert v['launch']==L
    from wcomr.policy_price_terminal_r1 import record
    from wcomr.policy_asset_price_review_r1 import exclusive_gate
    ready=record(v,'ready');grant=record(v,'grant');guard=record(v,'guardian')
    identity=ready['identity'];assert grant['runner']==identity and ready['GPU_context_held']
    assert grant['source_revision']==ready['source_revision']==L['source_revision']
    assert all(v['original_live_handles'].values()) and not v['own_UUID_lock_free']
    for snap,phase,runner in ((guard['mode_admission']['verified_snapshot'],'idle',None),(v['current_GPU'],'active',identity)):
        result=exclusive_gate(snap,gpu_uuid=L['gpu_uuid'],phase=phase,now=snap['observed_unix'],**({'runner':runner} if runner else {}))
        assert result['observation_passed']
    budget=adapt('src/wcomr/gpu_budget_pool_v2.py',(ROOT/'src/wcomr/gpu_budget_pool_v2.py').read_text())[0]
    code=r'''
import json,sys,pathlib,time
p=json.load(sys.stdin);ns={'__name__':'cal66_scope_budget'};exec(p['budget_code'],ns)
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');pool=ns['BudgetPool'](root);L=p['launch']
with pool.transaction() as v:
 j=v['jobs'][p['envelope_id']]
 assert j['status']=='RESERVED_OR_RUNNING' and j['run_id']==L['run_id'] and j['stage']==L['stage'] and j['source_revision']==L['source_revision'] and j['gpu_uuid']==L['gpu_uuid']
 if j.get('actual_GPU_submission_known'):
  assert j['launch_id']==L['launch_id']
 else:
  j.update(confirmed_GPU_submission=True,actual_GPU_submission_known=True,launch_id=L['launch_id'],admission_capture_sha256=p['capture_sha256'])
  pool.commit(v,dict(type='CONFIRM_EXTERNAL_HOST_SINGLE_RUNNER',job_id=p['envelope_id']))
 print(json.dumps(dict(status='CAL66_A6000_CENTRAL_ADMISSION_CONFIRMED',observed_unix=time.time(),launch=L,envelope_job=j,pool_totals=pool.accounting(v),capture_sha256=p['capture_sha256'],actual_unique_runner_accepted=True)))
'''
    return transport.four_ssh(code,dict(budget_code=budget,launch=L,envelope_id=ENVELOPE_ID,capture_sha256=sha(a.capture)))


def settle(a):
    """Re-read the original bill/settled subledger; never infer failure cost."""
    L=read(a.launch_ref)
    original=ssh(r'''
import pathlib,json,sys,hashlib
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);root=pathlib.Path(L['project']);out=root/'outputs'/L['run_id']
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(s/'pg-GPU-launch.json')==L
bill=read(out/'billing.json');pool=read(root/'reports/gpu-budget-v2.json');job=pool['jobs'][L['run_id']]
assert job['status']=='SETTLED' and job['billing_sha256']==sha(out/'billing.json') and job['actual_GPUh']==bill['actual_GPUh']
for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):assert bill[k]==L[k]
assert abs(bill['actual_GPUh']-bill['wall_seconds']/3600)<1e-12
print(json.dumps(dict(billing=bill,billing_sha256=sha(out/'billing.json'),launch=L,subledger_job=job)))
''',L)
    budget=adapt('src/wcomr/gpu_budget_pool_v2.py',(ROOT/'src/wcomr/gpu_budget_pool_v2.py').read_text())[0]
    code=r'''
import pathlib,json,sys,time
p=json.load(sys.stdin);ns={'__name__':'cal66_scope_budget'};exec(p['budget_code'],ns)
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');pool=ns['BudgetPool'](root);o=p['original'];bill=o['billing'];L=o['launch']
v=pool.read();job=v['jobs'][p['envelope_id']]
assert job['run_id']==L['run_id'] and job['stage']==L['stage'] and job['source_revision']==L['source_revision'] and job['gpu_uuid']==L['gpu_uuid']
after=pool.settle(p['envelope_id'],bill['actual_GPUh'],o['billing_sha256'])
receipt=dict(status='CAL66_A6000_CENTRAL_ENVELOPE_SETTLED',observed_unix=time.time(),original=o,envelope_id=p['envelope_id'],pool_after=after,old_unknown16_5_preserved=True,scientific_acceptance_not_implied=True)
target=root/'reports/cal66-a6000-envelope-settlement.json'
if target.exists():
 old=json.loads(target.read_text());assert old['original']==o;receipt=old
else:ns['atomic_json'](target,receipt)
print(json.dumps(receipt))
'''
    return transport.four_ssh(code,dict(budget_code=budget,original=original,envelope_id=ENVELOPE_ID))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['bind','preflight','launch-gpu','recover','capture','confirm-central','accept-gpu','settle-central'])
    for n in ('cpu-capture','cpu-acceptance','stage-ref','launch-ref','capture','recovery-authorization'):p.add_argument('--'+n,type=Path)
    p.add_argument('--gpu-uuid');p.add_argument('--mode',choices=['admission','halfway','terminal']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    if a.command=='bind':v=bind(a)
    elif a.command=='preflight':v=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=read(a.stage_ref),gpu_uuid=a.gpu_uuid))
    elif a.command=='launch-gpu':v=launch(a)
    elif a.command=='recover':
        proven.ssh=ssh;v=proven.recover(a);print(v['status']);return
    elif a.command=='capture':v=capture(a)
    elif a.command=='confirm-central':v=confirm(a)
    elif a.command=='settle-central':v=settle(a)
    else:
        v=accept_terminal(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture),central_settlement_pending=True)
    # Proven launch writes its own immutable receipt, including UNKNOWN.
    if not a.output.exists():write(a.output,v)
    print(json.dumps({k:v.get(k) for k in ('status','stage','launch_id','admissible','reasons','full_protocol_accepted','health')}))


if __name__=='__main__':main()
