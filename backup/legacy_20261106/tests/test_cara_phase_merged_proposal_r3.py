"""New readout identities and planning-only budget behavior; no execution."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_cara_phase_merged_card_r3 import build,selected_candidates
from wcomr.cara_fast_spec_r1 import profile_from


class MergedProposal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        refs=dict(card='plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json',
            bundle='plans/cara_next_stage_20261103/source_coverage/c1/PHASE_SINGLE7_CANDIDATE_POOLS_R3.json',
            history='plans/cara_next_stage_20261103/source_coverage/c1/C1_WHOLE_QUOTE_R1.json',
            robustness='reports/cara_phase_coverage_robustness_zero_GPU_r1_20261103.json',
            settlement='reports/cara_v1_P1_successor_final_settlement_r1_20261103.json')
        cls.inputs={k:json.loads((ROOT/p).read_bytes()) for k,p in refs.items()}

    def test_every_evaluated_candidate_has_distinct_A1_with_the_same_D(self):
        rows=selected_candidates(self.inputs['bundle'],profile_from(self.inputs['card']['profile']))
        self.assertEqual(len(rows),11)
        for row in rows:
            self.assertNotEqual(row['C_policy_sha256'],row['A1_policy_sha256'])
            self.assertEqual([i for i,a in enumerate(row['A1_actions'],1) if a=='D'],row['dense_steps'])
            for t in row['A1_updates']:
                self.assertTrue(9<=t<=19)
                self.assertEqual(row['C_actions'][t-1],'C')
                self.assertEqual(row['C_actions'][t-2],'D')

    def test_low_balance_stays_a_visible_shortfall_and_never_grants_execution(self):
        data=copy.deepcopy(self.inputs)
        data['settlement']['result']['snapshot']['ledger']['available_gpu_hours']=18.
        out=build(**data)
        self.assertEqual(out['budget']['remaining_snapshot_headroom_GPUh'],-1.25)
        self.assertFalse(out['executable']);self.assertFalse(out['GPU_authorized'])
        self.assertFalse(out['ledger_written']);self.assertEqual(out['GPU_submissions'],0)


if __name__=='__main__':unittest.main()
