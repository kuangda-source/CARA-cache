"""Source-bound N08 audit controls, including the saved full40 receipt."""
import copy
import gzip
import json
import math
from pathlib import Path
import unittest

from wcomr import balanced_repeat_acceptance_r1 as strict
from wcomr.balanced_repeat_roundoff_acceptance_r1 import _equal, accept

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'reports/wc_paper_N08_balanced_full40_terminal_collection_user_status_20261017.json.gz'
STD = ('timing_statistics', 'scene_methods', 0, 'complete_repeat_sample_std_seconds')


class RoundoffBoundary(unittest.TestCase):
    def test_one_ulp_only_at_registered_derived_std(self):
        a = .5033327597646108
        self.assertTrue(_equal(a, math.nextafter(a, 0), STD, []))
        b = math.nextafter(math.nextafter(a, 0), 0)
        self.assertFalse(_equal(a, b, STD, []))
        self.assertFalse(_equal(a, math.nextafter(a, 0), STD[:-1]+('complete_repeat_mean_seconds',), []))

    def test_nonfinite_negative_and_structure_rejected(self):
        self.assertFalse(_equal(float('nan'), float('nan'), STD, []))
        self.assertFalse(_equal(1., -1., STD, []))
        self.assertFalse(_equal({'x': 1}, {'x': 2}, (), []))
        self.assertFalse(_equal([1], [1, 2], (), []))
        self.assertFalse(_equal(1, 1., STD, []))


@unittest.skipUnless(CAPTURE.is_file(), 'Original full40 receipt is required for integration controls')
class OriginalFull40(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(gzip.decompress(CAPTURE.read_bytes()))

    def test_original_strict_failure_is_retained(self):
        with self.assertRaisesRegex(ValueError, 'per-frame, per-round'):
            strict.accept(self.value, self.value['launch'])

    def test_complete_original_acceptance_without_mutation(self):
        before = copy.deepcopy(self.value)
        r = accept(self.value, self.value['launch'])
        self.assertTrue(r['scientific_full_scope_accepted'])
        self.assertEqual((r['accepted_scientific_videos'], r['scored_scientific_videos']), (30, 30))
        self.assertEqual(len(r['offline_roundoff_bridge']['derived_statistic_differences']), 1)
        self.assertEqual(self.value, before)

    def rejected(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        with self.assertRaises((ValueError, KeyError, AssertionError)):
            accept(value, value['launch'])

    def test_summary_std_beyond_one_ulp_rejected(self):
        self.rejected(lambda v: v['final']['timing_statistics']['scene_methods'][1].__setitem__(
            'complete_repeat_sample_std_seconds', .5033327597646108+1e-8))

    def test_summary_mean_one_ulp_change_rejected(self):
        def change(v):
            r=v['final']['timing_statistics']['scene_methods'][0]
            r['complete_repeat_mean_seconds']=math.nextafter(r['complete_repeat_mean_seconds'], math.inf)
        self.rejected(change)

    def test_original_raw_time_change_rejected(self):
        self.rejected(lambda v: v['final']['rows'][-1].__setitem__('core_seconds', -1.))

    def test_source_change_rejected(self):
        self.rejected(lambda v: v['registration'].__setitem__('source_revision', '0'*40))

    def test_incomplete_denominator_rejected(self):
        self.rejected(lambda v: v['final']['rows'].pop())

    def test_failed_post_exit_rejected(self):
        self.rejected(lambda v: v['post_exit'].__setitem__('exit_code', 1))

    def test_actual_fee_change_rejected(self):
        self.rejected(lambda v: v['billing'].__setitem__('actual_GPUh', 0.))

    def test_lease_not_released_rejected(self):
        self.rejected(lambda v: v.__setitem__('own_UUID_lock_free', False))

