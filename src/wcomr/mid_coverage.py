"""Prefix-only coverage and state roundtrip controls, never a cache policy."""
import copy
import hashlib
import json
import random
from collections.abc import Mapping

import numpy as np
import torch
from .mid_scope import scope_gate, validate_scope, compare_prefix

WC_FIELDS = ['cnt', 'worldcache_step_skipped_count', 'accumulated_rel_l1_distance',
             'residual_cache', 'probe_residual_cache', 'residual_window',
             'probe_residual_window', 'previous_internal_states', 'previous_input',
             'previous_output', 'resume_flag', 'affline_scale_log_info',
             'affline_emb', 'crossattn_emb']


class PrefixComplete(Exception):
    """Expected after a complete solver update; not successful video generation."""


def tree_digest(value):
    h = hashlib.sha256()
    def walk(x):
        if isinstance(x, torch.Tensor):
            if not bool(torch.isfinite(x).all()):
                raise ValueError('Nonfinite state')
            h.update(str((str(x.dtype), list(x.shape))).encode())
            h.update(memoryview(x.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy()))
        elif isinstance(x, np.ndarray):
            h.update(str((str(x.dtype), x.shape)).encode()); h.update(x.tobytes())
        elif isinstance(x, Mapping):
            for key in sorted(x):
                h.update(str(key).encode()); walk(x[key])
        elif isinstance(x, (list, tuple)):
            h.update(type(x).__name__.encode())
            for item in x: walk(item)
        elif x is None or isinstance(x, (str, int, float, bool, np.generic)):
            h.update(repr(x).encode())
        else:
            raise TypeError('Uncovered state type: ' + type(x).__name__)
    walk(value)
    return h.hexdigest()


class StateRoundtrip:
    """Own net cache + entire scheduler dictionary + output and three RNGs.

    The ongoing caller's conditioning/closure is unchanged. This is an in-process
    restoration test, not an independently resumable whole-pipeline branch API.
    """
    def __init__(self, net, scheduler, output):
        self.net, self.scheduler = net, scheduler
        self.keys = [k for k in WC_FIELDS if hasattr(net, k)]
        self.net_state = copy.deepcopy({k: getattr(net, k) for k in self.keys})
        self.solver_state = copy.deepcopy({k:v for k,v in vars(scheduler).items() if not callable(v)})
        self.output = copy.deepcopy(output)
        self.python_rng = random.getstate()
        self.numpy_rng = np.random.get_state()
        self.cpu_rng = torch.random.get_rng_state().clone()
        self.cuda_rng = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []

    def restore(self):
        for k, v in copy.deepcopy(self.net_state).items(): setattr(self.net, k, v)
        methods = {k:v for k,v in vars(self.scheduler).items() if callable(v)}
        vars(self.scheduler).clear(); vars(self.scheduler).update(copy.deepcopy(self.solver_state))
        vars(self.scheduler).update(methods)
        random.setstate(self.python_rng); np.random.set_state(self.numpy_rng)
        torch.random.set_rng_state(self.cpu_rng)
        if self.cuda_rng: torch.cuda.set_rng_state_all(self.cuda_rng)
        return copy.deepcopy(self.output)

    def fingerprint(self):
        return tree_digest({'net': {k: getattr(self.net, k) for k in self.keys},
                            'solver': {k:v for k,v in vars(self.scheduler).items() if not callable(v)}, 'output': self.output,
                            'python_rng': random.getstate(), 'numpy_rng': np.random.get_state(),
                            'cpu_rng': torch.random.get_rng_state(),
                            'cuda_rng': torch.cuda.get_rng_state_all() if self.cuda_rng else []})

