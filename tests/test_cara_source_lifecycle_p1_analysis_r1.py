"""Complete input-equal reporting and once-freeze controls; no real metrics."""
import copy
from pathlib import Path
import unittest

import check_cara_source_lifecycle_p1_score_fixture_r1 as fixture
import test_cara_source_lifecycle_p1_scores_r1 as score_fixture
from wcomr.cara_source_lifecycle_p1_scores_r1 import accept_scores
from wcomr.cara_source_lifecycle_p1_analysis_r1 import complete_analysis,freeze_original_plans
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest


class P1AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f,packet=fixture.packet();packet['release']['actual_GPUh']=.1
        helper=score_fixture.P1FinalScoreTests('runTest');helper.packet=packet
        cls.packet,config,result,execution=helper.configured()
        cls.accepted=accept_scores(cls.packet,config,result,execution,cpu_validation=True)
        cls.summary=cls.f.root/'new-final-reader-fixture/algorithm-summary.json'

    @classmethod
    def tearDownClass(cls):cls.f.doCleanups()

    def analyze(self,**values):
        return complete_analysis(values.get('packet',self.packet),values.get('accepted',self.accepted),self.summary,cpu_validation=True)

    def test_full52_equal_input_groups_curves_and_actual_calibration_caps(self):
        result=self.analyze()
        self.assertEqual(result['logical_quality_positions'],52)
        self.assertEqual([len(t) for t in result['tables'].values()],[13]*3)
        for group,table in result['tables'].items():
            for value in table.values():
                self.assertEqual(value['inputs'],4 if group=='FOUR_OLD_CAL' else 2)
                self.assertEqual(len(value['LPIPS_curve']),93)
                self.assertEqual(value['inputs'],value['independent_clean_samples']+value['quality_aliases'])
        self.assertEqual(set(result['calibration_costs_and_original_plans']),{'19','22'})
        self.assertFalse(result['engineering_screen']['paper_validity_threshold'])
        self.assertFalse(result['scientific_method_established'])

    def test_missing_or_changed_role_and_clean_time_are_not_reportable(self):
        for mode in ('missing','clock','role'):
            accepted=copy.deepcopy(self.accepted)
            if mode=='missing':accepted['rows'].pop()
            elif mode=='clock':accepted['rows'][0]['T_DD']+=1
            else:accepted['rows'][0]['role']='ANOTHER_ROLE'
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.analyze(accepted=accepted)

    def test_original_algorithm_and_fit_selection_bytes_cannot_change(self):
        raw=self.summary.read_bytes();self.summary.write_bytes(raw+b' ')
        try:
            with self.assertRaisesRegex(ValueError,'immutable algorithm'):self.analyze()
        finally:self.summary.write_bytes(raw)

    def test_once_freeze_reuses_original_bytes_and_refuses_reselection(self):
        result=self.analyze();path=self.f.root/'new-original-FIT-freeze.json'
        first=freeze_original_plans(result,path,cpu_validation=True);sha=file_sha(path)
        self.assertEqual(first,freeze_original_plans(result,path,cpu_validation=True))
        self.assertEqual(file_sha(path),sha)
        changed=copy.deepcopy(result);changed['calibration_costs_and_original_plans']['19']['search_measured_charged_seconds']+=1
        with self.assertRaisesRegex(ValueError,'preserve the original'):freeze_original_plans(changed,path,cpu_validation=True)
        self.assertEqual(file_sha(path),sha)
        with self.assertRaises(ValueError):freeze_original_plans(result,path)


if __name__=='__main__':unittest.main()
