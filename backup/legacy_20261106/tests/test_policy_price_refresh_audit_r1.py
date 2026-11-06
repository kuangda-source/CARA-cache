import copy
import unittest
from wcomr.policy_interval_assets_r1 import cells, ROUNDS
from wcomr.policy_price_refresh_audit_r1 import audit_price_cells, make_repriced_bundle


def rows():
    return [dict(source=s,target=t,source_anchor_steps=[s-1,s],source_sha256='1'*64,
        older_source_sha256='2'*64,input_sha256='3'*64,original_parent_hashes_equal=True,
        source_shadow_writes_parent=False,extra_deep_teacher_pairs=0,new_error_labels=0,
        raw_interval_tensors_written=0,price_trials=[dict(round=r,action=a,seconds=.1,
            repeated_output_equal=True,shared_prefix_included=False,restore_copy_hash_write_included=False,
            boundary='AFTER_ALREADY_PAID_PROBES_THROUGH_WC_HEAD_RF_AND_SHARED_FUSION')
            for r,order in ROUNDS for a in order]) for s,t in cells()]


class PriceAudit(unittest.TestCase):
    def test_complete(self):
        r=rows();self.assertEqual(audit_price_cells(r,r)['readout_trials'],4872)
    def test_any_non_nearest_missing_repeat_fails(self):
        original=rows();r=copy.deepcopy(original);r[2]['price_trials'].pop()
        with self.assertRaises(ValueError):audit_price_cells(r,original)
    def test_changed_history_or_parent_fails(self):
        original=rows()
        for key in ('source_sha256','older_source_sha256','input_sha256'):
            r=copy.deepcopy(original);r[0][key]='4'*64
            with self.assertRaises(ValueError):audit_price_cells(r,original)
    def test_negative_price_nonfinite_and_different_output_fail(self):
        original=rows()
        for key,value in [('seconds',float('nan')),('seconds',0),('repeated_output_equal',False),
                          ('shared_prefix_included',True),('restore_copy_hash_write_included',True)]:
            r=copy.deepcopy(original);r[0]['price_trials'][0][key]=value
            with self.assertRaises(ValueError):audit_price_cells(r,original)
    def test_cannot_merge_without_exclusive_or_parity(self):
        for ex,pa in [(False,True),(True,False)]:
            with self.assertRaises(ValueError):make_repriced_bundle([],[],{},original_bundle_sha256='a',
                prices_sha256='b',profile_identity='c',exclusive_accepted=ex,parity_accepted=pa)

if __name__=='__main__':unittest.main()
