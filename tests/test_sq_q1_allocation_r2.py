"""Q1 host wrapper -> original capture -> temporary settlement, GPU ops stubbed."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_sq_q1_execution_r1 import script
from test_sq_q1_terminal_r1 import fixture
from test_sq_gpu_allocation_r1 import Clock,Storage,Operations
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.sq_q1_spec_r1 import RUN
from wcomr.sq_q1_stage_r1 import stage_path
from wcomr.sq_q1_terminal_r1 import settle_original,technical_terminal


@unittest.skipUnless(Path('/proc/self').exists(),'Real Linux child cleanup/lease required')
class WholeAllocationTests(unittest.TestCase):
    def test_guardian_capture_and_settlement_cover_pre_worker_failures(self):
        from wcomr import sq_control_storage_r1 as storage_module
        from wcomr import sq_q1_capture_r1 as capture_module
        from wcomr.sq_gpu_allocation_r1 import SystemOperations
        for case in ('credential','admission','spawn','child_failure','never_created','timeout','unknown','restore'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage=stage_path(project,'two_card')
                saved,scope,pool=fixture(project,stage_name=stage.name)
                output=project/'outputs'/RUN;output.mkdir(parents=True)
                for key,name in dict(launch='GPU-launch.json').items():
                    (stage/name).write_text(saved['files'][key]['raw_utf8'])
                storage=Storage(output);guardian=script('cara_sq_q1_guardian_r1')
                class Q1Operations(Operations):
                    def inspect_container(self,stage,registration_sha,uuid):
                        if self.case=='never_created':return None
                        value=super().inspect_container(stage,registration_sha,uuid)
                        value['Image']='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
                        value['HostConfig'].update(Memory=16*2**30,MemorySwap=16*2**30,CpusetCpus='24,25')
                        return value
                ops=Q1Operations(case);clock=Clock()
                code='import time;time.sleep(60)' if case in ('timeout','unknown') else 'raise SystemExit(7)'
                args=SimpleNamespace(project=project,stage=stage)
                with patch.object(storage_module,'storage_for',return_value=storage),\
                        patch.object(guardian.os,'sched_getaffinity',return_value={24,25}),\
                        patch.object(guardian,'container_arguments',return_value=[sys.executable,'-c',code]):
                    if case in ('child_failure','never_created'):guardian.run(args,'CPU_NON_SECRET',ops=ops,clock=clock)
                    else:
                        with self.assertRaises((ValueError,RuntimeError,OSError,subprocess.TimeoutExpired)):
                            guardian.run(args,None if case=='credential' else 'CPU_NON_SECRET',ops=ops,clock=clock)
                if ops.child is not None:self.assertIsNotNone(ops.child.poll())
                bill=json.loads((output/'Q1-billing.json').read_text())
                self.assertEqual(bill['billing_clock_owner'],'HOST_GUARDIAN')
                self.assertGreaterEqual(bill['wall_seconds'],3)
                self.assertFalse((output/'Q1-supervisor-billing-diagnostic.json').exists())
                state=json.loads((stage/'pg-host-guardian.json').read_text())
                launch=json.loads((stage/'GPU-launch.json').read_text());launch['guardian_identity']=state['identity']
                (stage/'GPU-launch.json').write_text(json.dumps(launch))
                before=pool.path.read_bytes()
                if case in ('unknown','restore'):
                    self.assertFalse(bill['wall_interval_complete']);self.assertEqual(pool.path.read_bytes(),before)
                    continue
                observed=ops.inspect_container(stage,launch['registration_sha256'],launch['gpu_uuid']) if ops.child else None
                with patch.object(SystemOperations,'inspect_container',return_value=observed),\
                        patch.object(capture_module,'same_live_process',return_value=False):
                    captured=capture_module.capture(project,stage,sha(stage/'GPU-launch.json'))
                self.assertEqual(captured['status'],'SQ_Q1_TERMINAL_CAPTURE_R1')
                settlement=settle_original(pool,captured,scope)
                self.assertEqual(settlement['actual_GPUh'],bill['actual_GPUh'])
                self.assertEqual(pool.read()['reserved_gpu_hours'],16.5)
                with self.assertRaises((KeyError,ValueError)):technical_terminal(captured,scope)
                original=sha(output/'Q1-billing.json');pending=sha(output/'Q1-release-pending-central.json')
                with patch.object(storage_module,'storage_for',return_value=storage):
                    with self.assertRaisesRegex(ValueError,'recover only'):
                        guardian.run(args,'CPU_NON_SECRET',ops=ops,clock=clock)
                self.assertEqual(sha(output/'Q1-billing.json'),original)
                self.assertEqual(sha(output/'Q1-release-pending-central.json'),pending)


class PendingReleaseTests(unittest.TestCase):
    def test_original_supervisor_diagnostics_do_not_overwrite_host_bill(self):
        guardian=script('cara_sq_q1_guardian_r1')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);saved,scope,pool=fixture(project);output=project/'outputs'/RUN
            output.mkdir(parents=True);storage=Storage(output)
            for key,name in dict(billing='Q1-billing.json',allocation_release='Q1-allocation-release.json',
                supervisor_billing='Q1-supervisor-billing-diagnostic.json',
                supervisor_release='Q1-supervisor-release-diagnostic.json').items():
                (output/name).write_text(saved['files'][key]['raw_utf8'])
            original=sha(output/'Q1-billing.json')
            guardian.pending_release(project/'.sync/CPU_ONLY',storage)
            pending=json.loads((output/'Q1-release-pending-central.json').read_text())
            self.assertTrue(pending['technical_accepted'])
            self.assertEqual(pending['billing_sha256'],original)
            self.assertEqual(sha(output/'Q1-billing.json'),original)
            self.assertEqual(json.loads((output/'Q1-billing.json').read_text())['wall_seconds'],100)
            self.assertEqual(json.loads((output/'Q1-supervisor-billing-diagnostic.json').read_text())['wall_seconds'],10)


if __name__=='__main__':unittest.main()
