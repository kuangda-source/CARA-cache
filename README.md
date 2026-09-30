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

Latest actual L0 acquisition: L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。

[L0 range recovery and interface gate](research/35_L0_RANGE_RECOVERY_AND_INTERFACE_GATE.md): L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。 Real scheduler CPU checks pass; stock guidance1 still computes both branches. No model/task/GPU acceptance.

Actual bounded-range r3: L0 CPU range-r3/sourcebd8253d已唯一实际启动，3PIDs2498231/2498232/2498233都/proc verified live，CPU获取锁持有、CUDA空/source协议hash一致/账本未变。官方精确206/64KiB旧prefix边界preflight通过；已完成2个16MiB chunk、重试0次，已fsync字节589299712（562MiB），另有在途文件长度602931200（575MiB）。未完整1289824400/整SHA验收或两模型融合。复用原530MiB，不改r2失败或扩大GPU预算。

[Native T2V conditional branch CPU preparation](research/36_L0_NATIVE_CONDITIONAL_CPU_PREPARATION.md): 已实现仅T2V的scope adaptation，guide1直接conditional、guide!=1保留原CFG运算，finally恢复，不改源文件/i2v。Local/Linux7检查通过；完整native T2V body+真实UniPC/CPU替身在4/50步guide5输入/timestep/输出bit equal，guide1分别4/50cond/0negative。不是实际模型/GPU parity；保留BF16guide1的stock抵消差异，不称guide1 OFF/ON bit invariant。

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

最新资源终态：[r3最后range失败与r4恢复](research/37_L0_RANGE_R3_TERMINAL_AND_R4_RECOVERY.md)。L0 range-r3/sourcebd8253d已exit1/1216.976277秒终态；最后range三次URLError，已提交43个16MiB chunk，保留1277165568字节（1218MiB），仍缺12658832字节。CFG4文件/两few-step JSON官方digest PASS，few-step模型MISSING；原3PIDs退出/CPU锁释放/source与协议一致/账本不变，完整审计后仅关闭本任务owned r3转发。下一新唯一r4从保留prefix续传，同官方revision/16MiB/3600秒上限；未新GPU、未完整few-step hash/真实融合。

## 最新全部adapter CPU验收

L0 range-r4/source7c0f2ec唯一实际续传成功，exit0/31.271029秒，最后12658832字节一次range完成/0retry。全部7文件官方digest与实际1200张量CPU有限性、300×2目标/rank/alpha及825基座header匹配通过；原3PIDs2502124/2502125/2502126退出/CPU锁释放/source与协议一致/账本不变，审计后仅owned临时转发关闭。真实融合尚未提交，实际模型/GPU parity仍未通过；新4GPUh仍待用户重要预算决定。

最新真实CPU融合：真实Wan5B两臂CPU fusion-r1/sourcec69e492已唯一启动。supervisor2502473/timeout2502474/runner2502475实际/proc live，独立fusion锁持有、CUDA空/source固定与账本未变。准入时MemAvailable59360669696字节（55.3GiB）、磁盘720206147584字节（670.7GiB）；3600秒CPU cap，当前完整输入hash阶段/未创建模型目录，尚未完成merge或产物验收。 [运行卡](research/38_L0_FULL_ADAPTER_PAYLOAD_AND_REAL_CPU_FUSION.md)。

最新完整原生源码/环境准备：官方固定Wan运行源码60文件已独立部署/全Gitblob与SHA匹配；旧参考import观察超时、PID后续消失，结果UNKNOWN。参考环境满足官方requirements版本元数据；新隔离env/full native import尚未通过。带PID/阶段持久回执的CPU runtime probe已准备/仅语法检查，未执行。fusion-r1仍同handles/3600秒CPU cap，CFG-only已有413tensor/首shard验收，尚未全两臂验收。 [准备与边界](research/39_L0_NATIVE_SOURCE_AND_ENVIRONMENT_PREPARATION.md)。

最新CPU融合进度：fusion-r1/sourcec69e492同3PIDs实际live，CFG-only一臂已全部825张量/3分片完成融合、独立公式、有限性、未目标字节不变与序列化重读验收；完整两臂及末尾原输入hash尚未完成。CPU锁持有/source一致/账本未变，维持3600秒cap，不重复启动。

最新两臂/环境门：真实CPU两臂均已825/3分片内部验收；完整posthash/终态与独立fresh artifact审计仍待。新独立env已创建，实际offline缓存解析缺Torch2.4.1+cu121，未装包。独立CPU终态审计程序已准备/语法检查，待原3PIDs退出/锁释放后唯一timeout900秒执行，不重跑融合/改stage/新GPU。 [准备](research/40_L0_CPU_FUSION_AUDIT_AND_ENV_CACHE.md)。

最新CPU融合终态：CPU fusion-r1/sourcec69e492已exit0/1960.417015秒终态，peak RSS30.8287GiB；两臂各825tensor/3分片/300目标/525未目标完整，18原输入融合前后官方digest一致，3PIDs退出/CPU锁释放/source与GPU账本不变。完整独立fresh产物审计尚未执行，不能称模型/任务/GPU就绪。

最新独立审计/二进制资源：CPU audit-r1/sourcedbe863c已唯一实际启动，3PIDs2505483/2505484/2505485 live、900秒cap/锁持有/source与GPU账本不变。fresh18输入/CFG-only825tensor与3shard/525untargeted通过，few-step+CFG尚待。官方Torch三wheel SHA与Flash官方asset ID/size已锁，Flash官方digest UNKNOWN；均未下载/安装，实际ABI/fullruntime未通过。 [运行卡](research/41_L0_FRESH_AUDIT_AND_BINARY_SOURCE_LOCK.md)。
