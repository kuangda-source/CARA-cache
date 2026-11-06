"""Real PA12 scope/parameter identity and stop-GPU boundary, no model calls."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.p_acr_profile528_contract_r1 import validate_contract,validate_local_bindings,require_new_GPU_permission,COUNTS

ROOT=Path(__file__).resolve().parents[1]


def config():return json.loads((ROOT/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json').read_text())


class ActualPAContract(unittest.TestCase):
    def test_complete_actual_bindings_and_gamma(self):
        c=config();v=validate_local_bindings(ROOT,c)
        self.assertEqual(c['scope_counts'],COUNTS)
        self.assertEqual(v['H1']['gamma'],.7235237005554214)
        self.assertEqual(v['coefficients']['A_gamma'],v['H1']['gamma'])
        self.assertFalse(c['actual_production_CPU_accepted'])

    def test_reduced_controls_or_points_refused(self):
        for key in ('baseline_parents','diagnostic_pairs'):
            c=config();c['scope_counts'][key]-=1
            with self.assertRaises(ValueError):validate_contract(c)
        c=config();c['states'].pop()
        with self.assertRaises(ValueError):validate_contract(c)

    def test_preselected_source_clock_refused(self):
        c=config();c['states'][0]['expected_source_birth']-=1
        with self.assertRaises(ValueError):validate_contract(c)

    def test_synthetic_gamma_cannot_replace_actual_H1(self):
        c=config();c['gamma']=.5
        with self.assertRaisesRegex(ValueError,'Actual frozen H1'):validate_local_bindings(ROOT,c)

    def test_old_window_or_numeric_CPU_does_not_authorize_GPU(self):
        c=config();old=json.loads((ROOT/'manifests/budget_authorization_20261012_wc_math_scheduler_new48gpuh.json').read_text())
        numeric=json.loads((ROOT/'reports/wc_p_acr_profile20_cpu_r1_independent_acceptance_20261015.json').read_text())
        for permission,proof in ((None,None),(old,None),(old,numeric)):
            with self.assertRaisesRegex(ValueError,'Fresh concrete PA12'):require_new_GPU_permission(c,permission,proof)
        c['GPU_authorized']=True
        with self.assertRaises(ValueError):validate_contract(c)


if __name__=='__main__':unittest.main()
