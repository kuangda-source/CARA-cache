"""Independent exhaustive global-order oracle and old first-choice parity."""
from itertools import combinations
import json
import math
from pathlib import Path
import unittest

from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_phase_coverage_topk_r1 import global_topk,seven_candidate_pool
from wcomr.cara_source_coverage_r1 import coverage_plans
from wcomr.policy_generator_r1.interval_grammar import Profile

ROOT=Path(__file__).resolve().parents[1]
METRICS={}


def oracle(profile,count,sigmas,tilt):
    result=[]
    for mask in combinations(range(1,profile.horizon+1),count):
        if not set(profile.protected_dense)<=set(mask):continue
        if any(b-a-1>profile.max_source_age for a,b in zip(mask,mask[1:]+(profile.horizon+1,))):continue
        past=[];values=[]
        for t in range(1,profile.horizon+1):
            if t in mask:past.append(t)
            elif len(past)<2:break
            else:
                s=sigmas[t-1]/sigmas[0];b=past[-1]
                distance=((t-b)/profile.horizon+sigmas[b-1]/sigmas[0]-s)/2
                values.append(round(math.exp(tilt*(s-.5))*distance*10**12))
        else:result.append((max(values,default=0),sum(v*v for v in values),mask))
    return sorted(result)[:3]


class GlobalTopK(unittest.TestCase):
    def test_global_top3_matches_independent_exhaustive_order(self):
        cases=0;different_peak_cases=0
        for n in (5,7,9):
            profile=Profile(n,(1,2,n),3,2,1,'GLOBAL_TOPK_CPU')
            for power in (1.,2.):
                sigmas=[(1-i/n)**power for i in range(n+1)]
                for count in range(3,n+1):
                    for tilt in (-2.,0.,2.,4.):
                        expected=oracle(profile,count,sigmas,tilt)
                        if not expected:
                            with self.assertRaisesRegex(ValueError,'No legal schedule'):
                                global_topk(profile,count,sigmas,tilt=tilt)
                        else:
                            plans=global_topk(profile,count,sigmas,tilt=tilt)['plans']
                            actual=[(p['peak_units'],p['squared_units'],tuple(p['dense_steps'])) for p in plans]
                            self.assertEqual(actual,expected,(n,power,count,tilt))
                            different_peak_cases+=len({r[0] for r in expected})>1
                        cases+=1
        METRICS.update(exhaustive_cases=cases,including_different_peak_runner_up_cases=different_peak_cases)
        self.assertGreater(different_peak_cases,0)

    def test_actual_grid_first_choice_unchanged_and_seven_distinct_candidates(self):
        card=json.loads((ROOT/'plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json').read_bytes())
        profile=profile_from(card['profile']);sigmas=card['schedule']['sigmas']
        for budget in (16,17,19,22):
            pool=seven_candidate_pool(profile,budget,sigmas)
            self.assertEqual(pool['unique_candidates'],7)
            for tilt in (0.,2.,4.):
                old=coverage_plans(profile,budget,sigmas,tilt=tilt,mode='single')['plans'][0]
                new=global_topk(profile,budget,sigmas,tilt=tilt)['plans'][0]
                self.assertEqual((new['dense_steps'],new['peak_units'],new['squared_units']),
                                 (old['dense_steps'],old['peak_units'],old['squared_units']))
            for row in pool['candidates']:
                self.assertEqual(row['policy']['counts'],dict(D=budget,A=0,C=36-budget))
        METRICS['actual36_seven_candidate_budgets']=[16,17,19,22]


if __name__=='__main__':unittest.main()
