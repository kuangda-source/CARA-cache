# Sparse refresh P probe R1 — S1 gate-stop, settled

**Outcome: NO_GO_S1_GATE.** S1 completed on the original GPU session, both frozen gate conditions failed, and the job exited normally without S2. The planned b/c x O1/O3/N1/N3 endpoint comparison was not executed. LPIPS was skipped because no complete8-video S2 collection exists. No endpoint-quality or CFG-branch endpoint-closure conclusion is available.

Run `cara-sparse-refresh-probe-r1-20261105`, launch `4fbe2d7463614c2e9fc40cca8ab34bf1`, GPU `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`, source `0eff7bbd981895b073e6fb0f95ca0a617bbf1572`. The frozen preregistration and masks were unchanged. Original launch SHA256 `ddcbcf72262217d2cb30af33e902156e79368378c76472bc226d3f2599598956`.

## S1 measurements

O1/seed0, original R18C prefix through28; P29 uses true-DD26 differences (age3). Each local mode used one warmup and three timed evaluations. Times below are timed medians; errors are guided MSE against the same-state D. P_sync includes residual synchronization and the same-age synthetic uncond A anchor.

| Step29 mode | Seconds | Cost / D | Guided MSE |
|---|---:|---:|---:|
| D | 6.831324787 | 1.000000000 | 0.000000000000 |
| C | 0.014951536 | 0.002188673 | 0.097472282589 |
| P_sync | 3.424755150 | 0.501331038 | 0.038316036535 |
| P14 | 3.449450293 | 0.504946024 | 0.147131301811 |
| P20 | 4.895669258 | 0.716650051 | 0.145908583359 |

| Frozen S1 gate | Measured | Requirement | Result |
|---|---:|---:|---|
| Median P_sync / D | 0.501331038468 | <=0.5 | FAIL |
| Amplitude kappa | 0.636225873259 | <0.45 | FAIL |

At30, guided C MSE versus the same-state D30 teacher: no-P control **0.133816001944**, sync **0.073570473352**, raw **1.651608597818**. Raw and sync P29 outputs/solver states were exactly equal. Frozen drift lambda=0.289331295339; kappa uses the registered amplitude formula with no clipping/refit. Sync has lower local next-C error than raw and no-P, while the registered kappa threshold still fails. These are local errors, not LPIPS.

P_k is **locally closed under the preregistered rule**: k20 MSE/C MSE=1.496923838>0.5. Relative timing deviations from k/28 were 0.989205% (k14) and 0.331007% (k20), both below10%; the error criterion closes it.

## Scope and decision

S1 produced20 local evaluations plus next-step comparisons and zero video frames. Collection status is S1_GATE_STOP; all8 S2 rows are NOT_REACHED. Go requires the dual S1 gate and an endpoint b or c criterion, so this run is no-go at S1. Neither endpoint criterion can be evaluated. The S1 raw/sync comparison does not supply a raw endpoint LPIPS comparison. No post-hoc tuning, rerun, new GPU job or metric job was performed.

## Release and actual settlement

Original wall interval: **2026-11-06T01:30:58.276043+08:00 to 2026-11-06T01:37:14.356878+08:00**, 376.080820087s. Guardian terminal; original guardian/CLI/supervisor/runner ended, container exited0 with OOMKilled=false, GPU released, Default mode restored and both locks free. Existing lifecycle validation accepted financial/resource closure separately from scientific endpoint acceptance.

Reservation **seq105 /1.05 GPUh** is now SETTLED by the single **seq106** event. Actual **0.10446689446870651 GPUh**; unused headroom **0.945533105531 GPUh**. Cumulative used **232.60499957255590 GPUh**; total remaining reserved **16.5 GPUh**, solely the unchanged old16.5 responsibility. Other ledger jobs were unchanged by this settlement. The settlement receipt was mirrored to this probe's original stage for accurate read-only status; this was not a second ledger transaction. No confirm10 settlement/path/container was touched. All50GiB/90C/4GiB gates stayed unchanged. No routines or retries were created. Blockers: none.

Evidence: [S1 raw measurements](s1.json), [collection](collection.json), [terminal status](terminal_status.json), [original terminal capture](terminal_capture.json), [unique settlement](settlement.json), [settled status](settled_status.json), and [machine analysis/provenance](analysis.json).
