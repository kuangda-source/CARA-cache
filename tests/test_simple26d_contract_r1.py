import copy,json,unittest
from pathlib import Path
from wcomr.simple26d_r1 import CONFIG,METHODS,plans,matrix,validate_contract
from wcomr.simple26d_post_r1 import full_rows,summaries

class SimpleTests(unittest.TestCase):
    def test_whole_scope_quota_and_support(self):
        c=json.loads((Path(__file__).resolve().parents[1]/CONFIG).read_text());validate_contract(c)
        self.assertEqual(len(matrix([r['name'] for r in c['requests']])),36)
        for k,v in plans().items():self.assertEqual(v.count('D'),26)
        for key,val in [('billed_limit_GPUh',12),('P_enabled',True),('methods',list(METHODS)[:-1]),('timing_claim','CLEAN_LATENCY')]:
            changed=copy.deepcopy(c);changed[key]=val
            with self.assertRaises(ValueError):validate_contract(changed)
    def test_missing_rejected_and_foreign_slots(self):
        rows=full_rows([],['a','b','c','d']);self.assertEqual(len(rows),36)
        value=summaries(rows,['a','b','c','d']);self.assertTrue(all(m['complete_four_scene_mean_LPIPS'] is None for m in value['methods']))
        actual=[{**matrix(['a','b','c','d'])[12],'status':'VIDEO_REJECTED'}]
        rows=full_rows(actual,['a','b','c','d']);self.assertEqual(rows[12]['status'],'VIDEO_REJECTED')
        with self.assertRaises(ValueError):full_rows(actual+actual,['a','b','c','d'])
        with self.assertRaises(ValueError):summaries(rows[:-1],['a','b','c','d'])

if __name__=='__main__':unittest.main()
