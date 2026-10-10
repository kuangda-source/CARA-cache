"""Expose the original interval verifier required by the unchanged full fixture.

Execution, controller and all existing verifier callables remain R1 objects.
Only the compatibility export missed by the first wrapper is added.
"""
from .source_aware_current_birth_sampling_r1 import (
    METHODS, STRATEGIES, CURRENT_BIRTH_RULE, CurrentBirthDeployment,
    CurrentBirthSamplingOwner, verify_batch, derive, run_batch, audit_vectors,
    DERIVATION_PROOFS)
from .source_aware_working_epoch_sampling_r1 import valid_P_interval
