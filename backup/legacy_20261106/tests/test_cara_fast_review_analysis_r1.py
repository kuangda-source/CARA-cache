"""Diagnostic aggregation retains every declared review and flags telemetry gaps."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.cara_fast_b36_figures_r1 import verify_analysis
from wcomr.cara_fast_review_r1 import plan_review, AXES
from wcomr.cara_fast_review_analysis_r1 import summarize_response, playback_record

ROOT=Path(__file__).resolve().parents[1]


class ReviewAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        analysis,_=verify_analysis(ROOT/'reports/cara_fast_B36_complete_analysis_r1_20261029.json')
        manifest=json.loads((ROOT/'reports/cara_fast_B36_original_score_manifest_r1_20261029.json').read_text())
        cls.plan=plan_review(analysis,manifest,b'2'*32)

    def response(self):
        return dict(schema='CARA_VIDEO_REVIEW_RESPONSE_R1',status='COMPLETE_RESPONSE_NOT_INDEPENDENTLY_ACCEPTED',
            package_id=self.plan['public']['package_id'],reviewer='TEST_DIAGNOSTIC_FIXTURE',
            responses=[dict(case_id=c['case_id'],full_watch_attested=True,notes='',
                played={side:[[0,5.8125]] for side in ('reference','candidate')},
                **{axis:'no_obvious_difference' for axis in AXES}) for c in self.plan['cases']])

    def test_complete_counts_are_not_independent_panel_evidence(self):
        r=self.response();case=next(c for c in self.plan['cases'] if c['role']=='F19_C')
        row=next(row for row in r['responses'] if row['case_id']==case['case_id'])
        row['detail']='worse'
        out=summarize_response(self.plan,r)
        self.assertEqual(out['by_role']['F19_C']['all_axes_no_obvious_difference'],3)
        self.assertEqual(out['by_role']['F19_C']['axes']['detail']['worse'],1)
        self.assertEqual(out['self_control_all_axes_no_difference'],4)
        self.assertEqual(out['positions'],32)
        self.assertEqual(out['reviewer_count'],1)
        self.assertFalse(out['independent_human_evidence'])
        self.assertFalse(out['new_selection'])

    def test_missing_playback_never_discards_ratings_or_changes_attestation(self):
        r=self.response();r['responses'][0]['played']={}
        r['responses'][1]['played']={'reference':[],'candidate':[]}
        out=summarize_response(self.plan,r)
        self.assertEqual(out['full_pair_playback_recorded'],30)
        self.assertEqual(len(out['playback_metadata_gaps']),2)
        self.assertEqual(out['full_watch_attestations'],32)
        self.assertEqual(out['excluded_positions'],0)
        self.assertEqual(len(out['per_input']),32)

    def test_incomplete_duplicate_and_QA_records_refused(self):
        for kind in ('partial','duplicate','watch','QA'):
            r=self.response()
            if kind=='partial':r['responses'].pop()
            elif kind=='duplicate':r['responses'][0]=copy.deepcopy(r['responses'][1])
            elif kind=='watch':r['responses'][0]['full_watch_attested']=False
            else:r['reviewer']='CPU_TEST_NOT_A_HUMAN'
            with self.subTest(kind=kind),self.assertRaises(ValueError):summarize_response(self.plan,r)

    def test_playback_union_and_invalid_metadata(self):
        self.assertEqual(playback_record([[0,3],[2,5.8125]],5.8125)['recorded_seconds'],5.8125)
        self.assertEqual(playback_record([[0,2]],5.8125)['status'],'PARTIAL_RECORDED_RANGE')
        self.assertEqual(playback_record([],5.8125)['status'],'NO_RECORDED_RANGE')
        self.assertEqual(playback_record([[2,1]],5.8125)['status'],'INVALID_PLAYBACK_METADATA')


if __name__=='__main__':unittest.main()
