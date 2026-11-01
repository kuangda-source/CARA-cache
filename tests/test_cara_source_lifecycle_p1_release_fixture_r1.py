"""The synthetic release fixture obeys the real immutable lifecycle schema."""
import copy
import unittest

from check_cara_source_lifecycle_p1_released_fixture_r1 import settled_fixture
from test_cara_budget_lifecycle_r1 import fixture,put
from wcomr.cara_s_endpoint_lifecycle_r1 import released_lifecycle
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUN_ID,GPU
from wcomr.cara_s_endpoint_lifecycle_r1 import SOURCE
from wcomr import cara_s_endpoint_lifecycle_r1 as lifecycle
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.policy_price_terminal_r1 import record


class P1ReleaseFixtureTests(unittest.TestCase):
    def setUp(self):
        self.capture,self.expected,self.job=fixture(host='two_card',gpu_uuid=GPU,run_id=RUN_ID,
            extra_sources={SOURCE:file_sha(lifecycle.__file__)})
        guardian=record(self.capture,'guardian');guardian['status']='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1';put(self.capture,'guardian',guardian)

    def test_original_schema_closes_fake_cost_and_release(self):
        result=released_lifecycle(self.capture,self.expected,settled_fixture(self.capture,self.job),cpu_validation=True)
        self.assertTrue(result['container_exit_success'])
        self.assertTrue(result['cost_settled'])
        self.assertTrue(result['GPU_released'])

    def test_fake_settlement_preserves_original_old_liability_and_origin(self):
        settlement=settled_fixture(self.capture,self.job)
        self.assertEqual(settlement['central_after']['reserved_gpu_hours'],16.5)
        for name in ('cap_gpu_hours','origin_used_gpu_hours','origin_gpu_jobs_launched'):
            self.assertEqual(settlement['central_before'][name],settlement['central_after'][name])

    def test_fake_settlement_cannot_clear_unknown_original_release(self):
        self.capture['files']['pending_release']={'exists':False}
        result=released_lifecycle(self.capture,self.expected,settled_fixture(self.capture,self.job),cpu_validation=True)
        self.assertFalse(result['container_exit_success'])
        self.assertFalse(result['GPU_released'])


if __name__=='__main__':unittest.main()
