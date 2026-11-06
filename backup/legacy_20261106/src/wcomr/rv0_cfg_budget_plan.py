"""Immutable two-branch refresh-position plans; standard-library structural contracts."""
from dataclasses import dataclass
import hashlib

MODES=('BASE','CFG0','CFG1','PAIRED')


def full_counts(mask):
    return tuple(sum(x=='D' for x in mask[slot::2]) for slot in (0,1))


def mask_sha256(mask):
    return hashlib.sha256(''.join(mask).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class CFGBudgetPlan:
    mode:str
    parent_mask:tuple
    prefix_calls:int=44
    maximum_age_solver_steps:int=32

    @property
    def swaps(self):
        return {'BASE':(),'CFG0':((45,47),),'CFG1':((46,48),),'PAIRED':((45,47),(46,48))}[self.mode]

    def action_mask(self):
        result=list(self.parent_mask)
        for early,late in self.swaps:result[early-1],result[late-1]='D','C'
        return tuple(result)

    def validate(self):
        p=self.parent_mask
        if (self.mode not in MODES or type(p) is not tuple or len(p)!=72
                or any(type(x) is not str or x not in ('C','D') for x in p)
                or type(self.prefix_calls) is not int or self.prefix_calls!=44
                or type(self.maximum_age_solver_steps) is not int or self.maximum_age_solver_steps!=32):
            raise ValueError('Immutable registered two-CFG position plan required')
        if (p[:14]!=('D',)*14 or p[44:48]!=('C','C','D','D')
                or p[70:]!=('D','D') or full_counts(p)!=(18,17)):
            raise ValueError('Frozen parent initialization/current-donor/tail/CFG quotas differ')
        result=self.action_mask()
        changes=tuple(i+1 for i,(a,b) in enumerate(zip(p,result)) if a!=b)
        expected=tuple(sorted(x for pair in self.swaps for x in pair))
        if (changes!=expected or result[:44]!=p[:44] or result[48:]!=p[48:]
                or full_counts(result)!=full_counts(p)):
            raise ValueError('Only registered within-CFG positions may change; quotas must remain')
        return self
