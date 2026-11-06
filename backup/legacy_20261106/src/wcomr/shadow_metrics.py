"""W1-D read-only tensor scoring; callers must supply same-state shadow truth.

No generator, cache, calibrator, RNG or refresh policy is referenced here.
This module does not itself establish that caller tensors share a latent state.
"""
import math
import torch


@torch.no_grad()
def tensor_error(prediction, truth, *, group_axes=None):
    """Score fp32 errors; zero-energy references yield undefined relative metrics.

Explicit group_axes maps names to tensor axes. Returns per-index diagnostics,
not saved tensors. No guessed latent/residual layout or implicit broadcasting.
"""
    if prediction.shape != truth.shape or prediction.numel() == 0:
        raise ValueError('Nonempty, exactly matching shapes required')
    if prediction.device != truth.device:
        raise ValueError('Diagnostic tensors must share a device')
    axes = group_axes or {}
    if any(not isinstance(axis, int) or not 0 <= axis < truth.ndim for axis in axes.values()):
        raise ValueError('Explicit group axis is outside tensor dimensions')
    p, t = prediction.detach().float(), truth.detach().float()
    if not bool(torch.isfinite(p).all() and torch.isfinite(t).all()):
        return {'status': 'NONFINITE_INPUT'}
    error = (p - t).square()
    mse = error.mean().item()
    energy = t.square().mean().item()
    predicted_energy = p.square().mean().item()
    dot = (p * t).mean().item()
    if not all(math.isfinite(x) for x in [mse, energy, predicted_energy, dot]):
        return {'status': 'NONFINITE_REDUCTION'}
    relative = mse / energy if energy > 0 else None
    cosine = dot / math.sqrt(energy * predicted_energy) if energy > 0 and predicted_energy > 0 else None
    out = {'status': 'OK', 'mse': mse, 'reference_mean_square': energy,
           'relative_mse': relative, 'relative_rmse': math.sqrt(relative) if relative is not None else None,
           'direction_cosine': max(-1.0, min(1.0, cosine)) if cosine is not None else None,
           'groups': {}}
    for name, axis in axes.items():
        reductions = tuple(i for i in range(t.ndim) if i != axis)
        e = error.mean(dim=reductions) if reductions else error
        ref = t.square().mean(dim=reductions) if reductions else t.square()
        out['groups'][name] = {'axis': axis, 'mse': e.tolist(),
                              'relative_mse': [a / b if b > 0 else None for a, b in zip(e.tolist(), ref.tolist())]}
    return out


@torch.no_grad()
def score_shadow_pair(*, residual_prediction, residual_truth, velocity_prediction,
                      velocity_truth, residual_axes=None, velocity_axes=None):
    """Keep residual and velocity measurements distinct, not proxy labels."""
    return {'residual': tensor_error(residual_prediction, residual_truth, group_axes=residual_axes),
            'velocity': tensor_error(velocity_prediction, velocity_truth, group_axes=velocity_axes),
            'evidence_scope': 'TENSOR_DIAGNOSTIC_ONLY; same-state identity must be established by caller'}
