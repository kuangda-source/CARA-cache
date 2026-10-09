"""Read-only guided-W1 operations on actual post-denoise branch velocities.

This core does not recover velocities from scalar PaidProbe statistics, collect
teachers, mark a supplied dense tensor as proven, or blend hidden features.
Collection must separately bind actual same-state outputs and true D anchors.
"""
import math
import torch

from .cfg_guided_w1_grid import GRID


def _pair(value):
    if (not isinstance(value, tuple) or len(value) != 2
            or any(not isinstance(v, torch.Tensor) or v.ndim != 5
                   or v.dtype != torch.float32 or not v.numel() for v in value)):
        raise ValueError('Conditional/negative-prompt FP32 BCTHW post-denoise tuple required')
    c, u = value
    if c.shape != u.shape or c.device != u.device:
        raise ValueError('Same actual output coordinates required')
    if not all(bool(torch.isfinite(v).all()) for v in value):
        raise ValueError('Finite post-denoise branch velocities required')
    return value


def _aligned(*pairs):
    parsed = [_pair(p) for p in pairs]
    first = parsed[0][0]
    if any(v.shape != first.shape or v.device != first.device for p in parsed for v in p):
        raise ValueError('All candidate/teacher outputs must use the same coordinates')
    return parsed


@torch.no_grad()
def shared_output_fusion(original, proposed, alpha):
    """Online readout: one frozen alpha for both branches, with no teacher input.

Exact endpoints preserve the original objects and values. Intermediate output
fusion is deliberately after final_layer/unpatchify/denoise condition handling.
"""
    original, proposed = _aligned(original, proposed)
    if type(alpha) not in (int, float) or not math.isfinite(alpha) or alpha not in GRID:
        raise ValueError('Only the preregistered shared 0/.5/1 grid is supported')
    if alpha == 0:
        return original
    if alpha == 1:
        return proposed
    result = tuple(a + alpha * (b - a) for a, b in zip(original, proposed))
    _pair(result)
    return result


@torch.no_grad()
def guided_velocity_moments(*, scene, state, original, proposed, dense):
    """Reduce direct CFG vectors, retaining branch diagnostics and source limits."""
    if type(scene) is not str or not scene or type(state) is not str or not state:
        raise ValueError('Explicit scene and state identities required')
    original, proposed, dense = _aligned(original, proposed, dense)
    ec, eu = (a - t for a, t in zip(original, dense))
    qc, qu = (b - a for a, b in zip(original, proposed))
    eg, qg = 8 * ec - 7 * eu, 8 * qc - 7 * qu
    # FP32 vectors are the actual output coordinate. Accumulate their reduced
    # products in FP64 to avoid large-sum/cancellation artifacts in CAL moments.
    square = lambda v: v.double().square().mean().item()
    dot = (eg.double() * qg.double()).mean().item()
    values = [square(eg), dot, square(qg)]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite guided moments')
    return {'scene': scene, 'state': state, 'base_guided_MSE': values[0],
            'guided_error_update_mean_dot': values[1], 'guided_update_mean_square': values[2],
            'diagnostics': {'original_branch_MSE': [square(ec), square(eu)],
                            'proposed_branch_MSE': [square(ec + qc), square(eu + qu)],
                            'velocity_shape': list(eg.shape), 'actual_CFG_coefficients': [8, -7],
                            'reduction_dtype': 'torch.float64',
                            'supplied_tensors_are_same_state_teacher_proven': False}}


@torch.no_grad()
def unit_increment_residual(*, current_probe, anchor_probe, anchor_residual):
    """Beta=1 prewarp control; caller must prove the anchor is strictly past D.

Unlike a fitted coefficient, this tests whether subtracting the shallow identity
component already explains the apparent deep-increment signal. No anchor or
calibrator mutation, fitting, state observation, warp or head is performed here.
"""
    values = (current_probe, anchor_probe, anchor_residual)
    if any(not isinstance(v, torch.Tensor) or not v.is_floating_point() or not v.numel() for v in values):
        raise ValueError('Floating probe/residual tensors required')
    first = values[0]
    if (any(v.shape != first.shape or v.device != first.device or v.dtype != first.dtype for v in values)
            or not all(bool(torch.isfinite(v).all()) for v in values)):
        raise ValueError('Finite same-coordinate probe/residual tensors required')
    result = anchor_residual + (current_probe - anchor_probe)
    if not bool(torch.isfinite(result).all()):
        raise ValueError('Nonfinite beta1 residual')
    return result
