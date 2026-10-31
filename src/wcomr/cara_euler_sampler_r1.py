"""Opt-in explicit Euler35 scheduler for the pinned Cosmos sampler.

The model, CFG closure and inference pipeline are unchanged. This adapter does
not load a model, authorize execution, select a cache policy or edit upstream.
"""
from contextlib import contextmanager
import copy

from .cara_euler_protocol_r1 import ExplicitEuler, reconstructed_grid


class CosmosEuler35:
    def __init__(self, grid):
        if grid != reconstructed_grid(35):
            raise ValueError('Exact declared Euler35 reconstruction required')
        self.grid=copy.deepcopy(grid)
        self.timesteps=None
        self._step_index=None

    def set_timesteps(self, num_steps, *, device, shift=5.0, use_kerras_sigma=True):
        import torch
        if num_steps!=35 or shift!=5.0 or use_kerras_sigma is not True:
            raise ValueError('Euler35 requires the declared pinned sampler inputs')
        if self.timesteps is not None:
            raise ValueError('One request per isolated Euler scheduler')
        self.timesteps=torch.tensor(self.grid['timesteps'],dtype=torch.int64,device=device)
        self.sigmas=torch.tensor(self.grid['sigmas'],dtype=torch.float32,device=device)
        self._engine=ExplicitEuler(self.grid)
        self._step_index=0

    def step(self, model_output, timestep, sample, *, return_dict=False, generator=None):
        if return_dict is not False or self._step_index is None or self._step_index>=35:
            raise ValueError('Only an active pinned sampler tuple-return update is supported')
        expected=self.timesteps[self._step_index]
        # The pinned sampler passes its original scalar timestep view. Identity
        # checking avoids a new device-to-host synchronization inside T_DD.
        if (timestep.ndim!=0 or timestep.dtype!=expected.dtype or timestep.device!=expected.device
                or timestep.data_ptr()!=expected.data_ptr()):
            raise ValueError('Original ordered timestep view required')
        if model_output.shape!=sample.shape or model_output.device!=sample.device or model_output.dtype!=sample.dtype:
            raise ValueError('Velocity and latent tensor identity differs')
        result=self._engine.step(model_output,self.grid['timesteps'][self._step_index],sample)
        self._step_index+=1
        return (result,)


@contextmanager
def installed_euler35(model, grid):
    """Install only for one explicit request; restore the original on every exit."""
    original=model.sample_scheduler
    if isinstance(original,CosmosEuler35):
        raise ValueError('Nested Euler installation is not supported')
    scheduler=CosmosEuler35(grid)
    model.sample_scheduler=scheduler
    try:
        yield scheduler
    finally:
        model.sample_scheduler=original
