"""The cross-worktree handoff must reject altered published evidence."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('handoff', ROOT / 'scripts/accept_cara_fast_sq_cpu_handoff_r1.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)
REVISION = '15b597da077d2bf33fb23150d4c4e7ffc2290af5'


class HandoffEvidenceTests(unittest.TestCase):
    def test_changed_published_production_source_is_refused(self):
        original = handoff.blob
        def changed(revision, name):
            data = original(revision, name)
            return data + b'\n' if revision == REVISION and name == 'src/wcomr/sq_s_execution_r2.py' else data
        with patch.object(handoff, 'blob', side_effect=changed), self.assertRaisesRegex(ValueError, 'production-critical source changed'):
            handoff.review(REVISION)

    def test_altered_original_capture_is_refused(self):
        original = handoff.blob
        def changed(revision, name):
            data = original(revision, name)
            if name.endswith('four_card_cpu_terminal_capture_r6_20261030.json'):
                value = json.loads(data)
                value['container_state']['ExitCode'] = 1
                return json.dumps(value).encode()
            return data
        with patch.object(handoff, 'blob', side_effect=changed), self.assertRaisesRegex(ValueError, 'capture hash changed'):
            handoff.review(REVISION)

    def test_inflated_saved_acceptance_is_refused(self):
        original = handoff.blob
        def changed(revision, name):
            data = original(revision, name)
            if name.endswith('four_card_cpu_accepted_r6_20261030.json'):
                value = json.loads(data)
                value['complete_tiny_paths'] = 21
                return json.dumps(value).encode()
            return data
        with patch.object(handoff, 'blob', side_effect=changed), self.assertRaisesRegex(ValueError, 'Saved acceptance differs'):
            handoff.review(REVISION)


if __name__ == '__main__':
    unittest.main()
