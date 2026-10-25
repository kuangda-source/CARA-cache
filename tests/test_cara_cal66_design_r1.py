import copy
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

from wcomr.policy_generator_r1.paired_budget_design import paired_budget

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cal66', ROOT/'scripts/prepare_cara_cal66_r1.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Design(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = module.build()
        cls.old = module.read(module.OLD)

    def test_deterministic_manifest(self):
        self.assertEqual(self.card, module.read(module.OUT))

    def test_whole_scope(self):
        c = self.card
        self.assertEqual(Counter(s['section'] for s in c['matrix']),
                         dict(QUALITY=52, TIMING_REPEAT=6, WARM=6, HISTORICAL_BRIDGE=2))
        self.assertEqual(len({s['id'] for s in c['matrix']}), 66)
        self.assertEqual(sum(s['actual_updates'] for s in c['matrix']), 2296)
        self.assertEqual(c['scope']['independent_quality_positions'], 156)
        self.assertFalse(any(s['role'].startswith(('NATIVE30', 'S20', 'SHARED20')) for s in c['matrix']))

    def test_each_formal_cohort_complete(self):
        for member in self.card['CAL_FIT_members']:
            self.assertEqual({s['role'] for s in self.card['matrix'] if s['section']=='QUALITY' and s['member']==member},
                             set(self.card['formal_roles']))

    def test_original_alpha_and_strong_masks(self):
        for role, arm in self.card['roles'].items():
            old_role = self.card['prior_role_aliases'].get(role, role)
            if old_role in self.old['roles']:
                self.assertEqual(arm, self.old['roles'][old_role])
            if arm['policy']:
                for t, (a, alpha) in enumerate(zip(arm['policy']['actions'], arm['policy']['shared_alpha']), 1):
                    self.assertEqual(alpha, (1. if t<25 else .5) if a=='A' else None)

    def test_age_confound_isolated(self):
        for n in (24,25):
            a = self.card['roles'][f'SHARED{n}_A_PHASE_ALL']['policy']
            b = self.card['roles'][f'SHARED{n}_A_PHASE_AGE3']['policy']
            self.assertEqual(a['dense_mask'], b['dense_mask'])
            self.assertEqual([i+1 for i,(x,y) in enumerate(zip(a['actions'],b['actions'])) if x!=y],[34,35])
            self.assertEqual(a['actions'].count('A')-b['actions'].count('A'),2)

    def test_external_mask_derivation(self):
        ext=module.read('docs/discussions/CAL66_6PRO_REFERENCE_20261025/03_CPU_Mask_Derivation.json')
        for row in self.card['mask_audit']['rows']:
            for family,data in row['families'].items():
                e=next(x for x in ext['rows'] if x['quota']==row['quota'] and x['family']==family)
                for key in ('dense','all_A_count','age3_A_count','replaced_A_positions'):
                    self.assertEqual(data[key],e[key])

    def test_quote_all_slots(self):
        q=self.card['quote']
        expected=(sum(q['arm_seconds'][s['role']] for s in self.card['matrix'])/3600+.5)*1.15
        self.assertAlmostEqual(expected,q['forecast_GPUh'])
        self.assertLess(expected,8.)
        self.assertEqual(q['cumulative_cap_GPUh'],226)
        self.assertFalse(q['limit_approved'])
        self.assertFalse(self.card['production_entry_CPU_accepted'])

    def test_matched_aliases_not_new_gpu_roles(self):
        for row in self.card['mask_audit']['rows']:
            self.assertIn(['full_energy','propagation_prior_only','simple_template'],row['mask_alias_groups'])

    def test_budget_point_equivalence_and_cluster_count(self):
        rows=[dict(prompt=str(i),candidate=[240.,240.],native=[320.,320.]) for i in range(4)]
        v=paired_budget(rows,resamples=1000)
        self.assertTrue(v['point_pass']); self.assertTrue(v['mean_budget_statistical_support'])
        self.assertEqual(v['prompts'],4);self.assertFalse(v['deployment_accepted'])
        self.assertAlmostEqual(v['V'],240/256)
        # Duplicated deterministic repeats add no inference precision.
        once=[dict(prompt=r['prompt'],candidate=r['candidate'][:1],native=r['native'][:1]) for r in rows]
        self.assertEqual(v,paired_budget(once,resamples=1000))

    def test_budget_absolute_and_relative_both_required(self):
        for c,n in [(258.,400.),(240.,280.)]:
            v=paired_budget([dict(prompt=str(i),candidate=[c],native=[n]) for i in range(4)],resamples=100)
            self.assertFalse(v['point_pass'])
        with self.assertRaises(ValueError):
            paired_budget([dict(prompt='a',candidate=[240.],native=[320.])]*2)
        with self.assertRaises(ValueError):
            paired_budget([dict(prompt=str(i),candidate=[float('nan')],native=[320.]) for i in range(4)])


if __name__=='__main__':
    unittest.main()
