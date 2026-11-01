"""One bound augmented-state WC/CFG/original-UniPC calibration transition."""
from .cara_read_write_state_r1 import FunctionalUniPC, PostUpdateState, UniPCMemory
from .cara_read_write_transition_r1 import WorldCacheMemory


class ReadWriteStep:
    """Keep solver history, physical cache and its discrete origins together.

The enclosing card binds real model/assets/input/condition hashes in owner.
This operator loads no weights, stores no trajectory and performs no dispatch.
"""
    def __init__(self, worldcache, scheduler, noise, conditions, *, owner):
        if (len(scheduler.timesteps) != 36 or len(scheduler.sigmas) != 37
                or scheduler._step_index is not None or scheduler._begin_index is not None):
            raise ValueError('Initialized untouched original36 UniPC grid required')
        self.worldcache = worldcache
        self.solver = FunctionalUniPC(scheduler)
        self.timesteps = scheduler.timesteps.detach().clone()
        self.noise, self.conditions, self.owner = noise, conditions, owner
        cache = WorldCacheMemory.capture(worldcache.net, owner=owner,
            timesteps=scheduler.timesteps, sigmas=scheduler.sigmas[:-1])
        self.grid = (cache.provenance.timesteps, cache.provenance.sigmas)
        self.initial = PostUpdateState(noise.clone(), UniPCMemory.capture(scheduler), cache.bundle())

    def __call__(self, state, action):
        cache = WorldCacheMemory(**state.cache)
        source = cache.provenance
        if (source is None or source.owner != self.owner or source.completed >= 36
                or (source.timesteps, source.sigmas) != self.grid
                or state.memory.step_index != (None if source.completed == 0 else source.completed)):
            raise ValueError('Bound source grid and actual solver history must advance together')
        index = source.completed
        timestep = self.timesteps[index]
        velocity, cache = self.worldcache.pair(cache, self.noise, state.latent,
            timestep.reshape(1, 1), self.conditions, action=action)
        latent, memory = self.solver.step(state.memory, velocity, timestep, state.latent)
        return PostUpdateState(latent, memory, cache.bundle())
