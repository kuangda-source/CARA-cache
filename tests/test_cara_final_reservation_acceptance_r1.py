"""A missing host/root, source drift or identity hit cannot clear final reservations."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import audit_cara_final_reservation_r1 as audit


class FinalReservationAcceptanceTests(unittest.TestCase):
    def values(self):
        return [dict(status='FINAL_RESERVATION_IDENTITY_CAPTURE', host=host,
            source_sha256={n:audit.sha(ROOT/n) for n in audit.SOURCES},
            capture_entry_sha256=audit.sha(Path(audit.__file__)), pool_sha256=audit.sha(ROOT/audit.POOL),
            baseline_sha256=audit.sha(ROOT/audit.BASELINE), GPU_submissions=0, ledger_written=False,
            endpoint_values_exported=False, videos_or_tensors_decoded=False,
            roots=[dict(requested_project=root, documents=[], identity_hits={}, read_errors=[])
                   for root in audit.PROJECTS[host]]) for host in ('four_card', 'two_card')]

    def execute(self, values, local=None):
        local = local or dict(documents=[], identity_mentions=[], read_errors=[])
        with tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
            paths = []
            for i, value in enumerate(values):
                path = Path(folder)/(str(i)+'.json'); path.write_text(json.dumps(value)); paths.append(path)
            with patch.object(audit, 'local_inventory', return_value=local):
                return audit.audit(paths)

    def test_complete_coverage_is_only_scoped_identity_evidence(self):
        result = self.execute(self.values())
        self.assertTrue(result['scoped_no_execution_evidence'])
        self.assertEqual(result['protected_group_count'], 32)
        self.assertTrue(result['original_DEV16_already_used'])
        self.assertTrue(result['first_use_delta_required'])
        self.assertFalse(result['final_GPU_dispatch_ready'])

    def test_missing_host_duplicate_host_or_missing_historical_root_refused(self):
        values = self.values()
        truncated = copy.deepcopy(values); truncated[1]['roots'].pop()
        for rows in (values[:1], [values[0], values[0]], truncated):
            with self.subTest(rows=rows), self.assertRaises(ValueError):self.execute(rows)

    def test_source_or_pool_drift_refused(self):
        for field in ('source_sha256', 'capture_entry_sha256', 'pool_sha256', 'baseline_sha256'):
            values = self.values(); values[1][field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):self.execute(values)

    def test_remote_hit_or_read_error_keeps_all_groups_protected(self):
        for field in ('identity_hits', 'read_errors'):
            values = self.values()
            values[1]['roots'][0][field] = ({'human_051':[dict(location='synthetic')]} if field=='identity_hits'
                else [dict(kind='JSON_SIZE_LIMIT')])
            with self.subTest(field=field):
                result = self.execute(values)
                self.assertFalse(result['scoped_no_execution_evidence'])
                self.assertEqual(result['protected_group_count'], 32)
                self.assertFalse(result['pool_reselected'])

    def test_local_mention_or_error_cannot_clear(self):
        for field in ('identity_mentions', 'read_errors'):
            local = dict(documents=[], identity_mentions=[], read_errors=[])
            local[field] = [dict(ref='synthetic-observation')]
            with self.subTest(field=field):
                self.assertFalse(self.execute(self.values(), local)['scoped_no_execution_evidence'])


if __name__ == '__main__':
    unittest.main()
