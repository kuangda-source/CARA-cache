"""Timing ordering, all repeats, rejection accounting and clock exclusions."""
import copy
import unittest
from statistics import mean
from wcomr.balanced_repeat_timing_r1 import SLOTS,SCENES,orders,matrix,summaries

def fixture():
    rows=[]
    for p in matrix():
        seconds=100. if p['slot'] in SLOTS[:3] else 80.
        value=0. if p['slot']=='FULL_NATIVE' else .2
        sha=p['scene']+'_'+p['slot'];ref=p['scene']+'_FULL_NATIVE'
        rows.append(dict(**p,status='COMPLETE',core_seconds=9999. if p['section']=='WARMUP' else seconds,
            audit=p['section']=='WARMUP',in_timing_hashes=0,in_timing_guided_copies=36 if p['section']=='WARMUP' else 0,
            research_checkpoints=0,write_deferred_after_main_timer=True,raw_model_audit='PASS',endpoint_audit='PASS',
            final_latent_sha256=sha,actions=None if p['slot']=='FULL_NATIVE' else ['DD']*36,A_history=None,
            decoded_video={'RGB_sha256':sha},video_artifact={'sha256':sha},
            LPIPS=dict(frames=93,frame_distances=[value]*93,mean_LPIPS=value,reference_sha256=ref,candidate_sha256=sha)))
    return rows

class RepeatTimingTests(unittest.TestCase):
    def test_complete40_and_equal_average_position_within_each_scene(self):
        self.assertEqual(len(matrix()),40)
        self.assertEqual(sum(r['section']=='TIMED' for r in matrix()),30)
        for i in (0,1):
            for s in SLOTS:self.assertEqual(sum(order.index(s) for order in orders(i)),6)
        self.assertNotEqual(orders(0),orders(1))

    def test_equal_linear_position_drift_and_warm_not_in_mean(self):
        rows=fixture()
        for row in rows:
            if row['section']=='TIMED':row['core_seconds']+=4*row['position']
        v=summaries(rows)
        for r in v['scene_methods']:
            self.assertAlmostEqual(r['complete_repeat_mean_seconds'],108. if r['slot'] in SLOTS[:3] else 88.)
            self.assertEqual(len(r['rounds']),3)

    def test_real_seconds_and_all_baseline_over_candidate_ratios(self):
        v=summaries(fixture())
        for r in v['contrasts']:
            self.assertEqual(r['actual_paired_rounds'],6);self.assertAlmostEqual(r['full_registered_speedup'],1.25)
        row=next(r for r in v['scene_methods'] if r['slot']=='GCR_EFFICIENT')
        self.assertTrue(all(r['main_seconds']==80. for r in row['rounds']))
        self.assertTrue(all(r['speedup_baseline_over_candidate']['FULL_NATIVE']==1.25 for r in row['rounds']))

    def test_rejected_repeat_keeps_full40_and_complete_mean_empty(self):
        rows=fixture();row=next(r for r in rows if r['section']=='TIMED' and r['slot']=='GCR_EFFICIENT')
        row.update(status='TEXT_REJECTED');row.pop('LPIPS')
        v=summaries(rows);r=next(r for r in v['scene_methods'] if r['slot']=='GCR_EFFICIENT' and r['scene']==row['scene'])
        self.assertIsNone(r['complete_repeat_mean_seconds']);self.assertEqual(r['valid_time_repeats'],2)
        self.assertEqual(v['formal_denominator'],30)
        pair=next(r for r in v['contrasts'] if r['candidate']=='GCR_EFFICIENT' and r['baseline']=='FULL_NATIVE')
        self.assertIsNone(pair['full_registered_speedup']);self.assertEqual(pair['actual_paired_rounds'],5)

    def test_in_timing_research_copy_changed_output_and_short_matrix_refused(self):
        for kind in ('copy','output','short'):
            rows=fixture();row=next(r for r in rows if r['section']=='TIMED')
            if kind=='copy':row['in_timing_guided_copies']=1
            elif kind=='output':row['final_latent_sha256']='another_trajectory'
            else:rows.pop()
            with self.assertRaises(ValueError):summaries(rows)

if __name__=='__main__':unittest.main()
