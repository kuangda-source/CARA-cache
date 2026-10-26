"""CPU guided-output moments, prompt-held-out fitting and actual replay audit.

Only actual adapter outputs may populate production moments. Surrogate loss
is explicitly separate from replayed loss; this module cannot claim quality.
"""
import itertools
import math

import numpy as np


def box_quadratic(G, b, ridge=0., prior=None):
    G, b = np.asarray(G, dtype=float), np.asarray(b, dtype=float)
    n = b.size
    p = np.zeros(n) if prior is None else np.asarray(prior, dtype=float)
    if (n not in (1, 2) or b.shape != (n,) or G.shape != (n, n) or p.shape != (n,)
            or not all(np.isfinite(v).all() for v in (G, b, p))
            or not math.isfinite(ridge) or ridge < 0):
        raise ValueError('Finite one/two-parameter moments and ridge required')
    G = (G+G.T)/2
    if np.linalg.eigvalsh(G).min() < -1e-10*max(1., np.linalg.norm(G, 2)):
        raise ValueError('Gram must be positive semidefinite')
    A, rhs = G+ridge*np.eye(n), b+ridge*p
    candidates = []
    for status in itertools.product((-1, 0, 1), repeat=n):
        k = np.array([max(s, 0) for s in status], dtype=float)
        free, fixed = [i for i,s in enumerate(status) if s == -1], [i for i,s in enumerate(status) if s != -1]
        if free:
            r = rhs[free] - A[np.ix_(free, fixed)]@k[fixed]
            k[free] = np.linalg.lstsq(A[np.ix_(free, free)], r, rcond=None)[0]
        if np.all(k >= -1e-10) and np.all(k <= 1+1e-10):
            k = k.clip(0, 1)
            candidates.append((float(k@G@k-2*b@k+ridge*np.sum((k-p)**2)), tuple(k)))
    return np.asarray(min(candidates)[1])


def output_moments(teacher, f00, f10, f01, f11, midpoint):
    arrays = [np.asarray(v, dtype=np.float64) for v in (teacher, f00, f10, f01, f11, midpoint)]
    if not arrays[0].size or any(v.shape != arrays[0].shape or not np.isfinite(v).all() for v in arrays):
        raise ValueError('Finite same-shape actual guided tensors required')
    teacher, f00, f10, f01, f11, midpoint = arrays
    e = f00-teacher
    u, v = f10-f00, f01-f00
    w = f11-f10-f01+f00
    basis = (u, v, w)
    G = np.array([[np.mean(a*b) for b in basis] for a in basis])
    b = -np.array([np.mean(e*a) for a in basis])
    predicted = f00+.5*u+.5*v+.25*w
    return dict(G=G.tolist(), b=b.tolist(), c=float(np.mean(e*e)),
                midpoint_bilinear_error_MSE=float(np.mean((midpoint-predicted)**2)),
                midpoint_actual_error_MSE=float(np.mean((midpoint-teacher)**2)),
                midpoint_affine_error_MSE=float(np.mean((midpoint-(f00+.5*u+.5*v))**2)),
                interaction_MSE=float(np.mean(w*w)),
                baseline_FULL_MSE=float(np.mean(e*e)),
                baseline_DEEP_MSE=float(np.mean((f11-teacher)**2)))


def aggregate(rows):
    if not rows:
        raise ValueError('Training rows required')
    groups = {}
    for r in rows:
        groups.setdefault(r['prompt'], []).append(r['moments'])
    def avg(key):
        return np.mean([np.mean([np.asarray(m[key], dtype=float) for m in group], axis=0)
                        for group in groups.values()], axis=0)
    return avg('G'), avg('b'), float(avg('c'))


def loss(k, G, b, c, ridge=0., prior=0.):
    x, y = k
    z = np.array([x, y, x*y])
    return float(c+z@G@z-2*b@z+ridge*((x-prior)**2+(y-prior)**2))


def fit(rows):
    """Always retain four-corner interaction; actual Phi validation is required.

Scalar is the exact minimum of the diagonal quartic surrogate on [0,1].
Band uses deterministic bounded multistart coordinate descent, not a claim
of a global nonlinear oracle. Each coordinate update is a convex quadratic.
The only regularization is the preregistered .05*trace(G[:2,:2])/2.
"""
    G, b, c = aggregate(rows)
    d = np.array([1., 1., 0.]); w = np.array([0., 0., 1.])
    coeffs = np.array([4*G[2,2], 6*(d@G@w), 2*(d@G@d-2*b[2]), -2*(b@d)])
    coeffs = np.trim_zeros(coeffs, 'f')
    roots = np.roots(coeffs) if len(coeffs) > 1 else []
    scalar_points = [0., 1.] + [float(z.real) for z in roots if abs(z.imag) < 1e-9 and 0 <= z.real <= 1]
    scalar = min(scalar_points, key=lambda k:(loss((k,k),G,b,c),k))
    ridge = .05*float(np.trace(G[:2,:2]))/2
    starts = list(itertools.product(np.linspace(0,1,5), repeat=2))+[(scalar,scalar)]
    candidates = []
    for start in starts:
        k = np.array(start, dtype=float)
        for _ in range(200):
            old = k.copy()
            for index in (0,1):
                other = k[1-index]
                direction = np.array([1.,0.,other]) if index == 0 else np.array([0.,1.,other])
                fixed = np.array([0.,other,0.]) if index == 0 else np.array([other,0.,0.])
                a = float(direction@G@direction)+ridge
                r = float(direction@(b-G@fixed))+ridge*scalar
                k[index] = np.clip(r/a, 0, 1) if a > 0 else (1. if r > 0 else scalar)
            if np.max(np.abs(k-old)) < 1e-12:
                break
        candidates.append((loss(k,G,b,c,ridge,scalar), tuple(k)))
    band = np.array(min(candidates)[1])
    affine_scalar_direction = np.ones(2)
    affine_scalar = box_quadratic([[affine_scalar_direction@G[:2,:2]@affine_scalar_direction]],
                                  [b[:2].sum()])[0]
    affine_band = box_quadratic(G[:2,:2], b[:2], ridge, np.full(2, affine_scalar))
    return dict(IG_SCALAR=[scalar,scalar], IG_BAND=band.tolist(), G=G.tolist(), b=b.tolist(),
                constant=c, ridge=ridge, lambda_reg=.05, prior_scalar=scalar,
                bilinear_surrogate_only=True, actual_Phi_required=True,
                affine_diagnostic=dict(IG_SCALAR=[float(affine_scalar)]*2, IG_BAND=affine_band.tolist()),
                surrogate_loss={name:loss(k,G,b,c) for name,k in [('IG_SCALAR',(scalar,scalar)),('IG_BAND',band)]})


def calibration(rows, expected_prompts, expected_steps):
    """Freeze coefficients using training prompts only. No replay is implied."""
    prompts, steps = tuple(expected_prompts), tuple(expected_steps)
    keys = [(r['prompt'],r['step']) for r in rows]
    if (len(prompts) != 2 or len(set(prompts)) != 2 or len(set(steps)) != len(steps)
            or len(keys) != len(set(keys)) or set(keys) != set(itertools.product(prompts,steps))):
        raise ValueError('Exact two-prompt registered state denominator required')
    folds = []
    for held in prompts:
        trained = [r for r in rows if r['prompt'] != held]
        folds.append(dict(held_out_prompt=held, training_prompts=[p for p in prompts if p != held],
                          coefficients=fit(trained)))
    return dict(status='COEFFICIENTS_PROPOSED_PENDING_ACTUAL_ADAPTER_REPLAY', folds=folds,
                final=fit(rows), expected_prompts=list(prompts), expected_steps=list(steps),
                deployable=False, scientific_result=False)
