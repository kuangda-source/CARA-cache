# WorldCache / OMR 实验文档与跨设备接续入口

更新日期：2026-10-01（北京时间）；文档版本：v1.0；实验计划版本：v1.1。

本项目研究视频世界模型的质量—时间折中：以 Cosmos-Predict2.5 上的 WorldCache 低开销改进为当前主线，OMR 物理纠正为条件候选。本文是持续更新的实验总览，固定使用此文件名；具体参数、原始回执和完整计划通过相对链接引用，适用于任何设备上的仓库副本。

结构参考既有 `physcache_full_experiment_report.md` 的背景、假设、实验演进、结果和下一步组织方式。仅借鉴文档结构，不继承 PhysCache 的结论、样本、预算或执行权限。

## 1. 当前结论与最重要的下一步

**暂停增加scalar复杂度；输入对照问题已回答，下一成本/资源窗口需重要决策。当前有机制信号，没有质量—时间收益。** 原开发VQA6平1misc降/scene等权−3.174603pp、MUSIQ3升4降/robot拒绝保持。重复/明显内容变化对照不验证物理正确性，不直接否定方法或切OMR。

| 项目 | 最新终态证据（2026-10-01） |
|---|---|
| 当前阶段 | 输入控制原8/126完整终态，下一窗口预算/范围提议 |
| 最近运行 | controls-r1/source72c9e24 exit0；全部3PIDs退出/global锁与GPU释放 |
| 覆盖/响应 | repeat0/42变化，blank14/42，cyclic14/42；126有效/0invalid |
| 审计 | 原始tokens/24输入重算/8视频/10模型文件/源码锁与本地原题summary全一致 |
| 评价边界 | 重复稳定/部分内容响应，不是物理准确金标准/235BJoint/方法接受 |
| 方法证据 | CAL8机制改善；VQA/MUSIQ未一致收益，clean速度/独立确认仍未证 |
| 成本 | 控制79.023695秒；累计3.6512467238638138/4GPUh，余1255.511794秒，无在途 |
| 下一步 | [完整计时程序](research/32_W1_CLEAN_TIMING_CPU_PREPARATION.md)原8/50已实现/本地Linux48CPU通过，提议4GPUh仍未扩额/新提交 |

证据：[控制结果](research/30_W1_VQA_INPUT_CONTROLS_RESULTS.md)、[控制终态审计](reports/w1_vqa_controls_r1_audit.json)、[本地重算](reports/w1_vqa_controls_r1_local_recompute.json)、[原VQA结果](research/28_W1_DEVELOPMENT_VQA_RESULTS.md)、[账本](reports/budget.json)。部分场景在三条件均相同不能隐去；即使controls通过也没有新的物理质量正结果。
此前：[固定重放结果](research/24_W1_FIXED_REPLAY_RESULTS.md)、[重放完整汇总](reports/w1_replay_r1_summary.json)、[CAL8机制结果](research/21_W1D_CAL8_RESULTS.md)、[CAL8分布/排序](reports/w1d_cal8_r1_analysis.json)。

历史阶段证据：[decode区间定位](research/17_DECODE_INTERVAL_RESULTS.md)、[下一轮准备卡](research/18_DECODER_POLICY_GATE.md)、[阶段汇总](reports/stage_r2_summary.json)。

依据：[F1 r3配对汇总](reports/f1_smoke_r3_summary.json)、[W1-P0终态结果](research/12_W1_P0_TERMINAL_RESULTS.md)、[实时恢复审计](reports/w1_p0_r1_recovery_audit.json)、[预算账本](reports/budget.json)。

最新非GPU资源进展：[L0审计](research/33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md)，历史Wan5B11文件官方完整hash可复用/两600tensor header结构匹配、16CPU通过；尚缺完整adapter/真实融合与隔离环境。OMR公开release仍Coming soon，未新生成或切换主线。

最新L0推进：[CFG真实payload/两配方CPU融合准备](research/34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md)。L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

最新实际资源运行：L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。 见[r2启动](reports/l0_adapter_assets_r2_launch_20261001.json)/[观察](reports/l0_adapter_assets_r2_live_observation.json)。

最新L0恢复与接口进展：[range39/真实scheduler/公共管线门](research/35_L0_RANGE_RECOVERY_AND_INTERFACE_GATE.md)。L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。 UniPC源码/CPU方程相同，但stock Wan guidance1仍两前向、原默认帧数/noise构造有差异；完整task/GPU parity待验收。

最新实际CPU恢复：L0 CPU range-r3/sourcebd8253d已唯一实际启动，3PIDs2498231/2498232/2498233都/proc verified live，CPU获取锁持有、CUDA空/source协议hash一致/账本未变。官方精确206/64KiB旧prefix边界preflight通过；已完成2个16MiB chunk、重试0次，已fsync字节589299712（562MiB），另有在途文件长度602931200（575MiB）。未完整1289824400/整SHA验收或两模型融合。复用原530MiB，不改r2失败或扩大GPU预算。 [r3 launch](reports/l0_adapter_assets_r3_launch_20261001.json)/[live](reports/l0_adapter_assets_r3_live_observation.json)。

原生公共管线准备：[T2V单条件scope CPU检查](research/36_L0_NATIVE_CONDITIONAL_CPU_PREPARATION.md)。已实现仅T2V的scope adaptation，guide1直接conditional、guide!=1保留原CFG运算，finally恢复，不改源文件/i2v。Local/Linux7检查通过；完整native T2V body+真实UniPC/CPU替身在4/50步guide5输入/timestep/输出bit equal，guide1分别4/50cond/0negative。不是实际模型/GPU parity；保留BF16guide1的stock抵消差异，不称guide1 OFF/ON bit invariant。 资源下载/真实融合仍按r3回执推进，GPU预算未变。

## 2. 研究背景、假设与判定方式

目标是在相同质量下更快，或在相同时间下质量更好。比较对象应包含合理调参的官方缓存与原生少步采样，避免只超过一个默认配置。研究成功需落在端到端质量—时间曲线上，特征误差降低只作机制证据。

| 假设 | 预期验证 | 当前状态 / 否定条件 |
|---|---|---|
| H-W1：简单收缩或浅深层增量校准能改善跨步残差近似 | 同状态 shadow → 固定跳步闭环 → 自由调度下的质量—时间对照 | CAL8同状态scalar机制信号；固定schedule技术通过，MUSIQ混合/开发VQA无代理收益，质量—时间未证，额外计算抵消收益则停止深化 |
| H-W1D：残差误差大小不能完全代表下游危害 | 对照残差 MSE、最终速度预测误差/方向与局部伪影 | CAL8所有8样本有内部排序差异；未联系视频物理损害，先全局scalar闭环 |
| H-J：减少不必要的 OMR 纠正调用/梯度可改善折中 | 先复现有效原版，再测稀疏、未来侧梯度与复用 | 资源与兼容性待复核；原版无效或 adapter 不匹配时不做归因 |
| H-L：预训练 CFG / 少步适配器是值得纳入的强基线 | 同一兼容 Wan5B 上原生、CFG-only、四步 Few-step+CFG 三臂 | L0 base/header和CFG真实payload通过；两配方CPU准备22通过，完整融合/任务与GPU仍未验证；小批次仅筛查可用性 |

不把 PhysCache 的历史物理损伤、抖动或运动结果当作本项目先验结论。若出现运动变少、模糊或动作未完成，不能仅凭“更平滑”指标宣称改进。

## 3. 技术路线与新增参考工作的定位

当前执行顺序：**F1 收尾 → F2 / W1-D → 预算允许的 L1 → W1/W2 深化或兼容资源具备后的 OMR**。非 GPU 的 L0 资源核对可穿插；一次仅运行一个昂贵任务。

- **WorldCache**：先简单收缩/全局校准，再考虑少量分组；固定跳步位置先比较近似器，避免调度变化掩盖机制。
- **QuantWM 启发的 W1-D**：借鉴“误差大小与下游影响分开测量”。当前 shadow 真值只用于评分，不能回写部署缓存、系数或刷新规则；诊断额外计算计入预算，部署测速关闭。暂不展开完整 KV 量化线。
- **LongLive-Plug L0/L1**：只在已核实兼容的 Wan2.2-TI2V-5B 上开展三臂测试；8 个预冻结场景、1 seed，条件具备且看质量前可登记扩到 12。提议上限 2 GPU·h 从现有 4 小时中划拨，先保留 F2/W1 成本，不自动增加预算。
- **OMR J6 / 组合 X3 / Physics-LoRA J5-P**：匹配生成器、VAE 与 adapter，并证明单模块有效后才进入；参数可叠加不代表能力可叠加，单模块加速比不能相乘。训练仍保留重大决策节点。

跨模型家族的参数兼容、适配器精确版本和机器可用性必须在执行前核实。Wan 与 Cosmos 不按绝对耗时直接排胜负。文献事实和未核实资源见[来源清单](manifests/plan_update_sources_20260930.json)；完整实验设计见[长程计划](plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_OMR_20260929.md)和[首批说明](plans/CODEX_FIRST_BATCH_WorldCache_OMR_20260929.md)。

## 4. 当前冻结协议与资源

| 条目 | F1 配置 / 边界 |
|---|---|
| 基模 | Cosmos-Predict2.5-2B post-trained；两臂使用相同运行适配 |
| 输入 | `av_002b815b-7595-4d54-a9f4-4c62c83d3009`、`common_sense_049c9292-db5f-490b-a72b-546775e8156c`、`physics_001`、`robot_000`；技术样本排除出独立确认集 |
| 输出 | seed 0；93 帧；高 432 × 宽 768；16 fps；guidance 7 |
| 实际采样器 | FlowUniPCMultistepScheduler / Karras；请求 35 步，实际 36 个时间点、72 次 CFG 前向 |
| WC 计数周期 | 保留官方 70-call horizon；记录末尾 reset 和每次真实深层计算，不能静默改成 72 |
| 解释范围 | 用户选择的当前代码技术对照，**不是论文 35 步 Euler 的精确复现** |
| 比较路径 | Native 对官方 WorldCache；F1 不安装收缩/校准原型 |
| 执行配置 | eager、匹配 offload、保留文本/视频/人脸安全管线；冷启动、加载与阶段时间分开 |
| 显存口径 | torch 峰值为上游最近一次 reset 之后；监督进程采样峰值不是瞬时精确峰值 |
| 资源快照 | 已使用两卡 A6000 服务器上的单张卡；另一台历史称“四卡 A6000”，实际核对为四张 RTX 6000 Ada；都需实时准入检查 |

来源：[输入与哈希](manifests/smoke.json)、[实际时间网格及源码锁定](manifests/f1_runtime_protocol.json)、[执行协议](research/04_F1_PROTOCOL.md)、[运行适配](manifests/runtime_adaptations.json)、[源码补全](manifests/runtime_completion.json)。`smoke.json` 的 `FROZEN_NOT_RUN` 是初始冻结时的标签，当前执行状态以后续终态回执为准，不改写历史 manifest 伪造新协议。

历史运行 r2 的源码提交为 `4814657`，r3 为 `57c8660`，W1-P0 为 `d98f447`，计划整合提交为 `3ddadbe`；文档提交不等于实机运行版本。新设备先核对部署源码、配置和模型哈希，不能直接以本地 HEAD 代表已有实验。

## 5. 实验演进与失败账本

| 记录 | 观察与证据 | 处理 / 科学含义 |
|---|---|---|
| F0 核心模型加载 | tokenizer 194、Reason1 729、DiT 689 个 key，无 missing/unexpected；[加载回执](reports/f0_core_load_r2.json) | 证明构造与权重匹配，不代表完整生成成功 |
| 安全管线就绪 | 原 gated access 问题解决；完整保留管线通过；[回执](reports/guardrail_pipeline_20260929.json) | “能运行过滤器”和“所有生成都通过过滤”是两个判断 |
| F1 r1 | 首个 Native 视频产出，旧 70-call 断言失败；[终态](reports/f1_smoke_r1_supervisor.json)、[解码检查](reports/f1_smoke_r1_decode.json) | 调度诊断发现实际 72 次调用；未保存的精确计数不得补造；不与 r2 混池测速 |
| 协议决定 | 用户要求先完成当前代码技术对照；[决定记录](research/10_SAMPLER_PROTOCOL_DECISION.md) | 固定 36 时间点 / 72 调用，保留 WC 70 计数周期；Euler 后续单列 |
| F1 r2 | 2 个 Native 输出；第三个被视频过滤，监督进程 1042.542395 秒后 exit 1；[终态](reports/f1_smoke_r2_supervisor.json) | 不关闭过滤器，不删失败凑通过率；WC 未开始，技术对照未完成 |
| 计划 v1.1 | 加入 L0/L1、W1-D、J6/X3/J5-P | 计划更新，没有启动新的 Wan / OMR / 训练任务 |

以上都是工程/规划进展；尚无新的研究方法得到质量—时间验证。

## 6. 历史 r2 样本记录（最新 F1/W1 结果见第 1 节链接）

下表自动按已归档 r2 Native 回执整理，时间不是整进程平均，也不能用于计算 WC 加速比。AV 为进程首样本；common 为第二样本，不能仅凭顺序宣称完全稳定的 warm 性能。

| Native 样本 | 单样本端到端秒 | 去噪秒 | 输出字节 | SHA256 前 12 位 |
|---|---:|---:|---:|---|
| av_002b815b-7595-4d54-a9f4-4c62c83d3009 | 312.333 | 257.319 | 1392057 | `173e7a9129b3` |
| common_sense_049c9292-db5f-490b-a72b-546775e8156c | 298.310 | 249.315 | 941506 | `b7f617acb09b` |

两个样本均记录 72 次 denoiser / 72 次 full / 0 次 skipped-deep，格式为 93 帧、768×432、16 fps。第三个场景被拒绝，第四个未执行；这不是全批次的“2/2 通过”。每个视频的完整 SHA256、字节数、服务器路径与逐步调用轨迹在 [Native 回执](reports/f1_smoke_r2_native.json)。安全拒绝本身不判定物理质量，尚需失败诊断。

视频保留在实验服务器 `outputs/f1-smoke-r2/native/` 下，仓库只存回执；Git clone 不会下载视频或模型。跨设备取回前使用已授权连接配置，取回后按回执校验 SHA256。没有可访问的视频时将视觉审查标记为待完成，不能以解码成功代替审查。

最新工程进展：r2 旧进程已核实退出；已实现 outcome protocol v1，使用官方 `keep_going=True` 保留拒绝事件并继续原定场景。过滤返回值不变，未知异常仍停止；r3 两臂重新运行，不混用 r2 时间。32 项本地及 11 项服务器 CPU/模拟 GPU 测试通过；r3 已启动，尚未证明实机全批续跑成功。见[结果处理协议](manifests/f1_outcome_protocol.json)。

## 7. 下一轮的执行与停止条件

1. 输入控制原8/126终态审计与本地重算完成，不重复评分/调prompt。原方法机制与负小代理边界保持，尚无质量—时间收益。
2. 余1255.511794秒，旧原8×两臂诊断3141.247秒（不是clean下界）；不能稳妥提交完整计时，不挑好子集替代原8。
3. [下一窗口](research/31_W1_NEXT_WINDOW_COST_AND_DECISION.md)提议新4GPUh原8×两臂×3repeat clean成本门，或先CPU核对替代资源。预算/范围待用户决定；新runner原8/50已实现/本地Linux48CPU与真实validate-only通过，未GPU、不自动扩额。
4. 批准后实现/CPU/协议与Git同步/hash部署/fresh锁GPU准入，失败与原拒绝保留，partial不凑完整结论；source/身份不混用旧run。
5. 成本通过也不替代强质量指标/调优WC和原生少步曲线/DEV独立确认。暂不加W2/切OMR、无人评/付费/训练。

## 8. 多设备、多对话同步约定

### 8.1 唯一入口与证据层级

- **本文**：维护当前结论、历史演进、主要结果和导航；不要为每次聊天复制一份“最新版”。
- **plans/**：研究设计、阶段和预算条件；**research/09_NEXT_ACTIONS.md**：当前有序队列。
- **reports/、manifests/**：可核验小回执与冻结协议。结论与回执冲突时先标 UNKNOWN 并核对原始证据。
- **research/02_CURRENT_STATE.md**：按时间追加过程记录，旧段落不是当前状态。
- **memory/handoffs/LATEST.md**：给下一位执行者的简短接续快照；这是项目文件，不是个人 Codex 记忆。
- **AGENTS.md**：所有新对话进入仓库时读取的规则。

### 8.2 新设备首次使用

```sh
git clone git@github.com:kuangda-source/worldcache-omr-experiments.git
cd worldcache-omr-experiments
git status --short --branch
git log -5 --oneline
```

需要该私有仓库的 GitHub 访问权限。设备路径可自行选择；SSH/HF 凭证和服务器连接配置在各设备本地配置，不写入 Git。没有授权的服务器访问时可以更新文档、检查代码，不把历史连接记录当作当前可用连接。

### 8.3 每次接续与交接

1. **同步前看工作区**：运行 `git status --short --branch` 和 `git fetch origin`。工作区干净且可快进时 `git pull --ff-only`；有本地未提交修改或分叉时先审阅并保留改动，不强制覆盖、不强推。
2. **读取入口**：`AGENTS.md` → 本文 → 下一步队列 → LATEST → 本次相关协议和回执。明确源码版本、run ID、剩余预算。
3. **执行者协调**：同时可有多个设备读仓库，但昂贵 GPU 作业只由一个执行者提交。已有 RUNNING / 状态未知任务先核验，不重复启动；换服务器也不能绕过全项目单任务约定。Git push 不是跨服务器分布式锁，当前监督锁只保护对应运行目录。
4. **每个实验独立身份**：新 run ID 与新输出目录，禁止覆盖旧运行。启动时记录执行设备/对话、源码 commit、协议、GPU UUID、PID/日志位置与预算上限到交接文件；结果以终态回执为准。
5. **更新同一组文件**：结果回执和预算 → 本文结论/结果/失败 → 下一步队列 → LATEST；协议变更另建版本并说明原因，不能倒改旧结果定义。
6. **发布可核验同步**：检查差异和敏感信息，按本次实际改动显式 `git add <文件>`，`git commit`，`git push origin HEAD`。被远端新提交拒绝时 fetch 后合并/解决冲突，保留双方实验记录；不 force-push。验证 `git ls-remote origin refs/heads/main` 与本地 `git rev-parse HEAD` 一致后才报告同步完成。

Git 同步的是代码、计划、文档与小回执，不是远端正在运行的进程、环境、视频或模型。接续快照不能替代实时进程核查。

### 8.4 新对话可直接使用的接续说明

> 请接续 `kuangda-source/worldcache-omr-experiments`。先同步 Git 并阅读 AGENTS.md、EXPERIMENT_REPORT.md、research/09_NEXT_ACTIONS.md、memory/handoffs/LATEST.md。核实相关 run 的远端进程、终态回执及预算，避免重复启动；按照现有协议完成最优先任务。每次有意义的变化同时更新实验文档、回执与交接并推送 GitHub。遇到重大预算、协议、训练或方向决策再询问用户。

## 9. 后续实验记录模板

新增实验时复制以下字段到本节或单独的 `research/` 记录并从本文链接；不要留有实际运行却无法找到来源的“口头结果”。

```text
实验 ID / 日期 / 执行者：
问题与假设 / 进入依据：
源码 commit / 协议和配置路径 / 模型 revision：
样本清单与 hash / seed / 对照臂 / 唯一变量：
硬件 UUID / 精度 / offload / 环境版本：
状态：PLANNED / RUNNING / COMPLETED / FAILED / TECH_BLOCKED / UNKNOWN
输出目录 / 日志 / PID与启动时间 / 终态回执：
成功、失败、拒绝、未执行的样本数：
冷启动与各阶段耗时 / 显存口径 / 本次和累计 GPUh：
结果表 / 原始证据链接 / 视频审查状态：
支持或否定什么 / 尚不能得出什么：
决定：继续、修复、暂停或转向；原因及下一步：
```

## 10. 文档更新记录

| 日期 | 变更 | 运行影响 |
|---|---|---|
| 2026-09-30 | v1.0：建立 PhysCache 风格的研究全景文档；汇总 F0/F1、v1.1 计划、原始结果、失败和跨设备接续规则 | 仅整理已归档证据，没有发起或重启实验 |

2026-09-30 接续：部署源提交 `57c8660`、归档哈希一致后启动 r3；[启动回执](reports/f1_smoke_r3_launch_20260930.json)。新的质量/加速结论仍待实际配对与视频审查。

2026-09-30 汇总工具：新增 `scripts/summarize_f1.py`，从两臂及监督器回执生成可追溯结果。只有两臂完整终态且输入、实际 setup、协议和版本一致时才输出逐样本时间比；拒绝留在固定分母内，冷首样本单列，质量状态仍为未审查。7 项针对性测试验证部分运行不产生加速结论、配置差异/重复记录/缺失结果/非有限耗时会被拒绝。未改动远端在跑源码。

终态回执归档后执行（文件未齐全时不要用其他轮回执补齐）：

```sh
python3 scripts/summarize_f1.py --native reports/f1_smoke_r3_native.json --worldcache reports/f1_smoke_r3_worldcache.json --supervisor reports/f1_smoke_r3_supervisor.json --output reports/f1_smoke_r3_summary.json
```

2026-09-30 r3 首个 Native AV 视频已完成：单样本端到端314.463s、去噪256.631s，72次完整前向、0次深层跳过。本地视频SHA256与回执一致，93帧完整解码通过，768×432，时间戳0–5.75s严格递增。[完整性回执](reports/f1_smoke_r3_first_native_decode.json)。任务已进入common场景；尚无WorldCache配对或质量审查结论。

2026-09-30 W1-D CPU准备：新增 `src/wcomr/shadow_metrics.py`，分别计算残差与最终速度预测的MSE、相对误差、方向余弦，并按显式张量轴汇总时间/通道等位置。零能量参考的相对误差记为空；非有限值显式报错状态。合成下游映射测试复现“残差更小、输出误差更大”的排序反转，仅验证评分逻辑，不是本模型的实验证据。尚未实现真实同状态shadow采样/部署不变性验收；未部署到在跑的F1。

2026-09-30 W1同状态shadow接入原型：`src/wcomr/shadow_forward.py`在选定缓存命中调用中，从当前probe输出直接补算剩余blocks与输出层，仅评分、不调用第二次缓存forward。显式request边界、独立记录；恢复RNG和registered buffers，计量hook排除诊断调用。固定上游源码配合CPU小网络的official/scalar/shrink三路径测试验证输出、缓存、anchor历史与部署计数保持；另测随机层及buffer恢复。全部48项测试通过。该原型未部署，尚不能保证真实CUDA模型所有未注册状态无副作用；真实模型同seed输出一致性、显存、成本验收及W1批次入口仍待实现/执行。

2026-09-30 r3实机拒绝续跑检查通过：physics_001记录为VIDEO_REJECTED，72次完整前向，无被拒绝mp4保存；随后进入原定robot_000，监督与子进程仍在运行。[现场回执](reports/f1_smoke_r3_rejection_continuation.json)。这验证了失败记录和继续执行机制，不代表4场景全通过，WorldCache结果仍待完成。

2026-09-30 Native r3终态：全部4场景已尝试，AV/common/robot被接受，physics输出被拒绝；整体状态ATTEMPTED_ALL_WITH_REJECTIONS。Native监督耗时1322.462s，正常exit0仅表示记录完整。机器人单样本295.289s、去噪249.675s；common单样本296.992s、去噪249.370s。[Native完整回执](reports/f1_smoke_r3_native.json)。WorldCache已开始初始化，[切换快照](reports/f1_smoke_r3_worldcache_start.json)不是终态；无配对速度或质量结论。

2026-09-30 首个WorldCache AV结果已保存，进入common：72次调用、38次完整计算、34次跳过深层；调用1和71的cache counter均为0，符合冻结70周期/72调用协议。实际setup（除输出目录与WC开关）、输入/采样/源码/结果处理协议与Native一致。单样本端到端213.119s、去噪152.435s；仅运行观察，未报告整批或质量等价加速。[在途快照](reports/f1_smoke_r3_worldcache_first_snapshot.json)。此外3个接受的Native视频全部哈希匹配并完整解码，[检查回执](reports/f1_smoke_r3_native_integrity.json)。

## F1 r3 最新技术结果（2026-09-30）

| 场景 | Native端到端s | WC端到端s | 耗时比N/WC | WC完整/跳过 |
|---|---:|---:|---:|---|
| AV（冷首样本） | 314.463 | 213.119 | 1.476× | 38/34 |
| common | 296.992 | 185.435 | 1.602× | 35/37 |
| robot | 295.289 | 184.523 | 1.600× | 35/37 |

全部7个接受视频哈希及完整解码通过。physics的Native拒绝/WC接受单列，不当作质量提升。详细边界和下一步见[技术结果记录](research/11_F1_R3_TECHNICAL_RESULTS.md)。

2026-09-30 W1-P0准备：同一AV工程样本、同seed在官方WC路径关闭/开启shadow各运行一次；在调用15/16、37/38诊断两分支。比较所有72次输出哈希、完整/跳过trace、缓存终态及视频哈希，要求精确相等。单任务900秒上限（0.25GPUh）从剩余预算扣除，先不测试候选效果。49项CPU测试通过，真实模型验收待运行。[冻结验收配置](manifests/w1_parity_protocol.json)。诊断计时含逐步哈希与额外补算，不作为部署速度。

2026-09-30 W1-P0 r1已启动：源d98f447，归档哈希一致；49项本地测试、13项Linux CPU/模拟GPU测试通过。监督进程2439296/子进程2439301经新准入后确认存活，单任务900秒上限。启动前已结算1.092568GPUh，在途另计。[启动回执](reports/w1_p0_r1_launch_20260930.json)。真实一致性结果未出，F1完整视频质量审查仍待完成。

2026-09-30 完整视频审查页已生成：本地 `reports/private/r3/review.html`，可从头播放、并列比较、查看原始prompt并导出观察JSON；七个视频已浏览器加载，首组播放到结尾，质量字段仍为空。[页面检查](reports/f1_review_ui_check.json)。这是非盲工程审查入口，不是已完成的质量评价。其他设备取回并按回执校验七个视频后，运行 `python3 scripts/build_f1_review.py` 重新生成页面；视频和HTML留在忽略目录，不上传GitHub。

## 2026-09-30 执行范围纠正：人工评价不前置

用户指出当前不应再次转入人工语义判断。核对原计划：首批F1-SMOKE要求生成成功、输出规格、缓存命中、显存与时间；长程计划§4.4将标准质量指标与盲化人工对比列为最终质量评价，§6.3优先要求同状态误差诊断。此前把完整视频审查反复列作当前优先待办，是执行方提前扩大评价流程，并非首批要求用户完成标注。

F1技术范围已完成；可选视频查看不阻塞W1。继续已启动的一致性验收、残差/最终速度误差和成本测量。未来作质量主张时再开展对应标准评测和必要人工补充。保留质量等价尚未验证的证据边界，现有审查页仅为可选工具，不引入PhysCache式人工语义评审主线。

2026-09-30 实机恢复与W1-P0收尾：通过现有FRPC/SSH取得终态，7项官方路径单样本parity checks全通过；原进程已退出、锁可获取，产物重哈希匹配。累计1.245197206/4GPUh，余2.754802794h。本次没有新增GPU任务。已准备W1-S1同状态三近似器实验卡，需实现独立评分入口及新版本无扰动验收再提交。详见[W1-P0结果](research/12_W1_P0_TERMINAL_RESULTS.md)与[下一实验卡](research/13_W1_S1_PREPARATION.md)。

W1-S1实现准备完成：58项本地CPU检查通过；评分使用同一官方部署轨迹、strictly-past full anchors、与候选插入一致的官方warp；区分warp前后及最终速度误差。新增900s监督模式，尚未启动GPU任务。协议与实现见[实验卡](research/13_W1_S1_PREPARATION.md)和`manifests/w1_same_state_protocol.json`。

W1-S1 r1初始化失败，未生成：启动环境缺少HF_HUB_CACHE，默认offline缓存无Guardrail1 blocklist目录。监督耗时75.011195s/0.020836443GPUh已结算；当前累计1.266033649/4GPUh。已把项目hfhub路径固定到监督器，6项本地真实子进程测试确认缓存环境，准备核验旧进程/锁后运行不同身份r2。保留[失败回执](reports/w1_s1_r1_failure_summary.json)（research文档链接需从总文档访问）。

W1-S1 r2已启动：源7e5bc10、部署哈希匹配、Linux6项监督器检查通过，新鲜GPU1准入24MiB/no compute apps；supervisor2444752/timeout2444757/runner2444759实机存活，项目cache环境已核实，进入off生成。见[启动回执](reports/w1_s1_r2_launch_20260930.json)及[现场快照](reports/w1_s1_r2_start_observation.json)。本地摘要器与7项回执有效性检查不会部署到在跑任务。

W1-S1 r2收尾：8项真实诊断一致性验收通过；四点velocity sum-MSE比scalar2.531、shrink5.395，均只有较早2/4点改善，默认方法记NO_GAIN_IN_SCOPE，不进入闭环。下一步只有一项因果修订：decay0.9→0最近full-pair beta，固定其他变量；上限900s现有预算内。详见[首轮机制结果与修订依据](research/14_W1_S1_INITIAL_RESULTS.md)。

单次recent修订已启动：源99f554f，16local/16Linux针对性检查通过，部署哈希匹配；旧PIDs缺失/锁可获取后重新准入GPU1，supervisor2447006/timeout2447012/runner2447014核实存活。官方off生成中，结果尚未得出，见[启动](reports/w1_s1_recent_r1_launch_20260930.json)。

最近pair修订已终态，仍NO_GAIN_IN_SCOPE：velocity sum-MSE比2.354，shrink控制5.395；各自off/on不变性通过。跨任务模型72output/cache/控制数值完全相同，但MP4及93帧decodedRGB不同，首个差异阶段未知，不作质量归因。详见[修订结果与复现问题](research/15_W1_S1_RECENT_RESULTS.md)和[下一阶段见证卡](research/16_POST_MODEL_REPRODUCTION_GATE.md)。

## 最新核验 — 2026-09-30 22:48：CAL8 W1-D运行，2/8技术通过

源`62f1c0d03ab7d789a7e5a86235e2d27cf920825c`，部署archive/源码hash一致，Linux44项CPU检查通过。已真实启动`outputs/w1d-cal8-r1`，GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704；supervisor2461004、timeout/PGID2461009、runner2461011 live。22:48只读观察：前两个AV/common样本各8点、四pair完整、ACCEPTED、17项OFF/ON检查全真；第三个human_199 OFF在跑。各样本点先按OFF trace冻结，truth只评分，局部decode flags恢复。此为非终态快照，不是全批成功。

本批一次加载8off/on，上限6000秒/1.666667GPUh，所有成本从原4h cap扣除。启动前已结算1.9977743149465987h，观察时在途另计0.32540379007657366h；旧ledger余额未包含在途，不能用来准入新任务。仍只有此昂贵任务；原FRPC/SSH可用，无需重新建隧道或索取凭证。勿修改部署源码、重启或另起作业。

证据：[部署](reports/w1d_cal8_r1_deployment_20260930.json)、[启动](reports/w1d_cal8_r1_launch_20260930.json)、[进程/GPU/日志](reports/w1d_cal8_r1_live_observation.json)、[真实runner部分快照](reports/w1d_cal8_r1_live_runner_snapshot.json)、[部分汇总](reports/w1d_cal8_r1_live_partial_summary.json)、[协议/进展](research/20_CAL_AND_W1D_PREPARATION.md)。部分scalar等样本velocity/postwarp误差比0.666140/0.820278；shrink1.132306/1.057422，无fallback。LIVE_PARTIAL_NO_DECISION：不据前两样本调公式、判全批成败或进入候选闭环，无质量/干净加速/独立确认结论。旧四工程点NO_GAIN_IN_SCOPE仍是旧范围，不向CAL扩张。

下一步：只读查原handles直至终态；原PIDs退出与锁释放、GPU监控归属/源码/视频哈希核验后归档runner/supervisor/audit及实际wall账本。完整8PAIR_PARITY_PASS才按固定screen汇总；部分/失败保留，不能补样本或重启凑全。随后按机制证据与实际余额自主推进；预算扩张/训练/重大方向决策再交用户。当前无需人评/训练/付费评分。Git只同步代码/小回执/文档；后续本地文档commit不改变此源62f1c0d运行身份。

## 最新接续 — 2026-09-30 23:09：5/8技术通过，分布分析就绪

原w1d-cal8-r1任务持续运行；supervisor2461004/timeout2461009/runner2461011均live，source62f1c0d保持。前5个样本各8诊断点、17项OFF/ON检查全真；第6个physics_045 OFF生成。当前[实时进程/GPU快照](reports/w1d_cal8_r1_live_observation.json)更新；22:48的runner/partial summary文件仍只归档前2样本，不是最新/终态。启动前结算1.997774315h，23:09在途0.668417069h额外，batch6000秒/原总4h cap不变，无第二任务。

已完成只读分布分析src/wcomr/w1d_analysis.py与CLI scripts/analyze_w1d_cal.py，严格校验每个分区非空/不重叠/完整覆盖、候选坐标匹配、group MSE与reference energy能重建整体值；按样本等权汇总，零官方误差比留空。scripts/plot_w1d_cal.py输出同状态散点/排序反转计数/velocity时间空间通道图，显示dependent/latent坐标范围，不把组当独立样本。11项针对性CPU检查通过，真实部分回执CLI与私有部分图检查通过；[CPU回执](reports/w1d_analysis_cpu_20260930.json)。仅本地代码，未部署到正在跑的job，无新科学结论或额外GPU成本。

终态归档/审计后执行原screen与新descriptive analysis；plot依赖可用pip install -e '.[analysis]'安装到本地环境。所有partial显式NO_DECISION。接续原PIDs，不重启/改公式/增加样本。没有重要问题时按协议自行收尾和评估下一有界任务。

## 以下为历史快照

## 最新接续 — 2026-09-30：CAL8终态，scalar机制信号，固定重放准备

w1d-cal8-r1（部署源62f1c0d）完整终态：8/8场景、每样本8点/17项OFF-ON检查全真；16接受视频重新hash匹配，原supervisor2461004/timeout2461009/runner2461011均退出，exit0/无stop reason，锁可用、GPU1 24MiB/noapps，699监控点无观察到其他compute。原始runner/supervisor/audit/summary/analysis/figure已归档reports/w1d_cal8_r1_*；旧live与partial文件都是历史，不得重启旧任务。

冻结screen MECHANISM_ONLY_CAL8：scalar7/8联合velocity/postwarp改善，等样本均值比0.759184683/0.893679139，0fallback；misc两指标恶化保留。shrink0/8 velocity改善，均值1.306201721，本CAL8收缩线不送闭环。8样本皆有内部排序反转，共40 dependent point-mode对比；组上scalar均7/8改善，暂不加W2。没有视频质量/干净速度/独立确认正结果。旧AV四工程点负结果保留原范围；CAL是开发数据。详细[结果](research/21_W1D_CAL8_RESULTS.md)。

本批监督3590.173902秒/0.997270528h，累计2.995044843355815/4h，余1.004955156644185h，无在途成本。下一固定schedule scalar-recent闭环最多3000秒/0.833333h，仍原budget内。CPU模块fixed_replay.py及24项针对性检查通过，协议已冻结完整8原trace/hash/参数；[准备卡](research/22_W1_REPLAY_PREPARATION.md)、[manifest](manifests/w1_fixed_replay_protocol.json)、[CPU回执](reports/w1_fixed_replay_cpu_20260930.json)。runner/监督模式尚未实现、未Linux部署、未CUDA/生成测试，不能称候选已经跑过。

下一步自主实现有监督runner：firstAV新official fixed replay对旧OFF严格复现，再scalar OFF/ON自身parity，通过后原其余7scalar OFF；共10generation，firstcandidateOFF计入8成员。自己当前latent/probe/full anchors，shadow truth只评分，不回放旧latent。不择优/替换misc；拒绝保留，技术异常停止。预算forecast2224.619秒+30%=2892.004秒，cap3000；提交前重新核验旧handles/锁/余额/GPU/source/hash/LinuxCPU。尚无第二任务/额外预算/训练/付费评分/人评。代码与docs推送后的新HEAD不改变旧source62运行身份。

## 以下为历史快照

## 最新接续 — 2026-10-01：fixed replay runner本地实现/CPU通过，待部署

原CAL8终态、scalar MECHANISM_ONLY和预算2.995044843/4h保持。已实现scripts/run_w1_replay.py、supervise_f1.py --w1-replay（单batch cap3000秒），以及replay_results/video_difference/summary CLI。19项本地针对性CPU检查通过；[回执](reports/w1_replay_local_cpu_20261001.json)。与旧CPU模块24项范围有重叠，不叠加计数。原manifest固定参数/样本/trace/reference hash未改；metadata初始NOT_IMPLEMENTED标签是冻结时历史，当前以此快照和后续运行回执为准。

runner先hash绑定完整CAL8/reference screen并重新计算screen、校验setup/input/runtime/scheduler/VAE；首AV official replay严格复现旧OFF，scalar OFF/ON output/cache/decoder/video及额外calibrator结束状态和controller记录一致，ON真值只评分。余7仅scalar OFF；每sample用自身状态，有限模型输出/固定独立blockcounts/实际controller past anchors/peak memory记录，完整93RGB对旧WC距离与temporal variation描述（非质量）。拒绝/异常保留；SIGTERM尽可能写TECH_BLOCKED，所有真实墙钟计费。无新GPU运行。

下一步：commit/hash部署并Linux CPU gates；重新核验旧PIDs/锁/预算、全部reference视频hash、GPU1 UUID/VRAM/apps，只启动新唯一outputs/w1-replay-r1一次。前门失败立即停止，不能据观察超时重复提交或改在跑代码。上限3000从余1.004955157h扣除，无扩额/训练/付费/人评。部署与launch receipt/PIDs/logs、总体docs和预算需同步GitHub。

## 以下为历史快照

2026-10-01 输入对照终态：原8/126、repeat完全一致/blank与cyclic各14变化，全hash/raw与成本审计通过；累计3.6512467238638138/4h。现有方法仍机制only/代理无收益；下一窗口具体成本方案待决定，未新GPU。见[控制结果](research/30_W1_VQA_INPUT_CONTROLS_RESULTS.md)和[成本方案](research/31_W1_NEXT_WINDOW_COST_AND_DECISION.md)。

2026-10-01 clean计时CPU准备：原8×2×3/48计时+2预热顺序冻结，runner/summarizer/14400秒监督实现，本地Linux48CPU、真实validate-only和未批准预算拒绝通过；主runtime/账本未变、新GPU未提交。见[准备卡](research/32_W1_CLEAN_TIMING_CPU_PREPARATION.md)。

2026-10-01 L0资源核验：Wan5B base资产11hash通过、native3文件/官方来源和两个公开LoRA release锁定，header结构及16CPU通过；无完整LoRA payload/真实融合/GPU，OMR公开资源未发布。GPU账本未变。

2026-10-01 L0 CPU获取live：两套锁定适配器匿名官方下载、source68afc3e/3600秒，同3PIDs真实live、CFG70MiB partial，未全SHA/融合/模型前向。主GPU账本不变，拥有的临时forward终态再关闭，未改变共享路线。

最新资源终态：[r3最后range失败与r4恢复](research/37_L0_RANGE_R3_TERMINAL_AND_R4_RECOVERY.md)。L0 range-r3/sourcebd8253d已exit1/1216.976277秒终态；最后range三次URLError，已提交43个16MiB chunk，保留1277165568字节（1218MiB），仍缺12658832字节。CFG4文件/两few-step JSON官方digest PASS，few-step模型MISSING；原3PIDs退出/CPU锁释放/source与协议一致/账本不变，完整审计后仅关闭本任务owned r3转发。下一新唯一r4从保留prefix续传，同官方revision/16MiB/3600秒上限；未新GPU、未完整few-step hash/真实融合。
