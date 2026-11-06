"""Cross-platform derived-float roundoff must not weaken original evidence gates."""
import copy,json,unittest
from wcomr.policy_generator_r1.historical_terminal import accept,post_replay_equal
from wcomr.policy_price_terminal_r1 import record
from test_cara_history104_combination_r1 import fixture
from test_policy_price_terminal_r1 import put

class Precision(unittest.TestCase):
    def test_derived_roundoff_only(self):
        a={'timing':{'fit_coefficients':{'offset':1.2},'timing_model_validated':False}}
        b=copy.deepcopy(a);b['timing']['fit_coefficients']['offset']+=3e-14
        self.assertTrue(post_replay_equal(a,b))
        b['timing']['fit_coefficients']['offset']+=1e-9
        self.assertFalse(post_replay_equal(a,b))
    def test_original_values_and_flags_exact(self):
        for a,b in [({'quality':{'LPIPS':.1}},{'quality':{'LPIPS':.1+1e-14}}),
                    ({'timing':{'budget_seconds':250.}},{'timing':{'budget_seconds':250.+1e-13}}),
                    ({'timing':{'timing_model_validated':False}},{'timing':{'timing_model_validated':True}}),
                    ({'timing':{'validation':[{'actual_seconds':250.}]}},{'timing':{'validation':[{'actual_seconds':250.+1e-13}]}})]:
            self.assertFalse(post_replay_equal(a,b))
    def test_nan_and_missing_fields_rejected(self):
        for x in (float('nan'),float('inf')):
            self.assertFalse(post_replay_equal({'timing':{'fit_coefficients':{'offset':x}}},{'timing':{'fit_coefficients':{'offset':x}}}))
        self.assertFalse(post_replay_equal({'a':1},{}))
    def test_full_acceptance_roundoff_and_material_failure(self):
        v=fixture();p=record(v,'post');p['scientific']['timing']['fit_coefficients']['offset']+=3e-14
        put(v,'post',p);e=record(v,'post_exit');e['final_result_sha256']=v['files']['post']['sha256'];put(v,'post_exit',e)
        self.assertTrue(accept(v)['full_protocol_accepted'])
        p['scientific']['timing']['fit_coefficients']['offset']+=1e-8;put(v,'post',p)
        e['final_result_sha256']=v['files']['post']['sha256'];put(v,'post_exit',e)
        with self.assertRaises(ValueError):accept(v)
if __name__=='__main__':unittest.main()
