# Principle fit: zero-GPU calibration of layout-error models against measured LPIPS

Repo not modified. Inputs were read via MCP get_file_contents into `src/`.

## Dataset (`dataset.csv`)
- **346 (layout, input) points** of per-input LPIPS-Alex vs the same-seed Native, covering 75 distinct layout variants (mask × alpha × light-C). WC_T006 and Natives are excluded.
- By source: sensitivity8 single-C 112, plus confirm4 F17/F19 8; C1 82; endpoint7/B36 28; CAL35 12 (light-C / F16 only, F19_A1 deduped); CAL66 40; DEV128 64.
- By batch: two-card H 242; A6000 104. A6000 is not bit-comparable to H, so each batch:input pair has its own intercept.
- Single-C points define s(t), so they are not used for evaluation. **Evaluation set: 234 multi-step points, 61 layout variants, 28 batch:input groups.**
- Indicator columns: `light_C`, `A_variant`, per-step `alpha`, `batch`, `T_pred`.

## Models
Per-step error is e_t = s(t)·drift(t)·[A: (1−κ_A·α)]·[light C: β_L]·extra, where drift(t) = ΣΔv since the last D. Each model links to measured LPIPS by log LPIPS = b_group + γ·log E. All models have ≤4 parameters.

Columns below are leave-one-layout-out (LOLO) Spearman in three forms (pooled, within-input, paired within-input differences), then leave-one-input-out (LOIO) within-input and paired. LOLO paired uses groups with ≥3 layouts (2916 pairs).

| model | extra term | LOLO pooled | LOLO within | LOLO paired | LOIO within | LOIO paired |
|---|---|---|---|---|---|---|
| M0 additive | – | .986 | .631 | .938 | .940 | .957 |
| RSS (L2 sum) | – | .989 | .846 | .941 | .933 | .952 |
| M1 compounding | κ_run^(age−1), κ_run=.81 | .989 | .869 | .955 | .930 | .959 |
| M2 contraction | λ^(#nonD after), λ=1.06 | .988 | .770 | .938 | .937 | .942 |
| M3 curvature (A) | c=3.9 | .984 | .666 | .924 | .890 | .941 |
| M4 soft-max | q=3.2 | .989 | .891 | .936 | .929 | .942 |
| **M5f σ-tilt** | σ_t^g, g=2.72 | **.992** | **.914** | **.955** | .933 | .958 |
| M6 single-C LPIPS weights | – | .972 | .369 | .893 | .569 | .928 |
| G0 (no s, drift=age) | – | .917 | .144 | .497 | .207 | .597 |
| S0 (s only, drift=1) | – | .959 | .800 | .677 | .829 | .691 |
| nD only / T only | – | .75 / .74 | – | −.18 | – | – |

Every s·drift model passes the held-out gate of ≥0.6. The baselines that drop s or drift fail it.

### Subsets that actually discriminate (LOLO paired Spearman / sign accuracy)
| model | CAL66 (180 pairs) | DEV128 (96) | competitive ≤1.25× best (117) | \|ΔLPIPS\|<.02 (778) |
|---|---|---|---|---|
| M5f | .83 / .88 | .21 / .89 | .55 / .74 | .66 / .73 |
| M4 | .82 / .92 | −.13 / .85 | .41 / .71 | .59 / .70 |
| M1 | .81 / .92 | −.28 / .79 | .35 / .72 | .61 / .77 |
| M0 | .65 / .86 | −.54 / .45 | .27 / .69 | .48 / .75 |

The high headline numbers come from gross structure: catastrophic early C runs in C1 versus everything else. Among near-optimal layouts, every model is weak. M5f is best there, at only about 0.55–0.66 Spearman.

## Parameters and physical reading
- **M5f:** κ_A = 0.26 (A removes about 26% of the cache drift error at α=1), g_σ = 2.72, γ = 0.32. A deviation injected at step t counts as ∝σ_t^2.7·s·drift. Errors made while noise is high reshape structure and propagate. Late-tail errors are mostly re-absorbed or sit below the perceptual floor. This fits the CAL66/DEV128 finding that SHARED25 beats S25_A (keep D21, drop D33).
- **M1:** κ_run = 0.81 < 1. Errors do **not** compound within a C/A run; they saturate.
- **M2:** λ ≈ 1.06, i.e. essentially no contraction.
- **M3:** A curvature adds nothing.
- **M6:** single-C LPIPS used directly as weights is worse than latent-MSE-based s. Single-C LPIPS is a poor additive unit.
- **Essential ingredients:** content-specific s(t), together with drift from the last D. Dropping either loses about 0.3–0.45 paired Spearman.

## misc_9699 (N3): F17 − F19_A1 excess
Measured F17 − F19_A1 is +0.071 on N3, against −0.001…+0.019 on the other 7 inputs. Predicted differences below are in-sample, applying the model ratio to measured F19.
- M0: about +0.010…+0.019 on every input (N3 +0.017).
- M1: about +0.005…+0.011 (N3 +0.009).
- M5f: about −0.001 on every input; it treats F17 and F19 as equal.

**No model explains N3.** Its s/Δv profile does not make it special. The excess is about 4–8× what any model predicts, so it is a non-additive, content-specific effect outside all candidate principles. M1/M0 get the size of F17 − F19 right for the other inputs. M5f under-predicts it, which means the tail is not entirely free.

Candidate explanations not testable with the current data:
- light-C failing on this content (N3 light-C was never measured);
- A extrapolation failing where the direction of Δv turns, which norms cannot see;
- an LPIPS threshold effect on high-frequency content.

## Generated layouts (DP over D/A placement, all C light, α=1, mean features; `gen_results_*.json`)
| nD | M5f optimum | nA | T (s) | ≤132.98? | M5f pred ratio vs F17 | M1 pred ratio vs F17 |
|---|---|---|---|---|---|---|
| 16 | DDDDDDDDDDDDADADAADAAAAAAAAAAAAAAACD | 19 | 132.62 | yes | 0.91 | 0.88 |
| 17 | DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD | 11 | 132.63 | yes | 0.82 | 0.80 |
| 19 | DDDDDDDDDDDDDDDDADADAAAAAAAAAAAAAAAD | 17 | 151.35 | no | 0.66 | 0.60 (M1 mask differs slightly) |
| 22 | DDDDDDDDDDDDDDDDDDDDADAAAAAAAAAAAAAD | 14 | 169.23 | no | 0.42 | 0.41 |

- M5f and M1 give the identical 17D optimum. Per-input optima differ only in 1–2 positions.
- M0 prefers more spread-out D (e.g. `DDDDDDDDDDADADADAADAADCAADCCCCAACCCD`) and predicts only about 5% gain over F17.
- Shared pattern: D at steps 1–13, alternating D around 14–20, no D after 20, then a long A run. The difference from F19/F17 is moving D from steps 21–33 to steps 9–13.
- **Extrapolation warning:**
  - No measured layout has an A run longer than 5 or zero D in 21–35.
  - κ_A was fitted mostly on short A runs.
  - The σ-tilt makes the tail look nearly free, yet the F17 vs F19 evidence says it costs about 0.01.
  - Treat the predicted 18–20% gain as a hypothesis, not a result.

## Verdict
- The principle "error = Σ s(t)·drift since last D, down-weighted by noise level, with A taking out about a quarter" is well supported for coarse ranking: held-out paired Spearman ≈0.95, with large margins over the nD/T baselines.
- The data **cannot discriminate** M1 (saturating runs), M4 (soft-max) and M5f (σ-tilt) at the frontier. They differ by ≤0.02 overall and are only ~0.4–0.66 on competitive pairs.
- N3 is unexplained.

## Minimal GPU measurement that would discriminate
About 16 runs, no new tooling:
1. **N3 decomposition** on N3 plus N1 as a control (8 runs):
   - F19_A1_LIGHT_C (isolates the light-C effect);
   - F17 mask with original C;
   - F19 mask with A at 22,23,25,26 (isolates late A);
   - F17 with D27 restored.
   This tells whether light-C, late A or tail-D loss produces the +0.071.
2. **Frontier test** on O1, O3, N1, N3 (8 runs):
   - the generated 17D layout (M5f = M1 optimum);
   - a "tail-D" variant with the same nD, moving D13 → D27.
   M5f predicts the generated layout wins by about 15–20%. M0 predicts about 5%. If tail D matters (as F17 vs F19 hints), the variant wins. This is the M5f-vs-M0/M1 tail-weight test, and it also validates long A runs.
