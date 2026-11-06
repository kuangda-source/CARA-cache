"""Original real scope/CPU references; synthetic authority/physical-loader metadata."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from wcomr import frozen_repair180_r2 as repair
from wcomr import frozen_shared_production_r1 as original
from wcomr.frozen_repair_entry_r2 import derive, validate_all_entries

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    config=json.loads((ROOT/repair.CONFIG).read_text())
    old=json.loads((ROOT/original.CONFIG).read_text())
    bound=json.loads((ROOT/config['references']['bound_inputs']['ref']).read_text())
    return config,old,bound


class IndependentRepairContract(unittest.TestCase):
    def test_complete180_exact_original_inputs_methods_prices_and_masks(self):
        config,old,bound=fixture();repair.match_original(config,old)
        self.assertEqual(repair.validate_contract(config,bound),original.validate_contract(old,bound))
        self.assertEqual(config['forecast_complete_GPUh'],15.055555555555555)
        self.assertEqual(config['cumulative_cap_GPUh'],113.)
        self.assertNotEqual(config['run_id'],old['run_id'])
        self.assertFalse(config['request_boundary_repair']['original_approval_reused'])

    def test_no_narrowing_repricing_retuning_or_replacing_refusals(self):
        good,old,bound=fixture()
        for change in (dict(method_ids=good['method_ids'][:-1]),dict(forecast_complete_GPUh=11.9),
                       dict(guardrails_enabled=False),dict(reference_method='RA_DEFAULT')):
            with self.subTest(change=change),self.assertRaises(ValueError):
                repair.match_original({**good,**change},old)
        bad=copy.deepcopy(good);bad['request_boundary_repair']['original_approval_reused']=True
        with self.assertRaises(ValueError):repair.match_original(bad,old)
        with self.assertRaises(ValueError):repair.validate_contract(old,bound)

    def test_original_failure_scope_and_full520_proof_are_bound(self):
        config,_,_=fixture();proof=repair.validate_repair_proof(ROOT,config)
        self.assertEqual(proof['successful_CPU_paths'],520)
        self.assertEqual(proof['expected_original_failure_reproductions'],4)
        self.assertEqual(proof['new_full520_paths_run'],0)
        bad=copy.deepcopy(config);bad['references']['refusal_boundary_CPU']['sha256']='0'*64
        with self.assertRaises(ValueError):repair.validate_repair_proof(ROOT,bad)

    def test_all_four_entry_derivations_are_exactly_reversible(self):
        proofs=validate_all_entries(ROOT)
        self.assertEqual(set(proofs),{'worker','post','supervisor','watcher'})
        for proof in proofs.values():
            self.assertTrue(proof['inverse_bytes_and_AST_equal'])
            self.assertFalse(proof['original_stage_or_script_written'])
        worker,_=derive(ROOT,'worker');supervisor,_=derive(ROOT,'supervisor');watcher,_=derive(ROOT,'watcher')
        self.assertIn('from wcomr.frozen_guardrail_boundary_r2 import execute',worker)
        self.assertIn("not in ('NATIVE', 'FIXED26')",worker)
        self.assertIn('run_wc_paper_N07_refusal_repair180_r2.py',supervisor)
        self.assertNotIn('scripts/run_wc_paper_N07_frozen_shared180_r1.py',supervisor)
        self.assertIn('postprocess_wc_paper_N07_refusal_repair180_r2.py',watcher)

    def test_physical_loader_reuse_does_not_edit_the_old_stage(self):
        config,old,bound=fixture()
        numeric=dict(status='SYNTHETIC_PHYSICAL_REUSE_CONTROL',source_sha256={})
        synthetic=(old,{'source_revision':'SYNTHETIC_NOT_DEPLOYED'},{},('calibration','specs'),{}, {},bound,numeric)
        with patch.object(original,'validate',return_value=synthetic) as loader:
            values=repair.validate(ROOT,ROOT)
        loader.assert_called_once_with(ROOT,ROOT)
        self.assertEqual(values[0],config)
        self.assertEqual(values[-1]['status'],'SYNTHETIC_PHYSICAL_REUSE_CONTROL')
        self.assertEqual(values[-1]['request_boundary_repair']['successful_CPU_paths'],520)
        self.assertEqual(set(values[-1]['metadata_entry_derivations']),{'worker','post','supervisor','watcher'})


if __name__=='__main__':unittest.main()
