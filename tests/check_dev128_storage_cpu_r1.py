"""Real tmpfs ENOSPC + original supervisor, CPU children, no real GPU or ledger."""
import errno,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def run(stage,output_root,fault_dir=Path('/fault')):
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 from wcomr.history104_storage_r2 import FixedJournal,StorageGuard,KEYS,SLOT_BYTES
 import wcomr.history104_storage_r2 as storage_module
 import wcomr.gpu_budget_pool_v2 as budget
 import wcomr.policy_generator_r1.dev128_execution as contract
 import wcomr.policy_generator_r1.production_exclusive as exclusive
 import wc_cara_dev128_worker_r1 as worker
 assert os.environ.get('CUDA_VISIBLE_DEVICES','')=='' and not list(Path('/dev').glob('nvidia*'))
 output_root.mkdir();checks=[];fault_dir=Path(fault_dir)
 assert os.path.ismount(fault_dir) and os.statvfs(fault_dir).f_blocks*os.statvfs(fault_dir).f_frsize<=128*2**20
 journal=FixedJournal(fault_dir/'journal');journal.create();journal.write('billing',{'version':1})
 with (fault_dir/'fill').open('wb',buffering=0) as f:
  try:
   while True:f.write(bytes(1024*1024))
  except OSError as e:assert e.errno==errno.ENOSPC
 def real_enospc():
  with (fault_dir/'probe').open('wb',buffering=0) as f:f.write(bytes(4096))
  raise AssertionError('Actual ENOSPC expected')
 try:real_enospc()
 except OSError as e:assert e.errno==errno.ENOSPC
 journal.write('billing',{'version':2});assert journal.read('billing')=={'version':2}
 # Corrupt the newest slot; previous generation remains readable.
 fd=os.open(journal.path,os.O_RDWR);os.pwrite(fd,b'X'*80,SLOT_BYTES*(KEYS.index('billing')*2+1));os.fsync(fd);os.close(fd)
 assert journal.read('billing')=={'version':1}
 checks.append(dict(scenario='real_ENOSPC_fixed_journal_and_torn_slot_recovery',status='PASS'))
 normal_atomic=budget.atomic_json;normal_open=Path.open
 for scenario in ('success','billing_enospc','ledger_enospc','monitor_enospc','state_enospc'):
  root=output_root/scenario;fixture=root/'.sync/stage';fixture.mkdir(parents=True);(fixture/'scripts').mkdir();out=root/'outputs'/contract.RUN;out.mkdir(parents=True)
  config=dict(host=contract.read(stage/'registration.json')['host'],forecast_complete_GPUh=.1,billed_limit_GPUh=.2,storage_contract_required=True);reg=dict(source_revision='STORAGE_CPU_FIXTURE')
  for n,data in [('registration.json',reg),(contract.CONFIG,config),(contract.CPU_PROOF,dict(CPU_fixture=True)),('pg-independent-CPU-acceptance.json',dict(production_CPU_accepted=True))]:normal_atomic(fixture/n,data)
  auth=dict(source_revision=reg['source_revision'],registration_sha256=budget.sha(fixture/'registration.json'),production_CPU_sha256=budget.sha(fixture/contract.CPU_PROOF),scope_counts=contract.COUNTS,billed_limit_GPUh=.2,gpu_uuid='GPU-CPU-fixture',launch_id=scenario)
  normal_atomic(fixture/'pg-GPU-authorization.json',auth)
  v=dict(schema=budget.SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=1.,origin_gpu_jobs_launched=0,jobs={},events=[],CPU_FIXTURE_ONLY_NOT_AUTHORITY=True);v.update(budget.BudgetPool.accounting(v));normal_atomic(root/'reports/gpu-budget-v2.json',v)
  durable=FixedJournal(root/'journal');durable.create()
  class Guard:
   output=out;journal=durable
   def check(self):return {'CPU_fixture':True}
   def persist(self,key,path,value,writer):self.journal.write(key,value);writer(path,value)
  runner="""import os,sys,pathlib,time
sys.path.insert(0,SOURCE)
from wcomr.gpu_budget_pool_v2 import process_identity,atomic_json
args=dict(zip(sys.argv[1::2],sys.argv[2::2]));s=pathlib.Path(args['--stage']);i={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};i['uid']=os.getuid()
assert os.fstat(int(os.environ['WC_LOCK_FD']));assert int(os.environ['WC_SUPERVISOR_PID'])==os.getppid()
atomic_json(s/'pg-runner-context-ready.json',dict(identity=i));deadline=time.monotonic()+20
while not (s/'pg-runner-context-granted.json').exists():
 assert time.monotonic()<deadline
 time.sleep(.02)
time.sleep(2.5)
""".replace('SOURCE',repr(str(stage/'src')))
  (fixture/'scripts/run_cara_dev128_r1.py').write_text(runner)
  (fixture/'scripts/postprocess_cara_dev128_r1.py').write_text('raise SystemExit(0)\n')
  def observe(uuid):
   apps=[];p=fixture/'pg-runner-context-ready.json'
   if p.exists():
    i=json.loads(p.read_text())['identity']
    if budget.same_live_process(i):apps=[i]
   return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,mps_processes=[],observed_unix=time.time())
  def atomic(path,value):
   if ((scenario=='billing_enospc' and Path(path).name=='billing.json') or
       (scenario=='ledger_enospc' and Path(path).name=='gpu-budget-v2.json' and any(j['status']=='SETTLED' for j in value.get('jobs',{}).values())) or
       (scenario=='state_enospc' and Path(path).name=='supervisor.json' and 'pool_after' in value)):
    real_enospc()
   return normal_atomic(path,value)
  def patched_open(path,*args,**kw):
   if scenario=='monitor_enospc' and path.name=='exclusive-monitor.jsonl' and args and args[0]=='a':real_enospc()
   return normal_open(path,*args,**kw)
  def smi(*args,**kw):
   text=(stage/'src/wcomr/gpu_budget_pool_v2.py').read_text()
   return ('GPU-CPU-fixture, NVIDIA RTX 6000 Ada Generation, 0, 8.9\n' if config['host']=='four_card' else 'GPU-CPU-fixture, NVIDIA RTX A6000, 0, 8.6\n')
  original=signal.getsignal(signal.SIGTERM);error=None
  try:
   with patch.object(contract,'validate',lambda *a:(config,reg)),patch.object(storage_module,'storage_for',lambda *a:Guard()),patch.object(exclusive,'observe',observe),patch.object(subprocess,'check_output',smi),patch.object(budget,'atomic_json',atomic),patch.object(Path,'open',patched_open):
    try:worker.supervise(SimpleNamespace(project=root,stage=fixture))
    except (OSError,RuntimeError,ValueError) as e:error=repr(e)
  finally:signal.signal(signal.SIGTERM,original)
  bill=durable.read('billing');assert bill['actual_GPUh']>0 and bill['launch_id']==scenario
  with budget.DeviceLease(root,'GPU-CPU-fixture'):pass
  ready=fixture/'pg-runner-context-ready.json'
  if ready.exists():assert not budget.same_live_process(json.loads(ready.read_text())['identity'])
  after=budget.BudgetPool(root).read();job=after['jobs'][contract.RUN]
  if scenario in ('billing_enospc','ledger_enospc'):assert job['status']=='RESERVED_OR_RUNNING' and error is not None
  else:assert job['status']=='SETTLED'
  if scenario=='success':assert error is None
  else:assert error is not None and not (out/'post-exit.json').exists()
  checks.append(dict(scenario=scenario,status='PASS',real_CPU_child_exited=True,lease_released=True,durable_bill_readable=True,original_failure_preserved=True,fixture_accounting_status=job['status'],real_ENOSPC_injected=scenario!='success'))
 return dict(status='DEV128_STORAGE_REAL_ENOSPC_SUPERVISOR_CPU_PASS',checks=checks,actual_tmpfs_ENOSPC=True,source_sha256={n:budget.sha(stage/n) for n in ('src/wcomr/history104_storage_r2.py','scripts/wc_cara_dev128_worker_r1.py','tests/check_dev128_storage_cpu_r1.py')},GPU_submissions=0,authoritative_ledger_written=False)
