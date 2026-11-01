"""Original CPU child identities and original guardian billing with a FIT service."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import test_cara_s_endpoint_host_guardian_r1 as legacy
from wcomr.cara_budget_original_handles_r1 import observe_original_process
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import atomic_json, sha

ROOT=Path(__file__).resolve().parents[1]
OBSERVATIONS=[]


@unittest.skipUnless(Path('/proc/self').exists(),'Original Linux PID/namespace witnesses required')
class GuardianFITTests(unittest.TestCase):
    def setUp(self):
        self.f=legacy.HostGuardianTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        shutil.copyfile(ROOT/'tests/check_cara_s_endpoint_allocation_fixture_r1.py',
                        self.f.stage/'check_cara_s_endpoint_allocation_fixture_r1.py')
        shutil.copyfile(ROOT/'tests/check_cara_source_lifecycle_p1_service_cpu_fixture_r1.py',self.f.stage/'CPU-fixture.py')

    def run_case(self,scenario):
        self.f.setup_launch('runner_failure' if scenario=='GPU_failure' else 'complete')
        # This is a temporary local CPU ledger; use the production central-host
        # label. No connection to, or mutation of, the real four-card host occurs.
        envelope=read_record(self.f.stage/'central-reservation.json')
        envelope['central_ledger_host']='four_card'
        atomic_json(self.f.stage/'central-reservation.json',envelope)
        template=read_record(self.f.stage/'CPU-launch-template.json')
        template['central_reservation_sha256']=sha(self.f.stage/'central-reservation.json')
        atomic_json(self.f.stage/'CPU-launch-template.json',template)
        atomic_json(self.f.stage/'CPU-fit-scenario.json',dict(scenario=scenario,CPU_fixture_only=True))
        with (self.f.stage/'CPU-guardian.log').open('x') as log:
            child=subprocess.Popen([sys.executable,str(self.f.stage/'CPU-fixture.py'),'guardian',str(self.f.stage)],
                stdout=log,stderr=subprocess.STDOUT,env=self.f.env,start_new_session=True)
            try: code=child.wait(timeout=30)
            finally:
                if child.poll() is None: child.terminate();child.wait(timeout=10)
        self.assertEqual(code==0,scenario=='success',(self.f.stage/'CPU-guardian.log').read_text()[-3000:])
        state=read_record(self.f.stage/'guardian.json')
        bill=read_record(self.f.stage/'billing.json')
        self.assertEqual(state['status'],'CARA_ENDPOINT_GUARDIAN_TERMINAL_R1')
        self.assertTrue(bill['wall_interval_complete'])
        self.assertEqual(bill['actual_GPUh'],bill['wall_seconds']/3600)
        self.assertEqual(bill['ended_monotonic'],state['ended_monotonic'])
        self.assertTrue(state['mode_restoration']['restored'])
        self.assertEqual(read_record(self.f.stage/'CPU-mode.json')['mode'],'Default')
        self.assertIsNone(self.f.foreign.poll())
        for identity in state['original_handles'].values():
            if identity is not None:self.assertFalse(observe_original_process(identity)['original_live'])
        witness=state['FIT_service_terminal_witness']
        if scenario=='cleanup_unknown':
            self.assertFalse(witness['complete'])
            self.assertIn('cleanup witness',witness['error'])
        else:
            self.assertTrue(witness['complete'])
        fit_child=self.f.stage/'CPU-FIT-child.json'
        if fit_child.exists():
            self.assertFalse(observe_original_process(read_record(fit_child)['identity'])['original_live'])
        if scenario!='start_failure' and scenario!='cleanup_unknown':
            closed=read_record(self.f.stage/'CPU-FIT-closed.json')
            self.assertLessEqual(closed['ended_monotonic'],bill['ended_monotonic'])
            self.assertLessEqual(bill['started_monotonic'],read_record(self.f.stage/'CPU-FIT-intent.json')['guardian_epoch'])
        if scenario=='start_failure':
            self.assertFalse((self.f.stage/'container-cli.log').exists())
            self.assertFalse(fit_child.exists())
        if scenario=='service_failure':
            self.assertNotEqual(witness['exit_code'],0)
        before={name:sha(self.f.stage/name) for name in ('GPU-launch.json','guardian.json','billing.json')}
        replay=subprocess.run([sys.executable,str(self.f.stage/'CPU-fixture.py'),'guardian',str(self.f.stage)],
            capture_output=True,env=self.f.env,timeout=5)
        self.assertNotEqual(replay.returncode,0)
        self.assertEqual(before,{name:sha(self.f.stage/name) for name in before})
        OBSERVATIONS.append(dict(scenario=scenario,guardian_exit_code=code,original_GPU_bill_unique=True,
            CPU_service_closed_before_bill=bool(witness['complete']),
            CPU_cleanup_unknown_retained=scenario=='cleanup_unknown',GPU_and_CPU_originals_ended=True,
            mode_restored=True,foreign_sentinel_preserved=True,no_replay=True,GPU_submissions=0,ledger_written=False))

    def test_complete_original_service_in_same_allocation_interval(self):self.run_case('success')
    def test_service_start_failure_never_creates_gpu_container(self):self.run_case('start_failure')
    def test_service_failure_stops_original_gpu_and_releases(self):self.run_case('service_failure')
    def test_gpu_failure_also_closes_original_service(self):self.run_case('GPU_failure')
    def test_cpu_cleanup_unknown_retains_failure_and_original_gpu_bill(self):self.run_case('cleanup_unknown')


if __name__=='__main__':unittest.main()
