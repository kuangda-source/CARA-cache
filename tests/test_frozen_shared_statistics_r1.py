"""Grouped statistics preserve paired seeds, denominators and speedup units."""
import copy
import unittest
from wcomr.frozen_shared_statistics_r1 import analyze

METHODS=['NATIVE','BASE','OURS']

def fixture():
    cases=[dict(id=f'p{i}_seed{s}',prompt_id=f'p{i}',seed=s) for i in range(8) for s in (17,43)]
    rows=[]
    for c in cases:
        native_sha=c['id']+'_NATIVE';i=int(c['prompt_id'][1:]);late=c['seed']==43
        for method in METHODS:
            loss=0. if method=='NATIVE' else (.3+.2*late)-(.1 if method=='OURS' else 0.)
            cost=(100.+20*late+10*i)*(.8 if method=='OURS' else 1.)
            artifact=c['id']+'_'+method
            rows.append(dict(case_id=c['id'],method=method,status='COMPLETE',raw_model_audit='PASS',endpoint_audit='PASS',
                core_seconds=cost,video_artifact={'sha256':artifact},LPIPS=dict(frames=93,frame_distances=[loss]*93,
                    mean_LPIPS=loss,reference_sha256=native_sha,candidate_sha256=artifact)))
    return cases,rows

def run(cases,rows):return analyze(cases,METHODS,rows,[('OURS','BASE')],reference_method='NATIVE',bootstrap_repetitions=128)

class GroupedStatisticsTests(unittest.TestCase):
    def test_known_constant_improvement_and_true_speed_ratio(self):
        c,r=fixture();v=run(c,r);pair=v['comparisons'][0]
        self.assertEqual(v['registered_formal_denominator'],48)
        self.assertEqual(v['registered_prompt_groups'],8)
        self.assertAlmostEqual(pair['full_registered_mean_LPIPS_change'],-.1)
        self.assertAlmostEqual(pair['full_registered_LPIPS_change_percent'],-25.)
        self.assertAlmostEqual(pair['full_registered_speedup_sum_baseline_over_sum_candidate'],1.25)
        self.assertTrue(all(abs(x+.1)<1e-12 for x in pair['full_registered_LPIPS_change_prompt_bootstrap95']))
        self.assertFalse(v['bootstrap']['frames_resampled_as_independent'])

    def test_speed_is_ratio_of_sum_times_not_mean_per_video_ratio(self):
        c,r=fixture()
        for row in r:row['core_seconds']=100.
        next(x for x in r if x['case_id']=='p0_seed17' and x['method']=='BASE')['core_seconds']=10.
        next(x for x in r if x['case_id']=='p0_seed17' and x['method']=='OURS')['core_seconds']=5.
        p=run(c,r)['comparisons'][0]
        self.assertAlmostEqual(p['full_registered_speedup_sum_baseline_over_sum_candidate'],1510./1505.)
        self.assertNotAlmostEqual(p['full_registered_speedup_sum_baseline_over_sum_candidate'],17./16.)

    def test_one_rejected_seed_does_not_become_a_full_two_seed_prompt(self):
        c,r=fixture();row=next(x for x in r if x['case_id']=='p0_seed43' and x['method']=='BASE')
        row.update(status='TEXT_REJECTED');row.pop('LPIPS');row.pop('core_seconds')
        v=run(c,r);pair=v['comparisons'][0];base=next(x for x in v['methods'] if x['method']=='BASE')
        self.assertEqual(v['registered_formal_denominator'],48)
        self.assertIsNone(base['full_registered_mean_LPIPS'])
        self.assertEqual(base['complete_two_seed_quality_prompts'],7)
        self.assertEqual(pair['missing_quality_prompt_ids'],['p0'])
        self.assertIsNone(pair['full_registered_mean_LPIPS_change'])
        self.assertAlmostEqual(pair['available_complete_prompt_LPIPS_change'],-.1)

    def test_reference_substitution_duplicate_and_short_matrix_refused(self):
        c,r=fixture()
        for kind in ('reference','duplicate','missing','missing_seed'):
            cases,rows=copy.deepcopy(c),copy.deepcopy(r)
            if kind=='reference':rows[-1]['LPIPS']['reference_sha256']='another_seed_or_prompt'
            elif kind=='duplicate':rows[-1]=copy.deepcopy(rows[0])
            elif kind=='missing':rows.pop()
            else:cases.pop()
            with self.assertRaises(ValueError):run(cases,rows)

    def test_zero_reference_fidelity_is_not_given_a_fake_percent_improvement(self):
        cases,rows=fixture()
        v=analyze(cases,METHODS,rows,[('OURS','NATIVE')],reference_method='NATIVE',bootstrap_repetitions=128)
        pair=v['comparisons'][0]
        self.assertIsNone(pair['full_registered_LPIPS_change_percent'])
        self.assertIsNone(pair['full_registered_LPIPS_change_percent_prompt_bootstrap95'])
        self.assertAlmostEqual(pair['full_registered_mean_LPIPS_change'],.3)

if __name__=='__main__':unittest.main()
