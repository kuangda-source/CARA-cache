"""Share one official prepared batch and its full RNG transition across paths."""
import copy
import random

import numpy as np
import torch

from .mid_coverage import tree_digest


class RNGState:
    def __init__(self):
        self.python = random.getstate()
        self.numpy = np.random.get_state()
        self.cpu = torch.random.get_rng_state().clone()
        self.cuda = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []

    def restore(self):
        random.setstate(self.python); np.random.set_state(self.numpy)
        torch.random.set_rng_state(self.cpu)
        if self.cuda:
            torch.cuda.set_rng_state_all(self.cuda)

    def signatures(self):
        return {k: tree_digest(v) for k, v in {
            'python': random.getstate(), 'numpy': np.random.get_state(),
            'torch_cpu': torch.random.get_rng_state(),
            'torch_cuda': torch.cuda.get_rng_state_all() if self.cuda else [],
        }.items()}


def input_signatures(args, kwargs):
    """Names retained; no tensor, condition or non-tensor argument is dropped."""
    return {'args': [tree_digest(x) for x in args],
            'kwargs': {k: tree_digest(v) for k, v in sorted(kwargs.items())}}


class PreparedInputReplay:
    def __init__(self, official):
        self.official = official
        self.calls = []
        self.batch = None

    def __call__(self, *args, **kwargs):
        request = input_signatures(args, kwargs)
        if self.batch is None:
            self.request = request
            before = RNGState()
            self.pre_rng = before.signatures()
            result = self.official(*args, **kwargs)
            self.post_rng = RNGState()
            self.post_signature = self.post_rng.signatures()
            self.batch = copy.deepcopy(result)
            self.batch_signature = input_signatures((), result)
            source = 'OFFICIAL_PREPARE_ONCE'
        else:
            if request != self.request:
                raise ValueError('Prepared input request differs')
            if RNGState().signatures() != self.pre_rng:
                raise ValueError('Pre-prepare RNG transition differs')
            # Reproduce preparation's RNG transition, not a new random batch.
            self.post_rng.restore()
            result = copy.deepcopy(self.batch)
            source = 'SHARED_OFFICIAL_PREPARED_BATCH'
        signature = input_signatures((), result)
        if signature != self.batch_signature or RNGState().signatures() != self.post_signature:
            raise ValueError('Prepared batch or full RNG transition differs')
        self.calls.append({'source': source, 'request': request, 'prepared': signature,
                           'rng_before': self.pre_rng, 'rng_after': self.post_signature})
        return result
