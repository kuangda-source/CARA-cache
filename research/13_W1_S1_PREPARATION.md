# W1-S1：同状态官方 / 收缩 / 标量校准诊断准备卡

日期：2026-09-30；状态 `IMPLEMENTED_CPU_VERIFIED_NOT_GPU_RUN`。三近似器评分入口与有界监督模式已实现，58项本地CPU测试通过；实机验收尚未启动。进入依据是 W1-P0 官方路径单样本 parity 通过。

## 要回答的问题

在同一个官方 WC 缓存命中状态、同一跳步位置，简单收缩或在线标量校准是否降低残差误差，并同时降低最终速度预测误差？先固定状态比较近似器，随后才考虑候选闭环与自由调度。

## 最小范围与预算

沿用 AV 工程场景、seed 0、93 帧、432×768、guidance 7、36 时间点 / 72 CFG 调用和 WC 70-call horizon。先复用调用 15/16/37/38 两组 CFG 分支，冻结选择后不按结果挑点。工程样本排除出未来独立确认；这不是 24 场景 CAL。

原始 4 GPU·h 余额为 2.754802794 h。准备以至多 900 秒 / 0.25 GPU·h（含加载、诊断、失败、flush）执行一个串行任务，预计主要计算约 350–650 秒，额外候选评分成本尚未实测，因此设硬上限而非承诺完成时间。此额度从现有余额扣除，不追加预算。只在实现验收完成、源码同步部署、重新准入后提交；本卡不表示启动。预留余额供候选专用 parity、固定 schedule 闭环和后续 F2，暂不启动 Wan/OMR。

## 实现与因果性要求

1. 部署 forward 仍返回官方 WC 输出。两套独立 calibrator 仅观察该请求、对应 CFG 分支、模型身份下真正发生的 full-compute anchor；当前 shadow truth 不进入 anchor、系数、缓存或下一次决策。
2. 在选定 skip 状态，用同一 probe、同一历史 full anchors、同一状态分别得到 official、shrink、scalar 预测，再共享一次 deep truth。候选必须遵循原有 warp 和输出 head 的位置及语义；记录 warp 前 residual 和 warp 后 residual / 最终速度各自的比较位置，防止把前后 warp 张量错当同状态。
3. 新 runner 需要独立的诊断候选评分入口。现有 `build_shadow_forward(..., mode='scalar'/'shrink')` 会替换部署近似、改变后续状态，不能直接把三次自由轨迹生成标为同状态三臂比较。
4. 保留 request / CFG / model reset、70 周期末尾重置、anchor 不足与非有限值回退；冻结现有默认 ridge、clip、decay、shrinkage，不扫参数。记录每个候选的 anchor steps、pairs、beta 或外推比例、fallback reason，以及 full/skip 计数。
5. 诊断候选及 head 调用须保持 RNG、registered buffers 和缓存不变，并被部署 BlockCounts 排除。先用针对性 CPU 检查确认无真值回写和三候选共享同一输入，再要求实机输出 / 缓存 / trace 与无诊断参考严格一致；失败则只记 TECH_BLOCKED。
6. 原始 W1-P0 off/on 视频相同，但新评分代码仍需独立实机无扰动验收。若新增实现无法直接复用原 off 参考并逐调用校验，应在 900 秒任务内重做 off/on，而非用“旧版本通过”替代新版本验证。

## 记录与停止条件

新 run ID `w1-s1-r1` 和新目录；保留提交、部署归档哈希、协议、GPU UUID、PID/进程组/日志、终态、所有诊断点、按阶段成本和原始失败。新 supervisor 入口必须沿用项目单任务锁、准入、外来 compute 进程冲突停止和总预算计账；不得单独启动未监督的生成进程。

若输出/缓存不一致、出现非有限值、锚点不合法、GPU 冲突或到达任务 / 总预算上限，终止自有进程组并记账，不重复启动。只有数值误差降低可标 `MECHANISM_ONLY`；没有优势记 `NO_GAIN_IN_SCOPE`，小分母回退过多或点数不足记 `INCONCLUSIVE`。四点改善不等于质量保持、干净测速收益或独立泛化。机制信号明确后再安排候选专用 parity 和固定跳步闭环。

## 实现接续记录

`src/wcomr/same_state.py`维护mode/CFG独立calibrator，观察真实full分支，预测先于truth补算；原始forward返回官方输出。直接提取固定官方flow片段，让各候选使用与现有注入相同的warp语义，并区分prewarp/postwarp/velocity评分。request、70周期、模型/expert变更均清空候选历史。新增随机buffer/RNG、空间变化flow与实际candidate首次skip匹配测试。

`check_w1_parity.py --same-state`新版本执行同seed off/on，要求72output/cache/video/trace不变、四点有限且anchor严格过去。`supervise_f1.py --w1-same-state`沿用全项目锁、GPU准入、外来计算冲突停止及记账，最多900s。一旦启动，应以新的launch/terminal回执覆盖这里的NOT_GPU_RUN快照。

## r1失败及r2实机接续

r1在初始化阶段因启动缺少项目HF_HUB_CACHE退出，0生成；75.011195s全部计账。已固定监督器环境，旧PIDs缺失/全项目锁可获取后，源`7e5bc10`归档哈希匹配且6项Linux监督器测试通过，重新准入GPU1 24MiB/no compute apps，启动不同目录`outputs/w1-s1-r2`。supervisor2444752/timeout2444757/runner2444759核实存活，HF_HUB_CACHE已指向项目hfhub，进入off生成。此段是运行快照，终态以后续回执为准；不改在跑源码。

数值摘要只从完整off/on终态生成，重核72输出/状态/视频/采样一致性、四点及past anchor，拒绝部分、非有限或不同truth的回执。预设工程筛查：候选无fallback，四点中至少三点velocity MSE低于官方，且四点velocity与postwarp residual的sum-MSE比均<1，才记MECHANISM_ONLY候选信号；两候选总velocity MSE都>=官方则记NO_GAIN_IN_SCOPE，否则INCONCLUSIVE。这是单场景相关四点的描述性筛查，不是统计确认，不据此扩大预算或作质量结论。
