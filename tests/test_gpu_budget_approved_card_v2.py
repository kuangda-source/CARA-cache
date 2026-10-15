"""All tests use temporary fake ledgers/GPUs/approvals; never a real reservation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
from wcomr.gpu_budget_pool_v2 import SCHEMA, atomic_json, sha


def fixture(root, *, cap=100.):
    pool = ApprovedCardBudgetPool(root)
    pool.path.parent.mkdir(parents=True)
    existing = dict(status='SETTLED', actual_GPUh=1.25, gpu_uuid='GPU-OLD', marker='UNCHANGED_OLD_JOB')
    ledger = dict(schema=SCHEMA, cap_gpu_hours=cap, origin_used_gpu_hours=10.,
                  origin_gpu_jobs_launched=5, jobs={'old': existing}, events=[])
    atomic_json(pool.path, ledger)
    job = dict(job_id='SYNTHETIC_FULL_CARD', run_id='SYNTHETIC_NOT_A_REAL_RUN',
        gpu_uuid='GPU-FAKE-A', forecast_GPUh=13., billed_limit_GPUh=14., source_revision='SYNTHETIC_REV',
        config_sha256='1' * 64, production_CPU_sha256='2' * 64, bound_input_fingerprint='3' * 64,
        launch_id='SYNTHETIC_SINGLE_LAUNCH', cumulative_cap_GPUh=cap, budget_origin_used_GPUh=10.,
        scope_counts=dict(scientific_paths=160, full_warmup_paths=20, total_paths=180))
    approval = dict(kind='SPECIFIC_WHOLE_CARD_APPROVAL', direct_user_authorization=True,
        user_reply_quote='SYNTHETIC FIXTURE, NO HUMAN APPROVAL ISSUED',
        whole_card_run=job['run_id'], forecast_complete_GPUh=job['forecast_GPUh'],
        **{k: copy.deepcopy(job[k]) for k in ('source_revision', 'launch_id', 'gpu_uuid',
            'config_sha256', 'production_CPU_sha256', 'bound_input_fingerprint', 'scope_counts',
            'billed_limit_GPUh', 'cumulative_cap_GPUh', 'budget_origin_used_GPUh')})
    path = Path(root)/'synthetic-approval.json';atomic_json(path, approval)
    job['authorization_sha256'] = sha(path)
    gpu = dict(uuid=job['gpu_uuid'], name='SYNTHETIC RTX A6000', compute_cap='8.6', memory_used_mib=0., pids=[])
    return pool, ledger, job, gpu, path, approval


class ApprovedWholeCardControls(unittest.TestCase):
    def test_reserve_full_limit_then_add_actual_once(self):
        with tempfile.TemporaryDirectory() as root:
            pool, before, job, gpu, path, _ = fixture(root)
            reserved = pool.reserve_specific_whole_card(job, gpu, path)
            self.assertEqual(pool.accounting(reserved)['reserved_gpu_hours'], 14.)
            self.assertEqual(reserved['jobs']['old'], before['jobs']['old'])
            settled = pool.settle(job['job_id'], 13.5, 'a' * 64)
            self.assertEqual(pool.accounting(settled)['used_gpu_hours'], 24.75)
            self.assertEqual(pool.accounting(settled)['reserved_gpu_hours'], 0.)
            self.assertEqual(settled['cap_gpu_hours'], before['cap_gpu_hours'])
            self.assertEqual(settled['origin_used_gpu_hours'], before['origin_used_gpu_hours'])
            self.assertEqual(settled['jobs']['old'], before['jobs']['old'])
            again = pool.settle(job['job_id'], 13.5, 'a' * 64)
            self.assertEqual(pool.accounting(again)['used_gpu_hours'], 24.75)

    def test_standing_rule_cannot_authorize_large_card(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, job, gpu, path, approval = fixture(root)
            approval['kind'] = 'STANDING_STRICT_UNDER12';atomic_json(path, approval)
            job['authorization_sha256'] = sha(path)
            with self.assertRaises(ValueError): pool.reserve_specific_whole_card(job, gpu, path)
            self.assertEqual(pool.accounting(json.loads(pool.path.read_text()))['reserved_gpu_hours'], 0.)

    def test_changed_card_price_source_or_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, original, gpu, path, _ = fixture(root)
            for key, bad in [('forecast_GPUh', 12.5), ('launch_id', 'other'), ('source_revision', 'other'),
                             ('production_CPU_sha256', '4' * 64), ('bound_input_fingerprint', '5' * 64)]:
                job = copy.deepcopy(original);job[key] = bad
                with self.assertRaises(ValueError): pool.reserve_specific_whole_card(job, gpu, path)
            job = copy.deepcopy(original);job['scope_counts']['total_paths'] = 179
            with self.assertRaises(ValueError): pool.reserve_specific_whole_card(job, gpu, path)

    def test_duplicate_and_busy_UUID_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, job, gpu, path, _ = fixture(root)
            busy = {**gpu, 'pids': [123]}
            with self.assertRaises(ValueError): pool.reserve_specific_whole_card(job, busy, path)
            pool.reserve_specific_whole_card(job, gpu, path)
            with self.assertRaises(ValueError): pool.reserve_specific_whole_card(job, gpu, path)
            self.assertEqual(pool.accounting(json.loads(pool.path.read_text()))['reserved_gpu_hours'], 14.)

    def test_real_balance_and_original_window_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, job, gpu, path, _ = fixture(root, cap=21.)
            with self.assertRaisesRegex(ValueError, 'cumulative balance'):
                pool.reserve_specific_whole_card(job, gpu, path)
        with tempfile.TemporaryDirectory() as root:
            pool, _, job, gpu, path, approval = fixture(root)
            job['budget_origin_used_GPUh'] = approval['budget_origin_used_GPUh'] = 0.
            atomic_json(path, approval);job['authorization_sha256'] = sha(path)
            with self.assertRaisesRegex(ValueError, 'original pool origin'):
                pool.reserve_specific_whole_card(job, gpu, path)

    def test_original_under12_method_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, job, gpu, _, _ = fixture(root)
            with self.assertRaises(ValueError): pool.reserve(job, gpu)
            job.update(forecast_GPUh=9., billed_limit_GPUh=10.)
            result = pool.reserve(job, gpu)
            self.assertEqual(pool.accounting(result)['reserved_gpu_hours'], 10.)


if __name__ == '__main__':
    unittest.main()
