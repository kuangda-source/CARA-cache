"""Actual Linux CPU children; GPU observations are explicit synthetic metadata."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from wcomr import cara_budget_supervisor_r1 as supervisor
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.gpu_budget_pool_v2 import atomic_json,sha,DeviceLease
from wcomr.history104_storage_r2 import FixedJournal

ROOT=Path(__file__).resolve().parents[1]
OBSERVATIONS=[]
CHILD='''import json,os,sys,time
from pathlib import Path
stage=Path(sys.argv[1]);scenario=sys.argv[2];sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
assert int(os.environ['WC_LOCK_FD'])>=0
os.fstat(int(os.environ['WC_LOCK_FD']))
if scenario=='no_context':time.sleep(20)
identity={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
if scenario=='wrong_ready':identity['start_ticks']+=1
atomic_json(stage/'pg-runner-context-ready.json',dict(identity=identity,CPU_fixture_only=True))
until=time.monotonic()+5
while not (stage/'pg-runner-context-granted.json').exists():
 if time.monotonic()>until:raise TimeoutError('CPU context grant')
 time.sleep(.01)
if scenario in ('hard_limit','thermal','storage','foreign'):time.sleep(20)
if scenario=='failed':raise SystemExit(7)
time.sleep(.04)
'''


@unittest.skipUnless(Path('/proc/self').exists(),'Actual Linux child identity/control required')
class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.stage=self.project/'.sync/cara-budget-calibration-GPU-CPU-SUPERVISOR'
        self.stage.mkdir(parents=True);(self.project/'.sync/gpu-locks').mkdir()
        for name in ['scripts/cara_budget_process_bootstrap_r1.py']:
            dest=self.stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        # Original registered import tree; no external project fallback in child.
        shutil.copytree(ROOT/'src',self.stage/'src',ignore=shutil.ignore_patterns('__pycache__'))
        self.guardian=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
        self.addCleanup(self.close_guardian)
        self.original_guardian=bind_original_process(self.guardian.pid)
        self.registration=dict(stage=str(self.stage),payload_sha256={supervisor.SOURCE:sha(supervisor.__file__),
            supervisor.BOOTSTRAP:sha(self.stage/supervisor.BOOTSTRAP)})
        atomic_json(self.stage/'registration.json',self.registration)
        (self.stage/'CPU-runner.py').write_text(CHILD)
        self.launch=dict(run_id='CPU-SUPERVISOR',launch_id='CPU-UNIQUE-SUPERVISOR',host='four_card',
            gpu_uuid='GPU-CPU-FIXTURE',stage=str(self.stage),source_revision='f'*40,scope_sha256='a'*64,
            billed_limit_GPUh=.01,guardian_identity=self.original_guardian,CPU_fixture_only=True,
            registration_sha256=sha(self.stage/'registration.json'),commands={})
        journal=FixedJournal(self.stage/'CPU-48MiB-control.journal');journal.create()
        class Storage:
            checks=0
            def __init__(self):self.journal=journal
            def persist(self,key,path,value,writer):self.journal.write(key,value);writer(path,value)
            def check(self):
                self.checks+=1
                if getattr(self,'fail',False) and self.checks>=3:raise OSError(28,'CPU fixture storage low water')
                return {}
        self.storage=Storage();self.thermal_calls=0

    def close_guardian(self):
        if self.guardian.poll() is None:self.guardian.terminate()
        self.guardian.wait(timeout=5)

    def observe(self,uuid):
        apps=[];ready=self.stage/'pg-runner-context-ready.json'
        if ready.exists() and (self.stage/'runner-start.json').exists():
            handle=read_record(self.stage/'runner-start.json')['identity']
            if observe_original_process(handle)['original_live'] is True:
                apps=[dict(pid=handle['pid'],start_ticks=handle['start_ticks'],uid=os.getuid(),gpu_uuid=uuid)]
        if self.scenario=='busy' or (self.scenario=='foreign' and apps):
            apps.append(dict(pid=self.guardian.pid,start_ticks=self.original_guardian['start_ticks'],uid=os.getuid(),gpu_uuid=uuid))
        return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,mps_processes=[],observed_unix=time.time())

    def thermal(self,uuid):
        self.thermal_calls+=1
        hot=self.scenario=='hot_before' or (self.scenario=='thermal' and self.thermal_calls>=2)
        return {'temperature.gpu':'95' if hot else '50'}

    def run_scenario(self,scenario,age=0):
        self.scenario=scenario;self.storage.fail=scenario=='storage'
        self.launch['commands']['runner']=[sys.executable,str(self.stage/'CPU-runner.py'),str(self.stage),scenario]
        if scenario=='hard_limit':self.launch['billed_limit_GPUh']=2./3600
        atomic_json(self.stage/'GPU-launch.json',self.launch)
        guardian={k:self.launch[k] for k in supervisor.IDENTITY}
        guardian.update(original_handles={'guardian':self.original_guardian},started_monotonic=time.monotonic()-age)
        atomic_json(self.stage/'guardian.json',guardian)
        kwargs=dict(cpu_validation=True,observe_gpu=self.observe,thermal=self.thermal,interval=.01,
                    context_timeout=1.,release_margin=.5,thermal_period=.03)
        if scenario=='complete':result=supervisor.supervise(self.project,self.stage,self.storage,**kwargs)
        else:
            with self.assertRaises((ValueError,RuntimeError,TimeoutError,OSError)):
                supervisor.supervise(self.project,self.stage,self.storage,**kwargs)
            result=read_record(self.stage/'supervisor.json')
            expected={'failed':'Original runner failed','hard_limit':'release margin','expired':'release margin',
                'no_context':'No original sole-runner','wrong_ready':'readiness differs','foreign':'Hardware exclusive gate',
                'busy':'Hardware exclusive gate','hot_before':'Thermal stop','thermal':'Thermal stop','storage':'storage low water'}
            self.assertIn(expected[scenario],result['error'])
        self.assertEqual(result['status'],'BUDGET_CALIBRATION_SUPERVISOR_TERMINAL')
        self.assertTrue(result['original_runner_ended']);self.assertFalse(result['complete_search_accepted'])
        if (self.stage/'runner-start.json').exists():
            handle=read_record(self.stage/'runner-start.json')['identity']
            self.assertFalse(observe_original_process(handle)['original_live'])
        self.assertIsNone(self.guardian.poll(),'Foreign CPU sentinel must never be stopped')
        with DeviceLease(self.project,self.launch['gpu_uuid']):pass
        self.assertFalse((self.stage/'billing.json').exists(),'Only the host guardian may bill')
        # Original intent/start never permits another child, including failures.
        with self.assertRaises(FileExistsError):supervisor.supervise(self.project,self.stage,self.storage,**kwargs)
        OBSERVATIONS.append(dict(scenario=scenario,original_runner_bound=(self.stage/'runner-start.json').exists(),
            original_runner_ended=result['original_runner_ended'],context_granted=result['context_granted'],
            error_type=result.get('error_type'),error=result.get('error'),foreign_CPU_sentinel_preserved=True,
            own_lease_released=True,no_supervisor_bill=True,no_replay=True))
        return result

    def test_complete_context_and_original_child_exit(self):
        result=self.run_scenario('complete');self.assertTrue(result['context_granted'])
        self.assertEqual(result['runner_exit_code'],0);self.assertGreater(result['observations'],0)

    def test_failed_child_does_not_repeat_or_bill(self):self.run_scenario('failed')
    def test_context_timeout_stops_only_own_child(self):self.run_scenario('no_context')
    def test_wrong_context_identity_refused(self):self.run_scenario('wrong_ready')
    def test_foreign_context_stops_only_own_child(self):self.run_scenario('foreign')
    def test_active_hard_deadline_stops_own_child(self):self.run_scenario('hard_limit')
    def test_original_guardian_age_not_reset_at_supervisor_start(self):
        self.run_scenario('expired',age=36)
        self.assertFalse((self.stage/'runner-intent.json').exists())
    def test_hot_running_observation_retained_before_stop(self):
        self.run_scenario('thermal')
        sample=self.storage.journal.read('telemetry');self.assertEqual(sample['thermal']['temperature.gpu'],'95')
    def test_hot_or_busy_before_dispatch_never_creates_runner(self):
        self.run_scenario('hot_before');self.assertFalse((self.stage/'runner-intent.json').exists())
    def test_busy_device_never_creates_runner(self):
        self.run_scenario('busy');self.assertFalse((self.stage/'runner-intent.json').exists())
    def test_storage_failure_stops_original_child(self):self.run_scenario('storage')
    def test_CPU_fixture_cannot_enter_production_mode(self):
        atomic_json(self.stage/'GPU-launch.json',self.launch)
        with self.assertRaises(ValueError):supervisor.supervise(self.project,self.stage,self.storage)
        self.assertFalse((self.stage/'supervisor-start.json').exists())


if __name__=='__main__':unittest.main()
