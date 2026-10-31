"""Real complete-reader CPU fixtures; no production search output is accessed."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import test_cara_budget_complete_r1 as fixture_module
from test_cara_budget_lifecycle_r1 import fixture
from wcomr import cara_budget_complete_r1 as complete
from wcomr import cara_s_uniform_endpoint_binding_r1 as binding
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import sha

PROPOSAL = 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'


class FreezeBinding(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / PROPOSAL).read_text())
        self.original_plan = copy.deepcopy(self.plan)
        self.f = fixture_module.CompleteTests()
        self.addCleanup(self.f.doCleanups)
        with patch.object(fixture_module, 'fixture', side_effect=lambda: fixture(
                host='two_card', gpu_uuid=self.plan['gpu_uuid'], billed_limit_GPUh=14.)):
            self.f.setUp()
        self.plan['CPU_fixture_only'] = True
        for key in ('launch_id', 'run_id', 'source_revision', 'scope_sha256'):
            self.plan['budget_comparator']['original_' + key] = self.f.launch[key]
        self.rehash()
        self.receipt = complete.freeze_once(self.f.project, self.f.stage, self.f.capture,
                                           self.f.expected, self.f.settlement, cpu_validation=True)
        self.path = Path(self.receipt['freeze_path'])

    def rehash(self):
        self.plan['scope_sha256'] = digest({k: v for k, v in self.plan.items() if k != 'scope_sha256'})

    def bind(self, **kwargs):
        return binding.bind_existing_freeze(self.plan, self.f.project, self.f.stage,
                                            self.f.capture, self.f.expected, self.f.settlement,
                                            self.receipt, **dict(cpu_validation=True, **kwargs))

    def test_complete_existing_freeze_readonly_full32(self):
        before = self.path.read_bytes()
        result = self.bind()
        self.assertEqual(result['counts']['new_GPU_paths'], 32)
        self.assertEqual(result['counts']['unique_new_scoring_pairs'], 12)
        self.assertEqual(result['counts']['logical_quality_positions'], 24)
        self.assertEqual(result['counts']['clean_timing_samples'], 26)
        self.assertEqual(self.f.calls, 112)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(result['new_freeze_created'])
        self.assertFalse(result['GPU_dispatch_ready'])
        self.assertFalse(result['whole_card_CPU_accepted'])
        self.assertFalse((self.f.output / 'calibration-frozen-mask.json').exists())
        self.assertEqual(json.loads((ROOT / PROPOSAL).read_text()), self.original_plan)

    def test_missing_freeze_is_not_created(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, 'regular query record'): self.bind()
        self.assertFalse(self.path.exists())

    def test_changed_freeze_bytes_refused(self):
        self.path.write_bytes(self.path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'freeze hash'): self.bind()

    def test_rehashed_changed_freeze_policy_refused(self):
        frozen = json.loads(self.path.read_text())
        frozen['selected']['query_id'] += 1
        self.path.write_text(json.dumps(frozen))
        self.receipt['freeze_sha256'] = sha(self.path)
        with self.assertRaisesRegex(ValueError, 'complete original acceptance'): self.bind()

    def test_wrong_actual_cost_receipt_refused(self):
        self.receipt['actual_GPUh'] += .1
        with self.assertRaisesRegex(ValueError, 'once-freeze receipt'): self.bind()

    def test_live_refused_before_scientific_read(self):
        self.f.capture['process_observations']['runner']['original_live'] = True
        with patch.object(complete, 'read_record', side_effect=AssertionError('Science read')):
            with self.assertRaises(ValueError): self.bind()

    def test_unsettled_refused_before_scientific_read(self):
        self.f.settlement['central_after'] = self.f.settlement['central_before']
        with patch.object(complete, 'read_record', side_effect=AssertionError('Science read')):
            with self.assertRaises(ValueError): self.bind()

    def test_partial111_refused_even_with_freeze(self):
        self.f.change(self.f.output / 'calibration-collection.json',
                      lambda value: value.update(complete_physical_paths=111))
        with self.assertRaisesRegex(ValueError, 'complete112'): self.bind()

    def test_wrong_original_launch_refused_before_reader(self):
        self.plan['budget_comparator']['original_launch_id'] = 'OTHER'
        self.rehash()
        with patch.object(complete, 'accept', side_effect=AssertionError('Wrong run read')):
            with self.assertRaisesRegex(ValueError, 'original two-card'): self.bind()

    def test_modified_proposal_refused(self):
        self.plan['new_policies']['SU19_CFG_C']['fingerprint'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'proposal digest'): self.bind()

    def test_cpu_fixture_cannot_bind_production(self):
        with patch.object(complete, 'accept', side_effect=AssertionError('Fixture science read')):
            with self.assertRaisesRegex(ValueError, 'CPU proposal'):
                binding.bind_existing_freeze(self.plan, self.f.project, self.f.stage,
                                             self.f.capture, self.f.expected, self.f.settlement,
                                             self.receipt)

    def test_forged_production_plan_still_rejects_cpu_capture(self):
        self.plan.pop('CPU_fixture_only')
        self.rehash()
        with patch.object(complete, 'read_record', side_effect=AssertionError('Fixture science read')):
            with self.assertRaises(ValueError):
                binding.bind_existing_freeze(self.plan, self.f.project, self.f.stage,
                                             self.f.capture, self.f.expected, self.f.settlement,
                                             self.receipt)


class PhysicalMapping(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / PROPOSAL).read_text())

    def test_equal_new_policy_keeps24_logical_and25_physical(self):
        for role in binding.NEW_ROLES:
            with self.subTest(role=role):
                result = binding.map_physical_slots(self.plan, self.plan['new_policies'][role])
                self.assertEqual(result['budget_role_representative'], role)
                self.assertEqual(result['counts'], dict(logical_quality_positions=24,
                    reused_metric_positions=12, new_logical_quality_positions=12,
                    new_GPU_paths=25, unique_new_scoring_pairs=8, clean_timing_samples=20))
                self.assertEqual(len(result['identity_controls']), 9)
                self.assertEqual(sum(k != v for k, v in result['proposal_slot_aliases'].items()), 7)
                by_id = {p['id']: p for p in result['physical_matrix']}
                for row in result['formal_matrix']:
                    if row['role'] == binding.BUDGET_ROLE:
                        self.assertEqual(row['metric_alias_of_role'], role)
                        self.assertEqual(by_id[row['physical_slot_id']]['role'], role)
                        self.assertEqual(by_id[row['physical_slot_id']]['member'], row['member'])

    def test_fingerprint_alone_cannot_deduplicate(self):
        policy = copy.deepcopy(self.plan['new_policies'][binding.NEW_ROLES[0]])
        policy['shared_alpha'][0] = .5
        result = binding.map_physical_slots(self.plan, policy)
        self.assertEqual(result['counts']['new_GPU_paths'], 32)

    def test_reused_rows_remain_byte_equivalent_objects(self):
        result = binding.map_physical_slots(self.plan, self.plan['new_policies'][binding.NEW_ROLES[0]])
        reused = lambda p: [r for r in p['formal_matrix'] if r['mode'] == 'REUSE_COMPLETE_SCORE']
        self.assertEqual(reused(result), reused(self.plan))


if __name__ == '__main__': unittest.main()
