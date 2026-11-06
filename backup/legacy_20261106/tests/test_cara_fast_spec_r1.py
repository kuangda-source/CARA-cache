import copy
import json
import math
import unittest
from pathlib import Path

from wcomr.cara_fast_spec_r1 import (digest, profile_from, select_baselines, uniform_mask)

ROOT=Path(__file__).resolve().parents[1]


class FastSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())

    def test_full_identity_masks_and_role_denominators(self):
        c=self.card; p=profile_from(c['profile'])
        self.assertEqual(digest({k:v for k,v in c.items() if k!='scope_sha256'}),c['scope_sha256'])
        self.assertEqual(c['counts']['physical_paths'],len(c['physical_matrix']))
        self.assertEqual(len({s['id'] for s in c['physical_matrix']}),60)
        self.assertEqual(len(c['formal_matrix']),32)
        self.assertEqual(sum(s['phase']=='A' for s in c['physical_matrix']),24)
        self.assertEqual(sum(s['purpose']=='calibration' for s in c['physical_matrix']),12)
        for name in ('F19_C','F19_A1','F18_C','F18_A1','UNIFORM19_C'):
            policy=c['roles'][name]['policy'];last=None
            for i,a in enumerate(policy['actions'],1):
                if a=='D':last=i
                else:
                    self.assertIsNotNone(last);self.assertLessEqual(i-last,p.max_source_age)
                    if a=='A':self.assertEqual(i-last,1);self.assertEqual(policy['shared_alpha'][i-1],1.)
            self.assertTrue(all(policy['dense_mask'][i-1] for i in p.protected_dense))
        self.assertEqual(c['roles']['F18_A1']['policy']['actions'][8],'C')
        a,_=uniform_mask(c['schedule'],p,19);b,_=uniform_mask(c['schedule'],p,19)
        self.assertEqual(a,b);self.assertEqual(len(a),19)
        bad=copy.deepcopy(c['schedule']);bad['sigmas'][2]=math.nan
        with self.assertRaises(ValueError):uniform_mask(bad,p,19)

    def fixture(self):
        c=self.card; rows=[];native=[]
        common=dict(host='CPU_ONLY',gpu_uuid='CPU_FIXTURE',scope_sha256=c['scope_sha256'],status='COMPLETE',eligible_clean_time=True)
        for m in c['FIT']:
            native.append(dict(common,member=m,T_DD=300.))
            for family,grid in c['finite_grids'].items():
                for i,candidate in enumerate(grid):
                    rows.append(dict(common,member=m,family=family,candidate=candidate,T_DD=200.+i*2,Alex=.1-i*.01))
        return rows,native

    def test_complete_fit_selection_and_unmatched(self):
        rows,native=self.fixture();c=self.card
        out=select_baselines(rows,native,c['FIT'],c['finite_grids'],c['scope_sha256'])
        self.assertTrue(all(v['candidate']==c['finite_grids'][k][1] for k,v in out['selected'].items()))
        for r in rows:r['T_DD']*=2
        out=select_baselines(rows,native,c['FIT'],c['finite_grids'],c['scope_sha256'])
        self.assertTrue(all(v['time_match']=='UNMATCHED' for v in out['selected'].values()))

    def test_partial_thermal_device_check_and_duplicates_refused(self):
        rows,native=self.fixture();c=self.card
        corruptions=[lambda x:x.pop(),lambda x:x.append(copy.deepcopy(x[0])),
                     lambda x:x[0].update(thermal_interrupted=True),
                     lambda x:x[0].update(member=c['CHECK'][0]),
                     lambda x:x[0].update(gpu_uuid='OTHER'),
                     lambda x:x[0].update(Alex=math.nan),
                     lambda x:x[0].update(T_DD=0.)]
        for change in corruptions:
            data=copy.deepcopy(rows);change(data)
            with self.assertRaises(ValueError):select_baselines(data,native,c['FIT'],c['finite_grids'],c['scope_sha256'])


if __name__=='__main__':unittest.main()
