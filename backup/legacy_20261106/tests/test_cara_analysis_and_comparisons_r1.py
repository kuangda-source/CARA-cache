import unittest

from test_policy_generator_r1 import fixture
from wcomr.policy_generator_r1.budgeted_planner import solve
from wcomr.policy_generator_r1.comparison_preparation import refresh_only,pure_proxy,simple_search
from wcomr.policy_generator_r1.evaluation_analysis import analyze,spearman,calibration_costs


def export():
    members=[['a',0],['a',1],['b',0]]
    candidates=[dict(fingerprint=f,roles=[role],phase=phase,predicted_seconds=9,proxy_loss=proxy,discrete_cost_units=8)
        for f,role,phase,proxy in [('c','SIMPLE_C','INITIAL',.4),('a','SIMPLE_A','INITIAL',.3),('g','JOINT','REFINEMENT',.1)]]
    rows=[]
    for f,loss in [('c',.2),('a',.15),('g',.1)]:
        for prompt,seed in members:
            rows.append(dict(fingerprint=f,prompt=prompt,seed=seed,split='CAL_FIT',status='COMPLETE',
                LPIPS=loss if prompt=='a' else loss+.02,measured_seconds=9,
                timing_protocol='SYNTHETIC',profile_identity='SYNTHETIC',
                endpoint_basis='NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS'))
    return dict(evidence_kind='SYNTHETIC_UNIT_FIXTURE',split='CAL_FIT',members=members,candidates=candidates,records=rows,
        budget_seconds=10,timing_protocol='SYNTHETIC',profile_identity='SYNTHETIC',shared_seconds=1,quantum_seconds=1,
        cost_events=[dict(event_id='paid1',kind='FIT',actual_GPUh=.5)],
        query_ledger=[dict(fingerprint=f,origin='NEW_EVALUATION',status='COMPLETE',physical_execution_ids=[f+'1',f+'2',f+'3']) for f in ('c','a','g')],
        query_limit=8,calibration_limit_GPUh=2)


class Analysis(unittest.TestCase):
    def test_prompt_equal_selection_and_refinement_increment(self):
        value=analyze(export())
        self.assertAlmostEqual(value['selection']['selected']['mean_LPIPS'],.11)
        self.assertAlmostEqual(value['best_initial_to_final_LPIPS_gain'],.05)
        self.assertEqual(value['correlation_complete_candidates'],3)
        self.assertEqual(value['cost']['unique_new_endpoint_executions'],9)
        self.assertFalse(value['production_acceptance_performed'])

    def test_missing_control_preserves_all_candidates_and_denominators(self):
        d=export();d['records']=d['records'][1:];v=analyze(d)
        self.assertIsNone(v['selection']['selected']);self.assertEqual(len(v['rows']),3)
        self.assertEqual(v['rows'][0]['registered_positions'],3)
        self.assertEqual(v['rows'][0]['missing_members'],[['a',0]])

    def test_fast_but_bad_tail_cannot_win(self):
        d=export()
        for r in d['records']:
            if r['fingerprint']=='g':r['LPIPS']=.19 if r['prompt']=='b' else 0
        self.assertEqual(analyze(d)['selection']['selected']['fingerprint'],'a')

    def test_foreign_split_and_duplicate_endpoint_refused(self):
        for mutation in ('foreign','duplicate'):
            d=export()
            if mutation=='foreign':d['records'][0]['split']='TEST'
            else:d['records'].append(d['records'][0])
            with self.assertRaises(ValueError):analyze(d)

    def test_overbudget_and_failed_candidate_remain(self):
        d=export()
        for r in d['records']:
            if r['fingerprint']=='g':r['measured_seconds']=11
        self.assertEqual(analyze(d)['selection']['selected']['fingerprint'],'a')
        d['records'][4]['status']='TECHNICAL_FAILURE'
        v=analyze(d)
        self.assertEqual(len(v['rows']),3);self.assertFalse(v['rows'][2]['feasible'])
        self.assertIsNone(v['selection']['selected'])  # A control failed: no tail baseline.

    def test_tied_and_constant_rank_correlation(self):
        self.assertAlmostEqual(spearman([1,1,2],[2,2,1]),-1)
        self.assertIsNone(spearman([1,1],[1,2]))

    def test_physical_dedup_does_not_erase_information_queries(self):
        d=export();d['query_ledger'][1]['physical_execution_ids']=['c1','c2','c3']
        d['query_ledger'][2].update(origin='ACCEPTED_PRIOR_ENDPOINT',physical_execution_ids=[])
        d['query_ledger'][0]['status']='REJECTED';v=analyze(d)['cost']
        self.assertEqual(v['attempted_information_queries'],3);self.assertEqual(v['unique_new_endpoint_executions'],3)
        d['cost_events']*=2
        with self.assertRaises(ValueError):analyze(d)


class Comparisons(unittest.TestCase):
    def test_refresh_only_has_fixed_readout_but_variable_refresh(self):
        p,c,_,b=fixture(n=8,minimum_A=1)
        for mode in ('A','C'):
            result=refresh_only(p,b['graph'],c,budget_seconds=30,quantum_seconds=.25,mode=mode)
            self.assertTrue(result['proposals'])
            for r in result['proposals']:
                self.assertLessEqual(r['predicted_seconds'],30)
                self.assertTrue(set(r['policy']['actions'])<={'D',mode})

    def test_simple_search_reproducible_same_Q_without_labels(self):
        p,c,_,_=fixture(n=8,minimum_A=1)
        a=simple_search(p,c,budget_seconds=30,quantum_seconds=.25)
        self.assertEqual(a,simple_search(p,c,budget_seconds=30,quantum_seconds=.25))
        self.assertEqual(a['logical_slots_registered'],8);self.assertLessEqual(len(a['slots']),8)
        self.assertEqual([s['role'] for s in a['slots'][:2]],['SIMPLE_C','SIMPLE_A'])
        self.assertFalse(a['proxy_or_endpoint_scores_used'])

    def test_pure_proxy_choice_precedes_endpoint_feedback(self):
        p,c,_,b=fixture(n=6,minimum_A=1)
        result=solve(p,b['graph'],budget_seconds=22,shared_seconds=c.shared_seconds,quantum_seconds=.25)
        selected=pure_proxy(result)
        self.assertEqual(selected['proxy_loss'],min(r['proxy_loss'] for r in result['proposals']))


if __name__=='__main__':unittest.main()
