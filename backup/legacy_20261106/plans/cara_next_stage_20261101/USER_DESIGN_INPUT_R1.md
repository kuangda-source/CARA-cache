# CARA-Cache 下一阶段实验与 Codex 交接方案

> **版本**：Draft R1 · 2026-11-01（Asia/Shanghai）  
> **用途**：交给原 Codex 作为科研执行与工程准备入口。**本文件是设计与交接，不是新 GPU 任务授权，也不修改任何既有冻结合同。**  
> **仓库**：`kuangda-source/CARA-cache`；本次读取的 `main` HEAD：`4c2735d1122c6cada6f39352196e2c396959faf0`。执行前重新获取 HEAD、账本和原任务句柄；本文件中的状态、额度均为快照。  
> **用户材料**：`815_CARA_RECENT_EXPERIMENTS_OPUS_REVIEW_20261031.md`（2026-11-01增补），以及其引用的研究715–817、Opus独立评审和双方关于 UniPC/Euler 的讨论。  
> **主目标**：在既定 Cosmos-2B 模型中形成有真实终点优势、可预算化生成的缓存刷新规则；在 UniPC 主协议建立核心方法后，以 Euler35 验证可迁移性并对齐 WorldCache 论文协议。保持 S/Q 作为独立候选，不让尚未证明的方法阻塞已验结果。

---

## 0. 给 Codex 的首要操作规则

1. **先同步事实，后准备代码**。阅读仓库 `AGENTS.md`、`research/02_CURRENT_STATE.md`、`research/09_NEXT_ACTIONS.md`、`plans/QUESTION_QUEUE.md`、`plans/cara_next_stage_20261028/WORKSTREAMS.json`、`research/815_CARA_RECENT_EXPERIMENTS_OPUS_REVIEW_20261031.md`、`research/817_CARA_BUDGET_SEARCH_COMPLETE_ACCEPTANCE_AND_FROZEN_WINNER_20261101.md`，并核对所有最新接受回执。旧文章、旧handoff中的“正在运行”不覆盖更晚的终态。
2. **当前仅使用两卡 RTX A6000 服务器**：四卡 RTX 6000 Ada 正在维护，遵守 `plans/cara_next_stage_20261028/mainline/r2/TWO_CARD_ONLY_HARDWARE_MAINTENANCE_20261031.json`；不得因旧AGENTS中“优先四卡”描述而探测、拷贝或派发维护主机。
3. **不得重跑已完成的 A32、B36、S真实采集、Q1 和 BudgetSearch112/51**；优先复用接受的RGB、manifest、SHA、评分及冻结mask。旧GPU失败、未过门、结算原件保留。
4. **本轮仅授权设计、资产清点、受影响路径代码与必要 CPU 验证、真实整卡报价**。不要依此文派 GPU；>4 GPUh 的新卡必须单独说明目的并取得用户批准（遵守当前更严格合同），且每次派发都要fresh设备独占、真实温控、账本与磁盘准入。低于阈值仍遵从仓库实际授权政策，不将本文件视为批准。
5. 不动原模型 checkpoint、原prompt/seed/CFG、已冻结 S/Q/搜索赢家、Native参考、旧质量门或原 `T_request` 部署限制。提出新的评价协议要**前瞻登记**，不得“改写”历史验收结果。
6. 一次只推进**一条有辨识力的 GPU 科学问题**。不要把新EULER适配、预算族生成器、Q-END、第二骨干和新预测器塞进同一卡。
7. 核心 scientific claim 与 engineering acceptance 严格分开；生产CPU控制只证明执行接口，不证明真实视频质量、真实吞吐或新颖性。

## 1. 已成立的证据和尚未成立的说法

### 1.1 已接受结果（严格按原批次和原参考使用）

| 证据 | 结果 | 可以支持什么 | 不能支持什么 |
|---|---|---|---|
| DEV128 / Shared25-C | 16新DEV；对S25-C参考LPIPS相对下降26.16%，16/16同向；原完整请求约1.269× | 相同25D预算下刷新布局有重要作用，高保真配置经新输入开发检验 | 自动生成算法已被证明、论文严格`T_DD`已有历史实测 |
| B36 / Shared25-C | UniPC、四旧CAL：`T_DD=185.806s`，1.361×，LPIPS 0.062266 | 当前统一论文时间下的高保真端 | 与历史DEV128 `T_request` 直接池化 |
| B36 / F19-C | `T_DD=148.448s`，1.703×，`T_request` 1.486×，LPIPS 0.249365 | 19D高速可行；相对同19D Uniform 0.468931，失真低46.82%、4/4同向 | 已达到LPIPS约0.10的原Fast研发目标；F19是自动方法 |
| B36 / F19-A1 | `T_DD=149.482s`，1.691×，LPIPS 0.231499，较F19-C低7.16% | 作为强读出对照，有轻度统计改善 | 已得到明确人类可见改善 |
| A32 | WC_T006、RA_T1已冻结但均比目标更快、记`UNMATCHED`；Native22匹配 | 可画不同速度—保真点 | 同延迟WC/RA全面被当前方法击败 |
| S真实采集 | 2 FIT×2父轨迹×27目标=108同状态标签，已结算3.039352411GPUh | 真实分支误差矩可供风险实验 | S生成的完整视频已经更优 |
| S在F19起点 | BR、DIAG、CFG均选 D21→D35 | 起点上的最终mask同一身份，必须去重 | 该起点可以分离CFG交叉项价值 |
| S在Uniform起点 | BR/DIAG选D22→D35；CFG选D25→D35 | 具备独立检验交叉项的不同执行策略 | 胜负已知；从Shared/F19父轨迹推到Uniform后仍可靠 |
| BudgetSearch19 | 51查询/112条完整接受，7.197644817GPUh；FIT RGB MSE由0.0427533降至0.0241206（-43.58%） | 强端点搜索基线已可直接使用 | 新CHECK、LPIPS或相同部署延迟已赢；搜索已收敛 |
| Q1 | 12状态真实读出，0.298756494 GPUh结算，codec bit方向有部分差异 | 同字节编码可在独立线继续 | 完整视频、峰值显存或速度有提升 |

**读入后必须核查冻结赢家**：

```text
BudgetSearch19 D = 1,2,3,4,5,6,7,10,12,14,16,17,18,20,22,24,25,32,36
冻结文件SHA256 = f1e0b08b9dc31fd9cd3c02a80b01cbb874e9348003ec6aad3a5aa9f82d848c86
```

注：上列冻结SHA是**冻结文件**的登记身份，不要误当作mask指纹。实际mask指纹和源SHA以817原件为准。

### 1.2 现在尚未被证明的核心主张

- S在相同19D、相同真实成本下优于DIAG/BR以及F19-A1与端点搜索。
- S可摆脱父轨迹分布／初始化依赖，形成跨预算的确定性生成规则。
- BudgetSearch19在旧CAL_CHECK和独立TEST上泛化，且RGB MSE搜索目标与Alex LPIPS方向一致。
- 当前方法在Euler35下仍表现相似，或WorldCache论文参数在本地Euler35上有相同数值。
- Q的压缩降低整体峰值显存或单请求延迟。

**论文中绝不将上述“待证实”写成已完成结论。**

## 2. 主计时与实验身份：未来一律双时钟

### 2.1 主论文口径

- `T_DD`：**去噪循环即将开始前CUDA同步并读取墙钟；最后VAE解码完成后CUDA同步并读取墙钟**，连续区间包含模型前向、probe、cache判断/重放、warp/head、求解器更新、必要同步及解码。它是WorldCache论文附录0.B的论文比较口径。**不要把`T_DD`理解成仅D动作耗时**。
- `T_request`：已有驻留模型的完整请求流程，包含条件准备、guardrail、编码/写盘及算法实际请求开销；作为部署并列指标，原完整请求的旧双预算限制保留。
- 模型加载、预热、离线标定、额外shadow、诊断复制/哈希、GPUh账单另报。**诊断ON产生的时间不能称部署延迟**。
- 相同输入/seed先在请求内平均原注册重复，再按**prompt等权**求均时；speedup定义为同批Native均时/方法均时；帧、repeat、影子状态均不是独立prompt。
- 禁止将`core_seconds`（含条件准备）重命名为`T_DD`，禁止拿旧完整请求1.269×推算Euler或严格去噪计时。

### 2.2 严格协议身份

每次样本至少登记：`model/checkpoint_sha、代码commit、prompt/input_SHA、negative_prompt、seed、CFG映射、solver类/阶数/校正设置、sigma时间网格完整数组及SHA、请求步数/实际更新数、双CFG调用次数、WC horizon/reset、缓存/warp/阈值配置、精度、动作mask/来源策略、两时钟、GPU UUID/温度/功耗、输出/解码SHA`。

**主UniPC基线**：Cosmos-Predict2.5-2B、T2W、768×432、93帧/16fps、请求35、UniPC/Karras实际36更新与72次CFG分支调用，当前合成`v_g=8v_c-7v_u`（请求guidance=7）。WC本地`horizon=70`，可能存在末端重置交互，必须保留身份并在每种方法中一致。

**Euler协议**：不是把`requested_steps`改为35就完成。需重新定义实际Euler网络调用数、完整sigma/时间网格、历史缓存年龄及结束规则、CFG调用顺序和WC重置机制；严格记录新的Native参考。

## 3. 阶段P0：先完成UniPC现有端点证据，确定是否存在可用的S增量

> 优先级：**最高**。原方案`research/801...`为6个逻辑角色/32条物理路径；Opus建议增加F19起点真实交换，形成7个逻辑角色。此卡决定下一步算法、不要被Euler适配阻塞。

### 3.1 固定的科学角色（4个旧CAL×7角色=28逻辑评价位置）

| ID | 方法 | 来源 | 核心辨识 |
|---|---|---|---|
| E1-0 | F19-C | B36原冻结结果（复用） | 同配额强手工结构 |
| E1-1 | Uniform19-C | B36原冻结结果（复用） | 简单结构基线 |
| E1-2 | F19-A1 | B36原冻结结果；另做同批重放/时间 | 高质量强简单读出 |
| E1-3 | Uniform-S-DIAG19-C | **新正式视频**，D22→D35 | 不使用CFG交叉项 |
| E1-4 | Uniform-S-CFG19-C | **新正式视频**，D25→D35 | CFG交叉项是否改变真实终点 |
| E1-5 | BudgetSearch19-C | **新正式视频**，按817冻结mask | 使用完整视频端点的搜索近邻 |
| E1-6 | F19-RiskSwap-C | **新正式视频**，D21→D35 | 局部风险建议是否改善F19强布局 |

**身份约束**：BR与DIAG在Uniform起点生成同一mask，物理只执行一次；F19起点的BR/DIAG/CFG生成同一mask，物理只执行一次。E1-6不能算成“CFG相对DIAG获胜”证据。

**不得更改**：原F19、Uniform、F19-A1冻结身份；E1-3/E1-4/E1-6的初始布局、唯一交换及来源；BudgetSearch winner来自原51次查询，**不得看到CHECK LPIPS后改选赢家**。

### 3.2 完整物理卡的两种候选scope（必须二选一冻结）

**A. 最小七角色端点卡：39条**

| 物理路径类别 | 数量 |
|---|---:|
| 四种新增角色 × 四旧CAL | 16 |
| Native35、F19-A1 × 四旧CAL（同批时钟与RGB复现） | 8 |
| 四新增角色 × 两CHECK的计时重复 | 8 |
| Native35、F19-A1、四新增角色各1 warm | 6 |
| allD真实性控制 | 1 |
| **合计** | **39** |

原F19-C、Uniform19-C的四CAL质量结果复用（前提是原SHA/模型/精度/seed/解码完全一致），但**不可把B36 F19-C的旧时间与这张卡直接当作同批严格时间比较**；净速度关系只能标旧批参照，或选scope B。

**B. 若要求与F19-C也有严格同批时延：46条**

在scope A上额外注册F19-C的`4正式＋2个CHECK计时重复＋1warm`共7条，合计46条。不要原卡执行后临时追加；**先由Codex将科学需求、成本和余量报用户确定**。其原质量与RGB可按身份复用，新增时间实测独立登记。若A/B范围有重复控制，先在完整scope设计中确定去重，不在运行中手工删除。

**现有32条草案**报价约4.556914 GPUh、建议硬限5.25，是历史32条的报价，**不能作为39/46条新卡的硬限**。必须以两卡实际单路径预估、模型加载、warm、控制、保存/释放、CPU评分、温度与15%左右适当缓冲重新给出全额报价；任何>4 GPUh卡需要独立用户批准。原32卡未启动且`whole32_CPU_accepted=false`。

### 3.3 E1最小工程验收（不重造审计系统）

- 核对冻结文件和计算代码：所有mask 19D、保护点有效、年龄语义、相同CFG与求解器、F19-RiskSwap真实交换且不等价于已有角色；旧模型/输入/评分SHA。
- 用**原有已接受**的加载、评分、财务、独占、恢复、拒绝与资源控制；对新增四种固定动作路由做受影响范围生产CPU；只补**一次完整整卡组合CPU**，不因为新增一个mask就重跑旧114条微型路径。
- Native ON/OFF、wrapper-allD与Native逐步/最终控制；对复用的旧Native/F19-A1 RGB做绑定SHA或明确拒绝复用；不能从失败的对照生成伪科学样本。
- 首先检查磁盘与GPU高温风险：此前Ada曾90℃热停，当前仅两卡在用；不改他人GPU进程、时钟、风扇、温度保护线。失控停止并保留账单和失败分母，不自动重派。
- 终态后分开报告：工程接受、GPUh、`T_DD/T_request`、每prompt全93帧LPIPS/PSNR/SSIM/参考时序诊断、旧CAL_FIT与旧CAL_CHECK结果。旧CHECK不是独立最终TEST。

### 3.4 E1的预注册对比与分支判断

1. 主机制：`Uniform-S-CFG19` 对 `Uniform-S-DIAG19`，固定同D和实际近时间。查看差异符号、两CHECK及四CAL等权均值、最差输入、时钟；约5%相对LPIPS或0.002绝对差可作**研发实用尺度**，不是把旧合同门槛事后修改。
2. 局部→终点：`F19-RiskSwap` 对 `F19-C`，是否如局部风险预测更保真；若退化，记为F19父状态局部评分不能保证终点交换价值，不扩大成D21永远重要。
3. 竞争：S-CFG、BudgetSearch19 对 F19-A1、F19-C、Uniform；同预算部署质量+时间一并比，不能只胜DIAG就自称新的竞争性主方法。
4. 搜索成本：S已用**3.039352411GPUh/108同状态标签**；BudgetSearch已用**7.197644817GPUh/51双FIT完整视频查询（102视频）**；搜索目标为RGB MSE、主评价为Alex LPIPS。既定上限相同≠真实费用相同；搜索51次≠默认301次；报告查询轨迹但**不重跑搜索**。

**冻结选择树**：

| 真实E1结果 | 下一步 |
|---|---|
| CFG优于DIAG，且接近/优于F19-A1、BudgetSearch | S可作为方法核心候选；冻结完整生成配方进入跨预算与确认；不立即声称跨模型 |
| CFG优于DIAG，但明显输强结构布局 | CFG交叉项成立为机制增量，不独自担任布局生成；启动最小结构化预算配方CPU原型 |
| CFG≈DIAG或更差 | 暂停当前S的一交换目标；**不要立刻补Uniform父风险再无限修复**；只选一条备用机制 |
| F19-RiskSwap退化 | 记录局部评分/终点错配；禁止把D21绝对化；优先测试终点响应或来源交互假设 |
| BudgetSearch CHECK胜出 | 搜索为强近邻；比较最终质量与实际校准费用，探索更廉价的结构化生成规则 |
| BudgetSearch FIT好而CHECK差 | 报告泛化/目标不一致，不回头重选赢家，不把端点搜索整体宣告无效 |

**门槛不必伪精确**：四旧CAL、其中只有两CHECK，足以做方向性科学筛选，不足以据小样本宣布泛化或统计显著。`TEST`必须在配方冻结后才使用。

## 4. 阶段P1：形成真正可迁移的预算化方法配方

E1后仅选**一条**入主线，不同时保留S修订器、搜索微调器、三参数结构族三个正式方法。

### 路线M-S：S实证成立时

- 固定基准计划生成规则、保护区、年龄支持、归一化噪声坐标、风险输入、数据使用量、候选语法、同成本预算和选策规则；生成动作mask，禁止在CHECK/TEST上挑赢家。
- 证明CFG交叉项在**同初始化**、**同搜索范围**和**同真实资源预算**下产生可解释、可部署的增量；当前F19起点三目标同mask则不得当作CFG差分证据。
- 从19D进一步生成一个预注册新预算/网格计划。若换预算全靠手填D21等位置，只能把它视为手工配置，而不是已证算法泛化。

### 路线M-STRUCT：S只表现为局部机制或失败时

- 先设计一个有限参数的**噪声坐标区域布局族**，如：早期保护、主体间隔、过渡窗口、尾部间隔；但“参数怎样从预算与校准生成”必须写死。**能够拟合F19/Shared25≠能够自动产生好配方**。
- CPU上检查19D、22D、25D等预算：输出合法、定额、和手工强布局差异可辨；在FIT上固定选择规则，在CHECK上验证，不事后手填每个预算赢家。
- **首选备用科学机制**：少量真实终点响应/交互（不重开GRAPH全表）。同一父计划与相同FIT，固定两个交换 i/j，比较`π, π⊕i, π⊕j, π⊕i⊕j`的端点误差，判断局部线性与跨步交互是否足够可预测。若不可预测则停止，不叠加一个大网络来强行拟合。

### 质量—预算折中：条件22D工作点

B36的`Native35 T_DD=252.812s`，1.5×预算为`168.541s`；19D为148.448s，25D为185.806s。按这两点简单线性**仅供开发选卡**，22D估计约167.13s、约1.51×，**不是正式实测**。若19D最优实测仍在LPIPS 0.20附近而达不到预期保真，可以将约20s加速余量用于新增D，优先预注册22D；不能靠按结果反复在19–25D扫出最佳掩码。

## 5. 阶段P2：外部近时间对照与独立输入确认

### 5.1 外部公平对照

- 当前WC_T006和RA_T1分别比约1.5×目标更快，A32标`UNMATCHED`，不得用它们与1.5×某点做“同时间全面击败”的主张。
- 在两个旧CAL_FIT上作**一次有限阈值选择**，尝试接近**最终实际选定主方法**的`T_DD`；若无匹配点，报告最近可达点并保留原UNMATCHED；不用CHECK/TEST调超参数。
- 主比较：`Native35、Native-k（开发阶段时间选）、WC/RA近时间、Uniform/强简单布局、最终方法`，统一checkpoint、输入、seed、精度、sigma网格、CFG、真实`T_DD`。
- WC的`README本地配置`与`论文配置`必须分列；不能拿论文Euler2.3×直接与本地UniPC1.7×做排行榜。

### 5.2 正式独立确认

- 原16新最终输入和16备用仍保护；执行前fresh核对样本是否曝光。原DEV128/旧CHECK用于开发，不得再当新方法独立确认。
- 方法、预算配方、校准费用、solver与时间边界、完整方法集合、失败分母、统计程序在TEST视频生成前锁定。Native参考每组同协议同种子。
- 先以**实际需要的六角色×16输入≈96正式路径**进行整卡报价（精确人数按去重后清单），另计必要Native、warm、控制、重复、评分；**不要把“16个prompt”错写成“16条视频”，也不要先声称8GPUh必够**。
- 分析先prompt内求均值，再prompt等权；给均值差、区间、最差输入和保真—时间前沿；机器指标附PSNR/SSIM、参考误差时序曲线、可复核的人工小样审查。MUSIQ作辅助，不随意成为新硬门。

## 6. 阶段P3：Euler35 跨求解器与 WorldCache论文协议验证（本次交接新增重点）

> **重要：先有一个在UniPC上由E1/E2支持并冻结的配方，再推进Euler的真实GPU。** Euler不是必须先跑才能决定现有S有没有价值，也不能从UniPC实验“估算”Euler准确度/加速比。若资金充裕可提前做Euler只读源码/CPU准备，但不得在方法还不明确时大规模派发。

### 6.1 为什么需要区分两个Euler问题

**问题E-SOLVER（机制迁移）**：仅改变求解器，其他条件尽可能一致，观察同一生成规则对Euler与UniPC的保真—计算收益。

**问题E-PAPER（与WorldCache原文对齐）**：按作者公开资料重建Euler35及WC论文超参，与同协议下Native和CARA比较，作为**论文协议重建**而不是声称“官方逐位精确复现”。

不要把两者混为一个实验：若同时改变solver、sigma网格、step count、WC阈值、光流缩放、评分骨干、参考对象，就无法单独归因于“Euler”。

### 6.2 已知协议差异（来源：仓库721/10及WorldCache原文）

| 字段 | 当前UniPC主协议 | WC论文描述／待重建Euler |
|---|---|---|
| 数值求解 | 本地FlowUniPC默认二阶/Karras | Euler、一阶 |
| 请求/实际更新 | 请求35／实际36；CFG两支72调用 | 论文35步Euler；具体调用数/网格以新运行验证 |
| 预测历史 | UniPC保存多步预测历史 | Euler本身不依赖多步预测历史 |
| WC步计数 | 本地horizon=70；实际72分支调用 | 新协议必须与真实调用数及重置契约匹配 |
| WC超参 | 历史本地README阈值0.06、显著性权重1.0、光流scale2.0、ATS有效系数5 | 论文描述τ0=0.08、运动系数2.0、saliency0.12、ATS系数4、warp空间scale0.5 |
| LPIPS | 本文固定Alex-to-**Native** | WC论文EgoDex评估对真实GT且使用PIQ/VGG等口径；不可直接混分 |
| 论文时间 | 现已具备新卡`T_DD` | 仍需同一设备同一代码边界实测 |

这里的“论文参数”基于公开原文和721审计整理；若原版Euler sigma网格、实现细节未固定，必须标`paper-style reconstructed`，不能冒充完整官方逐位复现。WC应用配置与CARA内部A融合alpha不是同一个参数。

### 6.3 EULER-E0：只读审查/CPU协议适配（不消耗新GPU视频）

**输出**：`EULER35_PROTOCOL.md`、`sigma_grid_and_call_contract.json`、`EULER35_CPU_ACCEPTANCE.json`，分别记录：

1. 固定Cosmos-2B权重/模型输入、flow速度的符号与sigma方向；新增Euler显式更新与原Native保持同一物理预测定义，禁止额外网络前向偷偷发生。
2. 真实固定Euler35的全部sigma/timestep数组、下标与末步；记录其SHA及单次实际更新/双CFG调用数，严禁将“requested35”等价于“实际35”当作无需验证。
3. 不用旧整数步号复制CARA mask：在**归一化噪声坐标**下输出合法D预算、保护、年龄上限与晚期间隔。不同长度的合法区间由算法生成，必要D数量从策略预算定义计算。
4. WC原wrapper forced-allD与Euler-native的同状态/同初噪/同条件对照，确保同prompt/negative_prompt/CFG/速度转换/更新器、历史与cache bookkeeping正确。微型CPU路径只用于协议控制；真实权重的逐步和RGB等价必须在未来Euler卡中检验。
5. **E-SOLVER可选控制**：若要宣称“只替换求解器”，须能让Euler和UniPC运行在相同显式sigma网格、相同更新次数和相同网络调用预算上（可选35或36，但必须实际一致）。做不到就只叫“不同协议整体比较”，不分析纯求解器因果效应。
6. `E-PAPER`单独准备WC的论文式阈值和warp等设置，显式冻结值与源码SHA；对论文未指定参数保留未解决事项，不能偷偷用本地README填空后说完全一致。
7. 固定**温度/设备/资源**准入：当前只两卡A6000；受维护四卡完全不使用。必要GPU smoke也需要独立执行授权。

### 6.4 EULER-E1：最小真实Euler试验卡（方法冻结后，独立报价/授权）

**建议科学矩阵**：选2个旧CAL（建议一个FIT、一个CHECK；如要用两个CHECK须说明没有单独校准）；seed0，每个运行原始Native作为同Euler参考：

| 角色 | 作用 |
|---|---|
| `EULER35_NATIVE` | 本协议完整参考与时间锚 |
| `EULER35_UNIFORM` | 相同D预算、当前Euler网格上的通用简单布局 |
| `EULER35_CARA_FROZEN_RULE` | 使用UniPC阶段冻结的一套规则，在Euler上合法重映射；仅允许预登记校准 |
| `EULER35_WC_PAPER_STYLE` | 论文式重建的WorldCache，在同Euler协议上公平比较 |

基础**2输入×4角色=8正式视频**；额外配两输入的`EULER35_WRAPPER_ALLD`验证（2路径）、必要warm（至少各1代表性角色，具体按原框架/统计协议）以及计时重复/拒绝分母；**全部实际物理路径必须在新卡manifest与报价中列出**，不能声称8就是整卡成本。若工程能力允许，选一个固定`EULER35_WC_README_UNIPC_PARAM`对照仅用于超参差异归因，必须事先增加角色/完整费用。

**硬门顺序**：

1. 先核对Euler实际更新数（论文目标35，最终以真实入口为准）与双CFG调用次数，再通过Euler Native与Euler wrapper-allD在同一真实输入下的逐步输出/终点latent与RGB一致性（容差／逐位要求按实际数值执行路径事先确定；不同精度不得臆称bitwise）；否则停止本卡科学排序。
2. 再验证Uniform和冻结规则完整自由运行，时间边界正确；不通过禁止进入论文主表。
3. 比较本**Euler参考**下的Alex LPIPS、PSNR、SSIM、参考时序残差、`T_DD/T_request`、实际D/C/A与来源年龄。Native与CARA使用同一实际Euler时间网格与初始化。
4. 根据`EULER35_CARA_FROZEN_RULE vs EULER35_UNIFORM/WC`的差异，决定扩成4旧CAL或保留为小规模敏感性结果。不要在结果后调整sigma或step保护来挽救Euler。

**不能这么做**：使用UniPC Native作为Euler参考；将Euler+CARA对UniPC Native的LPIPS当缓存失真；将不同solver的速度直接比作某个算法增量；把该2prompt小卡说成跨骨干泛化。

### 6.5 EULER-E2：何时推进

- EULER-E1稳定且受限输入上的优势明确：冻结Euler协议，用同规则在更多旧CAL/独立输入验证，并新增一个近时间WC或RA配置。
- EULER-E1平平或失败：先检查solver/时间网格/缓存horizon控制，判断是协议适配问题还是规则迁移失败；只做**一轮有限的定位**，不通过扫Euler步号创造“成功迁移”。
- 如果M-S在UniPC端点就不成立：Euler只保留`E-PAPER`最低成本的公平基线需要，不作为“算法跨求解器成功”的前置假设。

## 7. Q、第二骨干和其他探索：独立且后置

- **Q1已接受**，同字节下I/M×BR/CFG的局部读出有选择差异；Q-END只有在明确实际峰值、内存和稳定部署收益及完整费用后才准备。Q不依赖S成功，也不因它可能成立就改变UniPC-E1的比较范围。
- **Wan第二骨干**：Euler跨求解器是同一模型内的数值方法迁移；Wan是另一模型骨干迁移。两者不能互相替代。先Euler后Wan是当前预算的研究优先级，不是逻辑必须的顺序。
- 已失败R4_COMMON_LONG/IG Scalar-Band/旧GRAPH/F/B不自动恢复。若S失败，备用优先级只保留一条有限“终点响应与跨步交互”或“可生成的区域布局族”路线；本阶段不再开本体量化、蒸馏或训练新网络。
- F18、Q5(Native请求50实际51更新)、更激进16D不与本次端点/Euler小卡同时展开。

## 8. 预算、执行门槛和不重跑声明

最新已确认的**结算时快照**来自817：`used=190.984188275 GPUh`、`reserved=16.5 GPUh`、`available=18.515811725 GPUh`、`cap=226 GPUh`。不是实时可用余额；下一张卡必须核对当前账本与另一对话是否发起新授权。2026-10-31硬件约束为**只允许两卡A6000**。

**推荐资源顺序**：

1. 优先确保7角色端点卡（39或46路径）获得完整报价和批准；若新scope显著超过原32草案，请用户确认是否退回精简范围，不能隐形减少核心对照。
2. 为独立最终确认保留一笔真实可用预算；按实际6角色×16输入报价，不能把保护输入挪给Euler开发。
3. 只有端点胜负明确、冻结方法后，再考虑小Euler；其预定额度是**未授权条件计划**，若不足通过用户明确增量预算或替换低优先项目，不自作主张挪用保护资金。
4. 因已有文档称可按24GPUh增量提高总cap并通知，这只指总cap调整政策，不等同于自动批准某张新GPU实验；任何真实增加必须先按仓库当前规则完成财务登记与用户知情。

任何GPU实验的必需条件：源commit不可变、全部实验方法与seed、绝对路径/SHA/数据许可、source identity、完全计费、设备EXCLUSIVE_PROCESS/sole CUDA context验证、磁盘空间、温控、原工件只读、唯一intention、失败/拒绝保存及终态独立接受。UNKNOWN优先恢复旧句柄，不自动再次派发。GPU结束后无权重重算时不要改旧积分计算时间。

## 9. Codex交付任务（不需要GPU授权即可先做）

### 9.1 第一轮必须交付四项（按此顺序）

1. **`READINESS_AND_ASSET_REUSE.md`**：表格列E1每个角色的mask/来源、可复用视频和评分SHA、仍需新增输出/计时/预热/控制、与原32草案差异；另列当前在途任务/结算和用户授权状态。
2. **`ENDPOINT7_SCOPE_AND_QUOTE.md` + 完整机器manifest**：分别给39/46物理路径的完整清单、性能预计、GPUh和存储/时钟/温控预算，明确推荐选择哪一版、为啥；不重跑搜索与S采集。
3. **`EULER35_PROTOCOL_GAPS.md` + CPU数值控制**：标清Euler实际timestep网格、WC paper-style超参映射、旧70 vs 72计数差异、source/sigma hash、solver-only 是否可以真正做到；只实现受影响路径，不触发真实GPU。
4. **`DECISION_AND_FREEZE_GATE.md`**：登记E1可能结果、主方法候选及停止条件、22D条件、外部WC/RA近时间补点的触发；给出独立TEST的保护计划和真实确认卡报价流程。

### 9.2 实施次序与提交边界

- 只在各自workstream路径新增设计文件或受影响代码/测试；不要未经确认改`research/02_CURRENT_STATE.md`等生成页，按照仓库canonical JSON→模板→renderer机制更新。
- 优先完成E1的整卡生产CPU和科学身份绑定；Euler适配可以另分支/目录CPU准备，但**不得影响现有UniPC路径的模型输出**。
- 所有新的计划和CPU接受记录，包含`source HEAD`、配置SHA和现存原件引用；必要时生成简短机器登记，不把设计阶段误登记为scientific accepted。
- **交接反馈格式**：简短状态总表＋可复用资产清单＋一个推荐新卡＋完整实际报价＋用户需要批准的具体事项。**不要发散为多个同时待批准的GPU实验。**

### 9.3 验收清单（checklist）

- [ ] Git HEAD/当前GPU任务/中央账本重新核对；四卡维护规则生效。
- [ ] A32/B36/S/Q/搜索既有接受和冻结SHA只读复核，清单无重跑。
- [ ] E1 七角色全部19D、同模型/solver/CFG协议且无策略别名重复生成。
- [ ] 确定39或46路径的唯一物理manifest、独立完整报价与新卡用户批准需求。
- [ ] CPU只补受影响真实组合；Native/allD和旧RGB等价合同可执行。
- [ ] 新评分定义`Alex LPIPS、PSNR、SSIM、逐帧和参考时序`与旧MUSIQ辅助职责明确。
- [ ] S校准费用与BudgetSearch51查询费用、公平比较叙述固定；FIT/CHECK/TEST身份正确。
- [ ] Euler sigma-grid/速度符号/实际update/CFG calls/缓存horizon被源码和CPU控制绑定。
- [ ] E-SOLVER（单独求解器变动）和E-PAPER（论文式多参数重建）任务名不同。
- [ ] Euler Native与本Euler WC-wrapper-allD真实权重等价被列为先决硬门。
- [ ] Euler使用Euler Native参考；绝不混用UniPC Native或不同LPIPS骨干。
- [ ] 原16最终输入不用于开发或选择；正式独立确认前方法全部锁定。
- [ ] 未获新卡授权不提交GPU，不修改已接受结果和历史合同。

---

## 10. 关键原始依据（直接供Codex索引，不要求重新通读全部732篇研究日志）

**本仓库**（均需以执行前最新HEAD为准）：

- [入口与维护约束](https://github.com/kuangda-source/CARA-cache/blob/main/AGENTS.md)
- [815最近结果与独立评审](https://github.com/kuangda-source/CARA-cache/blob/main/research/815_CARA_RECENT_EXPERIMENTS_OPUS_REVIEW_20261031.md)
- [817预算搜索冻结](https://github.com/kuangda-source/CARA-cache/blob/main/research/817_CARA_BUDGET_SEARCH_COMPLETE_ACCEPTANCE_AND_FROZEN_WINNER_20261101.md)
- [801六角色/32路径基准设计](https://github.com/kuangda-source/CARA-cache/blob/main/research/801_CARA_UNIFORM_AND_BUDGET_COMPLETE_ENDPOINT32_PREPARATION_20261031.md)
- [756 B36完整结果](https://github.com/kuangda-source/CARA-cache/blob/main/research/756_CARA_B36_COMPLETE_ACCEPTANCE_RESULTS_AND_FIGURES_20261029.md)
- [798 S初始化敏感性](https://github.com/kuangda-source/CARA-cache/blob/main/research/798_CARA_S_INITIALIZATION_SENSITIVITY_ON_ACCEPTED_FIT_RISKS_20261031.md)
- [721 WC/Native协议差异审计](https://github.com/kuangda-source/CARA-cache/blob/main/research/721_WC_NATIVE_LPIPS_OFFICIAL_PROTOCOL_FORENSIC_AUDIT_20261027.md)
- [10 UniPC/Karras采样决策](https://github.com/kuangda-source/CARA-cache/blob/main/research/10_SAMPLER_PROTOCOL_DECISION.md)
- [722 双时钟旧结果边界](https://github.com/kuangda-source/CARA-cache/blob/main/research/722_CARA_PAPER_LATENCY_BOUNDARY_AUDIT_AND_MINIMAL_MEASUREMENT_PLAN_20261027.md)
- [Q已完成读出与独立计划](https://github.com/kuangda-source/CARA-cache/blob/main/plans/cara_cfg_mainline_20261027/02_CFG_Cache_Compression_Experiment.md)

**外部资料**：

- WorldCache v1（Euler35、模型、论文参数和去噪至解码边界）：https://arxiv.org/html/2603.22286v1
- UniPC NeurIPS2023：https://proceedings.neurips.cc/paper_files/paper/2023/file/9c2aa1e456ea543997f6927295196381-Paper-Conference.pdf

### 对Codex的最终明确指令

> 当前**只推进E1（UniPC七角色端点比较）的可执行准备和EULER-E0协议CPU设计**。E1先生成39/46两种完整物理scope供人类选择，并作一次整卡受影响CPU验证；任何>4GPUh的新卡仍须单独批准。不要重派A32/B36/S/Q/搜索，不修改DEV128或旧预算合同，不偷用TEST，不把Euler宣传成已复现。完成后仅上报**一个最推荐的新GPU卡**及完整报价，等待人类按现有授权规则处理。
