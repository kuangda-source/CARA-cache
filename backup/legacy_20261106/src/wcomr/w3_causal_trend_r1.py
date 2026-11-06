"""Isolated W3 T1/T2 interface: causal scalar histories and coherent CAD risk.

No generator, model forward, online teacher, frequency transform or source
mutation. Labels live in a separate type. Existing H1 protection/support domain
remains authoritative. Outputs use g^2 absolute MSE units exactly once.
"""
from dataclasses import dataclass
import math
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Observation:
    prompt: str
    seed: int
    step: int
    state_id: str
    sigma: Optional[float]
    source_kind: Optional[str]
    source_id: Optional[str]
    source_age: Optional[int]
    root_floor: float
    delta_c: Optional[float]
    delta_u: Optional[float]
    local_proxy: Optional[float]
    gain: Optional[float]
    protected: bool
    calibration_supported: bool

    def validate(self):
        if (not self.prompt or not self.state_id or type(self.seed) is not int
                or type(self.step) is not int or not 1 <= self.step <= 36
                or self.source_kind not in (None, 'D', 'P')
                or self.source_age is not None and (type(self.source_age) is not int or self.source_age < 0)
                or self.source_kind is not None and (not self.source_id or self.source_age is None)):
            raise ValueError('Explicit pre-action context/source/step required')
        values = (self.sigma, self.delta_c, self.delta_u, self.local_proxy, self.gain, self.root_floor)
        if any(v is not None and (not math.isfinite(v) or v < 0) for v in values):
            raise ValueError('Finite nonnegative observed statistics required')
        if (self.delta_c is None) != (self.delta_u is None):
            raise ValueError('Both current paid branches or an explicit missing pair required')
        if self.calibration_supported and (self.protected or self.gain is None or self.local_proxy is None):
            raise ValueError('Protected/missing calibration cannot become optimizer-supported')
        if self.calibration_supported and (self.source_kind is None or not 1 <= self.source_age <= 6):
            raise ValueError('Original age1-6 support must remain authoritative')


@dataclass(frozen=True)
class FeatureRow:
    observation: Observation
    model: str
    names: tuple
    values: tuple
    prefix_steps: tuple
    actual_sigma_available: bool


class CausalHistory:
    def __init__(self, prompt, seed, *, window=4):
        if window not in (4, 8, 16): raise ValueError('Registered scalar window4/8/16 required')
        self.prompt, self.seed, self.window = prompt, seed, window
        self.rows = []

    def push(self, row):
        if not isinstance(row, Observation): raise TypeError('Teacher-free typed observation required')
        row.validate()
        if (row.prompt, row.seed) != (self.prompt, self.seed) or row.step != len(self.rows) + 1:
            raise ValueError('No cross-prompt/seed history, gaps or future insertion')
        if self.rows and row.sigma is not None and self.rows[-1].sigma is not None and row.sigma > self.rows[-1].sigma:
            raise ValueError('Actual denoising sigma must be ordered; timestep is not sigma')
        self.rows.append(row)
        return {m: self.features(m) for m in ('T1', 'T2')}

    def features(self, model):
        if model not in ('T1', 'T2') or not self.rows: raise ValueError('Current T1/T2 prefix required')
        o = self.rows[-1]
        names = ('step_fraction', 'log1p_sigma', 'sigma_available', 'source_is_P', 'source_age',
                 'root_floor', 'delta_c', 'delta_u', 'paid_pair_available', 'local_proxy',
                 'gain', 'calibration_supported', 'source_reset')
        reset = not self.rows[:-1] or self.rows[-2].source_id != o.source_id
        values = (o.step / 36, math.log1p(o.sigma) if o.sigma is not None else 0., float(o.sigma is not None),
                  float(o.source_kind == 'P'), float(o.source_age or 0), o.root_floor,
                  o.delta_c or 0., o.delta_u or 0., float(o.delta_c is not None),
                  o.local_proxy or 0., o.gain or 0., float(o.calibration_supported), float(reset))
        selected = self.rows[-self.window:]
        if model == 'T2':
            extra_names = []; extra = []
            for branch in ('delta_c', 'delta_u'):
                paid = [r for r in selected if getattr(r, branch) is not None]
                a = np.array([getattr(r, branch) for r in paid], dtype=float)
                ema = 0.
                for value in a: ema = .5 * float(value) + .5 * ema
                # Slopes use actual noise coordinates, never an invented sigma.
                timed = [r for r in paid if r.sigma is not None]
                slope = 0.; span = 0.
                if len(timed) >= 2:
                    t = np.array([math.log1p(r.sigma) for r in timed]); v = np.array([getattr(r, branch) for r in timed])
                    centered = t - t.mean(); span = float(t.max() - t.min())
                    if float(centered @ centered) > 1e-20:
                        slope = float(centered @ (v - v.mean()) / (centered @ centered))
                extra_names.extend(branch + '_' + name for name in ('mean', 'std', 'ema', 'prefix_count', 'sigma_slope', 'sigma_span'))
                extra.extend((float(a.mean()) if len(a) else 0., float(a.std()) if len(a) else 0., ema,
                              len(a) / self.window, slope, span))
            extra_names.extend(('window_fraction', 'window_source_resets'))
            offset = len(self.rows) - len(selected)
            extra.extend((len(selected) / self.window,
                          sum(offset+i == 0 or r.source_id != self.rows[offset+i-1].source_id
                              for i, r in enumerate(selected)) / self.window))
            names += tuple(extra_names); values += tuple(extra)
        if any(not math.isfinite(float(v)) for v in values): raise ValueError('Nonfinite causal features')
        return FeatureRow(o, model, names, tuple(float(v) for v in values),
                          tuple(r.step for r in selected), o.sigma is not None)


@dataclass(frozen=True)
class SameStateLabel:
    prompt: str
    seed: int
    step: int
    state_id: str
    q_C: float
    q_A: float
    provenance: str

    def target(self, feature):
        o = feature.observation
        if (self.prompt, self.seed, self.step, self.state_id) != (o.prompt, o.seed, o.step, o.state_id):
            raise ValueError('Same actual state and prefix required, not another trajectory')
        if (not o.calibration_supported or not feature.actual_sigma_available or o.gain is None
                or any(not math.isfinite(v) or v < 0 for v in (self.q_C, self.q_A))
                or self.provenance not in ('SYNTHETIC_CPU_INTERFACE', 'REAL_SAME_STATE_POST_RF')):
            raise ValueError('Supported state, actual sigma, finite absolute same-state labels required')
        # Predict r_A and r_C-r_A directly. r already includes g^2 once.
        return np.array([o.gain**2 * self.q_A, o.gain**2 * (self.q_C - self.q_A)], dtype=float)


def coherent_scores(predicted, observation, *, costs, lam):
    """Project to nonnegative coherent risks, then recompute all CAD scores."""
    observation.validate()
    if set(costs) != {'C', 'A', 'D'} or any(not math.isfinite(v) or v <= 0 for v in costs.values()) or not math.isfinite(lam) or lam <= 0:
        raise ValueError('Exact positive CAD price/lambda scope required')
    if observation.protected or not observation.calibration_supported:
        return {'action': 'D', 'category': 'PROTECTED_OR_ORIGINAL_SUPPORT_FALLBACK',
                'scores': None, 'repair': False, 'teacher_used_online': False}
    raw = np.asarray(predicted, dtype=float)
    if raw.shape != (2,) or not np.isfinite(raw).all(): raise ValueError('Two finite coherent risk predictions required')
    r_A = max(0., float(raw[0])); r_C = max(0., float(raw[0] + raw[1]))
    risk = {'C': r_C, 'A': r_A, 'D': 0.}
    scores = {a: costs[a] + lam * risk[a] for a in ('C', 'A', 'D')}
    action = min(scores, key=lambda a: (scores[a], {'C': 0, 'A': 1, 'D': 2}[a]))
    return {'action': action, 'category': 'COHERENT_CAD_OPTIMIZER', 'scores': scores,
            'risk': risk, 'effective_delta_CA': r_C-r_A,
            'margin_CA': lam*(r_C-r_A)-(costs['A']-costs['C']),
            'margin_AD': lam*r_A-(costs['D']-costs['A']),
            'repair': bool(raw[0] < 0 or raw[0] + raw[1] < 0),
            'target_unit': 'GAIN_SQUARED_ABSOLUTE_MSE_NOT_MULTIPLIED_AGAIN', 'teacher_used_online': False}


class RidgeRisk:
    def __init__(self, *, model, ridge=1.):
        if model not in ('T1', 'T2') or not math.isfinite(ridge) or ridge <= 0: raise ValueError('Fixed T1/T2 ridge required')
        self.model, self.ridge = model, ridge
        self.mean = self.std = self.weights = None

    def fit(self, rows, *, forbidden_prompts=()):
        if not rows: raise ValueError('Training rows required')
        if any(f.model != self.model or f.observation.prompt in forbidden_prompts for f, l in rows):
            raise ValueError('Held prompt or unmatched feature model in training')
        names = rows[0][0].names
        if any(f.names != names for f, _ in rows): raise ValueError('Feature schema differs')
        x = np.array([f.values for f, _ in rows]); y = np.array([l.target(f) for f, l in rows])
        if not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('Finite training features/targets required')
        self.mean = x.mean(0); self.std = x.std(0); self.std[self.std < 1e-12] = 1.
        z = np.column_stack((np.ones(len(x)), (x-self.mean)/self.std))
        penalty = np.eye(z.shape[1])*self.ridge; penalty[0,0] = 0.
        # Small feature matrices use explicit, auditable normal-equation sums.
        # Finite weights/predictions are required regardless of the backend.
        gram = np.einsum('ni,nj->ij', z, z, optimize=False)
        rhs = np.einsum('ni,nj->ij', z, y, optimize=False)
        self.weights = np.linalg.solve(gram + penalty, rhs)
        if not np.isfinite(self.weights).all(): raise ValueError('Nonfinite fitted risk model')
        self.names = names; self.training_prompts = tuple(sorted({f.observation.prompt for f, _ in rows}))
        self.training_provenance = tuple(sorted({l.provenance for _, l in rows}))
        return self

    def predict(self, feature):
        if self.weights is None or feature.model != self.model or feature.names != self.names:
            raise ValueError('Frozen fitted model and matching teacher-free feature schema required')
        if not feature.actual_sigma_available:
            raise ValueError('Do not deploy missing/timestep-substituted sigma features')
        vector = np.r_[1., (np.asarray(feature.values)-self.mean)/self.std]
        if not np.isfinite(vector).all(): raise ValueError('Nonfinite online feature vector')
        prediction = np.einsum('i,ij->j', vector, self.weights, optimize=False)
        if not np.isfinite(prediction).all(): raise ValueError('Nonfinite predicted risk')
        return prediction


def local_regret(decision, feature, label, *, costs, lam):
    if decision['category'] != 'COHERENT_CAD_OPTIMIZER': return None
    target = label.target(feature); risks = {'A': target[0], 'C': target.sum(), 'D': 0.}
    true_scores = {a: costs[a]+lam*risks[a] for a in ('C','A','D')}
    return float(true_scores[decision['action']] - min(true_scores.values()))
