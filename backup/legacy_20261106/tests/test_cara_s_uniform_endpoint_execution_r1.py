"""Card composition and read-only failure recovery without model execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card, inspect_original

ROOT = Path(__file__).resolve().parents[1]


class CollectionControls(unittest.TestCase):
    def setUp(self):
        self.proposal = json.loads((ROOT / 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json').read_text())
        self.base = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        self.bound = map_physical_slots(self.proposal, self.base['roles']['UNIFORM19_C']['policy'])
        self.bound.update(CPU_fixture_only=True, original_freeze_sha256='CPU-FIXTURE',
                          proposal_scope_sha256=self.proposal['scope_sha256'])
        self.rehash()

    def rehash(self):
        self.bound['binding_sha256'] = digest({k: v for k, v in self.bound.items() if k != 'binding_sha256'})

    def card(self): return request_card(self.proposal, self.bound, self.base)

    def test_full_card_preserves_all_positions_and_alias_rows(self):
        card = self.card()
        self.assertEqual(len(card['physical_matrix']), 32)
        self.assertEqual(len(card['formal_matrix']), 24)
        self.assertEqual(len(card['roles']), 6)
        self.assertTrue(all(s['phase'] == 'B' and s['section'].startswith('B_') for s in card['physical_matrix']))
        self.assertEqual(card['roles']['F19_A1'], self.base['roles']['F19_A1'])
        self.assertEqual(card['roles']['ALLD'], self.base['roles']['ALLD'])
        self.assertFalse(card['GPU_dispatch_ready'])

    def test_changed_mapping_even_rehashed_is_refused(self):
        self.bound['physical_matrix'].pop(); self.rehash()
        with self.assertRaisesRegex(ValueError, 'equivalence'): self.card()

    def test_changed_proposal_refused(self):
        self.proposal['profile']['max_source_age'] = 27
        with self.assertRaisesRegex(ValueError, 'Exact proposal'): self.card()

    def test_different_parent_refused(self):
        self.base['scope_sha256'] = 'OTHER'
        with self.assertRaisesRegex(ValueError, 'parent'): self.card()

    def test_unknown_and_failed_remain_non_dispatchable(self):
        card = self.card()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'collection.json'
            for status, row_status in [('RUNNING', 'RUNNING'), ('FAILED_NO_REPLAY', 'TECH_FAILED')]:
                state = dict(phase='B', status=status, scope_sha256=card['scope_sha256'],
                    rows=[dict(slot=s, status=row_status if i == 0 else 'NOT_REACHED')
                          for i, s in enumerate(card['physical_matrix'])])
                path.write_text(json.dumps(state))
                before = path.read_bytes()
                recovery = inspect_original(card, path, cpu_validation=True)
                self.assertEqual(path.read_bytes(), before)
                self.assertFalse(recovery['dispatch_allowed'])
                self.assertFalse(recovery['scientific_accepted'])
                self.assertEqual(recovery['counts']['NOT_REACHED'], 31)

    def test_reordered_original_rows_refused(self):
        card = self.card()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'collection.json'
            path.write_text(json.dumps(dict(phase='B', status='RUNNING', scope_sha256=card['scope_sha256'],
                rows=[dict(slot=s, status='NOT_REACHED') for s in reversed(card['physical_matrix'])])))
            with self.assertRaisesRegex(ValueError, 'identity'): inspect_original(card, path, cpu_validation=True)

    def test_partial_cannot_claim_terminal(self):
        card = self.card()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'collection.json'
            path.write_text(json.dumps(dict(phase='B', status='TERMINAL', scope_sha256=card['scope_sha256'],
                rows=[dict(slot=s, status='NOT_REACHED') for s in card['physical_matrix']])))
            with self.assertRaisesRegex(ValueError, 'Incomplete'): inspect_original(card, path, cpu_validation=True)


if __name__ == '__main__': unittest.main()
