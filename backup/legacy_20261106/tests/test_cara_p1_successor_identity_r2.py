"""The successor has its own identity, resources and approval boundary."""
import json
from pathlib import Path
import unittest

from wcomr import cara_source_lifecycle_p1_identity_r1 as identity
from wcomr import cara_source_lifecycle_p1_runner_binding_r1 as binding
from wcomr.cara_source_lifecycle_p1_central_r1 import validate_authority
import provision_cara_source_lifecycle_p1_storage_r1 as old_storage
import provision_cara_source_lifecycle_p1_storage_r2 as new_storage

ROOT = Path(__file__).resolve().parents[1]


class SuccessorIdentityTests(unittest.TestCase):
    def test_complete_scope_and_new_run_are_bound_without_inheriting_old_authority(self):
        self.assertEqual(identity.RUN_ID, 'cara-source-lifecycle-V1-P1-full146-r2-20261102')
        self.assertEqual((binding.RUN_ID,binding.STAGE_NAME),(identity.RUN_ID,identity.STAGE_NAME))
        profile=json.loads((ROOT/binding.PROFILE).read_bytes())
        binding.validate_profile(profile,identity.SCOPE_SHA256)
        self.assertEqual(profile['hard_GPUh'],19.)
        self.assertEqual(profile['hosts']['two_card']['minimum_MemAvailable_GiB'],50)
        self.assertFalse(profile['execution_authorized'])
        old=json.loads((ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json').read_bytes())
        with self.assertRaisesRegex(ValueError,'Separate complete P1 GPU authority'):
            validate_authority(old,Path('/data20t/gaokuangda/worldcache_workspace'))

    def test_quote_keeps_full_scope_and_budgets_publication_before_new_GPU_approval(self):
        quote=json.loads((ROOT/binding.QUOTE).read_bytes())
        self.assertEqual((quote['semantic_positions'],quote['physical_generation_upper'],quote['snapshot_labels']),(146,142,64))
        self.assertEqual(quote['atomic_publication_fsync_allowance_seconds'],84.)
        self.assertLessEqual(quote['forecast_GPUh'],quote['hard_GPUh'])
        self.assertFalse(quote['failed_predecessor_artifacts_or_partial_FIT_reused'])
        self.assertFalse(quote['execution_authorized'])

    def test_new_private_storage_never_targets_the_failed_original(self):
        self.assertTrue(set(old_storage.P1_PATHS).isdisjoint(new_storage.P1_PATHS))
        self.assertEqual(new_storage.RUN,identity.RUN_ID)
        self.assertEqual(new_storage.OUTPUT,new_storage.ROOT/'outputs'/identity.RUN_ID)
        self.assertEqual(new_storage.HELPER_SHA,old_storage.HELPER_SHA)
        self.assertNotEqual(new_storage.JOURNAL,old_storage.JOURNAL)


if __name__ == '__main__':
    unittest.main()
