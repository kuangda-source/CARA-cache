# WorldCache / OMR experiments

Private research workspace for improving the quality–time tradeoff of video world models. Initial priority: reproduce Cosmos-Predict2.5-2B Native and WorldCache, then test simple residual calibration. OMR is a conditional second direction.

## 实验文档与跨设备接续

从[实验总文档](EXPERIMENT_REPORT.md)开始：研究假设、协议、已完成结果、失败、预算和下一步均有证据链接。新设备或新对话先同步 Git，再按文档中的接续顺序核实运行状态；后续持续更新同一文件。

## Current status

2026-10-01: source72c9e24 input controls terminal/all126 strict valid: matched-repeat0/42 changes, blank14/42, cyclic14/42; all PIDs absent/lockfree/GPU released, raw tokens/input tensors/model/source hashes audited and locally recomputed. [Control results](research/30_W1_VQA_INPUT_CONTROLS_RESULTS.md). This demonstrates repeat stability and partial content sensitivity, not physical validity or method acceptance. Prior VQA6tied/1misc lower/−3.174603pp, MUSIQ3higher4lower, robot rejection and CAL8 mechanism-only remain; no quality–time gain. Used3.6512467238638138/4GPUh, remaining1255.511794s, no in-flight job. [Next window cost/decision](research/31_W1_NEXT_WINDOW_COST_AND_DECISION.md): proposed new4GPUh for original8×twoarms×3 clean timing repetitions, not authorized/launched, or CPU resource preparation. No W2/OMR pivot, human review, paid scoring, training, or automatic budget extension. No further judge downloads needed. [Full timing runner CPU preparation](research/32_W1_CLEAN_TIMING_CPU_PREPARATION.md): original8/twoarms/3repeats plus2warmups frozen and implemented,48 local/Linux CPU checks and actual validate-only/unchanged4h refusal pass; no CUDA/model generation, new GPU window still pending.

Prior terminal run: Core assets and the retained safety pipeline are ready. F1 r2 completed two Native samples, then stopped when the physics_001 generated video was rejected by the output guardrail. WorldCache has not run; there is no paired speed/quality result. Charged cost: 0.473298 / 4 GPUh. Terminal receipts are in `reports/f1_smoke_r2_*.json`.

The [long-term plan](plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_OMR_20260929.md) and [first-batch instructions](plans/CODEX_FIRST_BATCH_WorldCache_OMR_20260929.md) are now v1.1: preserve the current WorldCache comparison, add QuantWM-inspired downstream diagnostics and a bounded compatible Wan5B/LongLive-Plug baseline. Combinations and training remain conditional. No new GPU job was launched by this plan update.

[L0 resource audit](research/33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md): existingWan5B all11 official file hashes verified; both600tensor LoRA headers match300targets each,16 CPU checks pass; fulladapter payload/realmerge/environment/GPU remain pending. OMR public artifacts stillComing soon; no route pivot or GPU cost. Historical r1/source68afc3e live snapshot has been superseded by the terminal audit below; no full-pair/merge/GPU readiness claim.

[L0 CFG actual payload / CPU fusion preparation](research/34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md): L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

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
