# WorldCache E3：结果研判与数学驱动的调度设计

日期：2026-10-12  
状态：研究分析与候选算法设计；不是新实验结果，不授予 GPU、SSH 或仓库写入权限。

## 0. 核心判断

E3 完成 64 个科学位置和全帧评分，使研究从个别正例进入了完整开发集组合对照。最有价值的新现象是：NONZERO 允许 P 后真正复用，CPD 的计算行为改善且平均失真只微变；同一修正 A 在该来源规则下却全场景退化。中心问题因此应从“找一个更好阈值”升级为“来源、修正和误差状态一致的多精度计算调度”。

建议方法骨架：**来源一致的预测—观测融合 + 保留相关性的误差估计 + 按预期收益与成本触发刷新**。首版只需标量/少量分组系数和短时域低维预测，不必重训 backbone，也不要求先训练终点价值网络。

已有无 P 正候选的确认线照常保留；P、W1、W3 可以协同开发，不要求每个模块先独立胜出。本轮完整 P 卡继续 USER_DEFERRED_RESULTS_DISCUSSION_FIRST，不执行、不重问、不改名缩卡绕过暂缓。

## 1. 来源和证据边界

[U1] 用户本轮粘贴《E3 完整结果讨论与 P 卡暂缓》，引用报告 369、370。本文没有访问 369/370 原件、视频或服务器。关于实现细节，超出摘要的部分一律作为待核查项，不猜测 KEEP/NONZERO 的具体代码更新方程。

[U2] 当前对话中此前报告的动作费用：C 0.16846 s，A 约 0.338 s，P 6.17331 s，含 P 状态维护的 D 6.25420 s。这些是已付浅层 probe 后、指定测量边界下的费用，不是最新干净端到端时间。

数学恒等式是本分析的推导；随机模型、代理函数、分桶方式和预算分配是拟议设计。外部论文只支持数学借鉴和近邻定位，不证明本地候选有效。参考资料见末尾。

## 2. 正式更新结果判断

### 2.1 已有事实

- 两规则 × 四 CAL × 八方法全部 64 位置完成，64 个兼容视频、完整 93 帧评分；零审计和评分失败。
- KEEP：阶段 W1 / β=1 相对同规则 CPD 的平均 LPIPS 降低 13.6735% / 12.7233%，3/4 与 4/4 场景改善。
- NONZERO：同两候选相对同规则 CPD 的平均 LPIPS 上升 50.9539% / 18.2840%，均 0/4 改善。
- NONZERO CPD 相对 KEEP CPD 的平均 LPIPS 仅上升 0.2273%，场景 2 正/2 负；P 后 C 从 0 增至 50，DD 从 51 降至 37，DD+PP 从 74 降至 62。
- NONZERO 的 W1 / β=1 有 33 / 37 次 P 来源读出；P 平均年龄 1.42 / 1.84 步，真实 D 参考平均比 P 早 9.42 / 7.19 步。没有发现 P 伪写为 D。
- RA 的 56 次 DD 仍少于 NONZERO CPD 的 62 次 DD+PP。不能用 DD 下降代替真实时间优势。

### 2.2 归一化后，交互比各自百分比更清楚

以下只做代数归一化：将 KEEP CPD 的四场景等权均值设为 1，使用用户提供的已舍入百分比。

| 方法 | KEEP | NONZERO |
|---|---:|---:|
| CPD | 1.000000 | 1.002273 |
| CPD + 阶段 W1 | 0.863265 | 1.512970 |
| CPD + 阶段 β=1 | 0.872767 | 1.185529 |

NONZERO 相对 KEEP，W1 自身均值约增加 75.26%，β=1 约增加 35.84%。这不是新的测量，也不是把两个相对率简单相减。

描述性交互对比可写为：

`I_A = (L_NONZERO,A - L_NONZERO,OFF) - (L_KEEP,A - L_KEEP,OFF)`。

归一化后，W1 为 +0.647432，β=1 为 +0.310489。说明来源规则对修正作用有很强的条件性影响。由于闭环动作与状态都改变，这不是对某一代码行的唯一因果归因；四个开发场景也不支持总体显著性宣称。

### 2.3 不应做的推断

- 不再说“P 后从来没有 C”；那已被本轮自然 NONZERO 轨迹更新。
- 50 次 C 不是 50 个独立场景，也不自动意味着 P 的净时间收益。
- 平均 0.2273% 的变化不是统计等价，不能掩盖逐场景差异。
- β=1 同样失败，排除了“全由拟合 β 不准解释”的简单说法，但不排除幅度、外推区间、warp、风险反馈等其他因素。
- KEEP 中 A 有效而没有 P 后 C，不足以证明 P 作为未来来源有不可替代贡献。
- 新方法首先应比较合理 RA、RA+A、正确来源的简单组合，不能只击败有参考不一致的旧实现。

## 3. 数学基础一：把 P 看成相关、有误差的观测

### 3.1 先把参考写一致

设最近可信 D 参考为 `(r_D, p_D)`，P 在时刻 s 产生 `(r_P, p_P)`，当前浅层信号为 p_t，β_D 只由过去真实 D 历史得到。为简化符号先省略 CFG 分支，且假设已经处于一致的残差/warp 坐标。

旧读出：

\[
\hat r_t^{old}=r_D+\beta_D(p_t-p_D).
\]

工作源读出：

\[
\hat r_t^{P}=r_P+\beta_D(p_t-p_P).
\]

定义 P 相对旧模型的 innovation：

\[
\iota_P=r_P-[r_D+\beta_D(p_P-p_D)].
\]

严格得到：

\[
\hat r_t^{P}=\hat r_t^{old}+\iota_P.
\]

因此，新的参考不仅“更年轻”，它把 P 提供的新信息和 P 的近似偏差一起注入了预测。它可能有益，也可能过量。

可执行的连续族是：

\[
\hat r_t^{(\gamma)}=\hat r_t^{old}+\gamma\iota_P,
\qquad \gamma\in[0,1].
\]

首版只用 γ∈{0, 0.5, 1}。不要在每次复用递归再加同一个 innovation：相同观测应只融合一次，存为工作状态；下一次读取从工作状态预测。多次 P 时，应针对当前先验计算新 innovation，保留来源依赖，不假设各次 P 独立。

若宣称以 P 为纯锚点，则零增量时应还原 r_P；显式 D/P 融合可以不还原 r_P，但必须为融合估计重新定义其质量，而不能继续把它的误差当成纯 P floor。

### 3.2 为什么可借鉴 Kalman，但不应硬套独立噪声假设

Kalman 预测—创新更新提供了“预测不一定全错、观测不一定全对”的结构 [R1]。本地 P 与旧预测来自同一生成轨迹和相关缓存，误差可能相关、带偏、非高斯，因此直接用独立噪声 Kalman 增益没有充分依据。

更合适的首版是相关误差的最小二乘融合。令 x* 为同状态目标，

\[
e_0=\hat x_0-x^*,\quad e_P=y_P-x^*,\quad
\hat x_\gamma=(1-\gamma)\hat x_0+\gamma y_P.
\]

在相同条件分桶下定义二阶矩，而非默认零均值协方差：

\[
A=\mathbb E\|e_0\|^2,\quad B=\mathbb E\|e_P\|^2,
\quad C=\mathbb E\langle e_0,e_P\rangle.
\]

则：

\[
J(\gamma)=(1-\gamma)^2A+\gamma^2B+2\gamma(1-\gamma)C.
\]

无退化情形下，约束于 [0,1] 的最小值为：

\[
\gamma^*=\operatorname{clip}_{[0,1]}
\frac{A-C}{A+B-2C}.
\]

分母是 `E||e_0-e_P||²`，不是任意正则参数；近零时不能用数值噪声确定大增益，应回退预登记的小增益/单来源。可以用 shrinkage 正则稳定估计，但此时要区分正则解与上述精确解。

这个推导不要求高斯、独立或无偏，但要求目标可比、二阶矩存在、校准分布与应用条件有合理联系。它只最小化指定表示上的均方误差，不保证终点 LPIPS 最优。

### 3.3 CFG 和非线性 head 必须处理正确

- 当前实际 CFG 是 `8c−7u`。γ / α 首版在两个分支间共享。
- 若直接对 guided 输出做线性融合，上述误差二次式精确成立。
- 若融合在 residual/warp/head 之前，则它只对该线性融合空间精确成立；非线性 head 后的 guided loss 必须用真实输出校准或用离散 γ 直接比较，不宣称残差最优等于 guided 最优。
- 两个分支的预测误差可用 2×2 Gram 二阶矩描述：

\[
M=\begin{bmatrix}
E\|e_c\|^2&E\langle e_c,e_u\rangle\\
E\langle e_c,e_u\rangle&E\|e_u\|^2
\end{bmatrix},\quad q_g=w^TMw,\quad w=(8,-7)^T.
\]

这包含偏置二阶贡献，不应误称为经过概率校准的安全置信度。CFG 交叉项属于 RA 已有基础 [R4]。我们的设计增量是让 M 随来源、修正方式和实际读出变化，而不是对所有 C/A/P 共用旧 D 的误差表。

全维 Kalman covariance 没必要。首版按 D/P 来源、早中晚噪声阶段做少量标量或2×2统计；后续确有需求再加小预测器。

## 4. 数学基础二：事件触发估计与多传感器调度

Trimpe 的事件触发框架直接比较“更新减少的预期估计损失”与“获得更新的成本”，并扩展到预测下一次更新时间 [R2]。ICML 2025 的多传感器调度研究把不同精度、成本的观测选择放进有限时域优化 [R3]。

这里的映射是研究借鉴，不是把网络当真实线性物理系统：

| 缓存动作 | 估计/控制解释 |
|---|---|
| C | 沿历史估计预测，不取得新的深层观测 |
| A | 改变廉价读出/修正，不等于独立新观测 |
| P | 有相关误差的近似观测，同时更新部分内部状态 |
| D | 获得当前实际 latent 上的完整输出 |

D 的“准确”只针对当前实际状态上的网络计算，不代表视频真实世界正确，也不让轨迹回到原生解。

### 4.1 为什么不能只比较当次误差

一个 P 当次便宜很少，却可能改变后续 C/A 的次数；一次 D 可能比连续多个 P 更划算。一个只选当前最便宜合法动作的贪心规则，无法自动照顾这一影响。

候选低维状态包括：当前噪声位置/步长、RA 现有 proxy、工作来源及年龄、可信校准年龄、innovation 大小、动作相关二阶矩、累计实际费用。

建议先用两步短时域：

\[
a_t^*=\operatorname{first}\arg\min_{a_{t:t+H-1}}
\sum_{k=t}^{t+H-1}
[\hat c_k(a_k)+\lambda\hat g_k^2\hat q_{g,k}(a_k)]
+\eta\hat V_{t+H},\quad H=2.
\]

- `q_g` 是平方误差代理；g 是从局部范数到后续偏差的增益近似，因此这里用 g²。也可以全程采用范数口径，但不能混用单位。
- `V` 是窗口末端来源质量/下一刷新需求的经验代理，不是已经精确学到的最终 LPIPS。
- λ 的单位将误差代理换为秒量级代价；由开发集工作点校准，不对每个测试场景调参。
- 只模拟低维来源/风险状态，不在线生成四条视频，更不运行所有 teacher 再挑最优。
- 用低阶漂移模型或分桶经验表预测未来 source error；不假装掌握未来 latent。
- H=1 是强简单对照，H=2 是首版；有价值才考虑 H=4、终端项或小回归器。
- 对当前浅层探测已付的成本可在同一步动作比较中消去，但完整部署计时必须计回；候选额外 head 和 source维护不能消去。

### 4.2 观测后信息不能用于观测前选择

选择 P/D 前只能使用已有特征、历史与预先校准的精度/成本。执行 P 后才能使用其实际 innovation 做融合与状态更新。若观测后发现 P 不可靠而再执行 D，两次成本都计入；这一回退概率也影响预期成本。

不能为了决定是否 P，先免费运行 P；不能在 cache hit 上免费获得同状态 dense 真值。

### 4.3 不把经典理论保证移植过来

Kalman 的线性随机模型、传感器调度的 Poisson 观测假设、控制系统的 Lyapunov 条件，当前视频网络均未自动满足。本方案应称为“估计/控制启发的经验调度”，不能称为已经证明稳定、最终误差有界或概率安全。

有限时域的模型失配、估计校准以及真实开销需要独立比较。数学框架的作用是给状态、更新和目标一致的定义，而不是给一个有名词的阈值贴标签。

## 5. 数学基础三：非均匀采样上的数值外推与误差控制

FoCa 已将 hidden feature 序列视为 feature-ODE，采用 BDF 启发预测与 Heun 校正；HyCa 按不同 feature dynamics 选择混合求解方式 [R5,R6]。因此“缓存可以用 ODE 解释”不是我们的独有贡献。

对本问题的直接启发：

1. 不仅记步数年龄，也记实际 sigma/time 间隔和归一化 probe 距离。Karras 的等步数不等于等噪声间距。
2. 区分工作来源年龄与用于拟合 β 的真实 D 历史跨度。年轻 P 不保证旧斜率模型仍适合当前状态。
3. 用候选 C/A 的差异监测超出外推适用域的程度，但差异不是自动可靠的真实误差估计：两个错误预测也可能接近。
4. 一种 trust-region 风格强度是 `alpha=min(alpha_phase, Delta/(||delta_guided||+eps))`。它只约束相对基线的修正幅度，不保证朝原生终点移动，必须与现有阶段规则对照。
5. 不为了做误差估计在线支付两个完整 deep 预测；尽量利用已有廉价提案和未来自然 D 揭晓的误差。

去噪时间不是视频物体运动的物理时间；不能把最小作用量、能量守恒、熵增等名词直接解释为潜变量轨迹规律。

## 6. 新的关键区分：来源不确定性与已经注入的轨迹误差

考虑简化误差动力学：

\[
e^{traj}_{t+1}\approx J_t e^{traj}_t+B_t\epsilon^{guided}_t.
\]

D 使当次 `epsilon_guided` 接近零（相对同状态完整计算），不会令过去积累的 `e_traj` 归零。P 只能改变当前工作估计及其误差状态，不能自动抹掉已经写入 latent 和 UniPC 历史的偏差。

RA 明确把重置量定义为区间控制代理，而不是全局终点误差上界，因此不能以它重置为零指责 RA 数学错误 [R4]。本地 KEEP/NONZERO 的确切实现尚未取得，本文也不将其静默替换为某个 Kalman 更新。

拟议扩展应分别维护：

- source estimate 及其误差统计：P 后可降低但通常非零；
- 自然策略的区间控制状态：按明确新合同更新；
- 已发生的计算费用与轨迹风险分析记录：不能把换来源当作免费清账。

风险统计是否采用加和、平方和或含相关项，需以实际目标和校准为依据。不要把同一出生误差按每步独立噪声重复融合，也不要在没有验证的情况下把一次校准余量当作全程误差保证。

## 7. 可以形成论文的方法增量

当前可开发的主张：

> 对带误差、且彼此相关的缓存来源，以同一参考语义完成读出、融合和风险评估，并联合选择修正强度、更新精度和更新时间。

与近邻的关系：

- RA 已覆盖 guided cross-term、传播先验与联合刷新。我们应复用它，而不是再宣称发现 CFG 抵消。
- FoCa、HyCa 已把外推和校正放在数值方法框架。我们的重点不是换一个 ODE 名字，而是异质来源、相关误差和触发成本。
- AdaCorrection 已有偏移估计及自适应修正权重；必须对照“动态调 α”这类通用表述 [R7]。
- BAG/GCache 已覆盖预算/轨迹门控和局部到全局影响；不能把普通 look-ahead 或小 controller 本身说成原创 [R8,R9]。
- 扩散语言模型也已有 Kalman 启发的 confidence extrapolation，不能声称“首次将 Kalman 用于扩散加速” [R10]。

应优先对照：合理 RA、RA+A 无 P、正确参考的简单 P+A、固定 γ、H=1 调度、H=2 完整方法。若贡献只有修正一个参考 bug，应诚实收窄；若一致来源估计＋调度在新输入和多个工作点有可复验额外价值，则可以成为方法贡献。

## 8. 目前最值得保留的两条路线

**论文确认线：**原冻结 RA+阶段A → E2 → 真实质量—时间曲线。不得用新 P 状态改变原 E2 科学问题。

**方法开发线：**自然 NONZERO 失败状态 → 来源一致读出/有限融合 → 来源相关风险 → H=1/H=2成本调度 → 新组合确认。

两条线共享校准和诊断代码，但不共享测试调参；P 正式完整卡继续暂缓。开发线的每一项都应有可运行的小候选，不要求先证明所有理论假设。

## 参考资料（本轮核对的一手来源）

[R1] R. E. Kalman. A New Approach to Linear Filtering and Prediction Problems. 1960. 原文 PDF，已检查预测—创新与误差结构。`https://www.cs.cmu.edu/~motionplanning/papers/sbp_papers/k/Kalman1960.pdf`

[R2] Sebastian Trimpe. Predictive and Self Triggering for Event-based State Estimation. CDC 2016 / arXiv:1609.07534. 重点 §III 的期望损失—通信成本决策，以及 predictive/self-trigger。`https://arxiv.org/html/1609.07534`

[R3] Mohamad Al Ahdab, John Leth, Zheng-Hua Tan. Optimal Sensor Scheduling and Selection for Continuous-Discrete Kalman Filtering with Auxiliary Dynamics. ICML 2025, PMLR 267. 重点是不同精度/成本观测与有限时域调度，本文不搬用其 Poisson/线性假设下的保证。`https://proceedings.mlr.press/v267/ahdab25a.html`

[R4] RA-CFGCache: From Branch-Level Criteria to Guided-Risk Control under Classifier-Free Guidance. arXiv:2609.36433v1. 重点 §3.2–3.4，区间风险重置不等于终点误差清零。`https://arxiv.org/html/2609.36433v1`

[R5] Shikang Zheng et al. Forecast then Calibrate: Feature Caching as ODE for Efficient Diffusion Transformers (FoCa). arXiv:2508.16211. `https://arxiv.org/html/2508.16211v1`

[R6] Shikang Zheng et al. Let Features Decide Their Own Solvers: Hybrid Feature Caching for Diffusion Transformers (HyCa). arXiv:2510.04188. `https://arxiv.org/html/2510.04188v1`

[R7] Dong Liu et al. AdaCorrection: Adaptive Offset Cache Correction for Accurate Diffusion Transformers. arXiv:2602.13357. `https://arxiv.org/html/2602.13357v1`

[R8] BAG: Budget-Aware Gating for Diffusion Caching. arXiv:2608.09231. `https://arxiv.org/abs/2608.09231`

[R9] From Local Mismatch to Global Impact: Optimizing Cache Reuse Policy for Efficient Diffusion (GCache). arXiv:2608.13043. `https://arxiv.org/abs/2608.13043`

[R10] Efficient Diffusion LLMs via Temporal-Spatial Parallel Decoding and Confidence Extrapolation. arXiv:2605.30753. 与视频源缓存任务不同，仅用于排除“Kalman＋扩散首次结合”的过强主张。`https://arxiv.org/html/2605.30753`
