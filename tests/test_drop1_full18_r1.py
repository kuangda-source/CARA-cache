"""The new contrast, complete denominators and whole-card authorization."""
import copy,json,unittest
from pathlib import Path
from wcomr.drop1_full18_r1 import CONFIG,COUNTS,METHODS,plans,matrix,validate_contract,full_rows,summaries

ROOT=Path(__file__).resolve().parents[1]

class Contract(unittest.TestCase):
    def setUp(self):self.c=json.loads((ROOT/CONFIG).read_text())
    def test_frozen_contrast(self):
        p=plans();validate_contract(self.c)
        self.assertEqual([p[m].count('D') for m in METHODS],[26,25,25])
        self.assertEqual([p[m].count('A') for m in METHODS],[0,0,1])
        self.assertEqual([n for n in range(36) if p['S26-C'][n]!=p['S25-C'][n]],[20])
        self.assertEqual([n for n in range(36) if p['S25-C'][n]!=p['S25-A'][n]],[20])
        self.assertEqual(p['S26-C'][22],'C')
    def test_invalid_whole_cards(self):
        changes=dict(scope_counts={**COUNTS,'total_paths':12},methods=list(METHODS)[:2],
            deleted_D_update=23,cumulative_cap_GPUh=113,autonomy_exclusive_upper_GPUh=8,
            billed_limit_GPUh=12,forecast_complete_GPUh=20,training=True,online_teachers=True,
            F_B_enabled=True,P_enabled=True,new_native_generation=True,endpoint_tuning=True,
            timing_claim='REPEATED_CLEAN',memory_policy='CLEAR_LIVE_CACHE',warmup_repeats=1,
            A_method='W1_ONE_PHASE',plans={**self.c['plans'],'S25-A':['D']*36})
        for k,v in changes.items():
            with self.subTest(k=k):
                bad=copy.deepcopy(self.c);bad[k]=v
                with self.assertRaises(ValueError):validate_contract(bad)
    def test_complete_matrix_and_missing_not_zero(self):
        scenes=[q['name'] for q in self.c['requests']];rows=matrix(scenes)
        self.assertEqual(len(rows),18)
        self.assertEqual(sum(r['section']=='WARMUP' for r in rows),6)
        retained=full_rows([],scenes);self.assertEqual(len(retained),18)
        result=summaries(retained,scenes)
        self.assertTrue(all(x['complete_four_scene_mean_LPIPS'] is None for x in result['methods']))
        self.assertTrue(all(x['scored_scenes']==0 for x in result['contrasts']))
        with self.assertRaises(ValueError):full_rows([rows[0],rows[0]],scenes)
    def test_contrasts_pair_every_scene(self):
        scenes=[q['name'] for q in self.c['requests']];rows=matrix(scenes)
        for r in rows:
            r.update(endpoint_audit='PASS',LPIPS={'mean_LPIPS':{'S26-C':.2,'S25-C':.3,'S25-A':.21}[r['method']]},core_seconds={'S26-C':100.,'S25-C':95.,'S25-A':96.}[r['method']],counts={'DD':26 if r['method']=='S26-C' else 25})
        z=summaries(rows,scenes)
        self.assertTrue(all(q['scored_scenes']==4 for q in z['contrasts']))
        self.assertAlmostEqual(z['contrasts'][0]['scene_rows'][0]['absolute_change'],-.09)
        self.assertAlmostEqual(z['contrasts'][1]['scene_rows'][0]['speedup_baseline_over_candidate'],100/96)

if __name__=='__main__':unittest.main()
