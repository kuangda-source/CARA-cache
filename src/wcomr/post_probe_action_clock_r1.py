"""One synchronous incremental-action clock on the unchanged paired executor.

Each replay computes its two probes outside this clock. All actual replay,
snapshot, probe and artifact work remains chargeable in the whole-card bill.
This diagnostic clock is not end-to-end latency or a pure kernel benchmark.
"""
from contextlib import contextmanager
from dataclasses import asdict
import math
import time

from .cfg_paired_probe_forward import PaidProbe

BOUNDARY='AFTER_TWO_PAID_PROBES_BEFORE_SELECT_THROUGH_POST_RF_AND_CACHE_COMMIT'


class ActionClock:
    def __init__(self, *, synchronize, clock=time.perf_counter):
        self.synchronize,self.clock=synchronize,clock
        self.packets=None;self.start=None;self.result=None

    def begin(self, packets):
        if (self.start is not None or self.result is not None or len(packets)!=2
                or any(not isinstance(p,PaidProbe) for p in packets)
                or [p.slot for p in packets]!=[0,1]
                or packets[0].counter%2 or packets[1].counter!=packets[0].counter+1):
            raise ValueError('Exactly one original two-paid-probe boundary required')
        # Metadata serialization and draining the shared prefix precede the clock.
        self.packets=[asdict(p) for p in packets]
        self.synchronize();self.start=self.clock()

    def finish(self, error=None):
        if self.result is not None:raise ValueError('One original action interval only')
        if self.start is None:raise ValueError('Protected or missing probe is not an action price')
        self.synchronize();seconds=self.clock()-self.start
        if not math.isfinite(seconds) or seconds<=0:
            raise ValueError('An observed action clock must have finite positive duration')
        self.result=dict(status='PASS' if error is None else 'ACTION_FAILED_INTERVAL_RETAINED',
            synchronized_wall_seconds=seconds,paid_packets=self.packets,boundary=BOUNDARY,
            selection_and_normal_commit_included=True,shared_probe_seconds_included=False,
            snapshot_restore_tensor_hash_or_write_included=False,
            complete_pair_or_clean_video_latency=False,
            error_type=None if error is None else type(error).__name__)
        return self.result


@contextmanager
def observe_post_probe_action(owner, *, synchronize, clock=time.perf_counter):
    """Wrap only the callback passed to the original base pair, never its body."""
    base=owner.base;original=base.pair;had='pair' in vars(base);prior=vars(base).get('pair')
    timer=ActionClock(synchronize=synchronize,clock=clock)
    def pair(noise,latent,timestep,conditions,choose):
        def paid(packets):
            timer.begin(packets)
            return choose(packets)
        return original(noise,latent,timestep,conditions,paid)
    base.pair=pair
    try:
        yield timer
    except BaseException as error:
        if timer.start is not None and timer.result is None:
            try:timer.finish(error)
            except BaseException:pass  # Preserve the original poisoned-pair error.
        raise
    finally:
        if had:base.pair=prior
        else:delattr(base,'pair')
