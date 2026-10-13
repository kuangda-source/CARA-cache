# WorldCache 基线差异表述与 CVPR 2027 补强计划

日期：2026-10-14

## 0. 结论与证据边界

不需要在 A6000 上重现文献的 2.3×，才有资格发表在 WorldCache 基础上的改进。应忠实运行可用实现、明确任务与计时协议，在本地同条件下比较合理调参的强基线，并将作者报告值与本地再评估值分开。

当前已经有值得冲 CVPR 的具体方法和初步实证；主要需要补强可比的质量—时间前沿、第二模型迁移、贡献归因和校准/部署代价，而不是继续增加模块数量。

**依据：**用户上传《WorldCache 实验总报告：方法、证据与论文收束讨论》，截止 2026-10-14 01:01，北京时间；外部核对使用 WorldCache 论文 HTML、作者项目页、CVPR 2027 官方页面及列出的原始文献。没有远端查询，也没有将报告中尚未查收的 60 路径结果视为已完成。

---

## 1. 2.3× 与本地 1.6× 不是同一个实验配置

| 项目 | WorldCache 文献 | 本地报告 |
|---|---|---|
| 任务与报告值 | Cosmos-2B I2W 2.30×；T2W 2.10× | 当前主线为文本生成视频 |
| 硬件 | 单 NVIDIA H200 | 单 RTX A6000 |
| 采样器 | 35 步 Euler | 请求 35 步 UniPC/Karras，实际 36 更新、72 CFG 分支调用 |
| 视频 | 93 帧 | 768×432、93 帧、16 fps |
| 工作负载 | 论文 PAI-Bench-G 完整评测套件 | 开发子集与四新提示词×两 seed 的确认 |
| 计时边界 | 附录 B 明确从去噪开始到解码完成，计入缓存与近似开销 | 干净主计时包括文本编码、去噪、VAE，算法开销保留 |
| 缓存工作点 | 主配置报告 τ0=0.08、ATS 系数 βd=4 等 | 每个本地批次以冻结 manifest 为准，不从旧结果猜测 |

这里的 2.30/2.10 为**作者报告的倍数**，不是根据其已舍入表格重新推断的数值。本地论文应使用未舍入的实际时间计算倍数。

这些是已确认的配置差异；它们各自解释了多少速度差异尚未被隔离测量。不要写成“差异主要由显卡造成”或“原论文不包含解码”。

### 本地 WorldCache 也不再只有旧 1.6×

首次技术复现为三个可配对场景 1.476–1.602×。新干净计时中，AV28 为 1.7088/1.7492×，Human199 为 1.5985/1.5962×。最终主表应使用最终冻结协议的结果，而不是固定沿用首轮技术复现数值。

### 质量数字也要绑定定义

WorldCache 的“99.4% quality retention”来自其 benchmark 分数语境，不是相对 Native 的 LPIPS 保留率。不能用 `1−LPIPS` 定义质量保留率，也不能将原文分数保留率与本地 LPIPS 下降比例直接比较。

---

## 2. 为什么硬件与计时会改变相对加速？

即使代码正确，缓存也不是把所有工作统一乘一个系数。可写成：

\[
T_{\mathrm{native}}=T_{\mathrm{shared}}+T_{\mathrm{denoise,native}},\qquad
T_{\mathrm{cache}}=T_{\mathrm{shared}}+T_{\mathrm{denoise,cache}}.
\]

若去噪部分的加速为 r：

\[
S_{\mathrm{total}}=
\frac{T_{\mathrm{shared}}+T_{\mathrm{denoise,native}}}
{T_{\mathrm{shared}}+T_{\mathrm{denoise,native}}/r}.
\]

不可跳过部分、浅层 probe、缓存读写、warp/head 和矩阵计算的比例不同，都会影响总倍数。GPU 更换后，这些组成部分不一定同比缩放。该式解释可能性，不能替代实际分解，也不能据此把本地速度“折算到 H200”。

---

## 3. 论文推荐表述

### 3.1 中文实验设置模板

> 我们使用公开实现，在统一的 Cosmos-Predict2.5-2B 文本到视频设置下重新评估 WorldCache。所有方法采用相同检查点、分辨率、视频长度、随机输入、数值精度和系统设置，在单张 RTX A6000 上运行。主协议使用 UniPC/Karras，请求 35 步并实际执行 36 次更新。加速比按同一协议下未加速模型与对应方法的实际延迟之比计算。主计时包含文本编码、去噪、VAE 解码以及所有算法必要开销，加载、预热、离线评分和研究取证单列。WorldCache 文献报告的 2.30× 对应其 H200 上的 I2W 设定，T2W 报告为 2.10×；这些文献数字与我们的本地再评估结果分开列示，不用于跨平台性能排名。

若某项实现或计时协议尚未验收，应修改该句，不可直接粘贴成已经完成的事实。

### 3.2 英文工作稿模板

> We re-evaluate WorldCache using its public implementation under our shared Cosmos-Predict2.5-2B text-to-video protocol on a single RTX A6000. All methods use matched checkpoints, inputs, output dimensions, numerical precision, and system settings. Our main protocol uses UniPC/Karras with 35 requested steps, corresponding to 36 solver updates. Speedup is computed against the uncached model under the same protocol. Our primary latency includes text encoding, denoising, VAE decoding, and all method-specific runtime overheads; loading, warm-up, offline evaluation, and research instrumentation are reported separately. The 2.30× headline reported by WorldCache corresponds to its Image2World setting on an H200, while its Text2World table reports 2.10×. We therefore distinguish author-reported results from our re-evaluated results rather than directly ranking cross-setting speedups.

### 3.3 表格标签

主表建议：

- Native (our protocol)
- WorldCache (re-evaluated)
- RA-CFGCache (ported and recalibrated)，若确为移植而非原模型上的官方入口
- Ours, efficiency configuration
- Ours, high-fidelity configuration

文献原数字另置背景小表，标注 `author-reported; different setup`。不要让 2.3× 与 A6000 本地结果在同一列直接加粗竞争。

表注需要固定：硬件、模型、任务、输出规格、actual updates、CFG 分支定义、计时组成、速度聚合方式。具体 threshold、kernel、precision、offload 和 commit 放实现清单。

### 3.4 速度聚合

在同一成对集合上，可预先选择：

\[
S=\frac{\sum_i T_{\mathrm{Native},i}}{\sum_i T_{\mathrm{method},i}}.
\]

同时报告逐视频比值分布或提示词分组区间。均时之比、逐样本倍数均值、几何均值是不同聚合方式，不混写。质量缺失与运行时间分母分别声明；拒绝样本不补零、不换 seed。

同一场景、同一轮次、同一计时边界下，Native/WC 与 WC/Ours 的倍数可相乘；跨论文、跨硬件、跨工作点的倍数不相乘。

---

## 4. 最小桥接实验：澄清差距，不把复现变成新主项目

### B0：无需新增生成的核对

核对官方实现版本、启用模块、阈值与 ATS、当前计时边界、dtype/attention backend、真实分辨率与 token 布局、是否 CPU offload。缺失字段从本地 manifest 补，不能凭旧聊天补值。

### B1：一次运行记录两个主要边界

1. 去噪＋解码：对齐论文附录的边界。
2. 文本编码＋去噪＋解码：保留本地服务式边界。

另报 denoising-only 作为诊断。算法必须执行的维护、额外 head 和同步不能删掉；所有基线采取同一处理。

### B2：本地 solver 桥接（拟议，不自动运行）

四个预登记开发提示词×两个 sampler（Euler35、本地 UniPC35）×Native/WC/一个候选，最多 24 条路径；已有兼容结果可复用。

固定本地硬件和输出规格，Euler、UniPC 各自配匹配的 Native 参考。工作点先用各自忠实配置，再给相同开发调参预算。不得将两个 sampler 的 Native 视频交叉作为缓存保真参考。

这只能建立本地 sampler 桥接，不是完整重现论文的 H200、I2W、1044 样本 benchmark。没有必要为得到 2.3× 自动租 H200 或展开原全套评测。

---

## 5. 冲 CVPR 最值得增加的证据

以下是本次研究建议，不是 CVPR 官方最低实验要求。

### 优先级 A：把比较对象推进到同费用/同保真的强基线

当前高保真 H1 使用更多 D，其 LPIPS 显著下降不能单独证明效率优于更激进的 RA。应在开发集上给予 WorldCache、RA 和候选相同、有界的工作点选择机会，然后冻结。

必须面对：

- WC 默认与合理调参工作点；
- RA 忠实移植与本地校准，说明其校准状态和成本；
- Native 少步：先选两三档，按实际时间匹配，而不是强求同 NFE；
- 一种直接的残差/缓存修正近邻：如 AdaCorrection 或 GP-Refiner，优先选择可忠实运行且最接近最终方法的一个。

每方法不必对全测试集扫十个阈值。开发期选三档，测试时固定。至少画原生保真—主延迟曲线，并在两类可比区域说明改进：同保真更快、同时间更准。

可预登记相近保真容忍区间，但不要在测试后选择最有利 LPIPS 水平。

### 优先级 B：第二个真正不同的骨干

优先完成核心 A＋精度分配的迁移，不要求把未成熟 P/B 全部移植。

成本受限时，Wan2.1-T2V-1.3B 的 480p 配置是可考虑的入口：有作者发布权重和明确 CFG 推理接口，且 RA 的原论文已经在这一模型上评估。若用户已有别的 Wan 配置且实现成本更低，可替换，但必须核实真实 CFG 路径与参数约定。

第二模型建议从 16–32 个冻结提示词、两个工作点起步；完整主模型建议先扩到 64 个未参与设计的提示词×两个 seed，预算允许再扩 128 个提示词。数字是规划目标，不是统计充分性的保证或投稿硬线。

不同模型分别建立 Native 参考；少量重新校准可以接受，但必须与零样本迁移分开命名，报告校准样本和成本。

### 优先级 C：明确 H1 的贡献究竟在读出还是在线调度

当前 H1 在开发和确认中都出现同一 26D/5A/5C、0P 序列。现有 60 卡已包含 FIXED_A 和 FIXED_PLAIN，先接收其真实终态，不重复同样实验。

- H1≈FIXED_A：可发展为校准导出的阶段策略，不制造内容自适应叙事。
- FIXED_A优于FIXED_PLAIN：支持修正本身的贡献。
- 两者也近似：高保真工作点主要是计算分配；低费用 A 的作用另由对应工作点证明。

可追加极小的同费用均匀/早晚分配强规则对照，测试是否只是简单前密后疏。静态或简单不等于不能发表；关键是它是否有可迁移设计依据和公平增量。

### 优先级 D：补“生成质量保持”，不只看贴近 Native

保留 LPIPS 主指标，并用相同视频计算少量直接相关的 VBench 维度，例如主体一致性、时序闪烁、运动平滑、动态程度、文本一致性。

同时看动态程度，避免把更静或更糊误认为更稳定。使用子集或部分指标时明确是 subset，不报告为官方完整 benchmark 总分。

无需为了缓存论文另外实现驾驶控制闭环。若标题强调物理世界模型能力，就补对应物理/语义指标；否则聚焦视频扩散原生保真。

可使用预登记的盲选视频对比作为感知补充；正式人评是否值得付费和组织，另行决定，不在这里承诺执行。

### 优先级 E：最小方法说明和部署成本

核心伪代码明确来源、读出、误差标定和动作成本；仅在实际线性 velocity 融合处使用线性数学，不省略 warp/head 的非线性路径。

报告：新增显存、在线控制和 head 开销、不可支持时的回退、最终必要校准成本。最小部署校准不是整个研究试错 GPUh。

可以用当前动作下包络条件作为一个小命题解释 A 的可选择区域，但不要把已有二次融合公式、共享强度或 cost+lambda×risk 本身写成首创或全局最优定理。

两项清楚且有实证的贡献优于三个不完整模块。F 当前不入主图；B 有限验证可以继续，但不绑定主稿是否能提交。

---

## 6. 推荐论文证据包

| 内容 | 主要信息 |
|---|---|
| Figure 1/主结果图 | 同一硬件和任务的质量—时间曲线，区分低费用和高保真工作点 |
| Figure 2/方法图 | CFG 一致读出、来源历史、实际误差—费用分配；继承组件与新增组件区分 |
| 主表 | 主模型与第二模型，Native/WC/RA/近邻/候选；时间、保真、相关质量、显存 |
| 核心消融 | 共享强度、来源一致性、阶段/固定序列、β=1、真实开销 |
| 校准与迁移表 | 源模型/新模型、重新校准范围、必要样本与费用 |
| 附录 | 论文与本地协议差异、solver 桥接、失败/拒绝统计、补充视频、复现配置 |

不需要把每个候选都跑完整个实验网格。先冻结两项主贡献，新增数据优先购买能改变论证的证据。

---

## 7. CVPR 2027 官方日程与工作节奏

2026-10-14 核对的官方日期：

- 注册：2026-11-10 AoE。
- 正文：2026-11-16 AoE。
- 补充材料：2026-11-23 AoE。
- 最终决定：2027-02-25。

正文 AoE 截止对应北京时间 2026-11-17 19:59（按当日 23:59 AoE 换算）；内部截止应更早。所有作者需提前完善 OpenReview；作者列表不要拖到注册后才解决。官方指南若更新，提交时再核对，不照搬旧年份政策。

建议的研究节奏（不是助手后台工作承诺）：

| 时间 | 目标 |
|---|---|
| 10/14–10/20 | 接收现有曲线；统一计时与基线配置；固定论文主要方法与两项贡献；启动第二模型接线 |
| 10/21–10/31 | 扩充冻结主测试；第二模型结果；明确同费用/同质量优势；10月底判断是否按CVPR提交 |
| 11/01–11/08 | 关键机制与成本补充；完成正文、主图、匿名复现材料 |
| 11/09–11/16 | 按时注册，最后检查数字、代码对应、图表和正文；不再为模块数量改变主方法 |

10 月底的评估重点是：是否能得到可比强基线下的增量、至少一个迁移、以及清楚的机制责任。它是资源与稿件判断，不是任意设定一个接收概率。

若提交 CVPR，就按其审稿与重复投稿政策执行，不将同一实质稿件在审稿期间并投期刊。若决定不走 CVPR，原期刊主计划仍可继续。

---

## 8. 来源

[U1] 用户上传 `WorldCache_Experiment_Report_for_6pro_20261014.md`，重点 §2、§5、§7–§9。它是本次私有结果的依据，不是助手独立远端审计。

[R1] WorldCache 原论文，§4.1、表1/2、附录A/B：`https://arxiv.org/html/2603.22286v1`

[R2] WorldCache 作者项目页：`https://umair1221.github.io/World-Cache/`

[R3] RA-CFGCache：`https://arxiv.org/html/2609.36433v1`

[R4] AdaCorrection：`https://arxiv.org/abs/2602.13357`

[R5] GP-Refiner：`https://arxiv.org/abs/2609.05981`

[R6] Wan2.1-T2V-1.3B 官方模型卡：`https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B`

[R7] VBench：`https://vchitect.github.io/VBench-project/`

[R8] CVPR 2027 日期：`https://cvpr.thecvf.com/Conferences/2027/Dates`

[R9] CVPR 2027 CFP：`https://cvpr.thecvf.com/Conferences/2027/CallForPapers`

[R10] CVPR 2027 OpenReview profile：`https://cvpr.thecvf.com/Conferences/2027/CompleteYourORProfile`

本次未运行 GPU、未改现有卡、未建立自动监控。上述样本、期限内研究安排与预算取舍均为建议。
