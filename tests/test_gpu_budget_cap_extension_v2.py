"""Financial controls use temporary synthetic ledgers, never the server pool."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.gpu_budget_cap_extension_v2 import EVENT, extend_cap
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA, atomic_json


def fixture(root):
    root = Path(root)
    pool = BudgetPool(root)
    value = dict(schema=SCHEMA, cap_gpu_hours=30., origin_used_gpu_hours=10.,
        origin_gpu_jobs_launched=7, authorization={'historical': 'PRESERVE'},
        jobs={'old': dict(status='SETTLED', actual_GPUh=2., gpu_uuid='GPU-SYNTHETIC-OLD'),
              'live': dict(status='RESERVED_OR_RUNNING', billed_limit_GPUh=5.,
                           gpu_uuid='GPU-SYNTHETIC-LIVE')}, events=[])
    value.update(pool.accounting(value)); atomic_json(pool.path, value)
    authority = dict(approval_state='HUMAN_APPROVED', direct_user_authorization=True,
        budget_cap_extension_explicitly_approved=True, approval_id='SYNTHETIC_ONLY_NOT_REAL_APPROVAL',
        user_reply_quote='SYNTHETIC FIXTURE; NO HUMAN APPROVAL ISSUED',
        previous_cumulative_cap_GPUh=30., cumulative_cap_GPUh=50., budget_origin_used_GPUh=10.)
    path = root/'synthetic-approval.json'; atomic_json(path, authority)
    return pool, value, path, authority


class CapExtensionControls(unittest.TestCase):
    def test_preserve_every_job_origin_and_actual_with_active_reservation(self):
        with tempfile.TemporaryDirectory() as root:
            pool, old, path, _ = fixture(root)
            result = extend_cap(root, path)['pool']
            allowed = {'cap_gpu_hours', 'available_gpu_hours', 'events'}
            self.assertEqual({k: v for k, v in result.items() if k not in allowed},
                             {k: v for k, v in old.items() if k not in allowed})
            self.assertEqual(result['cap_gpu_hours'], 50.)
            self.assertEqual(result['used_gpu_hours'], 12.)
            self.assertEqual(result['reserved_gpu_hours'], 5.)
            self.assertEqual(result['available_gpu_hours'], 33.)
            self.assertEqual(result['events'][-1]['type'], EVENT)
            original_bytes = pool.path.read_bytes()
            again = extend_cap(root, path)
            self.assertEqual(again['status'], 'ORIGINAL_CAP_EXTENSION_ALREADY_APPLIED_NO_WRITE')
            self.assertEqual(original_bytes, pool.path.read_bytes())

    def test_proposal_missing_permission_and_wrong_window_do_not_write(self):
        for key, bad in [('approval_state', 'PROPOSAL'), ('direct_user_authorization', False),
                         ('budget_cap_extension_explicitly_approved', False), ('user_reply_quote', ''),
                         ('approval_id', ''), ('previous_cumulative_cap_GPUh', 31.),
                         ('cumulative_cap_GPUh', 20.), ('budget_origin_used_GPUh', 0.)]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as root:
                pool, _, path, authority = fixture(root)
                authority[key] = bad; atomic_json(path, authority)
                original = pool.path.read_bytes()
                with self.assertRaises(ValueError): extend_cap(root, path)
                self.assertEqual(pool.path.read_bytes(), original)

    def test_changed_approval_cannot_reapply_an_existing_event(self):
        with tempfile.TemporaryDirectory() as root:
            pool, _, path, authority = fixture(root)
            extend_cap(root, path); original = pool.path.read_bytes()
            authority['user_reply_quote'] += ' CHANGED'; atomic_json(path, authority)
            with self.assertRaisesRegex(ValueError, 'Conflicting'): extend_cap(root, path)
            self.assertEqual(pool.path.read_bytes(), original)

    def test_stored_accounting_mismatch_is_not_silently_repaired(self):
        with tempfile.TemporaryDirectory() as root:
            pool, value, path, _ = fixture(root)
            value['used_gpu_hours'] = 0.; atomic_json(pool.path, value)
            original = pool.path.read_bytes()
            with self.assertRaises(ValueError): extend_cap(root, path)
            self.assertEqual(pool.path.read_bytes(), original)

    def test_foreign_approval_and_new_window_are_refused(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as other:
            pool, _, _, _ = fixture(root)
            _, _, foreign, _ = fixture(other); original = pool.path.read_bytes()
            with self.assertRaises(ValueError): extend_cap(root, foreign)
            self.assertEqual(pool.path.read_bytes(), original)
        with tempfile.TemporaryDirectory() as root:
            pool, _, path, _ = fixture(root); pool.path.unlink()
            with self.assertRaises(ValueError): extend_cap(root, path)
            self.assertFalse(pool.path.exists())


if __name__ == '__main__': unittest.main()
