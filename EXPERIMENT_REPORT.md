# WorldCache / OMR 实验文档与跨设备接续入口

更新日期：2026-09-30（北京时间）；文档版本：v1.0；实验计划版本：v1.1。

本项目研究视频世界模型的质量—时间折中：以 Cosmos-Predict2.5 上的 WorldCache 低开销改进为当前主线，OMR 物理纠正为条件候选。本文是持续更新的实验总览，固定使用此文件名；具体参数、原始回执和完整计划通过相对链接引用，适用于任何设备上的仓库副本。

结构参考既有 `physcache_full_experiment_report.md` 的背景、假设、实验演进、结果和下一步组织方式。仅借鉴文档结构，不继承 PhysCache 的结论、样本、预算或执行权限。

## 1. 当前结论与最重要的下一步

**F1 r3已完成两臂全部尝试，三组双方接受样本的端到端耗时比为1.476–1.602×。这证明当前配置下官方WorldCache有技术加速，但尚无质量等价或新方法正结果。继续WorldCache主线。** W1-P0 官方路径单样本诊断开关一致性已通过；候选改进仍待测。

| 项目 | 最新已归档证据 |
|---|---|
| 当前阶段 | F1技术计量完成；W1-P0官方单样本诊断一致性通过；W1-S1已实现并通过58项CPU测试，实机验收待执行 |
| 最近运行 | W1-P0 r1已exit0，7项checks通过；接续检查无项目运行进程、监督锁可获取 |
| 首要动作 | 部署W1-S1官方同状态三近似器评分，完成新版本实机无扰动验收；不等待人工语义标注 |
| 当前成本 | 已结算1.266033649/4GPUh；剩余2.733966351GPUh，无本项目在途GPU任务；W1-S1 r1初始化失败已结算 |
| 方法证据 | CPU/合成测试与资源就绪，不等于生成质量或真实加速收益 |
| 视频评价 | 已有格式检查；完整视频质量审查尚未完成 |
| 运行状态时效 | 本表来自仓库内终态回执；接续时必须查远端进程、锁、日志及预算，不能把文档当实时 GPU 状态 |

依据：[F1 r3配对汇总](reports/f1_smoke_r3_summary.json)、[W1-P0终态结果](research/12_W1_P0_TERMINAL_RESULTS.md)、[实时恢复审计](reports/w1_p0_r1_recovery_audit.json)、[预算账本](reports/budget.json)。

## 2. 研究背景、假设与判定方式

目标是在相同质量下更快，或在相同时间下质量更好。比较对象应包含合理调参的官方缓存与原生少步采样，避免只超过一个默认配置。研究成功需落在端到端质量—时间曲线上，特征误差降低只作机制证据。

| 假设 | 预期验证 | 当前状态 / 否定条件 |
|---|---|---|
| H-W1：简单收缩或浅深层增量校准能改善跨步残差近似 | 同状态 shadow → 固定跳步闭环 → 自由调度下的质量—时间对照 | 待真实模型测试；优于合成数据不算成立，额外计算抵消收益则停止深化 |
| H-W1D：残差误差大小不能完全代表下游危害 | 对照残差 MSE、最终速度预测误差/方向与局部伪影 | 待测；无重复排序差异则不增加敏感性模型复杂度 |
| H-J：减少不必要的 OMR 纠正调用/梯度可改善折中 | 先复现有效原版，再测稀疏、未来侧梯度与复用 | 资源与兼容性待复核；原版无效或 adapter 不匹配时不做归因 |
| H-L：预训练 CFG / 少步适配器是值得纳入的强基线 | 同一兼容 Wan5B 上原生、CFG-only、四步 Few-step+CFG 三臂 | 尚未做本地兼容性和 GPU 测试；小批次仅筛查可用性 |

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

1. F1 r3和W1-P0均已结束，不从旧RUNNING快照重启；每次提交前重新核验进程、锁、远端账本和GPU准入。
2. 依[W1-S1准备卡](research/13_W1_S1_PREPARATION.md)实现官方同状态三近似器诊断，保存真实anchor和fallback，当前truth只评分。准备卡尚不是已完成runner。
3. 针对新实现验收输出/缓存/trace不变及无真值回写后，按现有余额开展一个至多900秒/0.25GPUh工程任务。诊断开销全部计入预算。
4. 机制信号出现后再进入候选专用parity、固定schedule闭环及独立CAL/DEV和F2；工程样本不作独立确认。人工语义标注不作为进入W1的门槛。
5. L0可穿插资源核对；L1/Wan/OMR等待主线预算与兼容性。无新训练、付费评分或预算扩张。

遇到关键协议更换、扩大预算、训练立项或方向切换时留给用户决策。一般工程修复可继续，但不得中途改变在跑任务的源码/配置。操作顺序以[下一步队列](research/09_NEXT_ACTIONS.md)为准。

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
