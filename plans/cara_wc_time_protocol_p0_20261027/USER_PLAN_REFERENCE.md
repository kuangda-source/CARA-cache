# CARA-Cache × WorldCache：双时间口径、最小关键基线桥接与最终确认计划

**日期：2026-10-27**  
**性质：研究与实验设计；供原 Codex 对话实现/登记。未执行 GPU、未变更仓库、未增加预算授权。**  
**证据基线：** WorldCache arXiv:2603.22286v1（尤其附录 0.B）；CARA 仓库研究 716（DEV128）、721（WC 口径审计）、722（延迟边界审计）。实施前由 Codex 复核最新 git commit、对应报告 SHA、中央账本和现有任务状态。本文不能取代已签署的实验合同。

## 0. 执行决策（一页摘要）

1. **后续正式论文同时报告两种真实时间。** `T_DD`：从实际去噪循环入口到 VAE 解码完成的同步墙钟时间，与 WorldCache PAI-Bench-G 附录的口径对齐；`T_request`：原 guarded 完整请求口径，是部署及既有 257.7712338712067 s 与 `0.8×fresh Native` 双预算验收的唯一依据。保留已有 `T_generate` 作为「含条件准备的生成函数时间」，不得改名 `T_DD`。
2. **先证同一执行路径的因果等价，再比 WC 的缓存策略。** 当前固定 UniPC/Karras 36 实际步下先比 Native 与 WC-wrapper 强制全 D；若不一致，不将旧 WC–Native 全部归因于缓存跳过。
3. **补对照按最小化但不弱化基线原则设计。** 同批至少 Native、wrapper-allD、WC-README-UniPC、WC-PaperParams-UniPC、WC-CalibrationMatched-UniPC、RA（固定可复现版本）和冻结 Shared25-C。WC 定义与参数必须精确绑定到原代码、实际执行参数和源版本；`PaperParams-UniPC` 不是 Euler35 论文精确复现。
4. 在四个**已曝光旧 CAL**上做开发/归因桥接，允许有限 WC 阈值选择；**16 个原最终确认提示词保持未见**。把冻结的 WC 与 CARA 一起送入最终16，不能看到最终结果再选择阈值。DEV128 仍是单独已完成的开发阶段冻结确认，不改变其统计结论与门槛。
5. **不估计不存在的数据。** 旧 Alex、重新逐帧评分的 PIQ/VGG、已验 `T_request`、`T_generate` 可分列；没有起止时间戳的旧 `T_DD` 标 N/A。不能以估计外围开销、少量映射系数或旧视频重算，推定 Euler35 的质量、官方 H200 延迟或 EgoDex GT 结果。

## 1. 双计时合同（新运行一律适用）

| 字段 | 起止边界 | 纳入 | 排除 |
|---|---|---|---|
| `T_DD`（正文算法横轴） | 真实去噪 solver 循环入口（首次去噪更新之前） → **实际 VAE decode 结束且同步完成** | 全部 D/C/A、CFG 两支、probe、调度/阈值、插值、warp、采样求解器、decode，以及该连续边界内部的正常开销 | 循环前文本/条件/初噪声准备、外层 guardrail、视频编码/写盘、模型加载、请求清理 |
| `T_request`（部署主口径） | 既有正式 guarded 请求边界 | 方法安装、guarded pipeline、生成、编码、写盘、清理等原合同组成项 | 模型首次加载、卡级实验调度与独立离线评价 |
| `T_generate`（辅助已知口径） | 原 `generate_vid2world` 入口/出口 | 包含条件准备、去噪与 decode | 不得当作 `T_DD` |
| `T_load`, `GPUh_job`, `GPUh_cal` | 单独计账 | 模型加载、warm、实验执行和评分所占真实 GPU 时间 | 不得加入单次正式推理平均制造延迟 |

**埋点要求：**
- 在真正循环入口做一次 `torch.cuda.synchronize(); t0=time.perf_counter()`，在解码返回后做 `torch.cuda.synchronize(); t1=time.perf_counter()`；不在每一步人为插入同步，防止改变推理行为。需要时将 CPU 同步引入的共同扰动用 A/B 检查，并保存原子级位置/调用栈证据。
- 若代码存在不连续多处解码、异步流或缓存执行到其它流，必须明确 `T_DD` 的排布、所有流完成条件，不能通过将 `T_denoise + T_decode` 两个非连续区间简单相加冒充连续墙钟。
- 时间字段统一 `float seconds`、同步 CUDA、`time.perf_counter()`；包含所有在线预测器和多头费用。CUDA Event 的 kernel 时间可以作为诊断，不代替完整墙钟。
- `T_request` 沿原代码及 guardrail 行为保持不变，不改安全/拒绝逻辑以追求加速。模型和执行入口同硬件、显卡 UUID、驱动/CUDA、精度、attention/backend、offload、模型 resident、热状态与频率 telemetry 同表登记。
- 每个请求写：`task, prompt_id, seed, checkpoint_sha, source_sha, exact_config_sha, scheduler/sigmas_hash, actual_solver_updates, actual_CFG_branches, WC_horizon, requested_steps, action_sequence_branch_c/u, D_count_c/u, T_DD, T_generate, T_request, T_load, warm/status, guardrail_status, output_video_sha, initial_noise_sha_if_available, denoise_start/end timestamps, decode_end_timestamp, GPU_model/UUID, dtype, runtime_context`。
- 重复正式计时：固定输入下至少两轮交错/平衡执行；**时间重复不是新科学样本**。所有 prompt 首轮计时，不能只对少数 prompt 测速后赋值给其它 prompt。

**现有数据禁止改判：** DEV128 已实测 `T_request Native=312.988 s, CARA=246.675 s`，对应 1.269×；`T_generate Native=281.193 s, CARA=214.010 s`，对应 1.314×。`T_DD` 未采集，必须 N/A。原双预算继续只用 `T_request`。

## 2. 比较空间与评价问题

统一评价主设置：Cosmos-Predict2.5-2B，432×768、93 帧、16 fps、T2W、固定模型快照、同一负面/正面提示词、guidance 与种子，UniPC/Karras 请求35步/实际36个 solver 更新、72 CFG 支路调用，A6000 同一卡完整 guarded pipeline。**所有参与主比较的方法共同采用同一 Native35，独立质量测量和输出采样网格。**

评价分层：
- **计算保真：** `LPIPS-Alex-v0.1(to Native)` 是延续主指标，逐93帧先平均再以 prompt 等权。`PIQ/VGG(to Native)` 同一解码视频精确重评分作为桥接列，不使用 Alex→VGG 拟合公式，不重新设置既有门槛。
- **独立质量：** 原 MUSIQ_LONGER512、subject consistency、motion smoothness 三项质量门；必要的 dynamic degree 与局部时序诊断解释效果，不将 LPIPS 同义为客观生成质量。
- **时间：** `T_DD` 用于公平算法推理主比较；`T_request` 同表标出并独立验收。速比始终同一批、同一硬件 `mean(T_native)/mean(T_method)`，不与作者 H200 数字直接混算。
- **缺失与拒绝：** 预注册全体作为意向分母；完整配对群用固定的方法集合形成交集，共同报告覆盖率/拒绝原因，不能只留下有利成功视频。拒绝不隐去，不臆造数值填零。

### 核心对照身份

| 角色 | 行为与目的 | 强制约束 |
|---|---|---|
| `NATIVE_U36` | 原生 Native 36 次 D | 基准。冻结初始噪声、权重、scheduler、backend。|
| `WC_WRAPPER_ALLD_U36` | WC 包装/注册入口仍执行每一更新全部 D | **首先检验与 NATIVE 等价**；仅控制不作为加速结果。|
| `WC_README_U36` | 历史公开代码 README 技术配置：tau/显著性/flow/ATS/70 horizon 等均绑定实际版本 | 名字不得称论文配置或官方默认；维持历史含义。|
| `WC_PAPER_PORT_U36` | 在当前 UniPC 上映射论文缓存参数（如 tau .08、saliency .12、flow .5、ATS 原论文期望值） | 每个参数必须审计真正触达实际代码；不能把强制ATS设常数却变更其它机制后声称 exact paper。**不是 Euler35。**|
| `WC_TUNED_U36` | 有限且预登记的阈值/费用匹配 WC | 仅旧 CAL 调参，**选一套共享阈值**，不逐 prompt 调、不能看最终16。|
| `RA_LOCAL_U36` | 已披露适配版本 RA-CFGCache | 固定可复现身份与限制；若执行器无法相同预算直接比较，报告真实时间曲线。|
| `CARA_SHARED25_C_U36` | 既有冻结 Shared25-C | **绝不为了新基线临时改变 CARA 的 D mask、读出、phase。**|

**附加但不阻断当前桥接：** `S25_A_PHASE` 是重要强简单对照，在 DEV128 和 CAL66 已有配对证据；未来最终16可作为正式一臂。`NATIVE26` 是改变 sampler 时间网格的速度对照（DEV128 已测），按两个不同参考目标报告，不作为 WC 的相同网格替代。正式跨模型/跨设置测试另建卡。

## 3. 先做有限 WC 参数校准，再冻结完整卡

**研发 CAL：** 旧 AV28、Human199、Misc、AV51（四组长期开发已曝光；不得作为论文最终 TEST）。优先从前两个 prompt 的现有 WC 阈值扫描中查看实际命令/seed/source，不能把旧跨卡绝对时间混进新卡主表。

建议的有限选择：
1. `WC_README_U36` 原样；`WC_PAPER_PORT_U36` 先完成 CPU 参数等效表（含 ATS、70/72 分支 horizon 的准确含义）；绝不直接套 35 更新参数表。
2. 在 **WC_PAPER_PORT-U36 的其它参数不变** 的前提下，冻结至多两个预选 `tau`（例如 .04、.06，需先审查真实阈值比例与可行范围），每个在**两旧 CAL**同卡跑一次，得到真实 `T_DD/T_request` 和 Alex LPIPS。
3. **顺序约束：**先在同两个 CAL 上获得 `CARA_SHARED25_C_U36` 的新 `T_DD`（和相容的 Native），然后跑两个预定 tau；绝不能拿旧 `T_generate`/跨卡时间与新 `T_DD` 混用。选 `WC_TUNED_U36`：优先选择在两个 CAL 上与冻结 CARA `T_DD` **相近（示例 ±5%，仅为预先冻结的匹配公差）** 的候选中 LPIPS 较低者。若没有匹配者，选择时间差最近者并如实报告“不完全时间匹配”，不从几个点插值构造虚假视频/指标。若既有阈值两候选不包围目标，报告有限网格覆盖不足，而非运行时无限扩大搜索。
4. 对两个 CAL 的未入选阈值也保留结果和搜索费用；已用历史数据调出 Shared，因此不能宣称 WC 的两次试验与 CARA 全部历史研发费用严格相同。比较时将两种算法的开发资源与测试资源分离陈述。
5. **重要：** 若 `WC_PAPER_PORT_U36` 在 CUDA/模型适配中无法保持论文参数的真实语义（例如 ATS 步号/CFG horizon 无法可证地映射），先登记 `UNSUPPORTED_PORT`；不能悄悄代入其它默认值再叫 `PAPER_PORT`。

## 4. 推荐实验卡：基础对照 7 角色 × 4 CAL＋有限校准与时间复测

**这是整卡范围设计范本；不是已授权正式执行清单。** 在最新账本/机器/存储状态下由 Codex 重新报价与冻结。

### 4.1 执行阶段、依赖与角色

- **阶段 A（入口等价门）：** 两旧 CAL × `NATIVE_U36`,`WC_WRAPPER_ALLD_U36`,`WC_README_U36` = **6 正式路径**，完整初噪声/输出/latent 核对。此 6 路径计入最终 CAL 正式分母，不在阶段 B 默认重跑。若 wrapper 全 D 无法与 Native 在冻结容差内相容，暂停“缓存导致全部偏差”归因和论文主表，先定位路径；历史证据仍保留。若出现文本/视频正常拒绝，按既定身份记录，不能替换提示词。
- **阶段 B（其余基本角色）：** 在前两 CAL 先补 CARA、PaperPort 等新时钟后完成上述阈值预选，冻结一个 `WC_TUNED` 身份，然后补齐原4 CAL ×七角色（Native、wrapper-allD、WC_README、WC_PAPER_PORT、WC_TUNED、RA、CARA）= **28 个目标基本正式单元**，其中阶段 A 的6单元只要身份/生产口径相同即可直接归入；其它22个单元补跑。所有七角色采用同一配对 prompt/seed 参考。
- **参数预选诊断：** 两个 `tau` 候选 ×两旧 CAL = **4 条试探**；所选的2条身份完全相同时可归入上述 WC_TUNED 的最初2单元，另外2条属于开发额外记录。**不同身份或代码路径不相同则不允许复用、须重新报价。**
- **完整预热：** 最多 8 条（Native、allD、README、Paper、tau1、tau2、RA、CARA 各1；若 warm 入口需要另行覆盖更多变化则改范围并报价）。同进程驻留模型，不能把预热当正式样本。正式值仍需记录首调用/顺序。
- **独立计时复测：** 两个固定旧 CAL × 六个角色（Native、README、Paper、Tuned、RA、CARA），均衡反序各一轮 = **12 条额外重复**。相同 seed 和身份重复要核对输出一致；不把重复作为新的质量样本。
- **总执行规划上界：** 基本28＋额外未入选tau2＋预热8＋复测12 = **50 条路径**。如额外数值诊断/负载测试需增加，必须在冻结完整范围时另计，不应执行中临时追加。`PAPER_PORT` 不可行时不按原名派发，可缩成有真实身份的较小版本。

**开销：** 以历史 240–315 s/正式视频估算，50 路径的纯请求时间约3.3–4.4 GPUh，再加模型加载、准备、真实持卡、保存、warm/重试边界和释放、评分CPU。建议将 **5–7 GPUh** 作为*整卡预报价规划区间*，不是到账成本或硬批准。若热状态/显存/Guardrail导致更高成本，按最新可复现生产预测器重报价，保护最终16和迁移预算。

### 4.2 不增加GPU即可开展的 P0

- 同步读取最新仓库：721/722/716、历史 FAIR `.04/.06/.08`、WC wrapper 安装和全D钩子、scheduler 真实 sigma 和 horizon 70→72 关系、确切配置键到代码有效路径。
- 将 `T_DD` 同步埋点接入原生产调用；通过合成小张量和 CPU 控制确认只新增时间记录，不改变数值、拒绝行为、缓存/solver/RNG 状态。GPU 验收时加入 Native 真实同输入输出和全D wrapper 的初噪声哈希、实际条件与视频一致性。
- 生成 `CONTROL_IDENTITY_MATRIX.yaml`、`TIME_BOUNDARY_TESTS.json`、`WC_PORT_PARAMS.md`、`PRICE_QUOTE.md`、`MISSINGNESS_PLAN.md`。初始字段中未知者保留 `null`，不得按口头推测填通过。
- 如果与此前提出的19D高速实验合卡，先做角色/视频输入 fingerprint 去重并把整卡费用重算；不要不经合同调整把19D塞入已冻卡。 

## 5. 完整配对结果与统计验收

1. **完整请求与严格去噪+解码时间分列：** `T_request`、`T_DD`、`T_generate` 在同一接受原件中存数值，不能只报告 `T_DD` 以隐藏额外 CPU/WC 探针开销。
2. 每视频所有93帧 Alex 计算；新视频单独完成 PIQ/VGG 重评分、同一输入的 MUSIQ_LONGER512/subject/motion 质量，`NATIVE` 自身 LPIPS=0。不能把所有样本聚合成“所有角色平均”然后声称个别方法更好。
3. 四个旧CAL属于研发样本，成对 prompt 效应只作为开发描述。严格协方差/置信区间留给冻结最终16；不要把每个 frame、重复和两个分支当科学独立样本。
4. 相对改善 `1 - mean(L_method)/mean(L_baseline)`（相同完整可比较队列），并提供逐 prompt 差、平均绝对差、方向；另可报告 mean-of-per-prompt-relative-improvements 但必须命名并固定，不与前者混用。
5. 速度 `mean(T_native)/mean(T_method)`，同一 prompt 的重复先聚合；分硬件报告，不跨 A6000/Ada 直接混合。TDD与Trequest各独立计算加速比。
6. 明确 WC 纸面参数 port 和 README 都不是完全论文 Euler35/EgoDex benchmark；图例不得把本地 `WC_PAPER_PORT_U36` 简写成 `WorldCache (Official)`。
7. WC 同等速度/同等保真主比较至少包含：WC_TUNED、WC_PAPER_PORT、WC_README、RA、Shared25-C。速度匹配不完整就报告实测 Pareto 点，不能虚构同费用性能。

## 6. 最终16独立确认：在这一轮方法/基线冻结后才启动

**时间/文件/费用应作为全新申请。** DEV128是早先冻结后的开发继续门，不是此次新WC参数搜索的独立测试。原最终16身份保留，不能拿任何其中途质量/时间更改 WC 阈值、CARA布局或归因解释。

建议主结果最小角色：Native35、WC_PAPER_PORT_U36（若通过）、WC_TUNED_U36、RA_LOCAL_U36、CARA_SHARED25_C_U36、`S25_A_PHASE`（强简单内部参照）。README如与 port 差异很大且资源足够，可成为附录角色。最小 **6角色×16 prompts×1 seed=96正式输出**，加独立warm与固定部分 prompt 均衡复测，按实际接受状态/预算另行报价；已有兼容 Native 原件可以按合同重用，但每种同批相对加速比须有有效计时参考。全D wrapper 在 CAL 已通过身份控制后，可仅在最终2组做生产回归 sentinel，不必16组全部重做。

冻结前明确：正式主表一次性列出单独 `T_DD`、`T_request`、LPIPS Alex、PIQ/VGG 与独立质量守卫；主指标对齐的固定新输入共享队列；reject/missing 注册与置信区间计算；随机 seed 的 prompt 聚类重采样，不将重复视为新 n。预留 seed>0 的确认可根据余额另卡登记，不在主要结果出现后为好看的 prompt 定向增加 seed。

**注意：** 主表 WC_TUNED 是在旧CAL上得到的开发强基线，而 CARA Shared25-C 在历史CAL上经多轮开发。这是合理开发过程，但后续需以同一未见最终集公平验证；不宣称双方开发搜索支出完全相同。

## 7. Euler35／EgoDex／第二骨干：下一阶段，不与本次混合

只有想要声称“本文比 WorldCache 论文设定的最优官方实现更好”时，才需要分别恢复其 35-step Euler、实际 sigma 网格、相关参数/benchmark、硬件、GT评分和计时口径。**重新实现 Euler 后，Shared 原36步掩码不能按索引直接复用**：要用预登记通用策略生成/重校准，且采用 Native-Euler 作为对应计算参考；不得把不同 Native 的 LPIPS 直接当配对结果。

Q5 同一 Cosmos 换步数和第二骨干迁移也非常重要：它们验证能否通过同一生成流程获得不同设置下的刷新布局。它们与 Euler35 可以互补，但不合并成一次未控变量的大实验。P1 完成后优先级重新按照科学收益和余量评估。

## 8. 结果分支与停止条件

| 现象 | 处置 |
|---|---|
| wrapper全D ≠ Native | 停止“缓存跳过导致全部偏移”的因果结论，定位执行状态/初始化/后端；不据此废弃CARAvsS25强布局结果。|
| WC 调严后达到 Shared 同速同保真 | 不能再把旧激进 README 工作点作为主要优势；保留布局结果，研究明确差别（跨设置、端点、自动分配）。|
| WC 调严仍同速更差 | 优先将 Shared 的等速度优势在最终16确认；原“有价值的布局机制”故事增强。|
| WC 在更快速度时LPIPS较高、CARA更准但更慢 | 只能称不同 Pareto 工作点，不能声称严格支配。 |
| WC_PAPER_PORT语义不可审计 | 报告版本不支持，必须改名或不作为主对照；Euler 论文复现独立设计。 |
| 新严格TDD埋点与原数值不等价 | 修复时钟定位与执行器隔离；不得把旧`T_generate`替代为 TDD。|
| 预算不够覆盖所有开发角色 | 保 Native、allD、WC_TUNED、CARA；其余按重要性缩减；保原最终确认预算优先。 |

## 9. Codex 接续指令（可直接复制）

> 请在原 CARA-cache 对话中继续，不修改已完成 DEV128、IG、CAL66、721/722 的原件和统计结论。先核对当前 `main`/全部引用 SHA、中央账本、现存 GPU 任务与相关工程入口；读取本方案后输出 P0 的配置映射清单、时间边界埋点设计、三臂 fullD 等价 CPU/实际 GPU 最小验证、最小 CAL 开发卡预注册、所有方法完整费用/评分/热环境界。先准备和测试 CPU，不据此启动 GPU。当前主论文在新批次并列记录 `T_DD`（WorldCache 论文边界）与原 `T_request`，保留 `T_generate` 原辅助口径；绝不重算改判既有门槛。发展样本为四旧 CAL，选定 WC 单套参数后冻结，原最终16只做冻结确认。不得在最终16重调 WC 或 CARA。禁止把UniPC PaperParams映射当作论文Euler35精确复现，不以估算填历史 `T_DD`。所有本轮耗时、CUDA/CPU、质量模型与真实资源报价须单次汇总，符合已有 GPU 权限合同后才可申请执行。若主线高速19D探索正在准备，请同源/身份去重并单独改完整范围，不擅自附加。完成 P0 后交付增量文件而不是覆盖原合同。

## 10. 来源链接

- WorldCache arXiv 2603.22286v1：https://arxiv.org/html/2603.22286v1，附录 0.A/0.B。
- CARA 716：https://github.com/kuangda-source/CARA-cache/blob/main/research/716_CARA_DEV128_COMPLETE_ACCEPTANCE_AND_FROZEN_DECISION_20261027.md
- CARA 721：https://github.com/kuangda-source/CARA-cache/blob/main/research/721_WC_NATIVE_LPIPS_OFFICIAL_PROTOCOL_FORENSIC_AUDIT_20261027.md
- CARA 722：https://github.com/kuangda-source/CARA-cache/blob/main/research/722_CARA_PAPER_LATENCY_BOUNDARY_AUDIT_AND_MINIMAL_MEASUREMENT_PLAN_20261027.md

