"""CPU-only algebra checks for CARA innovation-gain proposals.

Synthetic tensors only. No Cosmos inference, no scientific performance claim,
no remote access, and no GPU execution. Coordinate/layout adaptation is not
implemented here; deployment must use the registered model adapter.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np


def inner(x: np.ndarray, y: np.ndarray) -> float:
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Matching finite arrays required")
    return float(np.sum(x * y, dtype=np.float64))


def block_projection(x: np.ndarray, block: int = 2) -> np.ndarray:
    """Orthogonal projection onto disjoint block constants, last two axes.

    Incomplete boundary blocks use their actual sizes. No padding, bilinear
    interpolation, channel mixing, or temporal mixing is used.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim < 2 or type(block) is not int or block < 1:
        raise ValueError("At least 2 dimensions and a positive integer block")
    out = np.empty_like(x)
    height, width = x.shape[-2:]
    for row in range(0, height, block):
        for col in range(0, width, block):
            part = x[..., row:row + block, col:col + block]
            out[..., row:row + block, col:col + block] = part.mean(axis=(-2, -1), keepdims=True)
    return out


def box_quadratic(G: np.ndarray, b: np.ndarray,
                  lower: float = 0.0, upper: float = 1.0,
                  ridge: float = 0.0, prior: np.ndarray | None = None) -> np.ndarray:
    """Minimize k'Gk - 2b'k + ridge*||k-prior||² for one/two coefficients.

    Exhaustively considers interior, edges and corners of the small box.
    G and b can be accumulated guided-output response moments. This routine
    optimizes that quadratic surrogate, not the nonlinear model itself.
    """
    G, b = np.asarray(G, dtype=np.float64), np.asarray(b, dtype=np.float64)
    n = b.size
    if n not in (1, 2) or b.ndim != 1 or G.shape != (n, n):
        raise ValueError("One or two coefficients only")
    if not np.isfinite(G).all() or not np.isfinite(b).all():
        raise ValueError("Finite moments required")
    if not (np.isfinite(lower) and np.isfinite(upper) and lower < upper and ridge >= 0):
        raise ValueError("Invalid bounds or ridge")
    G = 0.5 * (G + G.T)
    if np.linalg.eigvalsh(G).min() < -1e-10 * max(1., np.linalg.norm(G, 2)):
        raise ValueError("G must be positive semidefinite")
    p = np.zeros(n) if prior is None else np.asarray(prior, dtype=np.float64)
    if p.shape != (n,) or not np.isfinite(p).all():
        raise ValueError("Invalid prior")
    A, rhs = G + ridge * np.eye(n), b + ridge * p
    candidates = []
    # -1 = free; 0 = lower bound; 1 = upper bound
    for status in itertools.product((-1, 0, 1), repeat=n):
        k = np.zeros(n)
        fixed = [i for i, s in enumerate(status) if s != -1]
        free = [i for i, s in enumerate(status) if s == -1]
        for i in fixed:
            k[i] = lower if status[i] == 0 else upper
        if free:
            rf = rhs[free].copy()
            if fixed:
                rf -= A[np.ix_(free, fixed)] @ k[fixed]
            k[free] = np.linalg.lstsq(A[np.ix_(free, free)], rf, rcond=None)[0]
        if np.all(k >= lower - 1e-10) and np.all(k <= upper + 1e-10):
            k = np.clip(k, lower, upper)
            val = float(k @ G @ k - 2 * b @ k + ridge * np.sum((k-p)**2))
            candidates.append((val, tuple(k), k.copy()))
    if not candidates:
        raise RuntimeError("No feasible candidate")
    return min(candidates, key=lambda x: (x[0], x[1]))[2]


def check_all() -> dict:
    rng = np.random.default_rng(20261027)
    shape = (3, 7, 9)
    p_old, p_anchor, p_now, d_old, d_anchor, d_now = [rng.normal(size=shape) for _ in range(6)]
    ratio = 1.4
    r_old, r_anchor, r_now = p_old+d_old, p_anchor+d_anchor, p_now+d_now
    p_pred = p_anchor+ratio*(p_anchor-p_old)
    d_pred = d_anchor+ratio*(d_anchor-d_old)
    full = r_anchor+ratio*(r_anchor-r_old)
    deep = p_now+d_pred
    nu = p_now-p_pred
    eps_d = d_pred-d_now
    identity_error = float(np.max(np.abs((deep-full)-nu)))
    assert identity_error < 1e-12

    k_ls = inner(r_now-full, nu)/inner(nu, nu)
    k_cov = 1-inner(eps_d, nu)/inner(nu, nu)
    assert abs(k_ls-k_cov) < 1e-12
    trial = 0.37
    assert np.allclose(full+trial*nu-r_now, eps_d+(trial-1)*nu, atol=1e-12)

    low = block_projection(nu)
    high = nu-low
    assert np.allclose(block_projection(low), low, atol=1e-12)
    orthogonality = abs(inner(low, high))
    assert orthogonality < 1e-11
    y = r_now-full
    BL, BH = inner(low, low), inner(high, high)
    kL, kH = inner(y, low)/BL, inner(y, high)/BH
    ks = (BL*kL+BH*kH)/(BL+BH)
    q_scalar = inner(full+ks*nu-r_now, full+ks*nu-r_now)
    q_band = inner(full+kL*low+kH*high-r_now, full+kL*low+kH*high-r_now)
    theoretical_gap = BL*BH/(BL+BH)*(kL-kH)**2
    assert abs((q_scalar-q_band)-theoretical_gap) < 1e-10

    # Scalar cannot improve at all, while box-constrained two-band gain can.
    target = np.array([1., -1.])
    innovation = np.array([1., 1.])
    scalar = box_quadratic(np.array([[2.]]), np.array([0.]))
    band = box_quadratic(np.eye(2), np.array([1., -1.]))
    q0 = inner(target, target)
    qs = inner(scalar[0]*innovation-target, scalar[0]*innovation-target)
    qb = inner(band-target, band-target)
    assert np.isclose(q0, 2.) and np.isclose(qs, 2.) and np.isclose(qb, 1.)

    # Shared post-conversion alpha preserves CFG mixture, not hidden nonlinearity.
    c0, u0, c1, u1 = [rng.normal(size=(5,)) for _ in range(4)]
    alpha, guidance = 0.5, 8.
    combined = guidance*((1-alpha)*c0+alpha*c1)-(guidance-1)*((1-alpha)*u0+alpha*u1)
    mixed = (1-alpha)*(guidance*c0-(guidance-1)*u0)+alpha*(guidance*c1-(guidance-1)*u1)
    assert np.allclose(combined, mixed)
    nonlinear_gap = (1.+0.5*2.)**2 - (0.5*1.**2+0.5*3.**2)
    assert not np.isclose(nonlinear_gap, 0.)

    return {
        'status': 'PASS_SYNTHETIC_ALGEBRA_ONLY',
        'Cosmos_inference_performed': False,
        'remote_or_GPU_operations': False,
        'identity_max_abs_error': identity_error,
        'gain_formula_error': abs(k_ls-k_cov),
        'projection_orthogonality_abs': orthogonality,
        'raw_two_band_gap_error': abs((q_scalar-q_band)-theoretical_gap),
        'counterexample': {'fixed_full_loss': q0, 'scalar_loss': qs, 'two_band_loss': qb,
                           'scalar_k': scalar.tolist(), 'band_k': band.tolist()},
        'nonlinear_conversion_interpolation_gap': nonlinear_gap,
    }

if __name__ == '__main__':
    result = check_all()
    path = Path(__file__).with_name('05_synthetic_checks.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
