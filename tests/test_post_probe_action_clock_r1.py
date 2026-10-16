"""Deterministic CPU clock; real paired-callback boundaries, no measured GPU price."""
from types import SimpleNamespace
import unittest

from wcomr.cfg_paired_probe_forward import PaidProbe
from wcomr.post_probe_action_clock_r1 import ActionClock,observe_post_probe_action

PACKETS=(PaidProbe(0,20,True,.1,.2,.06),PaidProbe(1,21,True,.2,.3,.06))


class ClockControls(unittest.TestCase):
    def test_only_continuation_selector_and_commit_inside_clock(self):
        time=[0.];events=[]
        class Base:
            def pair(self,noise,latent,timestep,conditions,choose):
                time[0]+=50;events.append('two probes paid')
                value=choose(PACKETS);time[0]+=7;events.append('post RF outputs')
                return value
        owner=SimpleNamespace(base=Base());original=owner.base.pair
        def choose(p):time[0]+=2;events.append('ordinary select');return 'CC'
        with observe_post_probe_action(owner,synchronize=lambda:events.append('sync'),clock=lambda:time[0]) as timer:
            self.assertEqual(owner.base.pair(None,None,None,None,choose),'CC')
            time[0]+=3;events.append('normal commit');row=timer.finish()
        self.assertEqual(row['synchronized_wall_seconds'],12.)
        self.assertEqual(owner.base.pair,original);self.assertNotIn('pair',vars(owner.base))
        self.assertEqual(events,['two probes paid','sync','ordinary select','post RF outputs','normal commit','sync'])
        self.assertFalse(row['complete_pair_or_clean_video_latency'])
        self.assertFalse(row['shared_probe_seconds_included'])

    def test_failure_propagates_original_error_and_uninstalls_wrapper(self):
        time=[0.]
        def original(*args):
            args[-1](PACKETS);time[0]+=4;raise RuntimeError('ORIGINAL_P0_FAILURE')
        owner=SimpleNamespace(base=SimpleNamespace(pair=original))
        with self.assertRaisesRegex(RuntimeError,'ORIGINAL_P0_FAILURE'):
            with observe_post_probe_action(owner,synchronize=lambda:None,clock=lambda:time[0]) as timer:
                owner.base.pair(None,None,None,None,lambda p:'DD')
        self.assertIs(owner.base.pair,original)
        self.assertEqual(timer.result['status'],'ACTION_FAILED_INTERVAL_RETAINED')
        self.assertEqual(timer.result['error_type'],'RuntimeError')

    def test_protected_missing_duplicate_nonfinite_or_wrong_prefix_cannot_be_price(self):
        clock=ActionClock(synchronize=lambda:None)
        with self.assertRaises(ValueError):clock.finish()
        for bad in (PACKETS[::-1],PACKETS[:1],(object(),object())):
            with self.assertRaises(ValueError):clock.begin(bad)
        values=iter([1.,float('nan')]);clock=ActionClock(synchronize=lambda:None,clock=lambda:next(values))
        clock.begin(PACKETS)
        with self.assertRaises(ValueError):clock.begin(PACKETS)
        with self.assertRaises(ValueError):clock.finish()


if __name__=='__main__':unittest.main()
