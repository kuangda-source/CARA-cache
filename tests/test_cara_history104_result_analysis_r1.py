"""Synthetic accepted-terminal tests; never read live GPU scientific outputs."""
import copy,json,unittest
from wcomr.policy_generator_r1.historical_result_analysis_r1 import analyze_accepted,summarize,route,paired_summary
from wcomr.policy_generator_r1.historical_terminal import accept
from wcomr.policy_price_terminal_r1 import record
from test_cara_history104_combination_r1 import fixture
from test_policy_price_terminal_r1 import h

class Analysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture=fixture();cls.accepted=accept(cls.capture);cls.accepted.update(capture_ref='fixture',capture_sha256=h('fixture'))
    def result(self):return analyze_accepted(self.capture,self.accepted,capture_sha256=h('fixture'),expected_launch=self.capture['launch'])
    def test_complete_output_and_no_dispatch(self):
        r=self.result();self.assertEqual(len(r['baseline_role_table']),10);self.assertEqual(len(r['registered_comparisons']),11)
        self.assertEqual(len(r['budget_boundaries']),4);self.assertEqual(r['GPU_submissions'],0)
        self.assertFalse(r['P1_continuation']['GPU_dispatch_ready']);self.assertEqual(r['timing']['frozen_result'],self.accepted['scientific']['timing'])
    def test_partial_acceptance_rejected(self):
        a=dict(self.accepted,full_protocol_accepted=False)
        with self.assertRaises(ValueError):analyze_accepted(self.capture,a,capture_sha256=h('fixture'),expected_launch=self.capture['launch'])
    def test_wrong_sha_launch_and_forged_acceptance(self):
        for a,s,l in [(self.accepted,h('wrong'),self.capture['launch']),
                      (self.accepted,h('fixture'),dict(self.capture['launch'],launch_id='other')),
                      (dict(self.accepted,actual_GPUh=0),h('fixture'),self.capture['launch'])]:
            with self.assertRaises(ValueError):analyze_accepted(self.capture,a,capture_sha256=s,expected_launch=l)
    def test_missing_score_cannot_enter_analysis(self):
        c=copy.deepcopy(self.capture);c['scores'].pop(next(iter(c['scores'])))
        with self.assertRaises(ValueError):analyze_accepted(c,self.accepted,capture_sha256=h('fixture'),expected_launch=c['launch'])
    def test_running_original_rejected(self):
        c=copy.deepcopy(self.capture);c['original_live_handles']['runner']=True
        with self.assertRaises(ValueError):analyze_accepted(c,self.accepted,capture_sha256=h('fixture'),expected_launch=c['launch'])
    def test_prompt_cluster_and_ties(self):
        s=paired_summary([0,0,0,0],['a','b','c','d']);self.assertEqual(s['independent_prompts'],4);self.assertEqual(s['resamples'],256)
        self.assertEqual(s['zero_prompts'],4);self.assertEqual(s['descriptive_prompt_bootstrap95'],[0.,0.])
    def test_quality_never_changes_model_or_route(self):
        c=record(self.capture,'card');s=copy.deepcopy(self.accepted['scientific']);base=summarize(c,s,self.capture['requests'])
        for role,rows in s['quality'].items():
            for i,r in enumerate(rows):r['LPIPS']=(i+1)/100
        result=summarize(c,s,self.capture['requests']);self.assertEqual(result['timing'],base['timing']);self.assertEqual(result['P1_continuation'],base['P1_continuation'])
    def test_failed_model_vs_no_headroom_are_distinct(self):
        self.assertEqual(route({'timing_model_validated':False},[])['action'],'NEW_COST_CALIBRATION_AND_INDEPENDENT_VALIDATION_REQUIRED')
        self.assertEqual(route({'timing_model_validated':True},[])['action'],'NO_TESTED_24_25D_PLANNING_HEADROOM_KEEP_BUDGET')
    def test_components_close_without_double_counting_core(self):
        req=copy.deepcopy(self.capture['requests'])
        for x in req.values():
            r=x['result'];r.update(method_install_seconds=.2,guarded_pipeline_without_write_seconds=r['full_request_seconds']-1,video_write_seconds=.7,method_cleanup_seconds=.1)
        a=summarize(record(self.capture,'card'),self.accepted['scientific'],req)
        self.assertEqual(len(a['timing']['formal_component_means']),10)
        self.assertEqual(len(a['timing']['diagnostic_rows']),4)
        next(iter(req.values()))['result']['video_write_seconds']=500 # warm excluded, mutate formal instead
        key=next(k for k in req if k.startswith('CALIBRATION'))
        req[key]['result']['video_write_seconds']=500
        with self.assertRaises(ValueError):summarize(record(self.capture,'card'),self.accepted['scientific'],req)
    def test_missing_prompt_quality_rejected(self):
        s=copy.deepcopy(self.accepted['scientific']);s['quality']['S24_C'].pop()
        with self.assertRaises(ValueError):summarize(record(self.capture,'card'),s,self.capture['requests'])
if __name__=='__main__':unittest.main()
