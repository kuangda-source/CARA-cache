"""Preserve zero-step text refusals without weakening a fixed action mask.

The accepted numerical executors and the original failed N07 stage are
unchanged. This request-boundary adapter only repairs the unconditional
full-mask check after the ordinary text guardrail has refused a request.
"""
import ast
from functools import lru_cache
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

ORIGINAL_FIXED_SOURCE_SHA256 = 'ae3765032744f2a8527a7b37e1283d52fb6f1407007a1c290968f4b0b8726e4b'
VERSION = 'FROZEN_ZERO_STEP_TEXT_REFUSAL_BOUNDARY_R2'


def requires_complete_mask(result, actual):
    if result.get('status') != 'TEXT_REJECTED':
        if result.get('status') not in ('COMPLETE', 'VIDEO_REJECTED'):
            raise ValueError('Unknown fixed-mask request outcome')
        return True
    if (result.get('solver_steps') != 0 or result.get('guided_pairs') != 0
            or actual or result.get('source_history')
            or result.get('actions') or result.get('A_history')
            or result.get('guided') or result.get('final_latent') is not None
            or result.get('video_path') is not None
            or any(result.get(k) != 0 for k in
                   ('in_timing_guided_copies', 'in_timing_hashes', 'research_checkpoints'))):
        raise ValueError('A text refusal must retain zero actual computation and no output')
    return False


@lru_cache(maxsize=1)
def compile_fixed_boundary():
    from . import source_phase_fixed_mask_r1 as fixed
    path = Path(fixed.__file__)
    if hashlib.sha256(path.read_bytes()).hexdigest() != ORIGINAL_FIXED_SOURCE_SHA256:
        raise ValueError('The original fixed-mask executor changed')
    source = dedent(inspect.getsource(fixed.execute_fixed))
    before = 'if actual != list(replay_plan):'
    after = 'if _requires_complete_mask(result, actual) and actual != list(replay_plan):'
    if source.count(before) != 1:
        raise ValueError('Exactly one original post-request full-mask condition required')
    changed = source.replace(before, after)
    restored = changed.replace(after, before)
    if restored != source or ast.dump(ast.parse(restored)) != ast.dump(ast.parse(source)):
        raise ValueError('An undeclared request or numerical operation changed')
    namespace = {**vars(fixed), '_requires_complete_mask': requires_complete_mask}
    exec(compile(changed, str(path) + '#zero-step-refusal-boundary-r2', 'exec'), namespace)
    return namespace['execute_fixed'], dict(version=VERSION,
        original_fixed_source_sha256=ORIGINAL_FIXED_SOURCE_SHA256,
        post_request_condition_replacements=1, inverse_bytes_and_AST_equal=True,
        original_numerical_source_modified=False, guardrails_enabled=True,
        complete_and_video_rejected_masks_still_checked=True,
        refused_requests_replaced_or_retried=False)


def execute(inference, sample, method, **kwargs):
    from . import clean_speed20_r1 as clean
    from . import frozen_shared_execution_r1 as original
    from . import source_phase_fixed_mask_r1 as fixed
    from .simple26d_r1 import METHODS
    if method not in METHODS:
        return original.execute(inference, sample, method, **kwargs)
    adapted, proof = compile_fixed_boundary()
    with clean.patched(fixed, 'execute_fixed', adapted):
        result = original.execute(inference, sample, method, **kwargs)
    result['guardrail_request_boundary'] = dict(proof,
        actual_zero_step_text_refusal=result['status'] == 'TEXT_REJECTED')
    return result
