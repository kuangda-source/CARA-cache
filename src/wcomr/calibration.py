"""Strictly-past full-anchor residual calibration, independent of the generator."""
from dataclasses import dataclass
from typing import Hashable, Optional
import math
import torch


@dataclass
class Anchor:
    step: int
    probe: torch.Tensor
    residual: torch.Tensor


class ResidualCalibrator:
    def __init__(self, ridge=1e-6, clip=4.0, decay=0.9, min_energy=1e-12,
                 shrinkage=0.5):
        if not (ridge > 0 and clip > 0 and 0 <= decay <= 1 and
                min_energy > 0 and 0 <= shrinkage <= 1):
            raise ValueError("Invalid calibration parameters")
        if not all(math.isfinite(x) for x in (ridge, clip, decay, min_energy, shrinkage)):
            raise ValueError("Parameters must be finite")
        self.ridge, self.clip, self.decay = ridge, clip, decay
        self.min_energy, self.shrinkage = min_energy, shrinkage
        self.reset(None)

    def reset(self, context: Hashable):
        self.context = context
        self.anchors = []
        self.numerator = self.denominator = 0.0
        self.pairs = 0

    def _context(self, context):
        if context != self.context:
            self.reset(context)

    @staticmethod
    def _valid_pair(p, r):
        return (p.shape == r.shape and p.device == r.device and
                p.dtype == r.dtype and p.is_floating_point() and
                bool(torch.isfinite(p).all()) and bool(torch.isfinite(r).all()))

    @torch.no_grad()
    def observe_full(self, *, context, step, probe, residual):
        """Call only after an actual deployment full computation, never shadow truth."""
        self._context(context)
        if not self._valid_pair(probe, residual):
            self.reset(context)
            return False
        if self.anchors:
            a = self.anchors[-1]
            if step <= a.step:
                raise ValueError("Anchors must be strictly increasing")
            if (a.probe.shape != probe.shape or a.probe.device != probe.device
                    or a.probe.dtype != probe.dtype):
                self.reset(context)
            else:
                dp = probe.float() - a.probe.float()
                dr = residual.float() - a.residual.float()
                num, den = (dp * dr).mean().item(), dp.square().mean().item()
                if not (math.isfinite(num) and math.isfinite(den)):
                    self.reset(context)
                else:
                    self.numerator = self.decay * self.numerator + num
                    self.denominator = self.decay * self.denominator + den
                    self.pairs += 1
        self.anchors.append(Anchor(int(step), probe.detach().clone(), residual.detach().clone()))
        self.anchors = self.anchors[-2:]
        return True

    @torch.no_grad()
    def predict(self, *, context, step, probe, official, mode="scalar"):
        """No truth argument; returns official tensor unchanged on fallback."""
        self._context(context)
        if mode == "official":
            return official, "official"
        if mode not in ("scalar", "shrink"):
            raise ValueError(mode)
        if len(self.anchors) < 2:
            return official, "insufficient_anchors"
        a, b = self.anchors
        if step <= b.step:
            raise ValueError("Prediction can only use strictly past anchors")
        if (not self._valid_pair(probe, official) or probe.shape != b.probe.shape
                or probe.device != b.probe.device or probe.dtype != b.probe.dtype):
            self.reset(context)
            return official, "invalid_input_or_shape"
        if mode == "shrink":
            # First-order time extrapolation from true anchor steps; shrink increment.
            ratio = min((step - b.step) / (b.step - a.step), self.clip)
            prediction = b.residual + self.shrinkage * ratio * (b.residual - a.residual)
        else:
            if self.pairs == 0 or self.denominator <= self.min_energy:
                return official, "small_denominator"
            beta = self.numerator / (self.denominator + self.ridge)
            if not math.isfinite(beta):
                return official, "nonfinite_beta"
            beta = max(-self.clip, min(self.clip, beta))
            prediction = b.residual + beta * (probe - b.probe)
        if not bool(torch.isfinite(prediction).all()):
            return official, "nonfinite_prediction"
        return prediction, mode

    def receipt(self):
        return {"anchor_steps": [a.step for a in self.anchors],
                "pairs": self.pairs, "numerator": self.numerator,
                "denominator": self.denominator}


@torch.no_grad()
def score_shadow(prediction, truth):
    """Pure diagnostic scorer. Has no reference to calibrator/deployment state."""
    if prediction.shape != truth.shape:
        raise ValueError("Shadow shape mismatch")
    p, t = prediction.float(), truth.float()
    if not bool(torch.isfinite(p).all() and torch.isfinite(t).all()):
        return {"status": "NONFINITE", "relative_rmse": None}
    value = ((p - t).square().mean().sqrt() /
             t.square().mean().sqrt().clamp_min(1e-12)).item()
    return {"status": "OK", "relative_rmse": value}
