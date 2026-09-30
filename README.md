# WorldCache / OMR experiments

Private research workspace for improving the quality–time tradeoff of video world models. Initial priority: reproduce Cosmos-Predict2.5-2B Native and WorldCache, then test simple residual calibration. OMR is a conditional second direction.

## Current status

2026-09-30: Core assets and the retained safety pipeline are ready. F1 r2 completed two Native samples, then stopped when the physics_001 generated video was rejected by the output guardrail. WorldCache has not run; there is no paired speed/quality result. Charged cost: 0.473298 / 4 GPUh. Terminal receipts are in `reports/f1_smoke_r2_*.json`.

The [long-term plan](plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_OMR_20260929.md) and [first-batch instructions](plans/CODEX_FIRST_BATCH_WorldCache_OMR_20260929.md) are now v1.1: preserve the current WorldCache comparison, add QuantWM-inspired downstream diagnostics and a bounded compatible Wan5B/LongLive-Plug baseline. Combinations and training remain conditional. No new GPU job was launched by this plan update.

## Reproduce CPU checks

```sh
python3 -m venv .venv
.venv/bin/pip install -e . pytest
.venv/bin/python scripts/bootstrap_upstream.py
.venv/bin/python -m pytest -q
```

The integration tests extract the pinned upstream functions and execute a synthetic network. They do not establish full-model equivalence or performance. Upstream is downloaded to ignored `vendor/`; weights, videos, environments and credentials are never committed.

## Research records

- `plans/`: maintained plans based on user-supplied originals; revisions preserved in Git.
- `research/02_CURRENT_STATE.md`: evidence and unresolved dependencies.
- `research/09_NEXT_ACTIONS.md`: ordered execution scope.
- `memory/handoffs/LATEST.md`: continuation state.
- `manifests/upstream.json`: pinned WorldCache revision and cache-module hash.
- `src/wcomr/`: scalar calibration and shrinkage prototypes, with a version-checked in-memory hook.
- `reports/`: small receipts only; large artifacts stay outside Git.

Every meaningful code/config/result change is committed and pushed to this private repository. No autonomous training, full benchmark, or paid evaluation is part of the initial smoke batch.

F1 execution protocol and evidence limits: `research/04_F1_PROTOCOL.md`. `scripts/supervise_f1.py` has run real Native generation; the paired comparison remains incomplete.
