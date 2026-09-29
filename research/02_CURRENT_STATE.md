# Current state — 2026-09-29

## Scientific status

No GPU-generated sample or measured quality/time result from this project yet. Continue WorldCache F0/F1, conditional on runtime import and asset readiness. OMR resource availability is not established; the project page release section still says Coming soon.

## Implemented and checked

- Pinned official WorldCache commit and cache-module SHA256.
- Pure residual calibrator: only earlier true full-compute anchors; request/model/CFG isolation; finite and shape fallback; bounded scalar coefficient; actual-anchor-gap shrinkage.
- Narrow source hook preserves the official decision/warp path and injects only the approximate residual. CPU toy tests include reset, branch isolation, and all-full behavior.
- Stateless shadow scorer exists. A real-model shadow forward/trace runner is NOT implemented; therefore no fixed-schedule shadow claim.
- 17 CPU tests passed on macOS Python 3.9 / torch 2.8.0. This is not Linux GPU execution evidence.

## Resources / dependencies

- Two-card server: 2 A6000 49140 MiB, driver 570.133.20. Observed VRAM 336/24 MiB and no compute apps. Must recheck immediately before launch.
- Data disk approximately 682 GiB free; root only 13 GiB free. New files and any downloads must use data disk.
- Existing Cosmos checkout has torch 2.7.1+cu128 in its venv and cached Predict2.5-2B post-trained checkpoint, tokenizer, Reason1-7B. Preserve shared checkout, environment and caches.
- Existing checkout is a locally modified research version; it cannot be assumed to be the official baseline.
- Four-card SSH reaches authentication but current key is rejected. Pending user-provided login method. FRP is already running and intermittently reconnects; do not launch a duplicate shared tunnel.
- Pinned WorldCache tree lacks model source directories referenced by its inference configuration. Need a separately pinned, documented source completion shared across both baseline paths. Do not silently substitute the locally modified model.
- Guardrail1 cache snapshot currently contains only README; inspect complete safety dependencies before inference. No safety/access bypass.

## First-batch scope

User explicitly authorized the two/four A6000 resources. Start with F0 and four-scene, one-seed Native/official-WC technical smoke. One expensive job at a time, at most 4 GPU hours including failure/loading. Recheck UUID/VRAM/processes and retain PID, log, outputs and exit status. F2/W1 GPU scope follows measured F1 cost. No training or paid evaluation.
