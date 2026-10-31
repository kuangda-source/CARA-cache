"""Actual Linux CPU allocation chain; synthetic GPU/Docker and temporary ledger."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_host_guardian_r1 as host
from wcomr import cara_s_endpoint_lifecycle_capture_r1 as capture_module
from wcomr import cara_s_endpoint_lifecycle_r1 as lifecycle
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA,atomic_json,sha,DeviceLease
from wcomr.history104_storage_r2 import FixedJournal
import check_cara_s_endpoint_allocation_fixture_r1 as fixture

ROOT=Path(__file__).resolve().parents[1]
OBSERVATIONS=[]
DIAGNOSTICS=[]
SCENARIOS=('complete','runner_failure','missing_credential','busy','mode_failure',
           'no_container','init_failure','hard_limit','unknown','wrong_container','restore_busy','bootstrap_failure',
           'thermal_initial','thermal_running')


@unittest.skipUnless(Path('/proc/self').exists(),'Actual Linux original process identities required')
class HostGuardianTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.stage=self.project/'.sync/cara-S-endpoint-GPU-CPU-ALLOCATION'
        self.stage.mkdir(parents=True);(self.project/'.sync/gpu-locks').mkdir()
        shutil.copytree(ROOT/'src',self.stage/'src',ignore=shutil.ignore_patterns('__pycache__'))
        (self.stage/'scripts').mkdir()
        shutil.copyfile(ROOT/host.BOOTSTRAP,self.stage/host.BOOTSTRAP)
        shutil.copyfile(ROOT/'tests/check_cara_s_endpoint_allocation_fixture_r1.py',self.stage/'CPU-fixture.py')
        self.env=dict(os.environ,PYTHONPATH=str(self.stage/'src'),CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
        self.foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)'])
        self.addCleanup(self.close_foreign)
        atomic_json(self.stage/'CPU-foreign.json',bind_original_process(self.foreign.pid))
        atomic_json(self.stage/'CPU-mode.json',dict(mode='Default'))
        FixedJournal(self.stage/'CPU-control.journal').create()
        self.identity=dict(run_id='CPU-ALLOCATION',launch_id='CPU-UNIQUE-ALLOCATION',host='two_card',
            gpu_uuid='GPU-CPU-FIXTURE',stage=str(self.stage),source_revision='f'*40,
            scope_sha256='a'*64,billed_limit_GPUh=.01)
        names=(host.SOURCE,host.BOOTSTRAP,lifecycle.SOURCE,capture_module.SOURCE,
            'src/wcomr/cara_s_endpoint_guardian_journal_r1.py','src/wcomr/cara_s_endpoint_supervisor_r1.py')
        reg=dict(host='two_card',stage=str(self.stage),source_revision=self.identity['source_revision'],
            payload_sha256={n:sha(self.stage/n) for n in names},runtime_source_sha256={},container_image='sha256:'+'e'*64)
        atomic_json(self.stage/'registration.json',reg)

    def close_foreign(self):
        if self.foreign.poll() is None:self.foreign.terminate()
        self.foreign.wait(timeout=5)

    def setup_launch(self,scenario):
        if scenario=='hard_limit':self.identity['billed_limit_GPUh']=10./3600
        atomic_json(self.stage/'CPU-scenario.json',dict(scenario=scenario,CPU_fixture_only=True))
        atomic_json(self.stage/'GPU-authorization.json',dict(self.identity,execution_authorized=True,
            authorizes_replay=False,CPU_fixture_only=True))
        job=dict(self.identity,job_id=self.identity['run_id'],status='RESERVED_OR_RUNNING',
            registration_sha256=sha(self.stage/'registration.json'),authorization_sha256=sha(self.stage/'GPU-authorization.json'))
        atomic_json(self.stage/'central-reservation.json',dict(central_ledger_host='two_card',job=job))
        launch=dict(self.identity,registration_sha256=job['registration_sha256'],authorization_sha256=job['authorization_sha256'],
            central_reservation_sha256=sha(self.stage/'central-reservation.json'),container=self.stage.name+'-gpu',
            CPU_fixture_only=True,commands={role:[sys.executable,str(self.stage/'CPU-fixture.py'),action,str(self.stage)]
                for role,action in (('container_cli','cli'),('runner','runner'))})
        atomic_json(self.stage/'CPU-launch-template.json',launch)
        self.pool=BudgetPool(self.project)
        ledger=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
            jobs={'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5),
                  job['job_id']:job},events=[])
        ledger.update(self.pool.accounting(ledger));atomic_json(self.pool.path,ledger)

    def run_scenario(self,scenario):
        self.setup_launch(scenario)
        with (self.stage/'CPU-guardian.log').open('w') as log:
            child=subprocess.Popen([sys.executable,str(self.stage/'CPU-fixture.py'),'guardian',str(self.stage)],
                stdout=log,stderr=subprocess.STDOUT,env=self.env,start_new_session=True)
            try:code=child.wait(timeout=40)
            except subprocess.TimeoutExpired:
                child.terminate();child.wait(timeout=10)
                self.fail('CPU guardian timeout: '+(self.stage/'CPU-guardian.log').read_text()[-3000:])
        diagnostics=dict(scenario=scenario,exit_code=code,metadata={},logs={})
        for name in ('guardian.json','supervisor.json','runner-start.json','billing.json','CPU-container-state.json'):
            if (self.stage/name).exists():diagnostics['metadata'][name]=read_record(self.stage/name)
        for name in ('CPU-guardian.log','container-cli.log','runner.log'):
            if (self.stage/name).exists():diagnostics['logs'][name]=(self.stage/name).read_text()[-4000:]
        DIAGNOSTICS.append(diagnostics)
        self.assertEqual(code==0,scenario in ('complete','restore_busy'),json.dumps(diagnostics))
        guardian=read_record(self.stage/'guardian.json');bill=read_record(self.stage/'billing.json')
        self.assertEqual(guardian['status'],'CARA_ENDPOINT_GUARDIAN_TERMINAL_R1')
        expected={'runner_failure':'Original container CLI failed','missing_credential':'credential delivery failed',
            'busy':'Selected GPU is busy','mode_failure':'mode command failed','no_container':'Original container CLI failed',
            'init_failure':'Original container CLI failed','hard_limit':'release margin','unknown':'observation unknown',
            'wrong_container':'original Docker creation ID','bootstrap_failure':'Original container CLI failed'}
        stop_reason=guardian.get('error','')
        if scenario=='hard_limit':stop_reason+=' '+diagnostics['metadata'].get('supervisor.json',{}).get('error','')
        if scenario in expected:self.assertIn(expected[scenario],stop_reason,json.dumps(diagnostics))
        handles=guardian['original_handles']
        for handle in handles.values():
            if handle is not None:self.assertFalse(observe_original_process(handle)['original_live'])
        self.assertIsNone(self.foreign.poll(),'Foreign process must survive every stop/restore path')
        with DeviceLease(self.project,self.identity['gpu_uuid']):pass
        with patch.object(capture_module,'inspect_container',lambda name:fixture.inspect(self.stage,name)):
            capture=capture_module.capture_lifecycle(self.project,self.stage,sha(self.stage/'GPU-launch.json'))
        unknown=scenario in ('unknown','wrong_container')
        self.assertEqual(bill['wall_interval_complete'],not unknown)
        self.assertGreater(bill['wall_seconds'],0)
        self.assertEqual(bill['actual_GPUh'],bill['wall_seconds']/3600)
        self.assertEqual(guardian['billing_sha256'],sha(self.stage/'billing.json'))
        before=self.pool.read();released=None
        if unknown:
            self.assertEqual(capture['status'],'ORIGINAL_ENDPOINT_LIVE_OR_UNKNOWN')
            self.assertNotIn('files',capture)
            self.assertEqual(self.pool.read(),before)
        else:
            expected_sha=sha(self.stage/'GPU-launch.json')
            launch,accepted_bill=lifecycle.financial_terminal(capture,expected_sha,cpu_validation=True)
            self.assertEqual(accepted_bill,bill)
            for _ in range(2):
                prior=self.pool.read();after=self.pool.settle(launch['run_id'],bill['actual_GPUh'],sha(self.stage/'billing.json'))
                settlement=dict(central_ledger_host='two_card',launch_id=launch['launch_id'],
                    billing_sha256=sha(self.stage/'billing.json'),central_before=prior,central_after=after)
                released=lifecycle.released_lifecycle(capture,expected_sha,settlement,cpu_validation=True)
            self.assertEqual(len(after['events']),1)
            self.assertEqual(after['jobs']['old-unknown-16.5'],before['jobs']['old-unknown-16.5'])
            self.assertEqual(after['reserved_gpu_hours'],16.5)
            self.assertEqual(released['container_exit_success'],scenario=='complete')
            self.assertFalse(released['scientific_read_allowed'])
        if scenario=='complete':
            self.assertEqual(len({h['pid'] for h in handles.values()}),4)
            self.assertTrue(released['GPU_released']);self.assertTrue(released['mode_restored'])
        if scenario=='restore_busy':
            self.assertFalse(released['mode_restored'])
            self.assertEqual(read_record(self.stage/'CPU-mode-changes.json'),['EXCLUSIVE_PROCESS'])
        if scenario=='missing_credential':
            self.assertFalse(any(guardian['allocation_never_attempted_witness'].values()))
        if scenario=='hard_limit':self.assertTrue((self.stage/'pg-runner-context-granted.json').exists())
        if scenario.startswith('thermal_'):
            self.assertIn('Thermal stop >=90C',diagnostics['metadata']['supervisor.json']['error'])
            sample=fixture.storage_for(self.stage).journal.read('telemetry')
            self.assertEqual(float(sample['thermal']['temperature.gpu']),90.)
            self.assertEqual((self.stage/'runner-intent.json').exists(),scenario=='thermal_running')
            self.assertEqual((self.stage/'pg-runner-context-granted.json').exists(),scenario=='thermal_running')
        if scenario=='bootstrap_failure':
            witness=read_record(self.stage/'runner-start.json')
            self.assertFalse(witness['bootstrap_self_witness'])
            self.assertEqual(witness['witness_source'],'ORIGINAL_SUPERVISOR_POPEN_AFTER_CONFIRMED_EXIT')
            self.assertEqual(witness['parent_terminal_sha256'],sha(self.stage/'supervisor.json'))
            self.assertFalse((self.stage/'runner-dispatch-grant.json').exists())
        # An original stage is never replayed, even after a recorded failure.
        original_hashes={n:sha(self.stage/n) for n in ('GPU-launch.json','guardian.json','billing.json','CPU-control.journal')}
        repeat=subprocess.run([sys.executable,str(self.stage/'CPU-fixture.py'),'guardian',str(self.stage)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.env,timeout=5)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual(original_hashes,{n:sha(self.stage/n) for n in original_hashes})
        OBSERVATIONS.append(dict(scenario=scenario,actual_bound_process_roles=[r for r,h in handles.items() if h],
            original_processes_ended=True,foreign_CPU_sentinel_preserved=True,own_lease_released=True,no_replay=True,
            original_wall_interval_complete=bill['wall_interval_complete'],temporary_settlement_events=len(self.pool.read()['events']),
            operational_status=capture['status'],execution_success=False if released is None else released['container_exit_success'],
            mode_restored=guardian['mode_restoration']['restored'],error_type=guardian.get('error_type'),error=guardian.get('error'),stop_reason=stop_reason))

    def test_complete_chain(self):self.run_scenario('complete')
    def test_runner_failure_original_cost(self):self.run_scenario('runner_failure')
    def test_missing_credential_no_allocation(self):self.run_scenario('missing_credential')
    def test_busy_device_not_changed(self):self.run_scenario('busy')
    def test_mode_failure_no_dispatch(self):self.run_scenario('mode_failure')
    def test_cli_exits_without_container(self):self.run_scenario('no_container')
    def test_container_init_failure(self):self.run_scenario('init_failure')
    def test_original_hard_deadline(self):self.run_scenario('hard_limit')
    def test_original_child_exit_before_bootstrap_witness(self):self.run_scenario('bootstrap_failure')
    def test_unknown_container_no_settlement(self):self.run_scenario('unknown')
    def test_replaced_container_not_stopped(self):self.run_scenario('wrong_container')
    def test_busy_restore_not_forced(self):self.run_scenario('restore_busy')
    def test_thermal_initial_refuses_runner(self):self.run_scenario('thermal_initial')
    def test_thermal_running_stops_original_runner(self):self.run_scenario('thermal_running')
    def test_CPU_fixture_refused_in_production(self):
        self.setup_launch('complete');launch=read_record(self.stage/'CPU-launch-template.json')
        launch['guardian_identity']=bind_original_process(os.getpid());atomic_json(self.stage/'GPU-launch.json',launch)
        with self.assertRaisesRegex(ValueError,'CPU fixtures'):
            host.allocate(self.project,self.stage,fixture.storage_for(self.stage),None)
        self.assertFalse((self.stage/'guardian-intent.json').exists())


if __name__=='__main__':unittest.main()
