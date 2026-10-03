## 2026-10-03 H0首卡技术停止，费用/释放已审计，继续CPU模式定位

[终态与下一步](research/76_WC_H0_COMPLEMENT_R1_CARD_AND_RESULTS.md)：唯一wc-h0-complement-r1/source18e692e退出1，baseline20更新/40CFG，observed在首个eligible full call33触发新增 `H0 requires eval` 检查。完整四臂0、原件0，2状态/8臂分母保留，完整九门未完成；不是互补性负结果。CPU26的toy显式eval，未覆盖实际官方网络模式，先核查实际固定源码/构建与mode-sensitive路径，再无CUDA修复控制，不直接改原模型mode或重提r1。source/stage/失败回执封存，H1/H2/RV/训练后置。

全wall523.4742335593328秒已实计，累计4.856303261031603/12GPUh、33jobs，余7.143696738968397h，无inflight；原三PIDs/f1锁/指定GPU均已释放（24MiB/noapps）。另一GPU卡须新identity/source、具体范围/成本与完整实际门，不自动第二卡。以下在跑及旧预算文字为历史快照。

## 2026-10-03 H0首卡实际CPU26通过，唯一诊断已启动

[实际部署](reports/wc_h0_complement_r1_deployment_20261003.json)：冻结source18e692ebb0f23a6ed832e0d7ff74ec3a6acc0ca9，actual CPU26/C分支/完整四臂/原件误差/step13&20/source/assets/import/package全部通过，CUDA未初始化、原账本不变；源码已推送。唯一wc-h0-complement-r1 fresh准入并启动，[启动](reports/wc_h0_complement_r1_launch_20261003.json)/[现场](reports/wc_h0_complement_r1_start_observation_20261003.json)supervisor2657420/timeout2657436/runner2657438存活，初始化非终态。原GPU24MiB/noapps，child起算最多1200秒截止北京时间15:08:40，已预付1/3GPUh（在途5.044227085042899h、第33job），结束按实际全wall结算；已用4.710893751709566h/32job历史保留。只跟踪原句柄，不改在跑source或重提，不据live报互补性/视频收益。H1/H2/RV/训练后置。

## 2026-10-03 H0首卡：CPU门通过，实际部署准入待验证

用户2026-10-03 06:00:14UTC继续自主推进常规步骤、06:07:41再确认继续实验。H0首卡冻结第二CAL场景/两CFG四臂、6/23/27 dense回退与0.1/0.98，C严格过去同轨历史、真实D唯一路径；CPU原源码/完整shadow/失败分母/原件误差门通过。1200秒总cost/1170child，951.369秒规划包络含余量。当前未GPU启动，必须冻结source、actual assets/import及fresh UUID/VRAM/compute/f1锁/12h余额门；不重启r4/自动H1/H2/RV/训练。used4.710893751709566h/32jobs保留，原件不入Git。 [具体冻结卡](research/76_WC_H0_COMPLEMENT_R1_CARD_AND_RESULTS.md)。以下r4/旧授权条目为历史快照。

# WorldCache experiment rules

## 当前补验终态 — 2026-10-03

直接授权的唯一wc-mid-full-r4已执行并独立审计：104QKV/312case及九门/step13&18通过。实计1153.547616秒，累计4.710893751709566/12GPUh、32jobs，无inflight，PIDs/锁/GPU已释放。该单次授权已消耗，不重启同run或自动新增r5/H0/H1/RV；[75完整结果与下一卡边界](research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)。以下准备授权为历史。

## 当前直接补验授权 — 2026-10-03

用户当前直接授权七份文件、CPU及门通过后的唯一wc-mid-full-r4≤1800秒/现累计12GPUh，见[独立卡](research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)。旧1200秒及无r4约束保留其历史身份；本卡不授予自动下一窗。原已用4.390463858430222h/31jobs不变，必须actual CPU/source/assets及fresh GPU/锁/预算门。

## 最新执行授权 — 2026-10-03

[各项目累计12GPUh与恢复后队列](research/BUDGET_AUTHORIZATION_20261003.md)取代此前仅文档及旧预算限制；保留已用与历史账目，单昂贵任务，GPU优先WC。WC已用3.9117525685110333GPUh、28jobs保持，当前余额8.088247431488967GPUh。先中间刷新/全26深层覆盖准备和无扰动诊断，再H0互补性、H1来源×寿命；W1/replay已完成不重跑，RV后置。旧new4h/clean50不自动转为新队列。新runner须按明确12h权威账本校验，不能重新执行硬编码4h的旧launch。 下述2026-10-02原包适配/仅文档条目为当时快照。

- Read `EXPERIMENT_REPORT.md`, `research/02_CURRENT_STATE.md`, `research/09_NEXT_ACTIONS.md`, and `memory/handoffs/LATEST.md` before continuing. Follow the supplied plans in `plans/`; do not restart unrelated historical projects.
- User authorized experiment work on the two-card and four-card A6000 servers on 2026-09-29. Select using fresh GPU UUID, VRAM and compute-process observations. No stopping others' jobs, changing shared drivers, or treating idle utilization as admission.
- First batch: F0 and F1 (4 scenes, 1 seed, Native and official WC), one expensive job at a time. Self-imposed first-batch stop cap: 4 GPU hours including load, failure, diagnostics and flush. This is a conservative execution limit under the current user instruction, not an assertion that the plan itself grants GPU permission. Propose F2/W1 GPU scope from measured costs before expansion; no training or paid scoring in this batch.
- Keep upstream pinned and unmodified. Experimental runtime adaptations must be separately identified, versioned, and shared by both comparison paths where appropriate.
- True anchors are full computations within the current request, CFG branch and model/expert. Current shadow truth never updates deployed state. Reset on requests and model/condition changes. Fail safe on nonfinite inputs or insufficient anchors.
- Synthetic/CPU tests are implementation evidence only; no generated video or quality/latency claim without real receipts. Record UNKNOWN and TECH_BLOCKED honestly.
- User requests that every meaningful code/config/result change be committed and synchronized to the private GitHub repository `kuangda-source/worldcache-omr-experiments` before reporting completion. Keep code, plans, tests, manifests, summaries and small receipts in Git. Never commit credentials, machine connection secrets, weights, bulk tensors, or videos. Record artifact paths/hashes instead. Do not force-push or overwrite unrelated changes.
- A GitHub connector atomic tree/commit/ref update may be used when local Git credentials are unavailable. Verify the resulting commit and file tree; preserve remote README and parent history. Record local-to-remote mapping under ignored `.sync/`.

- Maintain `EXPERIMENT_REPORT.md` as the stable cross-device experiment overview. After meaningful experiment changes, update its evidence-bound results/decisions plus next actions and handoff in the same sync. Follow its Git conflict and single GPU submitter protocol; Git synchronization is not a distributed runtime lock.

- This repository is WorldCache-only. OMR plans, Wan/LongLive support preparation and future OMR edits belong to private kuangda-source/omr-experiments. Do not switch this queue to OMR; finish existing frozen WC work first. Shared legacy wcomr package/project identifiers and historical deployed paths are retained for compatibility.
