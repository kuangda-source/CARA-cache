"""Discrete source/validity chart for the original two-branch WC recurrence.

Sources are metadata, not differentiable sigma/index coordinates. Three fixed
physical slots are represented explicitly; invalid slots remain None. This
module never invents a zero feature or reconstructs a state from two anchors.
"""
from dataclasses import dataclass, replace
import math
import re

import torch


FEATURES = ('previous_input', 'previous_internal_states', 'residual_cache',
            'probe_residual_cache', 'previous_output')
WINDOWS = ('residual_window', 'probe_residual_window')


@dataclass(frozen=True)
class Source:
    step: int
    sigma: float
    action: str
    branch: int


@dataclass(frozen=True)
class CacheProvenance:
    owner: str
    timesteps: tuple[float, ...]
    sigmas: tuple[float, ...]
    completed: int = 0
    working: tuple = (None, None)
    residual: tuple = (None, None)
    output: tuple = (None, None)
    window: tuple = ((None, None, None), (None, None, None))

    @classmethod
    def start(cls, fields, *, owner, timesteps, sigmas):
        if not isinstance(owner, str) or not re.fullmatch('[0-9a-f]{64}', owner):
            raise ValueError('Bound request/model/condition owner digest required')
        times, scales = tuple(map(float, timesteps)), tuple(map(float, sigmas))
        if (len(times) != 36 or len(scales) != 36
                or any(not math.isfinite(v) for v in times+scales)
                or any(v < 0 for v in scales)
                or any(a < b for a,b in zip(scales, scales[1:]))):
            raise ValueError('Original complete36 timestep and source-sigma grid required')
        value = cls(owner, times, scales)
        value.slots(fields)
        return value

    def slots(self, fields):
        """Return all22 fixed physical feature slots with validity and source.

The adjoint additionally retains all floating solver/log/embedding/buffer
coordinates. This chart describes feature origins; it does not prune those
other coordinates or turn an inactive physical slot into a continuous zero.
"""
        if fields['cnt'] != 2*self.completed % 70:
            raise ValueError('Original paired counter and provenance step differ')
        result = {}
        for branch in (0, 1):
            sources = dict(previous_input=self.working[branch],
                previous_internal_states=self.working[branch], residual_cache=self.residual[branch],
                probe_residual_cache=self.residual[branch], previous_output=self.output[branch])
            for name in FEATURES:
                if len(fields[name]) != 2:
                    raise ValueError('Both original CFG branches required')
                result[(name, branch)] = (fields[name][branch], sources[name])
            for name in WINDOWS:
                if len(fields[name]) != 2 or len(fields[name][branch]) > 3:
                    raise ValueError('Three physical WC window slots required')
                if len(fields[name][branch]) != sum(source is not None for source in self.window[branch]):
                    raise ValueError('Original populated window length and validity differ')
                for index in range(3):
                    values = fields[name][branch]
                    result[(name, branch, index)] = (
                        values[index] if index < len(values) else None, self.window[branch][index])
        for path,(value,source) in result.items():
            if ((source is None) != (value is None)
                    or (value is not None and not isinstance(value, torch.Tensor))):
                raise ValueError('Fixed-slot validity/source differs: '+repr(path))
        return result

    def advance(self, before, after, *, action, timestep):
        self.slots(before)
        if (action not in ('C', 'D') or self.completed >= 36
                or float(timestep) != self.timesteps[self.completed]):
            raise ValueError('One bound original-grid hard transition required')
        points = tuple(Source(self.completed+1, self.sigmas[self.completed], action, branch)
                       for branch in (0, 1))
        working, residual, output, windows = points, self.residual, points, self.window
        if action == 'D':
            residual = points
            shifted = []
            for branch in (0, 1):
                populated = tuple(source for source in windows[branch] if source is not None)
                # Original source appends while len<=2, then preserves slot0
                # while replacing physical slots1/2 with previous2/newD.
                sources = populated+(points[branch],) if len(populated) < 3 else (
                    populated[0], populated[2], points[branch])
                shifted.append(sources+(None,)*(3-len(sources)))
            windows = tuple(shifted)
        elif any(source is None for source in self.residual):
            raise ValueError('C needs original populated true-D sources')
        if self.completed+1 == 35:
            working = residual = (None, None)
            windows = ((None, None, None), (None, None, None))
            # The unconditional call resets both output slots, then the final
            # source epilogue writes only its current (unconditional) output.
            output = (None, points[1])
        result = replace(self, completed=self.completed+1, working=working,
                         residual=residual, output=output, window=windows)
        before_slots, after_slots = self.slots(before), result.slots(after)
        for path,(value,source) in after_slots.items():
            previous, prior_source = before_slots[path]
            if source is not None and source == prior_source and value is not previous:
                raise ValueError('Preserved WC feature changed outside its source write: '+repr(path))
        return result

    def same_parent_chart(self, other):
        return (isinstance(other, CacheProvenance) and self.owner == other.owner
                and self.timesteps == other.timesteps and self.sigmas == other.sigmas
                and self.completed == other.completed)
