# WorldCache / OMR experiments

Private research workspace for improving the quality–time tradeoff of video world models. Initial priority: reproduce Cosmos-Predict2.5-2B Native and WorldCache, then test simple residual calibration. OMR is a conditional second direction.

## 实验文档与跨设备接续

从[实验总文档](EXPERIMENT_REPORT.md)开始：研究假设、协议、已完成结果、失败、预算和下一步均有证据链接。新设备或新对话先同步 Git，再按文档中的接续顺序核实运行状态；后续持续更新同一文件。

## Current status

2026-10-01: automated development VQA/source1f326b5 terminal: original8/42reference39candidate questions,all81 raw answers valid/token decode audited,7 comparable scenes6 tied/1misc lower,robot video-rejected retained,equal-scene delta-0.031746031746031744. [VQA results](research/28_W1_DEVELOPMENT_VQA_RESULTS.md)/[raw recomputed summary](reports/w1_vqa_r1_summary.json)/[terminal audit](reports/w1_vqa_r1_audit.json). Supervised60.966001s,all3 PIDs gone/lockfree/GPU1 released,used3.629295697609584/4GPUh,remaining0.370704302390416h. Prior scalar CAL8 mechanism/replay7accepted1reject/MUSIQ3higher4lower remain;no overall/physical/clean-speed/independent-confirmation gain. Next original8/42x3 input sensitivity controls (matched repeat/black/cyclic mismatch) cap300s frozen after method proxy/before control answers;runner implemented/local andLinux35 CPU checks/all24 real first-question inputs passed,not GPU run yet. [Control preparation](research/29_W1_VQA_INPUT_CONTROLS_PREPARATION.md). Small2B sparse10frame proxy not235B/standardJoint or physical correctness. No W2/generation expansion,human review,training,paid scoring or budget expansion. Assets official10 hashes complete;no further download needed.

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
