# WorldCache＋RA：CFG 协调的多精度缓存刷新

2026-10-10，v1.2。**当前方法开发总设计；不是实验结果或原卡范围变更回执。** v1.1接入48GPUh可用窗口，v1.2接入用户直接修改的单次4GPUh确认门槛，方法/实验范围不变。

依据用户最新科研对话及三份[原文包](../docs/integrated_development_20261009/README.md)，对照本库当前结果和源码适配。本文与[首窗口实验卡设计](WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)共同成为新的研究入口；旧登记、结果、失败和判据逐字保留。

## 1. 研究目标与开发方式

以 WorldCache/Cosmos 为执行基础，以本地校准 RA 联合控制为强基线，构建能完整生成视频的协同方法：

| 部件 | 研究问题 | 第一版方法 | 与其他部件的联系 |
|---|---|---|---|
| A／W1 | 复用时怎样更准？ | 双 CFG 共用修正强度；实际 guided 输出监督 | 改变 C 和近似来源的可复用寿命 |
| B／稀疏刷新 | 重算怎样更便宜？ | 协调稀疏 attention；少数层部分 MLP GEMM | 提供介于复用和 dense 刷新之间的 S |
| C／W3 | 怎样选择刷新？ | RA 联合风险＋来源质量感知的 C/A/S/D 选择 | 结合精度、创建成本和未来再刷新需求 |

三部件进入同一个开发周期。尽早运行 BASE-R、A、B、AB-naive、ABC 的完整视频，不以 A/B 各自显著胜出、终点 Q 可预测、所有局部点改善作为组合前置条件。接口正确性和实际跳过计算仍要验证，但不再先铺全层×全动作×全历史诊断矩阵。

新增贡献候选是三者的协同设计与实测优势；CFG 交叉项、传播加权、共用 mask、token 缓存各自已有相关工作，不能单独宣称首创。论文工作量来自有效方法、合理对照、交互解释和独立确认，不由模块数量保证。

## 2. 当前证据如何进入新设计

| 已有证据 | 本轮用途 | 保留的判断 |
|---|---|---|
| 官方 WC 三接受场景 1.476–1.602× | 可运行基线，沿用本地 UniPC/Karras 设置 | 技术复现，未复现原论文全部质量评估 |
| W1 内部 7/8 改善、预测 MSE −24.08%；七接受视频 4正3负，平均 loss 相对 −0.4388% | 保留近似信息，改 guided 目标；加入 β=1 强对照 | misc／AV51 全视频退化及自身状态反例保持 |
| 稀疏中位 1.219×、两深层组少约5.33%、视频少0.29%／1.41% | 复用核和敏感层结果；研究覆盖和 MLP 剩余成本 | 当前配置收益弱，不否定整个稀疏方向 |
| Human 单点刷新 LPIPS −2.81%，后续 full 18→16 | 缓存创建可能改变未来成本 | 单场景探索证据，不是固定预算或泛化优势 |
| 同配额 PAIRED +0.1198%，单槽 −4.0194%／−13.3910%；三条轨迹强抵消 | 联合近似、执行和路由的动机 | 抵消/交互是机制，未部署的新规则不能被旧手工换点结果代替 |
| 真实 S22 同动作成对接口等价；完整 Toy/生产资产 CPU 通过 | 复用恢复、计量和接线资产 | 真实全36步政策等价仍待必要控制 |

权威结果分别见 [138](../research/138_WC_W1_APPROVED_FIVE_REFERENCE_EXECUTION_AND_RESULTS.md)、[141](../research/141_WC_W1_OWN_STATE_APPROVED_EXECUTION_AND_RESULTS.md)、[134](../research/134_WC_SPARSE_COST_CONDITIONS_EXPLORATORY_RESULTS.md)、[164](../research/164_WC_CFG_BUDGET_MATCHED_COMPLETE_RESULTS_20261009.md)、[187](../research/187_WC_COMMON_COMPLETE_CFG_MECHANISM_RESULTS_20261009.md)、[193](../research/193_WC_REAL_PAIRED_INTERFACE_COMPLETE_RESULTS_20261009.md)、[197](../research/197_WC_COMPLETE_NATIVE_POLICY_REAL_BATCH_PREPARATION_20261009.md)。旧拒绝、超时和费用不删除。

## 3. 实际 CFG 与测量对象

当前实际闭包是 `c + 7*(c-u)`，故 guided 误差为：

\[
e_g=8e_c-7e_u=e_m+7.5e_d,\qquad
e_m=(e_c+e_u)/2,\quad e_d=e_c-e_u.
\]

遵循当前源绑定与 [177 的核对](../research/177_WC_CFG_JOINT_BASELINE_CPU_READINESS_RESULTS_20261009.md)，保留原 FP32 运算顺序。早期142的7/−6解释保留历史身份，不作为新实现依据。u 在本批是负提示词分支。

同一实际 latent、solver、条件、缓存历史下，比较 **post-denoise／pre-solver** 的实际输出。隐特征上的8/−7组合只能是待校准 proxy，不能直接叫真实 guided 误差。参考 teacher 也必须在该实际状态上完整计算，不能用另一原生轨迹的预测代替。

## 4. 动作与来源合同

| 动作 | 付出的计算 | 写入语义 |
|---|---|---|
| C | 双浅 probe＋原 WC 复用 | 读工作缓存；保持 dense anchors |
| A | C＋低维 W1 修正 | 修正读出；默认不改写 dense anchors |
| S | 所选稀疏／部分深层实际执行 | 写近似工作缓存，来源误差非零 |
| D | 双分支真正 dense 深算 | 更新工作缓存和合法 dense 校准 anchors |

新控制首版采用 C/C、A/A、S/S、D/D。关闭态忠实保留原 WC 的 CC/DC/CD/DD；接口的四动作能力不要求控制器第一版开发全部交叉模式。

每个来源至少记录 request／CFG slot／model／condition／backend／layout 指纹、创建步、当前步、mode、密度、更新区域、估计创建误差、质量模型版本。工作缓存与 dense 校准 anchors 分离：

- D 只消除同当前状态、匹配后端的创建近似误差，不消除过去 latent／solver 偏移。
- S/P 的 `age=0` 不是误差零；部分 token 虽重新计算，其上游或 K/V 仍可能近似。
- A 不把修正读出当新真值；诊断 teacher 不进入部署历史。
- S、同量化全边 MF、原生 D 分别标记，MF 不自动成为 dense teacher。
- 分支、请求、条件、时间周期、形状、算子/近似器版本改变时，清理不兼容统计、拓扑和层缓存。新增层状态必须纳入实际恢复与费用记录。

## 5. A：CFG 协调修正

原始、未 warp 的共同坐标中，若 p=h2−h0、r=h28−h0、d=h28−h2，则 r=p+d：

\[
\hat r_t=r_b+\beta(p_t-p_b)
=p_t+d_b+(\beta-1)(p_t-p_b).
\]

增加 β=1 对照，区分当前浅层恒等成分与深层可预测增量。保留现有 β 和原近似。首批不同时改变 warp／Gamma／head 位置，不能把坐标变换的收益归因于 β。

令 v_b^0 是原 WC 读出，v_b^1 是原 W1 读出，q_b=v_b^1−v_b^0；两分支共用 α：

\[
v_b(\alpha)=v_b^0+\alpha q_b,\qquad \alpha\in\{0,0.5,1\}.
\]

首版在输出空间校准，也可比较一次共享最小二乘 α；两种方案先选一种部署，避免扩大调参。输出融合不自动等价于 warp 前系数融合；两 head 路径、读写和同步全部计费。

\[
\mathcal L=\|8e_c-7e_u\|^2+\lambda(\|e_c\|^2+\|e_u\|^2).
\]

忽略分支正则时，设 e_g^0 为原 guided 误差、q_g=8q_c−7q_u，则：

\[
\alpha^*=\operatorname{clip}\left(
-\frac{\sum_i\langle e_{g,i}^0,q_{g,i}\rangle}
{\sum_i\|q_{g,i}\|^2+\epsilon},0,1\right).
\]

有正则时按完整二次目标求解，不能套用无正则公式。数据／能量不足回退原近似。CAL 按场景等权汇总，不让多个相关状态或两次重复充当独立样本。只用离线合法 teacher 或 D 上“决策前预测—执行后真值”更新未来参数；cache hit 不偷偷执行当前 dense。

正常修订：共享系数→D/S 两来源系数，或受正则约束双系数，或最多三阶段；每轮只增加一种自由度。小参数拟合是计划内方法，不要求全量重训。Tiny head／LoRA 留作有具体收益目标的后续卡，尚未执行或批准。

## 6. B：更便宜的刷新

### B1：协调稀疏 attention

沿用 `sparge_routed_no_pv.py` 和当前 no-PV 核。现有 router 同时返回 block mask 与分支量化数据；共享 mask 时 **不能复用另一分支的量化 Q/K、scale 或输出**。

首版保留深层 c→u 顺序：c 的当前层产生 mask，u 的对应层使用同一 mask 和自身当前 Q/K/V。这是 conditional-led shared mask，须测参考分支偏置。浅层 paired 接口没有自动提供每个深层的双 Q/K。

在同实际执行边数/预算下比较独立与共同 masks，报告行/head 密度差异；不以 union 多算冒充协调收益。下一版双侧 coarse-QK max／受限 union 需深层交错或 batch 接线，另登记峰值显存与成本。

共同 mask 可按2／4次实际 S 机会复用，记录跨越的实际去噪步、cache hits、拓扑年龄和重建成本；内容仍用当前 Q/K/V。模型/形状/条件不兼容立即失效。6、23、27 attention dense 回退保留现有适用范围；没有证据把它扩成 MLP 禁用名单。

### B2／P0：少数层部分 MLP

先完整 attention，仅4–8个实测 MLP 占比高、显存允许的层部分执行。活跃比例0.5／0.75，共用 CFG 时空块集合；首版由已可见双 probe／历史／轮换表选择，比较同配额随机、轮换与廉价风险规则。

\[
\hat F_l(X)[M_l]=F_l(X[M_l]),\qquad
\hat F_l(X)[\bar M_l]=F_{l,cache}[\bar M_l].
\]

真正执行 gather→缩小 MLP GEMM→scatter；缓存投影后的 MLP 输出，当前 norm／time modulation／gate 在源码确认的边界处理。完整计算再 blend 只作诊断。93视频帧不是 latent token 时间长度；N、d、块形状从实际运行张量读取。

\[
M_{MLP}\approx2L_sNd\,b_{elem},\qquad
C_{P0}\approx C_{attn}+\rho C_{selected\ MLP}+C_{other}+C_{select}+C_{gather/scatter}.
\]

只改少数层，就只用这些层的 MLP 占比估算。先估容量和 live VRAM，不保存全部扩展维；内存不足先在新版本中减少层数，不追改已冻结卡。P0 可运行后接 B1，成为 S 档。活跃 query＋陈旧 K/V 的全深层 P1 单列后续，当前不重写全部模型。

## 7. C：来源质量感知调度

先实现 RA 的联合风险、Cosmos 校准传播先验和共同 C/D 刷新，固定实际 CFG／时间网格。WC saliency proxy 和官方 Di proxy 的定义分别记录；公开 Wan/FLUX 表不能直接载入。没有传播校准的版本只叫不加传播的消融，不能替代 BASE-R。

扩展动作 proxy 与 source、age、approximation version 绑定：

\[
\hat q_g(a)^2=64\hat q_c(a)^2+49\hat q_u(a)^2
-112\hat\rho(a)\hat q_c(a)\hat q_u(a).
\]

该式是经验预测。相关性限制在合法范围；非有限/不兼容统计回退可行保守动作，不把裁剪后的数叫误差保证。

首版选择 **预计风险可接受的最便宜可行动作**，另加经 CAL 标定的近似来源质量/频繁 S 约束。作为解释可写：

\[
a_t=\arg\min_{a\in\mathcal A_t}
\{\hat g_t\hat q_g(a)+\lambda\hat C(a)+\nu\hat B(post\text{-}cache,a)\}.
\]

仅开发一个规则/查表版本，各项尺度在 CAL 固定。决策信息来自 paid probes 和历史；深层 QK 统计只在上层选择 S 后计算，不能免费用于 C/S 选择。成本来自 clean measurements，C<A<S<D 是待测假设，慢的 S 不因名称而优先。

记录来源质量、工作缓存年龄、RA 区间累积量三个对象；S 后不得把它们无条件清零。可校准重新基准化，但 RA 累积分数不是历史终点误差真值。

周期模型说明协同动机：

\[
\bar c_a=c_C+(c_a-c_C)/K_a.
\]

便宜刷新可能寿命短，A 可能改善 S 后续读出。该式不是保证；完整运行记录创建成本、后续复用长度、D/S 次数和真实时间。以后可保留 Yq=L_C−L_D、Yt=T_C−T_D 反事实标签作为小 head 候选，不把大量终点标签设为本轮规则生成视频的通用前置条件。

## 8. 源码落点与当前缺口

| 现有资产 | 可复用职责 | 新工作／未有能力 |
|---|---|---|
| `calibration.py`、`integration.py`、`shadow_forward.py`、`fixed_replay.py` | 过去真实 anchor、W1 读出、warp/head、teacher 隔离 | β=1、guided α 目标、D/S 来源分离校准 |
| `cfg_paired_probe_native_policy.py`、`cfg_paired_probe_production.py` | 双 paid probes、原四动作与尾部周期 | RA 选择器；不改已经封存的生产 stage |
| `cfg_complete_native_policy_sampling.py` | 完整采样和实际向量/状态控制 | 新多精度 batch，不能把现有 CPU 当作新模块通过 |
| `refresh_deployment.py` 的 RefreshLedger／SimpleRefreshAdapter | 工作来源和 true_dense_history 分离、attention 替换 | 质量字段、MLP 层缓存、A/S/D 状态转移 |
| `sparge_routed_no_pv.py`、`sparge_no_pv.py` | mask/LUT/量化/真实块核 | topology 与分支量化分离、shared mask、有限复用 |
| 177/官方 RA 固定源捕获 | 代理与 CFG 映射参考 | Cosmos rho／传播表尚未生成、校准预算待登记 |

现有核、快照和测试按源/shape/backend 兼容复用；新改动只补必要控制。MLP 的实际 norm/gate 注入位置必须先映射官方源码，不能凭上述候选接口名声称代码已有。

## 9. 评价、修订与论文收敛

首窗口覆盖一个 W1 正例 AV28、Human 和困难 misc／AV51，沿原 CAL8 seed0；必要接口卡仍用已经准备的 Common／Human seed3。两个用途不混配 Native。使用七已接受参考；robot 拒绝保留原8/7/1分母，不能替换为容易样本。

主要报告场景等权全93帧 LPIPS、去噪时间、完整 pipeline wall；辅助运动/清晰度/语义代理与尾部退化，默认自动评价，不增加非必要人评。部署路径关闭 teacher/hash/dump 后单独预热、重复计时；全部取证和失败开销仍入 GPU 账本。

比较调优 WC、校准 RA、同算子直接组合和完整方法；不只打败“S 当 D 清零”弱对照。允许单模块弱而组合有效，补必要2×2交互消融。正常允许1–2轮具体问题驱动的修订，保留版本和旧结果；不以单阈值否定方向，也不不断扩自由度回避无净收益。

冻结后新4提示词×1 seed作小确认，必要时加第二seed；论文阶段另提报未曝光16–32或更多提示词、多seed、至少三档真实质量—时间点和一项设置/模型迁移。当前窗口是开发，不保证完整投稿证据。

## 10. 权限与当前卡

[最新窗口授权](../research/199_WC_NEW_REMAINING_48_GPUH_AUTHORIZATION_20261009.md)：以已用29.895246589658527为起点，新增可用48GPUh，新累计上限77.89524658965853；65提交不变。约20GPUh仍是第一开发批的拟议分配，其余28尚未登记为作业。原[只读50h快照](../reports/wc_integrated_design_resource_snapshot_20261009.json)保留历史，执行前刷新新权威账本。

H-T63 原16路／6.704055834GPUh登记与全部CPU结果保留，尚未批准或执行，仍超过新4GPUh门槛。本轮提出新的分阶段必要控制，详见首窗口；不把4路称为原16路通过，不取消或改写旧卡，也不拆卡绕过4GPUh。重提案的目的、证据覆盖和损失明确后再冻结独立执行卡与完整成本。

按[2026-10-10直接执行授权](WORLD_CACHE_EXECUTION_POLICY_20261010.md)，已授权设计内完整单次预测≤4GPUh自主／>4才具体确认。累计77.89524658965853、全部失败入账、一GPU槽、原锁和UUID保持；训练范围仍需按已授权设计处理。旧6.704整卡仍超过新门槛，GPU goal的该卡授权等待不因改门槛而伪造解除。绑定旧50或2GPUh政策的冻结stage保留，下一执行卡需绑定当前窗口与4GPUh授权并验证受影响入口。

## 11. 一手参考与归属

- [RA-CFGCache v1](https://arxiv.org/html/2609.36433v1)：联合 proxy、传播校准与共同控制是借用基础；本地适配与新增部件分别报告。官方源仍固定于176已捕获版本。
- [ToCa](https://arxiv.org/html/2410.05317v4)、[RAS](https://arxiv.org/html/2502.10389)、[DuCa](https://arxiv.org/html/2412.18911v3)：token/模块级计算复用与选区比较的近邻。
- [SpargeAttn 官方实现](https://github.com/thu-ml/SpargeAttn)：继续使用项目已绑定版本；不以仓库最新代码覆盖已验收核。

2026-10-09核对上述一手页面；作者其他平台结果不当作本地收益。用户原文另列 SpargeAttention2 蒸馏作为后续提案，本轮不因文档提及就下载或训练。
