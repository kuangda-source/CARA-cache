"""Regression against the actual published E1 launch, without GPU/media work."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from wcomr import cara_endpoint7_acceptance_interface_r1 as repair
from wcomr import cara_s_endpoint_artifacts_r1 as original

ROOT = Path(__file__).resolve().parents[1]


class ActualLaunchCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = json.loads((ROOT / 'reports/cara_endpoint7_final_original_r1_20261101.json').read_text())['result']['lifecycle']
        cls.assets = json.loads((ROOT / repair.ASSETS).read_text())
        from wcomr.cara_endpoint7_binding_r1 import proposal
        selected = json.loads((ROOT / 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
        old = json.loads((ROOT / 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json').read_text())
        cls.proposal = proposal(selected, old)
        registration = repair.record(cls.capture, 'registration')
        encoded = (json.dumps(cls.proposal, indent=2, allow_nan=False) + '\n').encode()
        assert hashlib.sha256(encoded).hexdigest() == registration['payload_sha256'][original.PROPOSAL]

    def test_real_launch_without_manual_model_field(self):
        launch = repair.record(self.capture, 'launch')
        self.assertNotIn('model_sha256', launch)
        before = copy.deepcopy(self.capture)
        result = repair.model_identity(self.capture, self.proposal, self.assets,
                                       self.proposal['model_sha256'])
        self.assertEqual(result['model_sha256'], self.proposal['model_sha256'])
        self.assertFalse(result['original_launch_has_model_sha256'])
        self.assertEqual(self.capture, before)

    def test_changed_actual_model_rejected(self):
        with self.assertRaisesRegex(ValueError, 'model identity differs'):
            repair.model_identity(self.capture, self.proposal, self.assets, '0' * 64)

    def test_conflicting_explicit_launch_model_rejected(self):
        capture = copy.deepcopy(self.capture)
        launch = repair.record(capture, 'launch')
        launch['model_sha256'] = '0' * 64
        raw = json.dumps(launch)
        capture['files']['launch'].update(raw_utf8=raw, bytes=len(raw.encode()),
                                         sha256=hashlib.sha256(raw.encode()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'model identity differs'):
            repair.model_identity(capture, self.proposal, self.assets, self.proposal['model_sha256'])

    def test_duplicate_registered_model_rejected(self):
        assets = copy.deepcopy(self.assets)
        row = next(row for row in assets['files'] if row['digest'] == self.proposal['model_sha256'])
        assets['files'].append(row)
        with self.assertRaisesRegex(ValueError, 'One registered'):
            repair.model_identity(self.capture, self.proposal, assets, self.proposal['model_sha256'])

    def test_unregistered_model_rejected(self):
        proposal = dict(self.proposal, model_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'One registered'):
            repair.model_identity(self.capture, proposal, self.assets, '0' * 64)

    def test_wrong_gpu_rejected(self):
        proposal = dict(self.proposal, gpu_uuid='GPU-other')
        with self.assertRaisesRegex(ValueError, 'host/GPU binding differs'):
            repair.model_identity(self.capture, proposal, self.assets, proposal['model_sha256'])

    def test_source_record_and_function_are_not_mutated(self):
        def read_launch(capture, *, key='launch'):
            return record(capture, key)
        # Bind exactly the original record dependency without changing its module.
        original_function = repair.scoped_function(read_launch, record=repair.record)
        def derived_record(capture, key):
            return dict(repair.record(capture, key), model_sha256=self.proposal['model_sha256'])
        adapted = repair.scoped_function(original_function, record=derived_record)
        self.assertIs(original_function.__code__, adapted.__code__)
        self.assertNotIn('model_sha256', original_function(self.capture))
        self.assertIn('model_sha256', adapted(self.capture))
        self.assertIs(original.record, repair.record)

    def test_unreleased_gpu_cannot_open_model_or_artifacts(self):
        with patch.object(repair, 'released_lifecycle', side_effect=ValueError('still live')), \
                patch.object(repair, 'file_sha', side_effect=AssertionError('opened early')):
            with self.assertRaisesRegex(ValueError, 'still live'):
                repair.released_artifacts({}, '', {})


if __name__ == '__main__':
    unittest.main()
