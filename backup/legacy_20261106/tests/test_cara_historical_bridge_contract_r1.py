"""Frozen budgets, alpha schedule, scope and quote checks, without model inference."""
import copy
import json
import unittest
from pathlib import Path
from wcomr.policy_generator_r1.historical_bridge import historical_policies, runtime_budget
from wcomr.policy_generator_r1.interval_grammar import Profile

ROOT=Path(__file__).resolve().parents[1]
class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card=json.loads((ROOT/'manifests/cara_historical_bridge104_scope_quote_r1_20261024.json').read_text())
        d=copy.deepcopy(cls.card['profile'])
        for k in ('protected_dense','alpha_candidates'):d[k]=tuple(d[k])
        cls.policies=historical_policies(Profile(**d))
    def test_historical_alpha_is_not_global_one(self):
        p=self.policies['S26_A_PHASE']
        self.assertEqual([i+1 for i,a in enumerate(p['actions']) if a=='D'],list(range(1,22))+[24,27,30,33,36])
        self.assertEqual([a for a in p['shared_alpha'] if a is not None],[1.,1.]+[.5]*8)
    def test_boundary_changes_only_prefix_D(self):
        for n in (24,25,26):
            c=self.policies[f'S{n}_C'];a=self.policies[f'S{n}_A_PHASE']
            self.assertEqual(c['dense_mask'],a['dense_mask']);self.assertEqual(c['counts']['D'],n)
            self.assertEqual([t for t in range(24,37) if c['actions'][t-1]=='D'],[24,27,30,33,36])
            for t,v in enumerate(a['shared_alpha'],1):
                if v is not None:self.assertEqual(v,.5 if t>=25 else 1.)
    def test_budget_never_grows_with_slower_reference(self):
        self.assertEqual(runtime_budget(400),257.7712338712067)
        self.assertEqual(runtime_budget(300),240)
        with self.assertRaises(ValueError):runtime_budget(0)
    def test_complete_pairs_and_no_select(self):
        rows=self.card['matrix'];self.assertEqual(len(rows),104);self.assertEqual(len({r['id'] for r in rows}),104)
        for role in self.card['policies']:
            for split in ('CALIBRATION','VALIDATION'):
                rr=[r for r in rows if r['role']==role and r['section']==split]
                self.assertEqual(len(rr),4);self.assertEqual({r['member'] for r in rr},set(self.card['CAL_FIT_members']))
        self.assertEqual(self.card['scope']['post_CPU_score_pairs'],72)
        self.assertEqual(self.card['scope']['SELECT_paths'],0)
    def test_quote_includes_complete_GPU_occupancy(self):
        q=self.card['quote'];self.assertAlmostEqual(sum(q['components'].values())*1.25,q['forecast_GPUh'])
        self.assertLess(q['forecast_GPUh'],q['billed_limit_GPUh']);self.assertLess(q['billed_limit_GPUh'],12)
        self.assertEqual(q['cumulative_cap_GPUh'],226)
        self.assertFalse(q['post_GPU_release_CPU']['GPU_held'])
    def test_validation_reverses_block_order(self):
        rows=self.card['matrix']
        for member in self.card['CAL_FIT_members']:
            a=[r['role'] for r in rows if r['member']==member and r['section']=='CALIBRATION']
            b=[r['role'] for r in rows if r['member']==member and r['section']=='VALIDATION']
            self.assertEqual(a,b[::-1])
if __name__=='__main__':unittest.main()
