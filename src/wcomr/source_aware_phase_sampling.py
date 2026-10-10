"""Fixed creation-phase controller in the accepted ordinary sampling path.

The original dynamic module is unchanged. The only deployment substitution is
the controller constructor; all physical execution and restore code is reused.
"""
import hashlib
import inspect
import types

from . import source_aware_partial_sampling as base
from .source_aware_phase_control import CreationPhaseCPDController

METHODS = base.METHODS
verify_batch = base.verify_batch
audit_vectors = base.audit_vectors


def bind_globals(original, replacements):
    if original.__closure__:
        raise ValueError('Only closure-free entry functions can be rebound')
    for name in replacements:
        if name not in original.__globals__:
            raise ValueError('Missing explicit original global binding: '+name)
    result = types.FunctionType(original.__code__,
        {**original.__globals__, **replacements}, original.__name__, original.__defaults__)
    result.__kwdefaults__ = original.__kwdefaults__
    if result.__code__ is not original.__code__:
        raise ValueError('Original bytecode changed outside global binding')
    return result


class CreationPhaseSamplingOwner(base.DynamicSamplingOwner):
    pass


CreationPhaseSamplingOwner.__init__ = bind_globals(base.DynamicSamplingOwner.__init__,
    {'SourceAwareCPDController': CreationPhaseCPDController})
run_batch = bind_globals(base.run_batch,
    {'DynamicSamplingOwner': CreationPhaseSamplingOwner})

DERIVATION_PROOFS = {
    'constructor': {'original_source_sha256': hashlib.sha256(
        inspect.getsource(base.DynamicSamplingOwner.__init__).encode()).hexdigest(),
        'only_global_binding': 'SourceAwareCPDController', 'original_bytecode_identical': True},
    'batch': {'original_source_sha256': hashlib.sha256(
        inspect.getsource(base.run_batch).encode()).hexdigest(),
        'only_global_binding': 'DynamicSamplingOwner', 'original_bytecode_identical': True},
    'original_module_globals_unchanged': True,
}
