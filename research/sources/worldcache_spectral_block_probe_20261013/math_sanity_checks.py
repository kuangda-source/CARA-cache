"""CPU-only algebra checks; not Cosmos/WorldCache experiments or latency benchmarks.
Run: python math_sanity_checks.py
Requires NumPy. No model weights, CUDA, internet, or user repository access.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


def energy(x: np.ndarray) -> float:
    return float(np.vdot(x, x).real)


def softmax(x: np.ndarray) -> np.ndarray:
    v = np.exp(x - x.max(axis=-1, keepdims=True))
    return v / v.sum(axis=-1, keepdims=True)


def run() -> dict:
    rng = np.random.default_rng(20261013)
    x = rng.normal(size=(16, 20))
    fx = np.fft.fft2(x, norm="ortho")
    parseval_error = abs(energy(x) - energy(fx)) / energy(x)
    assert parseval_error < 1e-12

    # Haar on disjoint 2x2 spatial cells: an exact orthogonal transform.
    a, b = x[::2, ::2], x[::2, 1::2]
    c, d = x[1::2, ::2], x[1::2, 1::2]
    bands = [(a+b+c+d)/2, (a-b+c-d)/2,
             (a+b-c-d)/2, (a-b-c+d)/2]
    haar_error = abs(sum(energy(z) for z in bands)-energy(x))/energy(x)
    assert haar_error < 1e-12

    # A cyclic spatial shift preserves magnitude, not phase or the signal itself.
    y = np.roll(x, 3, axis=1)
    fy = np.fft.fft2(y, norm="ortho")
    magnitude_distance = np.linalg.norm(np.abs(fx)-np.abs(fy))
    complex_distance = np.linalg.norm(fx-fy)
    assert magnitude_distance < 1e-10 and complex_distance > 1

    # With unchanged input, two different filters still induce a distance.
    freq_y, freq_x = np.meshgrid(np.fft.fftfreq(16), np.fft.fftfreq(20), indexing="ij")
    radius = freq_y**2 + freq_x**2
    old_filter, new_filter = np.exp(-5*radius), np.exp(-10*radius)
    filter_drift = np.linalg.norm((new_filter-old_filter)*fx)
    assert filter_drift > 0

    # CFG and a shared linear transform commute; cross-phase term is required.
    ec, eu = rng.normal(size=x.shape), rng.normal(size=x.shape)
    fc, fu = np.fft.fft2(ec, norm="ortho"), np.fft.fft2(eu, norm="ortho")
    direct = energy(8*ec-7*eu)
    expanded = 64*energy(fc) + 49*energy(fu) - 112*float(np.vdot(fc, fu).real)
    cfg_error = abs(direct-expanded)/direct
    assert cfg_error < 1e-12

    # Active queries with all fresh K/V equal selected rows of full attention.
    n, dk, dv = 12, 5, 7
    q, k, v = rng.normal(size=(n,dk)), rng.normal(size=(n,dk)), rng.normal(size=(n,dv))
    active = np.array([0, 3, 7, 10])
    full = softmax(q @ k.T / np.sqrt(dk)) @ v
    fresh = softmax(q[active] @ k.T / np.sqrt(dk)) @ v
    fresh_row_error = np.max(np.abs(fresh-full[active]))
    assert fresh_row_error < 1e-12

    # Same active queries, but stale inactive K/V: verify a conservative bound.
    inactive = np.ones(n, dtype=bool)
    inactive[active] = False
    delta_k, delta_v = np.zeros_like(k), np.zeros_like(v)
    delta_k[inactive] = 0.05*rng.normal(size=(int(inactive.sum()),dk))
    delta_v[inactive] = 0.05*rng.normal(size=(int(inactive.sum()),dv))
    p_stale = softmax(q[active] @ (k+delta_k).T / np.sqrt(dk))
    stale = p_stale @ (v+delta_v)
    observed = np.linalg.norm(stale-fresh, "fro")
    bound = (
        np.linalg.norm(q[active], 2) * np.linalg.norm(delta_k, "fro") * np.linalg.norm(v, 2)
        / (2*np.sqrt(dk))
        + np.linalg.norm(p_stale, 2) * np.linalg.norm(delta_v, "fro")
    )
    assert observed <= bound + 1e-12

    # Residual reuse keeps current identity path; stale output replacement does not.
    h_old, h_now = rng.normal(size=(6,4)), rng.normal(size=(6,4))
    r_constant = rng.normal(size=(6,4))
    desired = h_now + r_constant
    residual_reuse = h_now + r_constant
    stale_output_reuse = h_old + r_constant
    assert np.array_equal(desired, residual_reuse)
    overwrite_error = np.linalg.norm(stale_output_reuse-desired)
    assert overwrite_error > 0

    return {
        "scope": "Synthetic CPU algebra only; NOT real-model efficacy or speed evidence",
        "parseval_relative_error": parseval_error,
        "haar_relative_error": haar_error,
        "shift_magnitude_spectrum_distance": float(magnitude_distance),
        "shift_complex_spectrum_distance": float(complex_distance),
        "distance_from_changing_filter_only": float(filter_drift),
        "cfg_quadratic_relative_error": cfg_error,
        "fresh_kv_active_attention_max_abs_error": float(fresh_row_error),
        "stale_kv_attention_error": float(observed),
        "stale_kv_conservative_bound": float(bound),
        "stale_output_overwrite_error": float(overwrite_error),
        "checks": "PASS"
    }

if __name__ == "__main__":
    result = run()
    path = Path(__file__).with_name("math_sanity_results.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
