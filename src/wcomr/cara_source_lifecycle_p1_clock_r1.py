"""Read the original guardian's allocation epoch; never create a second bill."""
import copy
import math
import time

from .cara_budget_original_handles_r1 import observe_original_process


class OriginalAllocationClock:
    def __init__(self, guardian, context):
        keys = ('source_revision', 'launch_id', 'host', 'gpu_uuid', 'scope_sha256')
        if (any(guardian[k] != context[k] for k in keys)
                or guardian['CPU_fixture_only'] is not False
                or guardian.get('ended_monotonic') is not None
                or type(guardian['started_monotonic']) not in (int, float)
                or not math.isfinite(guardian['started_monotonic'])
                or guardian['started_monotonic'] <= 0
                or guardian['started_monotonic'] != context['guardian_started_monotonic']):
            raise ValueError('Live original P1 guardian epoch and exact allocation identity required')
        self.identity = copy.deepcopy(guardian['original_handles']['guardian'])
        self.started = guardian['started_monotonic']
        self.context = copy.deepcopy(context)
        self.last = 0.
        self()

    def __call__(self):
        if observe_original_process(self.identity)['original_live'] is not True:
            raise ValueError('Original guardian/boot/namespace is not confirmed live')
        elapsed = time.monotonic()-self.started
        if not math.isfinite(elapsed) or elapsed < self.last:
            raise ValueError('Original allocation monotonic epoch changed')
        self.last = elapsed
        return elapsed
