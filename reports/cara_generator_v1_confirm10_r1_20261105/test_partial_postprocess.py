"""Complete-cohort selection and incomplete-run inference boundary; CPU only."""
import copy
import json
from pathlib import Path
import unittest

from partial_postprocess import analyze,complete_groups

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


class PartialResults(unittest.TestCase):
    def setUp(self):
        self.card=json.loads((ROOT/'plans/cara_next_stage_20261105/confirm10/manifest.json').read_text())
        self.collection=json.loads((HERE/'collection.json').read_text())

    def test_only_complete_input_groups(self):
        members=complete_groups(self.card,self.collection)
        self.assertEqual(members,list(self.card['inputs_by_alias'].values())[:4])
        broken=copy.deepcopy(self.collection)
        native=next(r for r in broken['rows'] if r['slot']['member']==members[0] and r['slot']['role']=='NATIVE35')
        native['status']='NOT_REACHED'
        self.assertEqual(complete_groups(self.card,broken),members[1:])

    def test_descriptive_effect_does_not_accept_the_full_run(self):
        members=complete_groups(self.card,self.collection)
        values=dict(F17_A2_LIGHT_C=.30,R18C=.20,R16C=.25,R21C=.15)
        rows=[dict(slot=r['slot'],Alex=values[r['slot']['role']],T_DD=130.,mask_matches=True)
              for r in self.collection['rows'] if r['status']=='COMPLETE' and r['slot']['section']!='warm'
              and r['slot']['role']!='NATIVE35']
        self.card['bootstrap']['replicates']=1000
        result=analyze(self.card,dict(complete_members=members,rows=rows,native_T_DD={m:250. for m in members}))
        self.assertAlmostEqual(result['contrasts'][0]['mean_delta'],-.10)
        self.assertEqual(result['status'],'INCOMPLETE_PARTIAL')
        self.assertEqual(result['full_run_verdict'],'NOT_EVALUABLE_INCOMPLETE')
        self.assertFalse(result['whole_run_success'] or result['noninferiority_test'] or result['significance_test'])


if __name__=='__main__':unittest.main()
