"""Small measurement helpers; do not modify outputs, RNG or cache decisions."""
import functools
import time


class StageTimes:
    def __init__(self, synchronize, clock=time.perf_counter):
        self.synchronize, self.clock = synchronize, clock
        self.values = {}
        self._originals = []

    def wrap(self, owner, attribute, label):
        original = getattr(owner, attribute)

        @functools.wraps(original)
        def measured(*args, **kwargs):
            self.synchronize()
            start = self.clock()
            try:
                return original(*args, **kwargs)
            finally:
                self.synchronize()
                value = self.values.setdefault(label, {"calls": 0, "seconds": 0.0})
                value["calls"] += 1
                value["seconds"] += self.clock() - start

        setattr(owner, attribute, measured)
        self._originals.append((owner, attribute, original))

    def reset(self):
        self.values = {}

    def close(self):
        for owner, attribute, original in reversed(self._originals):
            setattr(owner, attribute, original)
        self._originals.clear()


class BlockCounts:
    """Count shallow calls versus last-block calls, without trusting cache counters."""
    def __init__(self, blocks):
        if len(blocks) < 2:
            raise ValueError("Need at least two blocks")
        self.reset()
        self.handles = [blocks[0].register_forward_pre_hook(self._first),
                        blocks[-1].register_forward_pre_hook(self._last)]

    def _first(self, module, args):
        self.first += 1

    def _last(self, module, args):
        self.last += 1

    def reset(self):
        self.first = self.last = 0

    def result(self):
        if not 0 <= self.last <= self.first:
            raise RuntimeError("Inconsistent block counts")
        return {"denoiser_calls": self.first, "full_calls": self.last,
                "skipped_deep_calls": self.first - self.last}

    def close(self):
        for handle in self.handles:
            handle.remove()
