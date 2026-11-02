"""Final proposed19GPUh quote/config binding using explicit CPU-only metadata."""
import json
from pathlib import Path
import tempfile
import unittest

import test_cara_source_lifecycle_p1_entry_r1 as fixture
from wcomr import cara_source_lifecycle_p1_runner_binding_r1 as binding
from wcomr.cara_fast_fidelity_r1 import file_sha

ROOT=Path(__file__).resolve().parents[1]
QUOTE='plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json'


class P1ProfileQuoteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=fixture.Fixture(self.temp.name)
        self.f.profile=json.loads((ROOT/binding.PROFILE).read_bytes())
        (self.f.stage/binding.PROFILE).write_bytes((ROOT/binding.PROFILE).read_bytes())
        self.f.reg['payload_sha256'][binding.PROFILE]=file_sha(self.f.stage/binding.PROFILE)
        self.f.quote=json.loads((ROOT/QUOTE).read_bytes())
        self.f.authority['billed_limit_GPUh']=19.;self.f.write()

    def test_full_original_scope_and_conservative_components_bind_final_proposed_profile(self):
        card,reg,authority,profile,quote=binding.validate_inputs(self.f.project,self.f.stage)
        self.assertEqual(profile['hard_GPUh'],19.)
        self.assertEqual(quote['profile_sha256'],file_sha(self.f.stage/binding.PROFILE))
        self.assertEqual(quote['semantic_positions'],146)
        self.assertEqual((quote['physical_generation_upper'],quote['physical_model_pairs_upper']),(142,5176))
        self.assertFalse(quote['snapshot_is_measured_V1_cost'])
        self.assertFalse(quote['P1_GPU_authorized'])
        self.assertFalse(profile['execution_authorized'])

    def test_no_single_card_authority_still_cannot_pass_even_with_final_quote(self):
        self.f.authority['execution_authorized']=False;self.f.write()
        with self.assertRaisesRegex(ValueError,'single P1 authority'):
            binding.validate_inputs(self.f.project,self.f.stage)

    def test_old_hard_limit_or_omitted_whole_cost_component_is_refused(self):
        self.f.authority['billed_limit_GPUh']=18.;self.f.write()
        with self.assertRaisesRegex(ValueError,'hard limit'):binding.validate_inputs(self.f.project,self.f.stage)
        self.f.authority['billed_limit_GPUh']=19.
        self.f.quote['components_seconds'].pop('shadow_state_capture_hash_restore');self.f.write()
        with self.assertRaisesRegex(ValueError,'quote'):binding.validate_inputs(self.f.project,self.f.stage)


if __name__=='__main__':unittest.main()
