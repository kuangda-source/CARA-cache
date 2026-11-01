"""CPU-prepared state operations for the proposed read/write-value planner.

UniPC equations come from the pinned upstream class. Only its mutable memory
is made explicit; this module does not differentiate Cosmos, load weights,
run a suffix, or authorize an experiment.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import inspect
from pathlib import Path
from typing import Optional

import torch


UNIPC_SHA256 = 'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3'
MEMORY_FIELDS = ('model_outputs', 'timestep_list', 'lower_order_nums',
                 'last_sample', '_step_index', '_begin_index', 'this_order')


@dataclass(frozen=True)
class UniPCMemory:
    model_outputs: tuple[Optional[torch.Tensor], ...]
    timestep_list: tuple[Optional[torch.Tensor], ...]
    lower_order_nums: int
    last_sample: Optional[torch.Tensor]
    step_index: Optional[int]
    begin_index: Optional[int]
    this_order: Optional[int]

    @classmethod
    def capture(cls, scheduler):
        # Preserve graph edges. Inference checkpointing has its own detached
        # CPU-backed owner; deepcopy/detach here would erase the history VJP.
        return cls(tuple(scheduler.model_outputs), tuple(scheduler.timestep_list),
                   scheduler.lower_order_nums, scheduler.last_sample,
                   scheduler._step_index, scheduler._begin_index,
                   getattr(scheduler, 'this_order', None))

    def install(self, scheduler):
        scheduler.model_outputs = list(self.model_outputs)
        scheduler.timestep_list = list(self.timestep_list)
        scheduler.lower_order_nums = self.lower_order_nums
        scheduler.last_sample = self.last_sample
        scheduler._step_index = self.step_index
        scheduler._begin_index = self.begin_index
        if self.this_order is None:
            vars(scheduler).pop('this_order', None)
        else:
            scheduler.this_order = self.this_order


class FunctionalUniPC:
    """Apply one original update on explicit memory, without mutating a caller.

The registered pilot supports the original second-order flow scheduler, fixed
grid and no auxiliary solver. Discrete indices/orders are held fixed for the
local derivative. Floating prediction history and last_sample remain in graph.
"""
    def __init__(self, scheduler):
        if type(scheduler).__name__ != 'FlowUniPCMultistepScheduler':
            raise ValueError('Pinned original UniPC class required')
        source = Path(inspect.getfile(type(scheduler)))
        if hashlib.sha256(source.read_bytes()).hexdigest() != UNIPC_SHA256:
            raise ValueError('Pinned original UniPC source required')
        if (scheduler.config.solver_order != 2 or scheduler.solver_p is not None
                or scheduler.config.thresholding or not scheduler.predict_x0
                or scheduler.config.prediction_type != 'flow_prediction'
                or scheduler.num_inference_steps is None):
            raise ValueError('Registered initialized second-order flow UniPC required')
        # Take a detached configuration/grid template once, before any graph
        # rollout. Every call replaces all mutable update memory below.
        self._template = copy.copy(scheduler)
        vars(self._template).update(copy.deepcopy({
            k: v for k, v in vars(scheduler).items()
            if k not in MEMORY_FIELDS and not callable(v)}))
        self.source_sha256 = UNIPC_SHA256

    def step(self, memory, model_output, timestep, sample):
        scheduler = copy.copy(self._template)
        memory.install(scheduler)
        updated = scheduler.step(model_output, timestep, sample, return_dict=False)[0]
        return updated, UniPCMemory.capture(scheduler)


@dataclass(frozen=True)
class PostUpdateState:
    """One post-solver state used by CPU controls of the four-corner split.

cache is an indivisible bundle of values AND provenance (both CFG branches,
source sigmas/indices, windows and working state). A production cache adapter
must supply that bundle; this type alone does not certify its completeness.
RNG/conditions must be restored by the enclosing runner before either action.
"""
    latent: torch.Tensor
    memory: UniPCMemory
    cache: dict


def read_write_corners(cached, dense):
    """Keep latent + entire solver memory together; swap the whole cache.

10/01 are paid diagnostic interventions, not deployable cheap actions. No
scalar interpolation of discrete cache source indices is performed here.
"""
    if (cached.memory.step_index != dense.memory.step_index
            or cached.memory.begin_index != dense.memory.begin_index
            or cached.latent.shape != dense.latent.shape
            or cached.latent.dtype != dense.latent.dtype
            or cached.latent.device != dense.latent.device):
        raise ValueError('Aligned post-update C/D states required')
    return {
        '00': cached,
        '10': PostUpdateState(dense.latent, dense.memory, cached.cache),
        '01': PostUpdateState(cached.latent, cached.memory, dense.cache),
        '11': dense,
    }


def factorial_effects(losses):
    """Signed terminal loss changes; negative values mean an improvement."""
    import math
    if (set(losses) != {'00', '10', '01', '11'}
            or any(type(v) not in (int, float) or not math.isfinite(v)
                   for v in losses.values())):
        raise ValueError('Four complete finite endpoint losses required')
    return dict(read=losses['10'] - losses['00'],
                write=losses['01'] - losses['00'],
                interaction=losses['11'] - losses['10'] - losses['01'] + losses['00'],
                total=losses['11'] - losses['00'])
