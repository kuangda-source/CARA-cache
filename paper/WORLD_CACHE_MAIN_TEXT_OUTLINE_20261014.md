# WorldCache 正文思路、最小算法与图表框架

2026-10-14。本轮形成正文框架，不修改已交付的TCSVT `main.tex`，也不自动决定投稿渠道。实验收尾见[收束计划](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md)，最新归因见[420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)。

## 1. 论文的中心问题和题目

**CFG-Aligned Cache Correction with Calibrated Compute Allocation for Video Diffusion**

中文：**面向视频扩散的CFG一致缓存修正与校准式计算分配**。

中心问题：缓存控制器通常评价一种复用预测，但接入修正或部分更新后，实际送入求解器的预测、它的来源误差和执行费用可能已经变化。如何把它们重新对齐，获得有价值的保真—效率工作点？

论文讲清楚两个问题：

- **输出怎样修正：**让当前浅层变化进入复用预测，两CFG分支共享强度，在真实velocity空间保持一致；不同来源使用合适参考。
- **计算怎样分配：**标定实际执行动作的guided误差与费用，得到可验证、可冻结部署的计算安排。

当前不以“内容自适应调度优于静态”或“全四动作连续前沿”为核心。MID与固定策略等价，使正文可以更加简洁：给出校准构造与阶段部署，并用强规则/强基线说明其价值。

## 2. 两项方法贡献与证据责任

### C1．CFG一致、来源条件化的廉价修正读出

最小核心为当前probe＋过去D剩余深层增量的β=1读出、共享阶段强度、实际warp/head/RF后的融合。复杂β回归不是默认成立的前提。

证据链：同状态16点来源一致A全部优于C；P参考失配2/8对融合8/8；效率配置完整视频/平衡测速；同26D位置下固定A比plain平均失真低3.52%、多0.88秒。

原生坐标、共享强度与来源处理是具体设计，不把普通外推、线性混合或CFG交叉项写成首次发现。P源融合目前承担来源机制证据，不将H1的0P高保真改善归功于它。

### C2．对可执行动作校准的计算分配

使用同状态、同guided空间的动作误差，来源×阶段统计、传播幅度平方与实际增量费用；保护/缺支持回退明确。当前高保真策略得到D1–24、A25–29、C30、D31、C32–35、D36，可以冻结部署。

证据链：实际动作校准与可执行策略→完整视频/四新提示词双seed→固定与强规则归因。旧风险排除A的下包络分析用于简短设计说明/附录。主张是可用校准与计算安排，不是加权和公式首创、全局最优或内容自适应优势。

在公平前沿与简单规则补验前，C2的独立效率优势仍需具体比较。当前先称“高保真工作点和阶段部署”，不使用三λ窄范围描述整个150–223秒区间。

第三条可写为系统验证：冻结骨干、完整视频、真实计时、来源机制及迁移/部署成本；不为凑贡献强行增加F、B或H2模块。

## 3. Problem Formulation：指标与范围

对同条件、同初始噪声的完整Native输出 \(V_{ref}\)，研究

\[
\min_{\pi,\mathcal A}\mathbb E[D(V_{\pi,\mathcal A},V_{ref})]
\quad\text{s.t.}\quad\mathbb E[T_{\pi,\mathcal A}]\le B.
\]

其中 \(D\) 的主实证为全帧LPIPS，\(T\) 为模型驻留的文本＋去噪＋VAE及全部正常算法费用。少步Native作为强替代基线，使用完整Native参考。这个问题定义不是已被全局求解的优化证明；部署评分只是局部经验代理。

保真加速与生成质量保持分别评价。不能把 \(1-LPIPS\) 叫质量保留率，也不能把相对失真下降等同于物理能力提高。

## 4. Method：与代码严格对应的数学定义

### 4.1 原生残差坐标和β=1结构

令 \(o_t^b\) 为分支 \(b\) 的Transformer输入hidden，\(h_t^{k,b}\) 为probe输出，\(h_t^{L,b}\) 为完整栈输出：

\[
p_t^b=h_t^{k,b}-o_t^b,
\quad r_t^b=h_t^{L,b}-o_t^b,
\quad d_t^b=h_t^{L,b}-h_t^{k,b},
\quad r_t^b=p_t^b+d_t^b.
\]

对真实D锚点 \(a\)，

\[
\widehat r_t^{b,D}=r_a^b+(p_t^b-p_a^b)=p_t^b+d_a^b.
\]

β=1含义是保留当前浅层增量、冻结历史剩余深层增量。因 \(\Delta r\) 自带 \(\Delta p\)，β接近1不能全部解释成学会了深层动态。旧拟合β和固定收缩放消融/附录，正文先写最小有效版本。

### 4.2 精确输出算子与共享强度

定义 \(\Phi_t^b(\widehat r;W)\) 为完整候选路径：`warp(o_t+widehat_r, r_W)`→final head/unpatchify→原RF转换，其中warp第二参数仍是真实工作残差\(r_W\)。原 \(v_C^b\) 是完整原WC cache continuation，含当前probe和原残差窗口的 \(\Gamma_t^{WC}\) 插值，不能简化成直接复制 \(r_W\)。

\[
v_{A,D}^b=(1-\alpha_t)v_C^b+
\alpha_t\Phi_t^b(\widehat r_t^{b,D};W),
\quad \alpha_t=\begin{cases}1&t<25\\0.5&t\ge25.\end{cases}
\]

两个分支共享α。实际Cosmos CFG为 \(v_g=8v_c-7v_u\)，所以共享α在这个线性输出空间满足

\[
v_{g,A}=(1-\alpha)v_{g,C}+\alpha v_{g,candidate}.
\]

这是实现一致性恒等式，不保证终点质量改善。共同α与原CFG定义不可变；原WC \(\Gamma^{WC}\)、新的来源 \(\gamma_{src}\) 和传播 \(g_t\) 用不同符号。

### 4.3 来源扩展：真实D与近似P

当有合法P工作来源，另构造 \(\widehat r_t^{b,P}=r_P^b+(p_t^b-p_P^b)\)，分别跑完整候选输出路径及同一α，再融合：

\[
v_A^b=(1-\gamma_{src})v_{A,D}^b+\gamma_{src}v_{A,P}^b.
\]

来源γ只作用于post-RF velocity；不能把hidden或warp前线性关系当作相同公式。D历史只由真实D更新。P保留正出生误差先验，实际误差未知且不当作零。C/A只推进原WC的previous input/internal states等普通C bookkeeping；residual/probe residual窗口、工作残差和出生步不更新，不冒充新D。D/P才写残差窗口。

γ的当前实际来源为旧N1八个自然P状态、四CAL的同状态guided误差，按teacher能量归一化再等权拟合，冻结γ0.7235237006；不是当前16点绝对误差或最终LPIPS最优γ。用权重 \(w_j\ge0\) 表示该归一化，在固定输出/状态上

\[
Q_0=\sum_jw_j\|e_{0,j}\|^2,\quad
Q_1=\sum_jw_j\|e_{1,j}\|^2,\quad K=\sum_jw_j\langle e_{0,j},e_{1,j}\rangle,
\]
\[
\gamma^*=\operatorname{clip}_{[0,1]}
\frac{Q_0-K}{Q_0+Q_1-2K}.
\]

可给短命题：PSD二阶矩、非负固定权重与非退化分母下，该γ最小化这组固定输出的经验二次误差，不高于两个端点。它不推出未见场景、完整视频或控制稳定性保证。正文篇幅不足时，将P扩展与命题移到来源机制小节/附录。

### 4.4 动作误差、费用和阶段部署

已付的两分支probe hidden漂移与本地ρ组成联合根代理 \(\ell_t\)，不是 \(p_t-p_W\) 的完整张量误差：

\[
\ell_t=\sqrt{(8\delta_c-7\delta_u)^2+
112\delta_c\delta_u(1-\rho)}.
\]

对来源×阶段格 \(z\)，用实际标签标定

\[
x_t=(b_W+\ell_t)^2,\quad
\widehat q_C=s_zx_t,\quad
\widehat q_A=a_z\widehat q_C,\quad
\widehat q_P=\mu_{P,z}^{birth},\quad \widehat q_D=0.
\]

\(s_z\)为C真实MSE均值/代理均值，\(a_z\)为A/C真实MSE均值之比；这是经验tied-scale标定，不是逐样本最小二乘或协方差上界。旧正floor \(b_W\) 与新qP单位不同，不写成 \(b_W=\sqrt{q_P}\)。D当前局部误差0不表示重置已有latent/solver偏差。

\[
a_t=\arg\min_{a\in\mathcal A_t}
\{c_{a,source}+\lambda g_t^2\widehat q_a\}.
\]

\(g_t\)来自真实同状态CC/DD与Dense续推的终点latent差/当前guided差幅度比，所以MSE用平方；不是Jacobian范数上界。动作报价在双probe已支付之后，D/P来源A报价分别对应必要head数量；原报价有旧计时转移，部署profile另补。

当前ρ支持query age1–6，保护步/缺ρ/g回退D；仅新表缺格而旧proxy有效时回到原π0，并非所有UNKNOWN都D。P另需真实历史投影、完整双分支和连续次数许可。无online teacher或四个真实动作试算。

MID在开发及八冻结确认视频均得到同一阶段序列，当前固定mask跳过表评分/argmin且输出等价。正文因此区分**离线/开发期的校准决策规则**与**当前实际阶段部署**。

## 5. Algorithm 1：主方法最小可执行版本

正文以当前D/A/C阶段部署给出最小算法，P扩展另列。完整输入包括原WC/RF/CFG/UniPC算子、校准导出的完整计划、α、保护/支持规则；不是只给几个实验卡名称。

```text
Input: frozen generator, original WC operators, full plan π, shared α
State: original WC caches/windows; last true-D anchors (pD, rD) for both branches

for each ordinary denoising update t:
    if actually protected:
        require π[t] == D
        action = D
        v = original full forward pair, heads and RF
        capture its actual prefix and commit real WC state / true-D anchors
    else:
        compute both paid shallow probes using the same actual latent
        action = π[t]                     # current compiled D/A/C deployment
        if planned C/A has invalid ready/proxy/gain support:
            fail with the original technical refusal; do not silently change π

        if action == D:
            v = full deep continuation from the already paid prefixes, heads and RF
            commit real WC state and true-D anchors
        else:
            vC = original WC interpolation, warp, head and RF
            if action == A:
                rhat[b] = rD[b] + p_current[b] - pD[b]
                vCandidate[b] = Φ_t^b(rhat[b]; W)
                v[b] = (1-α[t]) * vC[b] + α[t] * vCandidate[b]
            else:
                v = vC
            advance original C previous-input/internal-state bookkeeping
            preserve residual windows, working-source birth and true-D anchors

    send 8*v_conditional - 7*v_unconditional to the original UniPC update
    commit a complete pair only; preserve original RNG and solver history
```

这不是已省掉所有控制路径的全新实现。当前fixed仍付root/合法性检查；α=.5需要普通C和修正head，当前probe既供A也供普通WC插值。可简化β回归统计、P投影/γ等未使用状态，但须新增等价与真实测速后再纳入最终版本。不得把计划删减当已经测得的费用节省。

伪代码描述当前已验收fixed实现：unsupported的计划C/A会技术拒绝；自动改D属于尚未实现/验收的新fallback。读出自身的原候选guard仍保留：候选不能形成时返回原C并记录原因，不能将无实际修正的事件当额外方法收益。

两个配置都需要完整可复现定义：

|部署配置|动作来源|读出|必要固定输入|
|---|---|---|---|
|效率A_NO_P|本地校准RA式共同CC/DD控制|CC时用D参考阶段β=1 A；不启用P|冻结ρ/g表、RA阈值、保护与支持域、α、原WC算子|
|高保真FIXED_A|校准导出的完整36步计划π|D/A/C按上面Algorithm1执行|完整π、α、原合法域/状态语义、原WC算子|

效率配置在eligible pair上用原联合根风险累计与冻结阈值决定C/D：D直接完整continuation，C使用上述A读出；D更新可靠锚点，A保留D历史。它不是新的绝对q四动作argmin，也不由当前三λ生成。正式正文同时给出该RA式控制的引用、实际本地参数和完整配置清单，不能只靠高保真伪代码覆盖两种配置。

## 6. 正文结构：约8页主体的论证顺序

|章节|建议篇幅|正文要讲什么|主要证据|
|---|---:|---|---|
|1 Introduction|0.9页|缓存近似需要兼顾实际输出与计算费用；本文提供一致修正与校准分配|效率与高保真两个实际点，分开叙述|
|2 Related Work|0.6页|缓存预测/近似、CFG控制、预测修正/不确定性重算|WorldCache、RA、AdaCorrection、GP-Refiner准确边界|
|3 Problem and Design Rationale|0.5页|固定原模型/CFG/网格；目标是匹配Native保真加速；读出—评分—费用为何要绑定|CFG耦合/来源失配简洁引出|
|4 Method|2.0页|β=1坐标与velocity共享修正；来源扩展；动作标定；校准阶段部署和Algorithm1|公式与代码位置对应|
|5 Experiments|3.7页|统一协议→公平主结果→归因→机制→迁移/成本→简洁案例|每节一个论证职责，不按卡号时间展开|
|6 Conclusion|0.2页|强化已证实的两项价值与适用范围|不在结尾另开F/B项目|

正文的实验子节：

1. **Protocol and Baselines：**模型/任务/输入/CFG/实际更新、固定参考、全帧指标、两计时边界、调参公平和分母。
2. **Fidelity–Latency Trade-offs：**调过的WC/RA、少步Native、近邻与两种部署配置；同费用或同保真比较，逐提示词分布。
3. **Contribution Attribution：**MID=fixed的等价；fixed A/plain；强简单规则；共享强度与β=1必要对照。
4. **Source and Phase Mechanism：**D/P早晚16点、P参考失配/融合、必要的guided与分支误差关系。旧E3反转用于解释设计，不平均展示所有历史尝试。
5. **Transfer and Deployment：**第二骨干、模型内重新标定、必要离线费/线上税/显存、最终重复计时。
6. **Qualitative Evidence：**同场景同seed完整视频与固定时间点，公平展示动态内容；不新增非必要人工门槛。

若公平前沿只支持特定高保真区域，就把该目标作为核心应用条件；不要改指标掩盖已注册反例。若简单规则达到同样分配质量，就采用更简洁部署并突出读出/机制贡献。

## 7. 主图和主表：一张图只承担一个任务

|图表|职责|当前可填与待补|
|---|---|---|
|Figure 1：实际效率—保真图|让读者立即看到同质量更快/同时间更准|现有点可填；调过的基线/少步/新共同测试后才能主张前沿|
|Figure 2：方法总览|离线动作标定小侧栏＋在线读出/执行主链|蓝/绿表示新增读出与一致校准，灰表示原WC/RA；P扩展虚线，F/B不入主图|
|Figure 3：来源/阶段机制|实际输出误差为何需要按来源与阶段校准|16点、P旧参考2/8与融合8/8；不把state当独立video|
|Table 1：最终共同性能|Native/WC/RA/近邻/两配置，秒、倍数、LPIPS、相关自动质量、显存、分母|先开发冻结，再新测试；旧跨批次秒数不拼|
|Table 2：关键归因|固定A/plain、两强规则、共享强度/β1/阶段、实际开销|原60部分已完，其余按明确缺口补|
|Table 3：部署与迁移|最小必要校准、费用、在线维护税、第二模型重新标定|当前依赖可整理，最小费用不得凭历史整卡猜值|

方法图的视觉中心是“**实际输出修正与对应评分的一致性**”，不是把WC、RA、W1、稀疏四个盒子串起来。当前高保真部署标注26D/5A/5C；动态四动作评分放离线/通用框架侧栏，不暗示其已贡献内容自适应收益。

F频域特征、B局部约7.1%省时、旧H2、早期技术失败、取证和恢复细节放独立探索/复现附录。只有新终点和净费用成立，才单独提出下一版并入；不把它们作为本稿未完成主模块。

## 8. 相关工作比较的准确落点

|基础/近邻|已有能力|本文应证明的具体增量|
|---|---|---|
|WorldCache|probe、运动/显著性调度、投影混合、warp、阶段阈值|当前浅层增量的实际输出修正及其动作校准，而非再次提出phase/cache|
|RA-CFGCache|guided联合误差、跨支相关、传播先验与共同刷新|新增可选修正读出、对应真实误差/报价与来源语义|
|AdaCorrection|偏移估计、缓存/新鲜预测混合|本方法实际坐标、CFG耦合、来源/执行对象和必要费用的具体差异|
|GP-Refiner|GP预测修正、不确定性触发重算|不要求GP后验的轻量动作标定、精确读出/来源维护及真实取舍|

不能以“使用不同基模”代替算法新颖性，也不因近邻存在就新增一个GP/频谱模块。用最接近且可忠实运行的一个近邻做直接比较。

来源：[WorldCache](https://arxiv.org/html/2603.22286v1)、[RA-CFGCache](https://arxiv.org/html/2609.36433v1)、[AdaCorrection](https://arxiv.org/html/2602.13357v1)、[GP-Refiner](https://arxiv.org/html/2609.05981)。

## 9. 摘要与引言的写作骨架

摘要五句即可形成主干：

1. 视频扩散缓存减少重复深层计算，但修正后实际输出、原风险估计和费用可能失配。
2. 本文提出CFG一致缓存修正，将当前浅层变化与可靠历史结合，在真实输出空间共享修正强度。
3. 对可执行动作的guided误差和费用进行轻量标定，并导出可部署的计算分配。
4. 在【最终冻结模型/测试/基线范围】下，达到【同保真节时或同费用失真改善】，部署标定/显存为【实际结果】。
5. 同状态机制与固定刷新消融说明优势来自【已被数据归因的部件】。

方括号在最终公平结果验收后填写；不提前写SOTA、跨骨干通用或虚拟组合数字。

引言按四段：成本/应用问题→现有方法评价对象与修正动作不一致→本方法的具体解法→两项方法贡献及最强同条件结果。可以现在写问题、方法与贡献初稿；最终性能句等主表锁定。

## 10. 交稿前的证据检查

保留有影响的反例和拒绝分母，但不把正文写成实验流水账。Human fixed-A的退化放归因完整表；robot seed43及RA拒绝保留共同测试分布；P来源组合反转用于说明来源机制；HIGH的全视频退化放开发/敏感性材料。

最终主张—证据配对：廉价修正→公平效率点与归因；校准分配→强简单规则/同费用比较；迁移→新骨干冻结测试；部署成本→必要标定与真实维护税。F/B局部结果不承担已经完成的主方法主张。

代码锚点：[原残差坐标](../cache/runtime/cosmos_predict2/_src/predict2/inference/worldcache_utils.py)、[D参考读出](../src/wcomr/cfg_guided_w1_deployment.py)、[P来源velocity融合](../src/wcomr/math_n2_source_readout_r1.py)、[真实风险表](../src/wcomr/source_phase_table_fit_r1.py)、[H1动作校准](../src/wcomr/source_phase_absolute_h1_control_r1.py)、[阶段部署控制](../src/wcomr/source_phase_fixed_mask_r1.py)。
