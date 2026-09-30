# WorldCache / OMR experiments

Private research workspace for improving the quality–time tradeoff of video world models. Initial priority: reproduce Cosmos-Predict2.5-2B Native and WorldCache, then test simple residual calibration. OMR is a conditional second direction.

## 实验文档与跨设备接续

从[实验总文档](EXPERIMENT_REPORT.md)开始：研究假设、协议、已完成结果、失败、预算和下一步均有证据链接。新设备或新对话先同步 Git，再按文档中的接续顺序核实运行状态；后续持续更新同一文件。

## Current status

2026-10-01: fixed scalar replay source31a797d terminal (all8 trajectories pass,7 accepted/robot video-rejected,0fallback), followed by automated MUSIQ sourcea51e3e4 terminal (original8 denominator,7 complete93-frame pairs,3 higher/4 lower,equal-scene normalized delta+0.004254295). [Replay results](research/24_W1_FIXED_REPLAY_RESULTS.md), [imaging results](research/25_W1_IMAGING_RESULTS.md), [audited/recomputed scores](reports/w1_imaging_r1_summary.json). All GPU jobs released;settled3.612360697/4GPUh,remaining0.387639303h. No consistent imaging/overall/semantic/physical quality gain,clean speed or independent confirmation;no W2 expansion. CPU acquisition r1 direct Hub metadata failed; r2 SSH-proxy download reached750MiB but ended timeout124; all PIDs gone/cache retained. CPU mirror r3 source202e21d ended with connection IncompleteRead exit1/1153.880144s; all3 PIDs gone/lockfree/hashes and GPU budget unchanged,partial2890MiB retained. New r4 same cache/revision/official hashes/3600s CPU cap prepared. [R3 audit](reports/w1_judge_assets_r3_audit.json). VQA GPU runner/900s supervisor/terminal raw summary implemented: [preparation](research/27_W1_VQA_RUNNER_PREPARATION.md), local25 and Linux25 CPU checks pass, all15 real video inputs and42 original question files pass CPU preflight. Actual runner refuses partial assets before model load/forward. No GPU VQA score or model weights load yet; complete assets, deployment and fresh admission still required;no human evaluation or GPU budget extension.

Prior terminal run: Core assets and the retained safety pipeline are ready. F1 r2 completed two Native samples, then stopped when the physics_001 generated video was rejected by the output guardrail. WorldCache has not run; there is no paired speed/quality result. Charged cost: 0.473298 / 4 GPUh. Terminal receipts are in `reports/f1_smoke_r2_*.json`.

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

F1 execution protocol and evidence limits: `research/04_F1_PROTOCOL.md`. `scripts/supervise_f1.py` completed both r3 arms and W1-P0; see terminal receipts rather than historical RUNNING notes.
