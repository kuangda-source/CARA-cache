"""Immutable offline action-mask controls for the audited step-22 window.

A placement swap changes two actions in one CFG branch. Equal refresh counts
are a diagnostic constraint, not equal runtime or an online routing policy.
"""
from dataclasses import dataclass
import hashlib


def cfg_full_counts(mask):
    return tuple(sum(action == 'D' for action in mask[slot::2]) for slot in (0, 1))


def mask_sha256(mask):
    return hashlib.sha256(''.join(mask).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class FixedMaskPlan:
    parent_mask: tuple
    swap_calls: tuple = ()
    prefix_calls: int = 44
    maximum_age_solver_steps: int = 33

    def validate(self):
        if (type(self.parent_mask) is not tuple or len(self.parent_mask) != 72
                or any(type(a) is not str or a not in ('C', 'D') for a in self.parent_mask)
                or type(self.prefix_calls) is not int or self.prefix_calls != 44
                or type(self.maximum_age_solver_steps) is not int
                or not 1 <= self.maximum_age_solver_steps <= 33
                or type(self.swap_calls) is not tuple or len(self.swap_calls) not in (0, 2)):
            raise ValueError('Fixed-mask immutable 72-call/step22/age contract differs')
        if self.parent_mask[:14] != ('D',)*14 or self.parent_mask[70:] != ('D', 'D'):
            raise ValueError('Fixed-mask initialization or post-reset full actions differ')
        if self.swap_calls:
            n, m = self.swap_calls
            if (type(n) is not int or type(m) is not int
                    or not self.prefix_calls < n < m <= 68 or (n-m) % 2
                    or self.parent_mask[n-1] != 'C' or self.parent_mask[m-1] != 'D'):
                raise ValueError('Swap needs ordered same-CFG C/D donors outside protected calls')
        result = self.action_mask()
        if (result[:self.prefix_calls] != self.parent_mask[:self.prefix_calls]
                or result[68:] != self.parent_mask[68:]
                or cfg_full_counts(result) != cfg_full_counts(self.parent_mask)):
            raise ValueError('Fixed-mask protected actions or per-CFG refresh quota differs')

    def action_mask(self):
        result = list(self.parent_mask)
        if self.swap_calls:
            n, m = self.swap_calls
            result[n-1], result[m-1] = 'D', 'C'
        return tuple(result)
