import copy,json,unittest
from pathlib import Path
from wcomr.policy_generator_r1.historical_timing_analysis import analyze
class Analysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card=json.loads((Path(__file__).resolve().parents[1]/'manifests/cara_historical_bridge104_scope_quote_r1_20261024.json').read_text())
    def rows(self):
        rows=[]
        for r in self.card['matrix']:
            if r['section'] not in ('CALIBRATION','VALIDATION'):continue
            n=320+2*self.card['CAL_FIT_members'].index(r['member'])
            c=self.card['policies'][r['role']]
            t=n if c is None else n+3+6*(c['counts']['D']-36)+.15*c['counts']['A']
            rows.append(dict(r,status='COMPLETE',complete_request_boundary=True,diagnostic=False,seconds=t))
        return rows
    def test_known_model_and_fixed_budget(self):
        a=analyze(self.card,self.rows());self.assertTrue(a['timing_model_validated']);self.assertAlmostEqual(a['fit_coefficients']['per_D'],6)
        self.assertLessEqual(a['budget_seconds'],257.7712338712067)
    def test_validation_cannot_change_coefficients(self):
        rows=self.rows();a=analyze(self.card,rows)
        for r in rows:
            if r['section']=='VALIDATION' and r['role']!='NATIVE':r['seconds']+=10
        b=analyze(self.card,rows);self.assertEqual(a['fit_coefficients'],b['fit_coefficients']);self.assertFalse(b['timing_model_validated'])
    def test_missing_duplicate_and_nonfinite_refused(self):
        rows=self.rows()
        for bad in [rows[:-1],rows[:-1]+[rows[0]]]:
            with self.assertRaises(ValueError):analyze(self.card,bad)
        rows[0]['seconds']=float('nan')
        with self.assertRaises(ValueError):analyze(self.card,rows)
    def test_diagnostic_and_rejection_refused(self):
        for field,value in [('diagnostic',True),('status','VIDEO_REJECTED')]:
            rows=self.rows();rows[0][field]=value
            with self.assertRaises(ValueError):analyze(self.card,rows)
    def test_quality_cannot_change_time_fit(self):
        a=self.rows();b=copy.deepcopy(a)
        for i,r in enumerate(b):r['LPIPS']=i*1000
        self.assertEqual(analyze(self.card,a),analyze(self.card,b))
if __name__=='__main__':unittest.main()
