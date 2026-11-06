"""Full matrix/reuse/time boundaries, without remote or model execution."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_s_uniform_endpoint_plan_r1 import build,validate,quote,include_budget_comparator


class CompleteEndpointPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(name):return json.loads((ROOT/name).read_text())
        cls.args=(load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'),
            read('reports/cara_s_initialization_sensitivity_r1_20261031.json'),
            read('reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json'),
            read('reports/cara_fast_B36_complete_analysis_r1_20261029.json'),
            read('reports/cara_s_initialization_numeric_CPU_accepted_r3_20261031.json'))

    def test_complete_scope_and_whole_quote(self):
        plan=build(*self.args);cost=quote(plan,self.args[3])
        self.assertEqual(len(plan['formal_matrix']),20)
        self.assertEqual(len(plan['physical_matrix']),25)
        self.assertEqual(cost['proposed_hard_GPUh'],4.25)
        self.assertTrue(cost['requires_separate_over4_GPUh_approval'])
        self.assertFalse(plan['GPU_dispatch_ready'])
        self.assertAlmostEqual(cost['forecast_GPUh']*3600,sum(cost['components_seconds'].values()))

    def changed_plan(self,change,message):
        plan=build(*self.args);change(plan)
        with self.assertRaisesRegex(ValueError,message):validate(plan)

    def test_missing_scientific_position(self):
        self.changed_plan(lambda p:p['formal_matrix'].pop(),'Complete20')

    def test_missing_physical_position(self):
        self.changed_plan(lambda p:p['physical_matrix'].pop(),'Complete25')

    def test_warm_cannot_count_as_clean_time(self):
        def change(p):
            p['physical_matrix'][0]['eligible_clean_time']=True
            next(r for r in p['physical_matrix'] if r['section']=='FORMAL')['eligible_clean_time']=False
        self.changed_plan(change,'warm exclusion')

    def test_duplicate_identity_control(self):
        self.changed_plan(lambda p:p['identity_controls'].__setitem__(1,copy.deepcopy(p['identity_controls'][0])),
            'replay controls')

    def test_alias_not_extra_generation(self):
        def change(p):
            next(r for r in p['physical_matrix'] if r['section']=='FORMAL')['role']='SU19_DIAG_C'
        self.changed_plan(change,'role/member coverage')

    def changed_evidence(self,index,change,message):
        args=copy.deepcopy(self.args);change(args[index])
        with self.assertRaisesRegex(ValueError,message):build(*args)

    def test_changed_original_reference(self):
        def change(s):
            next(r for r in s['rows'] if r['role']=='F19_C')['reference']['sha256']='0'*64
        self.changed_evidence(2,change,'original reference')

    def test_changed_model_precision(self):
        def change(s):
            next(r for r in s['rows'] if r['role']=='F19_A1')['candidate']['precision']='0'*64
        self.changed_evidence(2,change,'model and precision')

    def test_no_duplicate_risk_masks(self):
        def change(d):
            d['origins']['Uniform19_C']['choices']['CFG']=copy.deepcopy(d['origins']['Uniform19_C']['choices']['DIAG'])
        self.changed_evidence(1,change,'two distinct')

    def test_no_new_endpoint_fitting(self):
        self.changed_evidence(1,lambda d:d.update(endpoint_results_used=True),'FIT-only')

    def test_partial_numeric_evidence(self):
        self.changed_evidence(4,lambda d:d.update(production_paths=35),'complete numerical')

    def test_no_implicit_execution_authority(self):
        self.changed_plan(lambda p:p.update(GPU_authorized=True),'no GPU execution')

    def test_complete_joint_comparison(self):
        core=build(*self.args);plan=include_budget_comparator(core)
        cost=quote(plan,self.args[3])
        self.assertEqual(plan['core25_scope_sha256'],core['scope_sha256'])
        self.assertEqual(len(plan['physical_matrix']),32)
        self.assertEqual(len(plan['formal_matrix']),24)
        self.assertEqual(cost['proposed_hard_GPUh'],5.25)
        self.assertFalse(plan['budget_comparator']['policy_bound'])
        self.assertFalse(plan['GPU_dispatch_ready'])

    def test_no_silent_budget_comparator_removal(self):
        plan=include_budget_comparator(build(*self.args))
        plan['formal_matrix'].pop()
        with self.assertRaisesRegex(ValueError,'Complete24'):validate(plan)

    def test_partial_budget_selection_refused(self):
        plan=include_budget_comparator(build(*self.args))
        plan['budget_comparator']['partial_running_results_accessed']=True
        with self.assertRaisesRegex(ValueError,'Unbound budget'):validate(plan)

    def test_budget_comparator_not_duplicated(self):
        plan=include_budget_comparator(build(*self.args))
        with self.assertRaisesRegex(ValueError,'duplicate'):include_budget_comparator(plan)


if __name__=='__main__':unittest.main()
