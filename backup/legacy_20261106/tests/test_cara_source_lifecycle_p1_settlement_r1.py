"""Production-shaped simulated captures and real temporary ledger I/O only."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_cara_source_lifecycle_p1_central_r1 as reservation_tests
from test_cara_budget_lifecycle_r1 import fixture, put
from wcomr import cara_source_lifecycle_p1_central_r1 as central
from wcomr.cara_s_endpoint_lifecycle_r1 import IDENTITY, SOURCE as LIFECYCLE_SOURCE
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr.policy_price_terminal_r1 import record


class P1SettlementTests(unittest.TestCase):
    setUp = reservation_tests.P1CentralTests.setUp

    def financial(self):
        envelope, snapshot = self.f.reserved()
        capture, _, _ = fixture(run_id=central.RUN, billed_limit_GPUh=18., host='two_card',
            gpu_uuid=self.f.authority['gpu_uuid'], extra_sources={
                central.SOURCE:sha(central.__file__), LIFECYCLE_SOURCE:sha(Path(central.__file__).parent/'cara_s_endpoint_lifecycle_r1.py')})
        identity = {k:self.f.authority[k] for k in IDENTITY}
        registration = record(capture,'registration')
        registration.update({k:identity[k] for k in ('host','stage','source_revision')})
        reg_sha = put(capture,'registration',registration)
        auth_sha = put(capture,'authorization',self.f.authority)
        job = dict(envelope['job'],registration_sha256=reg_sha,authorization_sha256=auth_sha)
        env_sha = put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
        launch = record(capture,'launch');launch.update(identity,CPU_fixture_only=False,
            registration_sha256=reg_sha,authorization_sha256=auth_sha,central_reservation_sha256=env_sha)
        expected = put(capture,'launch',launch)
        capture['container']['manifest_sha256'] = reg_sha
        for name in ('pending_release','billing','guardian'):
            value = record(capture,name);value.update(identity)
            if name=='guardian':
                value.update(status='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1',billing_sha256=capture['files']['billing']['sha256'])
                value['container_terminal_witness']['container'] = capture['container']
            put(capture,name,value)
        ledger = snapshot['ledger'];ledger['jobs'][central.RUN] = job;ledger.update(self.f.pool.accounting(ledger))
        atomic_json(self.f.pool.path,ledger)
        return capture,expected

    def test_unique_actual_settlement_preserves_increment_and_old_holds(self):
        capture, expected = self.financial();before = self.f.pool.read()
        first = central.settle(self.f.project,capture,expected);raw = self.f.pool.path.read_bytes()
        self.assertEqual(first, central.settle(self.f.project,capture,expected))
        self.assertEqual(raw,self.f.pool.path.read_bytes())
        after = self.f.pool.read();self.assertEqual(after['cap_gpu_hours'],250.)
        self.assertEqual(after['reserved_gpu_hours'],16.5)
        self.assertEqual(after['jobs'][central.RUN]['actual_GPUh'],.05)
        self.assertEqual(len(after['events']),len(before['events'])+1)
        for name,value in before['jobs'].items():
            if name!=central.RUN:self.assertEqual(after['jobs'][name],value)

    def test_lost_ledger_write_recovers_original_settlement_only(self):
        capture, expected = self.financial();before = self.f.pool.path.read_bytes()
        with patch.object(central,'atomic_json',side_effect=OSError('Original write lost')):
            with self.assertRaises(OSError):central.settle(self.f.project,capture,expected)
        self.assertEqual(before,self.f.pool.path.read_bytes())
        saved = read_record(self.f.project/'reports'/(central.RUN+'.central-settlement.json'))
        self.assertEqual(saved,central.settle(self.f.project,capture,expected))
        self.assertEqual(saved['central_after'],self.f.pool.read())

    def test_receipt_failure_and_unknown_original_never_charge(self):
        capture, expected = self.financial();before = self.f.pool.path.read_bytes()
        with patch.object(central,'create',side_effect=OSError('Receipt unavailable')):
            with self.assertRaises(OSError):central.settle(self.f.project,capture,expected)
        self.assertEqual(before,self.f.pool.path.read_bytes())
        capture['process_observations']['runner']['original_live'] = None
        with self.assertRaises(ValueError):central.settle(self.f.project,capture,expected)
        self.assertEqual(before,self.f.pool.path.read_bytes())

    def test_failed_overrun_keeps_whole_actual_bill(self):
        capture, expected = self.financial()
        billing = record(capture,'billing');billing.update(ended_monotonic=20+19*3600,wall_seconds=19*3600,actual_GPUh=19.)
        bill_sha = put(capture,'billing',billing)
        guardian = record(capture,'guardian');guardian.update(ended_monotonic=billing['ended_monotonic'],billing_sha256=bill_sha,
            error_type='TimeoutError',container_exit_code=1)
        capture['container']['state']['ExitCode'] = 1
        guardian['container_terminal_witness']['container'] = capture['container'];put(capture,'guardian',guardian)
        settled = central.settle(self.f.project,capture,expected)
        self.assertEqual(settled['central_after']['jobs'][central.RUN]['actual_GPUh'],19.)
        self.assertTrue(settled['central_after']['budget_overrun_recorded'])
        self.assertEqual(settled['central_after']['reserved_gpu_hours'],16.5)
        self.assertEqual(settled,central.settle(self.f.project,capture,expected))

    def test_changed_authority_or_bill_cannot_recharge(self):
        capture, expected = self.financial();central.settle(self.f.project,capture,expected)
        before = self.f.pool.path.read_bytes()
        billing = record(capture,'billing');billing['actual_GPUh'] += .01;put(capture,'billing',billing)
        with self.assertRaises(ValueError):central.settle(self.f.project,capture,expected)
        self.assertEqual(before,self.f.pool.path.read_bytes())


if __name__ == '__main__':
    unittest.main()
