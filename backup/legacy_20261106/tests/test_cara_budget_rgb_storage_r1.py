import io
import unittest
import numpy as np
from wcomr.cara_budget_rgb_storage_r1 import rgb_storage_plan


class StorageTests(unittest.TestCase):
    def test_saved_bytes_match_and_include_every_query(self):
        shape=[3,93,2,4];output=io.BytesIO()
        np.save(output,np.zeros(shape,dtype=np.float32),allow_pickle=False)
        plan=rgb_storage_plan(shape=shape,max_queries=3,native_teachers=2,
                              extra_full_rgb_paths=4,reserved_other_bytes=123)
        self.assertEqual(plan['NPY_bytes_per_path'],len(output.getvalue()))
        self.assertEqual(plan['maximum_retained_RGB_paths'],12)
        self.assertEqual(plan['total_accounted_bytes'],12*len(output.getvalue())+123)
        self.assertFalse(plan['physical_storage_admitted'])

    def test_full_resolution_cost_exceeds_old_32GiB(self):
        plan=rgb_storage_plan(shape=[3,93,432,768],max_queries=301,native_teachers=2,
                              extra_full_rgb_paths=0,reserved_other_bytes=0)
        self.assertEqual(plan['maximum_retained_RGB_paths'],604)
        self.assertGreater(plan['retained_NPY_bytes'],32*2**30)
        self.assertFalse(plan['full_GPU_storage_quote'])

    def test_partial_or_missing_scope_refused(self):
        base=dict(shape=[3,93,432,768],max_queries=3,native_teachers=2,
                  extra_full_rgb_paths=0,reserved_other_bytes=0)
        for change in ({'shape':[3,92,432,768]},{'max_queries':True},{'max_queries':0},
                       {'native_teachers':0},{'extra_full_rgb_paths':-1},{'reserved_other_bytes':1.5}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                rgb_storage_plan(**{**base,**change})


if __name__=='__main__':unittest.main()
