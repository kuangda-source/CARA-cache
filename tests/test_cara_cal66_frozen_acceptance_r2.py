"""Counterfactual acceptance checks based on the completed real CPU receipt."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_cara_cal66_entry_cpu_r2 import accept
from audit_cara_cal66_recovery_preparation_r2 import audit

CAPTURE = ROOT / 'reports/cara_CAL66_frozen_entry_CPU_progress_r3_20261025_2030.json'
ACCEPTED = ROOT / 'reports/cara_CAL66_frozen_entry_CPU_accepted_r3_20261025.json'
QUOTE = ROOT / 'manifests/cara_CAL66_full_recovery_quote_r2_20261025.json'

class FrozenAcceptance(unittest.TestCase):
    def setUp(self):
        self.v = json.loads(CAPTURE.read_text())

    def reseal_proof(self):
        raw = (json.dumps(self.v['proof']['data'], indent=2, allow_nan=False) + '\n').encode()
        self.v['proof']['sha256'] = hashlib.sha256(raw).hexdigest()

    def test_complete_real_original(self):
        self.assertTrue(accept(self.v)['frozen_request_chain_CPU_accepted'])

    def test_failed_fixture_and_legacy_acceptance_cannot_pass(self):
        for name in ('cara_CAL66_frozen_entry_CPU_check_r2_20261025_2017.json',
                     'cara_CAL66_entry_CPU_exited_r1_20261025.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                accept(json.loads((ROOT / 'reports' / name).read_text()))

    def test_running_nonzero_oom_or_gpu_visible_refused(self):
        for key, value in (('Running', True), ('ExitCode', 1), ('OOMKilled', True)):
            v = copy.deepcopy(self.v); v['container']['state'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): accept(v)
        self.v['container']['device_requests'] = [{'Count': 1}]
        with self.assertRaises(ValueError): accept(self.v)

    def test_mutable_boundary_or_incomplete_preload_refused(self):
        for key, value in (('actual_class_frozen', False), ('actual_class', 'fixture.Sample'),
                           ('preload_validated_slots', 65), ('old_bug_reproduced', False)):
            original = copy.deepcopy(self.v)
            self.v['proof']['data']['frozen_boundary'][key] = value; self.reseal_proof()
            with self.subTest(key=key), self.assertRaises(ValueError): accept(self.v)
            self.v = original

    def test_missing_flow_refused_after_valid_reseal(self):
        self.v['proof']['data']['numeric']['checks'].pop(); self.reseal_proof()
        with self.assertRaises(ValueError): accept(self.v)

    def test_old_mutable_numeric_fixture_refused_after_valid_reseal(self):
        self.v['proof']['data']['numeric']['checks'][0]['actual_frozen_InferenceArguments'] = False
        self.reseal_proof()
        with self.assertRaises(ValueError): accept(self.v)

    def test_changed_alpha_or_failed_replay_refused(self):
        for key in ('original_alpha_and_D_preserved', 'failed_slot_replay_refused', 'writer_failure_retained'):
            original = copy.deepcopy(self.v)
            self.v['proof']['data']['numeric']['checks'][0][key] = False; self.reseal_proof()
            with self.subTest(key=key), self.assertRaises(ValueError): accept(self.v)
            self.v = original

    def test_changed_runtime_or_missing_class_binding_refused(self):
        self.v['runtime_actual_sha256']['cosmos_predict2/config.py'] = '0' * 64
        with self.assertRaises(ValueError): accept(self.v)
        self.setUp()
        self.v['registration']['runtime_source_sha256'].pop('cosmos_predict2/config.py')
        with self.assertRaises(ValueError): accept(self.v)

    def test_broken_proof_hash_refused(self):
        self.v['proof']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): accept(self.v)

    def test_reuse_only_unchanged_components_and_never_gpu_permission(self):
        v = audit(CAPTURE, ACCEPTED, QUOTE)
        self.assertTrue(v['old_entry_acceptance_superseded'])
        self.assertFalse(v['GPU_dispatch_ready']); self.assertFalse(v['new_GPU_authorization'])
        self.assertEqual(v['registered_paths'], 66)
        self.assertEqual(len(v['repaired_source_sha256']), 3)

if __name__ == '__main__': unittest.main()
