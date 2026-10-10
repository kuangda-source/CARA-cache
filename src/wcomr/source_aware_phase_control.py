"""A fixed creation-phase prior on the unchanged source-aware C/P/D rule."""
import ast
from dataclasses import dataclass
import hashlib
import inspect
import textwrap

from . import source_aware_cpd_control as base
from .cfg_ra_joint_control import finite_nonnegative


@dataclass(frozen=True)
class CreationPhasePrior(base.PartialPrior):
    early_creation_floor: object = None
    late_creation_floor: object = None
    boundary: int = 25

    def __post_init__(self):
        super().__post_init__()
        if (type(self.boundary) is not int or self.boundary != 25
                or any(not finite_nonnegative(v) or v == 0
                       for v in (self.early_creation_floor,self.late_creation_floor))):
            raise ValueError('Bound positive creation floors and the fixed step25 boundary required')

    def creation_floor_at(self, step):
        if type(step) is not int or not 1 <= step <= 36:
            raise ValueError('Actual logical P creation step required')
        return self.early_creation_floor if step < self.boundary else self.late_creation_floor


class CreationPhaseCPDController(base.SourceAwareCPDController):
    def __init__(self, calibration, threshold, costs, partial_prior=None):
        if partial_prior is not None and not isinstance(partial_prior,CreationPhasePrior):
            raise ValueError('Explicit creation-phase prior or no P required')
        super().__init__(calibration,threshold,costs,partial_prior)


DERIVATION_PROOFS = {}


def _derive(name, before, after, count):
    original=textwrap.dedent(inspect.getsource(getattr(base.SourceAwareCPDController,name)))
    assert original.count(before)==count
    changed=original.replace(before,after)
    assert changed.count(after)==count
    inverse=changed.replace(after,before)
    assert inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
    namespace=dict(vars(base),CreationPhaseCPDController=CreationPhaseCPDController)
    exec(compile(changed,__file__+'#creation-phase-'+name,'exec'),namespace)
    DERIVATION_PROOFS[name]={'original_method_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'explicit_sites':count,'inverse_AST_and_original_bytes_equal':True}
    return namespace[name]


# Only P creation changes. C keeps the existing source floor and D remains the
# only reset. Replay uses this controller so phase decisions restore faithfully.
CreationPhaseCPDController._choice=_derive('_choice','p.creation_floor_proxy','p.creation_floor_at(step)',2)
CreationPhaseCPDController.restore=_derive('restore',
    'SourceAwareCPDController(self.calibration,self.threshold,self.costs,self.partial_prior)',
    'CreationPhaseCPDController(self.calibration,self.threshold,self.costs,self.partial_prior)',1)
