"""Original allocation epoch binding, with explicit synthetic OS observations."""
import copy
import unittest
from unittest.mock import patch

from wcomr.cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock


class P1ClockTests(unittest.TestCase):
    def setUp(self):
        self.context = dict(source_revision='1'*40, launch_id='2'*32, host='two_card',
            gpu_uuid='GPU-CPU-UNIT-FIXTURE', scope_sha256='3'*64, guardian_started_monotonic=100.)
        self.guardian = dict(self.context, CPU_fixture_only=False, started_monotonic=100.,
            original_handles=dict(guardian={'explicit_CPU_unit_identity': True}))

    def test_uses_original_whole_allocation_epoch_and_includes_idle_time(self):
        with patch('wcomr.cara_source_lifecycle_p1_clock_r1.observe_original_process', return_value={'original_live': True}), \
                patch('wcomr.cara_source_lifecycle_p1_clock_r1.time.monotonic', side_effect=[125., 200.]):
            clock = OriginalAllocationClock(self.guardian, self.context)
            self.assertEqual(clock(), 100.)

    def test_ended_foreign_or_unconfirmed_original_guardian_refused(self):
        for fault in ('ended', 'source', 'launch', 'epoch', 'unknown'):
            guardian = copy.deepcopy(self.guardian)
            if fault == 'ended': guardian['ended_monotonic'] = 150.
            elif fault == 'source': guardian['source_revision'] = '0'*40
            elif fault == 'launch': guardian['launch_id'] = '0'*32
            elif fault == 'epoch': guardian['started_monotonic'] = 101.
            with self.subTest(fault=fault), patch(
                    'wcomr.cara_source_lifecycle_p1_clock_r1.observe_original_process',
                    return_value={'original_live': None if fault == 'unknown' else True}), \
                    self.assertRaises(ValueError):
                OriginalAllocationClock(guardian, self.context)

    def test_original_liveness_loss_or_epoch_regression_stops_the_meter(self):
        with patch('wcomr.cara_source_lifecycle_p1_clock_r1.observe_original_process',
                   side_effect=[{'original_live': True}, {'original_live': False}]), \
                patch('wcomr.cara_source_lifecycle_p1_clock_r1.time.monotonic', return_value=125.):
            clock = OriginalAllocationClock(self.guardian, self.context)
            with self.assertRaises(ValueError):
                clock()
        with patch('wcomr.cara_source_lifecycle_p1_clock_r1.observe_original_process', return_value={'original_live': True}), \
                patch('wcomr.cara_source_lifecycle_p1_clock_r1.time.monotonic', side_effect=[125., 124.]):
            clock = OriginalAllocationClock(self.guardian, self.context)
            with self.assertRaises(ValueError):
                clock()


if __name__ == '__main__':
    unittest.main()
