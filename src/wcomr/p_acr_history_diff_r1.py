"""Simple history-difference comparator, not official FasterCache reproduction.

Only ordinary real DD pairs may update the history. Current omitted-branch
teachers and approximate READOUT/P sources do not enter this comparator.
"""
from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class PastCFGDelta:
    context: tuple
    step: int
    delta_c_minus_u: torch.Tensor

    @classmethod
    @torch.no_grad()
    def from_actual_DD(cls, *, context, step, pair, semantic_action, diagnostic_only):
        if (semantic_action != 'DD' or diagnostic_only or not context or type(step) is not int or step <= 0
                or not isinstance(pair, tuple) or len(pair) != 2
                or pair[0].shape != pair[1].shape or pair[0].dtype != pair[1].dtype or pair[0].device != pair[1].device):
            raise ValueError('Strictly actual deployment DD in one context required')
        return cls(context, step, (pair[0] - pair[1]).detach().clone())

    @torch.no_grad()
    def readout(self, dense_one, *, context, step, direction):
        if (context != self.context or step <= self.step or direction not in ('Pc','Pu')
                or dense_one.shape != self.delta_c_minus_u.shape or dense_one.dtype != self.delta_c_minus_u.dtype
                or dense_one.device != self.delta_c_minus_u.device):
            raise ValueError('Compatible strictly-past true DD difference required')
        if direction == 'Pc':return dense_one, dense_one-self.delta_c_minus_u
        return dense_one+self.delta_c_minus_u, dense_one
