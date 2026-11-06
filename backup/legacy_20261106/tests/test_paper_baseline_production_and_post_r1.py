"""Finite-scope, wrong Native counts and rejected/missing-data safeguards."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.paper_baseline_grid_r1 import METHODS,point,matrix
from wcomr.paper_baseline_production_r1 import validate_contract,audit_row
from wcomr.paper_baseline_post_r1 import full_rows,summaries

ROOT=Path(__file__).resolve().parents[1]
SCENES=['a','b','c','d']

def synthetic_rows():
    rows=[]
    for planned in matrix(SCENES):
        method=planned['method']
        cost,loss=(300.,0.) if method=='NATIVE35' else (120.,.2)
        if method=='RA_DEFAULT':cost,loss=110.,.15
        if method=='A_NO_P':cost,loss=100.,.1
        rows.append(dict(**planned,status='COMPLETE',endpoint_audit='PASS',core_seconds=cost,
            baseline_grid_point=point(method),actions=None,
            LPIPS=dict(frames=93,frame_distances=[loss]*93,mean_LPIPS=sum([loss]*93)/93)))
    return rows

class ProductionPostTests(unittest.TestCase):
    def test_whole66_contract_and_exact_variable_step_total(self):
        c=json.loads((ROOT/'configs/wc_paper_N05_core66_production_r1_20261016.json').read_text())
        plan=validate_contract(c)
        self.assertEqual(len(plan),66)
        self.assertEqual(sum(point(p['method'])['actual_updates'] for p in plan),2220)
        for key,value in [('methods',c['methods'][:-1]),('scope_counts',{**c['scope_counts'],'scientific_paths':40}),
                          ('P_ACR',True),('billed_limit_GPUh',12.),('head_elision',True)]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):validate_contract(bad)

    def test_native18_is_full19_and38_CFG_not_full36(self):
        p=next(r for r in matrix(SCENES) if r['section']=='TIMED' and r['method']=='NATIVE18')
        r=dict(**p,status='COMPLETE',baseline_grid_point=point('NATIVE18'),solver_steps=19,guided_pairs=19,
            scheduler_timesteps=list(range(19)),in_timing_hashes=0,research_checkpoints=0,
            in_timing_guided_copies=0,audit=False,write_deferred_after_main_timer=True,core_seconds=1.,
            installed_thresholds=[dict()],actions=None,native_block_CFG_counts=dict(first=38,last=38),
            native_count_adaptation=dict(inverse_bytes_and_AST_equal=True),
            request_memory_lifecycle=dict(components_alive_after=0,within_request_algorithm_or_guardrails_changed=False))
        audit_row(r,p)
        for key,value in [('solver_steps',36),('native_block_CFG_counts',dict(first=36,last=36)),
                          ('actions',['DD']*19)]:
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):audit_row(bad,p)

    def test_observed_prefix_keeps_all_unreached_and_failed_positions(self):
        runs=[dict(p,status='COMPLETE') for p in matrix(SCENES)[:5]]
        runs[-1]['status']='RUNNING';rows=full_rows(runs,SCENES)
        self.assertEqual(len(rows),66)
        self.assertEqual(rows[4]['status'],'TECH_FAILED_TERMINAL_RUNNER_INCOMPLETE')
        self.assertEqual(sum(r['status']=='NOT_REACHED' for r in rows),61)
        with self.assertRaises(ValueError):full_rows(runs[::-1],SCENES)
        with self.assertRaises(ValueError):full_rows(runs+[runs[0]],SCENES)

    def test_known_joint_cost_fidelity_dominance_is_observed_not_interpolated(self):
        v=summaries(synthetic_rows(),SCENES)
        row=next(r for r in v['contrasts'] if r['candidate']=='A_NO_P' and r['baseline']=='WC_DEFAULT')
        self.assertEqual(row['paired_scenes'],4)
        self.assertAlmostEqual(row['complete_mean_seconds_saved'],20.)
        self.assertAlmostEqual(row['complete_mean_LPIPS_absolute_change'],-.1)
        self.assertTrue(all(abs(r['speedup_baseline_over_candidate']-1.2)<1e-12 for r in row['scene_rows']))
        frontier={r['method']:r for r in v['observed_finite_grid_frontier']}
        self.assertTrue(frontier['A_NO_P']['observed_non_dominated'])
        self.assertIn('A_NO_P',frontier['WC_DEFAULT']['dominated_by'])
        self.assertFalse(v['continuous_frontier_or_time_interpolation_claim'])

    def test_rejected_RA_is_not_zero_filled_or_folded_into_four_case_mean(self):
        rows=synthetic_rows();row=next(r for r in rows if r['section']=='TIMED' and r['method']=='RA_DEFAULT')
        row.update(status='TEXT_REJECTED');row.pop('LPIPS');row.pop('endpoint_audit')
        v=summaries(rows,SCENES);ra=next(r for r in v['methods'] if r['method']=='RA_DEFAULT')
        self.assertEqual(ra['denominator'],4);self.assertEqual(ra['scored_scenes'],3)
        self.assertIsNone(ra['complete_four_scene_mean_LPIPS']);self.assertIsNone(ra['complete_four_scene_mean_seconds'])
        self.assertEqual(ra['scene_rows'][0]['status'],'TEXT_REJECTED')
        self.assertIsNone(ra['scene_rows'][0]['LPIPS'])
        x=next(r for r in v['contrasts'] if r['candidate']=='A_NO_P' and r['baseline']=='RA_DEFAULT')
        self.assertEqual(x['paired_scenes'],3);self.assertIsNone(x['complete_mean_LPIPS_absolute_change'])

    def test_all_timing_survives_missing_reference_quality_without_fake_mean(self):
        rows=synthetic_rows();next(r for r in rows if r['section']=='TIMED' and r['method']=='A_NO_P').pop('LPIPS')
        v=summaries(rows,SCENES);a=next(r for r in v['methods'] if r['method']=='A_NO_P')
        self.assertEqual(a['timed_scenes'],4);self.assertEqual(a['scored_scenes'],3)
        self.assertEqual(a['complete_four_scene_mean_seconds'],100.)
        self.assertIsNone(a['complete_four_scene_mean_LPIPS'])

    def test_tampered_frame_mean_and_reduced_matrix_are_rejected(self):
        rows=synthetic_rows();rows[22]['LPIPS']['mean_LPIPS']+=.1
        with self.assertRaises(ValueError):summaries(rows,SCENES)
        with self.assertRaises(ValueError):summaries(rows[:-1],SCENES)

if __name__=='__main__':unittest.main()
