"""Complete-video Alex objective with one-frame activation storage.

The fitting boundary is the unencoded float video: original (1+decode)/2,
clamp to RGB [0,1], then Alex's [-1,1] normalization. Formal encoded-video
Fidelity-v2 acceptance remains separate. First-order VJPs are supported; this
module does not load metric weights, decode a VAE or authorize GPU work.
"""
import math

import torch
from torch.autograd.function import once_differentiable


def float_rgb(decoded):
    """Original standard-mode normalization before quantization/guardrails."""
    return ((1.0+decoded)/2).clamp(0, 1).float()


class _StreamingAlex(torch.autograd.Function):
    @staticmethod
    def forward(ctx, candidate, reference, objective):
        value, gradient = objective.value_and_vjp(candidate, reference)
        ctx.save_for_backward(gradient)
        # Fidelity averages the per-frame FP32 scores in Python float64.
        return torch.tensor(value, dtype=torch.float64, device=candidate.device)

    @staticmethod
    @once_differentiable
    def backward(ctx, weight):
        (gradient,) = ctx.saved_tensors
        return gradient*weight, None, None


class StreamingAlexTerminal:
    """Frame-equal LPIPS scalar and gradient with frozen metric parameters.

One candidate frame graph is active at a time. The full decoded video and its
cotangent still occupy memory; this does not solve VAE activation storage.
Callers must bind real Alex weights/version, model decode, original 93-frame
geometry, reference identity and actual resource bounds in their own card.
"""
    def __init__(self, alex, *, geometry=(432, 768), frames=93):
        if (not isinstance(alex, torch.nn.Module) or frames != 93
                or not isinstance(geometry, tuple) or len(geometry) != 2
                or any(type(n) is not int or n <= 0 for n in geometry)):
            raise ValueError('Frozen module, complete93 denominator and explicit geometry required')
        self.alex, self.geometry, self.frames = alex, geometry, frames
        self._ready()

    def _ready(self):
        if any(m.training for m in self.alex.modules()) or any(p.requires_grad for p in self.alex.parameters()):
            raise ValueError('Frozen eval Alex metric required')

    def value_and_vjp(self, candidate, reference):
        self._ready()
        shape = (1, 3, self.frames, *self.geometry)
        if (torch.is_inference_mode_enabled() or not isinstance(candidate, torch.Tensor)
                or not isinstance(reference, torch.Tensor) or candidate.shape != shape or reference.shape != shape
                or not candidate.is_floating_point() or not reference.is_floating_point()
                or candidate.device != reference.device or reference.requires_grad
                or not bool(torch.isfinite(candidate).all() and torch.isfinite(reference).all())):
            raise ValueError('Complete same-geometry float videos and constant Native reference required')
        gradient = torch.empty_like(candidate)
        values = []
        for index in range(self.frames):
            with torch.enable_grad():
                frame = candidate[:, :, index].detach().requires_grad_()
                native = reference[:, :, index].detach()
                x, n = float_rgb(frame), float_rgb(native)
                score = self.alex(x*2-1, n*2-1).reshape(-1).mean()
                if not bool(torch.isfinite(score)):
                    raise ValueError('Nonfinite complete-video Alex objective')
                weight = torch.autograd.grad(score/self.frames, frame)[0]
            if not bool(torch.isfinite(weight).all()):
                raise ValueError('Nonfinite Alex input VJP')
            gradient[:, :, index] = weight
            values.append(float(score.detach()))
        value = sum(values)/self.frames
        if not math.isfinite(value):
            raise ValueError('Nonfinite frame-equal Alex reduction')
        return value, gradient

    def loss(self, candidate, reference):
        return _StreamingAlex.apply(candidate, reference, self)
