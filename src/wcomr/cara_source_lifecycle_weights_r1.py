"""Frozen current-input UniPC coefficients; no terminal sensitivity claim."""
import torch

from .cara_read_write_state_r1 import FunctionalUniPC, UniPCMemory, UNIPC_SHA256


def current_velocity_weights(scheduler):
    """Square the original step's response to one unit of current velocity.

The original corrector AND predictor execute at fixed previous history/sample.
All prior model predictions are zero in this scalar control; linearity makes
the coefficient depend on the fixed scheduler grid/order, not on a video.
This is a numerical scale, not a full-trajectory adjoint or LPIPS gradient.
"""
    if scheduler._step_index is not None or scheduler._begin_index is not None:
        raise ValueError('Untouched initialized original UniPC required')
    solver = FunctionalUniPC(scheduler)
    memory = UniPCMemory.capture(scheduler)
    # Preserve the original solver's B,C,... einsum convention even for this
    # one-element coefficient control.
    sample = torch.zeros(1, 1, 1, 1, 1, dtype=torch.float32)
    coefficients = []
    with torch.no_grad():
        for timestep in scheduler.timesteps:
            zero, next_memory = solver.step(memory, torch.zeros_like(sample), timestep, sample)
            unit, _ = solver.step(memory, torch.ones_like(sample), timestep, sample)
            coefficient = float((unit-zero).item())
            if not torch.isfinite(torch.tensor(coefficient)):
                raise ValueError('Nonfinite original current-velocity coefficient')
            coefficients.append(coefficient)
            sample, memory = zero, next_memory
    return dict(schema='CARA_SOURCE_LIFECYCLE_FROZEN_UNIPC_SCALE_R1',
        original_UniPC_source_sha256=UNIPC_SHA256, coefficients=coefficients,
        weights=[value*value for value in coefficients], actual_updates=len(coefficients),
        timesteps=[float(v) for v in scheduler.timesteps], sigmas=[float(v) for v in scheduler.sigmas],
        current_corrector_and_predictor_included=True, terminal_sensitivity=False,
        video_quality_evidence=False, GPU_submissions=0)
