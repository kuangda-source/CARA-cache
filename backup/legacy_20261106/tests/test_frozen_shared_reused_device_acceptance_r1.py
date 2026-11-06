"""Saved original captures only; no network, model or GPU operations."""
import copy
import unittest
from pathlib import Path

from wcomr import frozen_shared_reused_device_acceptance_r1 as audit

ROOT = Path(__file__).resolve().parents[1]


class PriorRequestRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = audit.read_json(ROOT / 'reports/wc_paper_N07_frozen_shared180_R1_terminal_collection_20261017_0530.json.gz')
        cls.launch = cls.value['launch']
        cls.later = audit.read_json(ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_GPU_launch_20261017.json')['dispatch']
        cls.admission = audit.read_json(ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_ready_admission_acceptance_20261017.json')

    def context(self, value=None, later=None, admission=None):
        return audit.released_request_context(value or self.value, self.launch,
                                             later or self.later, admission or self.admission)

    def test_actual_old_failure_is_fully_retained_and_capture_is_immutable(self):
        from wcomr.frozen_shared_production_r1 import fingerprint
        before = fingerprint(self.value)
        result = audit.accept(self.value, self.launch, self.later, self.admission)
        self.assertFalse(result['scientific_full_scope_accepted'])
        self.assertTrue(result['terminal_receipt_audit_accepted'])
        self.assertEqual(result['original_status_counts'], dict(COMPLETE=40, TEXT_REJECTED=8,
                         VIDEO_REJECTED=0, TECH_FAILED=1, NOT_REACHED=131))
        self.assertEqual(result['accepted_scientific_videos'], 20)
        self.assertEqual(result['scored_scientific_videos'], 20)
        self.assertFalse(result['original_request_release_context']['physical_UUID_currently_idle'])
        self.assertEqual(before, fingerprint(self.value))
        self.assertEqual(audit.sha(ROOT / 'src/wcomr/frozen_shared_acceptance_r1.py'), audit.ORIGINAL_SHA)

    def test_original_gate_failure_is_preserved(self):
        from wcomr.frozen_shared_acceptance_r1 import accept
        with self.assertRaisesRegex(ValueError, 'Own UUID must be released'):
            accept(self.value, self.launch)

    def test_unknown_compute_pid_is_not_attributed(self):
        v = copy.deepcopy(self.value)
        v['compute_apps'] = self.launch['gpu_uuid'] + ', 999999999\n'
        with self.assertRaises(ValueError): self.context(v)

    def test_old_compute_pid_is_not_released(self):
        v = copy.deepcopy(self.value)
        v['compute_apps'] = self.launch['gpu_uuid'] + ', ' + str(self.launch['supervisor_pid'])
        with self.assertRaises(ValueError): self.context(v)

    def test_live_old_handle_is_not_released(self):
        v = copy.deepcopy(self.value)
        v['original_processes']['supervisor_pid'] = self.launch['supervisor_identity']
        with self.assertRaises(ValueError): self.context(v)

    def test_new_reservation_identity_cannot_change(self):
        for key in ('source_revision', 'launch_id', 'authorization_sha256', 'supervisor_start_ticks'):
            v = copy.deepcopy(self.value)
            v['pool']['jobs'][audit.LATER_RUN][key] = 'WRONG'
            with self.subTest(key=key), self.assertRaises(ValueError): self.context(v)

    def test_later_must_be_active_and_specifically_approved(self):
        for key, replacement in [('status', 'SETTLED'), ('kind', 'UNAPPROVED')]:
            v = copy.deepcopy(self.value)
            v['pool']['jobs'][audit.LATER_RUN][key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError): self.context(v)

    def test_prior_bill_must_be_settled(self):
        v = copy.deepcopy(self.value)
        v['pool']['jobs'][self.launch['run_id']]['status'] = 'RESERVED_OR_RUNNING'
        with self.assertRaises(ValueError): self.context(v)

    def test_failed_later_admission_is_not_sufficient(self):
        a = copy.deepcopy(self.admission); a['GPU_admitted'] = False
        with self.assertRaises(ValueError): self.context(admission=a)

    def test_later_time_must_follow_original_settlement(self):
        l = copy.deepcopy(self.later); l['started_unix'] = 0
        with self.assertRaises(ValueError): self.context(later=l)

    def test_other_gpu_activity_does_not_change_original_release(self):
        v = copy.deepcopy(self.value); v['compute_apps'] += '\nGPU-OTHER, 2222222\n'
        self.assertFalse(self.context(v)['physical_UUID_currently_idle'])

    def test_scientific_rows_still_must_match(self):
        v = copy.deepcopy(self.value); v['final']['rows'][0]['status'] = 'NOT_REACHED'
        with self.assertRaises(ValueError): audit.accept(v, self.launch, self.later, self.admission)

    def test_original_inverse_and_ast_are_exact(self):
        proof = audit.derived_acceptor()[3]
        self.assertTrue(proof['inverse_bytes_and_AST_equal'])
        self.assertTrue(proof['original_financial_tensor_video_statistics_gates_unchanged'])
        self.assertFalse(proof['original_capture_fields_written'])


if __name__ == '__main__':
    unittest.main()
