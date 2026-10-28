"""Actual S/Q actor persist calls and full journals; GPU/mount observations stubbed."""
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_sq_control_storage_r1 as journal_tests
from test_sq_gpu_allocation_r1 import Operations,Clock
from test_sq_q1_execution_r1 import script
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.history104_storage_r2 import StorageGuard
from wcomr.sq_control_storage_r1 import storage_for
from wcomr.sq_gpu_allocation_r1 import run_allocation
from wcomr.sq_q1_spec_r1 import RUN,PROFILE,QUOTES

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(Path('/proc/self').exists(),'Actual Linux process/lease controls required')
class JournalAllocationTests(unittest.TestCase):
    setUp=journal_tests.JournalTests.setUp
    def fixture(self):
        project=self.root;stage=project/'.sync/CPU_REAL_JOURNAL';stage.mkdir(parents=True)
        self.config['run_id']=RUN
        self.config['output_mount']=str(project/'outputs'/RUN)
        Path(self.config['output_mount']).mkdir(parents=True)
        atomic_json(stage/'history104-storage.json',self.config)
        atomic_json(stage/'registration.json',dict(source_revision='CPU_SYNTHETIC_NO_GPU'))
        target=stage/PROFILE;target.parent.mkdir(parents=True,exist_ok=True)
        atomic_json(target,json.loads((ROOT/PROFILE).read_text()))
        for name in QUOTES.values():
            atomic_json(stage/name,json.loads((ROOT/name).read_text()))
        authority=dict(direct_user_authorization=True,run_id=RUN,host='two_card',
            gpu_uuid='GPU-CPU-SYNTHETIC-ONLY',launch_id='CPU_NO_HUMAN_GPU_AUTHORITY',
            source_revision='CPU_SYNTHETIC_NO_GPU',scope_sha256='a'*64,whole_GPUh=.1)
        return project,stage,authority

    def test_actual_Q1_guardian_persists_allocation_and_pending_release(self):
        project,stage,authority=self.fixture();guardian=script('cara_sq_q1_guardian_r1')
        from wcomr import sq_q1_execution_r1 as execution
        ops=Operations('success')
        with patch.object(execution,'validate',return_value=({},dict(source_revision=authority['source_revision']),authority)),\
                patch.object(StorageGuard,'check',return_value=dict(CPU_fixture_mount_only=True)),\
                patch.object(guardian.os,'sched_getaffinity',return_value={24,25}),\
                patch.object(guardian,'container_arguments',return_value=[sys.executable,'-c','raise SystemExit(0)']):
            result=guardian.run(SimpleNamespace(project=project,stage=stage),'CPU_NON_SECRET',ops=ops,clock=Clock())
        guard=storage_for(stage)
        self.assertEqual(result['container_exit_code'],0)
        self.assertTrue(guard.journal.read('allocation_release')['allocation_release_accepted'])
        self.assertTrue(guard.journal.read('pending_release')['GPU_released'])
        self.assertEqual(guard.journal.read('billing')['billing_clock_owner'],'HOST_GUARDIAN')
        self.assertIsNotNone(ops.child.poll())

    def test_actual_Q1_missing_credentials_still_has_original_durable_bill(self):
        project,stage,authority=self.fixture();guardian=script('cara_sq_q1_guardian_r1')
        from wcomr import sq_q1_execution_r1 as execution
        ops=Operations('success')
        with patch.object(execution,'validate',return_value=({},dict(source_revision=authority['source_revision']),authority)),\
                patch.object(StorageGuard,'check',return_value=dict(CPU_fixture_mount_only=True)),\
                patch.object(guardian.os,'sched_getaffinity',return_value={24,25}):
            with self.assertRaisesRegex(ValueError,'Credential'):
                guardian.run(SimpleNamespace(project=project,stage=stage),None,ops=ops,clock=Clock())
        guard=storage_for(stage)
        self.assertIsNone(ops.child)
        self.assertTrue(guard.journal.read('billing')['wall_interval_complete'])
        self.assertTrue(guard.journal.read('pending_release')['allocation_release_accepted'])

    def test_actual_Q1_supervisor_failure_retains_independent_diagnostic(self):
        project,stage,authority=self.fixture();worker=script('cara_sq_q1_worker_r1')
        from wcomr import sq_q1_execution_r1 as execution,wc73_exclusive_r1 as exclusive
        atomic_json(stage/'pg-host-guardian.json',dict(authority,billing_clock_owner='HOST_GUARDIAN',
            started_monotonic=time.monotonic(),started_unix=time.time()))
        with patch.object(execution,'validate',return_value=({},dict(source_revision=authority['source_revision']),authority)),\
                patch.object(StorageGuard,'check',return_value=dict(CPU_fixture_mount_only=True)),\
                patch.object(exclusive,'observe',return_value=dict(CPU_SYNTHETIC_GPU_OBSERVATION=True)),\
                patch.object(exclusive,'verify',return_value=None),\
                patch.object(worker.subprocess,'Popen',side_effect=OSError('CPU controlled no exec')):
            with self.assertRaisesRegex(OSError,'controlled no exec'):
                worker.supervise(SimpleNamespace(project=project,stage=stage))
        diagnostic=storage_for(stage).journal.read('supervisor_billing_diagnostic')
        self.assertEqual(diagnostic['billing_clock_owner'],'SUPERVISOR_DIAGNOSTIC')
        self.assertFalse(diagnostic['chargeable']);self.assertTrue(diagnostic['diagnostic_only'])
        self.assertFalse((storage_for(stage).output/'Q1-billing.json').exists())

    def test_S_prefix_uses_the_same_real_journal_and_complete_host_clock(self):
        project,stage,authority=self.fixture();ops=Operations('success');guard=storage_for(stage)
        with patch.object(StorageGuard,'check',return_value=dict(CPU_fixture_mount_only=True)):
            result=run_allocation(project,stage,authority,dict(source_revision=authority['source_revision']),guard,
                dict(guardian_release_margin_seconds=180),'S',lambda:[sys.executable,'-c','raise SystemExit(0)'],
                'CPU_NON_SECRET',ops=ops,clock=Clock())
        self.assertEqual(result['status'],'SQ_S_HOST_GUARDIAN_TERMINAL')
        self.assertEqual(guard.journal.read('billing')['status'],'SQ_S_ORIGINAL_WALL_BILL')
        self.assertTrue(guard.journal.read('allocation_release')['allocation_release_accepted'])
        self.assertTrue((guard.output/'S-allocation-release.json').exists())
        self.assertIsNotNone(ops.child.poll())


if __name__=='__main__':unittest.main()
