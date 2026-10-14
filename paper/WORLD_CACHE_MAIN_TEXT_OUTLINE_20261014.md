# WorldCache 正文思路、最小算法与图表框架

**设计接续说明：** 新P-ACR/W3-MixTrend见[425](../research/425_WC_P_W3_DESIGN_UPDATE_AND_NEXT_STEPS_20261014.md)。它们尚未验证或并入，本文当前两配置、数学定义、数据与摘要数值保持冻结；只有新闭环结果支持且另作合入决定后再修改正文。

2026-10-14。本阶段实验已收束，原B三臂诊断也已完成；当前只整理已有证据与论文，不新增实验。本文件不修改已交付的TCSVT `main.tex`，也不自动决定投稿渠道。最终证据范围见[424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)，固定归因见[420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)，独立B结果见[423](../research/423_WC_B_FULL312_COMPLETE_ENDPOINT_RESULTS_AND_READOUT_BOUNDARY_20261014.md)。旧[收束设计](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md)中的新实验范围仅作未执行建议。

## 1. 论文的中心问题和题目

**CFG-Aligned Cache Correction with Calibrated Compute Allocation for Video Diffusion**

中文：**面向视频扩散的CFG一致缓存修正与校准式计算分配**。

中心问题：缓存控制器通常评价一种复用预测，但接入修正或部分更新后，实际送入求解器的预测、它的来源误差和执行费用可能已经变化。如何把它们重新对齐，获得有价值的保真—效率工作点？

论文讲清楚两个问题：

- **输出怎样修正：**让当前浅层变化进入复用预测，两CFG分支共享强度，在真实velocity空间保持一致；不同来源使用合适参考。
- **计算怎样分配：**标定实际执行动作的guided误差与费用，得到可验证、可冻结部署的计算安排。

当前以两个已完成工作点和修正归因组织正文。MID与固定策略等价，使正文可以更加简洁：给出校准构造与阶段部署，报告实际保真—费用取舍。内容自适应优势、全四动作连续前沿和相对强简单规则的分配优势均不属于当前已完成主张。

## 2. 两项方法贡献与证据责任

### C1．CFG一致、来源条件化的廉价修正读出

最小核心为当前probe＋过去D剩余深层增量的β=1读出、共享阶段强度、实际warp/head/RF后的融合。复杂β回归不是默认成立的前提。

证据链：同状态16点来源一致A全部优于C；P参考失配2/8对融合8/8；效率配置完整视频/平衡测速；同26D位置下固定A比plain平均失真低3.52%、多0.88秒。

原生坐标、共享强度与来源处理是具体设计，不把普通外推、线性混合或CFG交叉项写成首次发现。P源融合目前承担来源机制证据，不将H1的0P高保真改善归功于它。

### C2．对可执行动作校准的计算分配

使用同状态、同guided空间的动作误差，来源×阶段统计、传播幅度平方与实际增量费用；保护/缺支持回退明确。当前高保真策略得到D1–24、A25–29、C30、D31、C32–35、D36，可以冻结部署。

证据链：实际动作校准与可执行策略→完整视频/四新提示词双seed→MID与固定阶段部署等价、同26D的A/plain归因。旧风险排除A的下包络分析用于简短设计说明/附录。主张是可用校准与计算安排，不是加权和公式首创、全局最优或内容自适应优势。

当前C2定位为“高保真工作点和校准导出的阶段部署”。同费用强基线与简单规则比较尚未完成，作为未来扩大分配优势主张的证据建议保留，当前不执行；三λ窄范围不描述整个150–223秒区间。

第三条可写为系统验证：冻结骨干、完整视频、实际计时、新输入双seed确认和来源机制。第二模型迁移与最小部署profile尚未完成，不列为已验证贡献；F、B和H2不增加主方法模块数。

## 3. Problem Formulation：指标与范围

对同条件、同初始噪声的完整Native输出 \(V_{ref}\)，研究

\[
\min_{\pi,\mathcal A}\mathbb E[D(V_{\pi,\mathcal A},V_{ref})]
\quad\text{s.t.}\quad\mathbb E[T_{\pi,\mathcal A}]\le B.
\]

其中 \(D\) 的主实证为全帧LPIPS，\(T\) 为模型驻留的文本＋去噪＋VAE及全部正常算法费用。旧少步Native开发资产保留各自协议身份；它尚未进入当前最终共同确认，新的同口径少步比较仅列为建议。这个问题定义不是已被全局求解的优化证明；部署评分只是局部经验代理。

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

\(g_t\)来自真实同状态CC/DD与Dense续推的终点latent差/当前guided差幅度比，所以MSE用平方；不是Jacobian范数上界。动作报价在双probe已支付之后，D/P来源A报价分别对应必要head数量；原报价有旧计时转移，最终最小部署profile尚未完成，当前不补开实验。

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
|5 Experiments|3.7页|统一协议→开发工作点→冻结确认→固定归因→来源机制与已有计时→简洁案例|全部使用已完成证据，每节一个论证职责|
|6 Conclusion|0.2页|强化已证实的两项价值与适用范围|不在结尾另开F/B项目|

正文使用以下已完成实验子节：

1. **Protocol and Re-evaluated Baselines：**Cosmos-Predict2.5-2B、A6000、768×432/93帧、实际36更新/72分支调用、CFG 8/−7；同提示词同seed完整Native参考，全帧LPIPS与实际主计时。主边界为文本编码＋去噪＋VAE及算法必要费用，加载/预热/写盘/取证另列。WorldCache与本地校准RA按各批manifest定义，作者报告2.30×/2.10×另列背景，不作跨平台排名。
2. **Measured Fidelity–Latency Operating Points：**420四CAL、seed0同批比较。效率A_NO_P为148.8959秒/LPIPS0.3781446，相对WC时间少13.72%、失真低11.16%，四场景均改善；相对RA平均多2.09秒、失真低9.67%。高保真MID为222.9058秒/0.0585928，Native加速1.2674×。P_OFF为已有来源条件配置的次要质量取舍点。这里是已测配置比较，不声称完成合理调参强基线的整个前沿。
3. **Frozen Confirmation on New Inputs：**417的四新提示词×seed17/43、五方法、40正式＋10预热。H1八视频均评分，提示词等权LPIPS0.0530368、Native加速1.2681×；相对同批P_OFF失真低84.6018%，八视频均改善。效率A与P_OFF对RA各6/7可配对改善；RA一格拒绝，完整八视频RA保真均值不填，robot seed43反例保留。开发与确认分开，不把帧当独立视频，也不把已曝光输入再称下一版未见。
4. **Readout and Schedule Attribution：**420四正式MID/FIXED_A终态、动作、93帧RGB一致；两轮AV28预热144guided逐位一致。固定26D位置，五A对plain平均失真低3.5196%、多0.8762秒，四场景3改善/1退化；Human增加2.9476%。LOW与plain相同，HIGH均失真比MID高16.5427%、四视频各93/93帧退化；三λ仅改变A0/5/7，均26D/0P，是窄区敏感性。固定部署已实现的等价与修正增量分别解释，不推导内容自适应或简单规则优越性。
5. **Source/Phase Mechanism and Runtime Evidence：**D/P×早晚16同状态点、P旧D参考2/8与来源一致融合8/8，以及必要的guided/分支误差关系。旧E3来源规则反转解释来源语义的重要性。已有两场景20正式正反测速作为效率配置的重复计时证据，保留各轮波动和Human对RA速度排序变化；不能代替新版高保真重复测速。报告当前实现依赖，不填未测最小校准费、维护税或显存。
6. **Qualitative Evidence：**使用已有同场景同seed完整视频与固定时间点展示两个配置，给出与定量表对应的案例身份。LPIPS证明Native保真，定性材料不另行生成物理/语义质量结论，不新增人工评审。

已完成证据的论证顺序为性能→冻结确认→归因→机制。主文保持Cosmos本地协议、Native保真和两种实际配置的范围；未来强基线、强规则、迁移与部署profile统一列在第10节，不作为本阶段继续计算的前置条件。

## 7. 主图和主表：一张图只承担一个任务

|图表|职责|使用的已完成证据|
|---|---|---|
|Figure 1：实测效率—保真工作点|让读者立即看到两个不同费用下的实际保真取舍|420开发点与417冻结确认分面；标出效率A与高保真H1，不连成连续λ前沿|
|Figure 2：方法总览|离线动作标定小侧栏＋在线读出/执行主链|蓝/绿表示新增读出与一致校准，灰表示原WC/RA；P扩展虚线，F/B不入主图|
|Figure 3：来源/阶段机制|实际输出误差为何需要按来源与阶段校准|16点、P旧参考2/8与融合8/8；不把state当独立video|
|Table 1：共同开发结果与冻结确认|分别呈现同批方法比较与新输入证据|开发表列Native/WC/RA/A_NO_P/P_OFF/H1；确认另分表，RA缺格、各自分母与可配对子集明确|
|Table 2：固定刷新归因|拆开修正读出、相同D位置与阶段重放|MID/fixed A/plain及四场景变化；附预热guided与正式RGB等价的各自范围，Human反例完整保留|
|Table 3：已完成平衡测速，可移附录|说明效率配置的实际时间与波动|旧20正式测速两场景/正反两轮，按原五配置身份；不替代新版高保真重复或部署profile|

方法图的视觉中心是“**实际输出修正与对应评分的一致性**”，不是把WC、RA、W1、稀疏四个盒子串起来。当前高保真部署标注26D/5A/5C；动态四动作评分放离线/通用框架侧栏，不暗示其已贡献内容自适应收益。

F频域特征、B完整诊断、旧H2、早期技术失败、取证和恢复细节放独立探索/复现附录，不并入当前主方法。F为RAW预测改善但动作/regret不变，Haar/FFT没有当前决策增量；已登记的差值CPU假设未执行。

**B附录的准确范围：**423登记三臂已完成，4父＋12后缀、16输出、312pairs，全部93帧评分。三臂共享首次真实C状态，分别返回C、保存Dense速度或保存L2速度，随后恢复原pi0。四状态等权C/Dense/L2的LPIPS为0.3272410/0.3289287/0.3300823；Dense对C三改善一退化、均失真增加0.5157%，L2对C两改善两退化、增加0.8682%。两个晚期点L2与Dense接近，Human早期代价保留；来源与阶段共变，不单独归因为来源。

额外父复放检查在两P点成立：原父和诊断首读出均C，后续guided/终态/动作/RGB一致。两D点原父物理动作也是CC，但实际为A读出、α=.5；三臂首步统一纯C、α=0，因此首次guided与终态/RGB不等价，物理动作尾一致。原差异不改写为四点父等价通过，也不能据其不同直接断言恢复错误；Dense/L2对纯C的比较不表述为替换原父A的收益。

B本卡没有实际B刷新执行、新B来源、连续B闭环或干净端到端测速，保存速度不计作在线免费动作。旧L2局部约7.1%节时与本卡终点后果保持各自身份；登记三臂完成不升级为B净加速。详见[423](../research/423_WC_B_FULL312_COMPLETE_ENDPOINT_RESULTS_AND_READOUT_BOUNDARY_20261014.md)。

## 8. 相关工作比较的准确落点

|基础/近邻|已有能力|本文具体增量与当前比较范围|
|---|---|---|
|WorldCache|probe、运动/显著性调度、投影混合、warp、阶段阈值|当前浅层增量的实际输出修正及其动作校准，而非再次提出phase/cache|
|RA-CFGCache|guided联合误差、跨支相关、传播先验与共同刷新|新增可选修正读出、对应真实误差/报价与来源语义|
|AdaCorrection|偏移估计、缓存/新鲜预测混合|本方法实际坐标、CFG耦合、来源/执行对象和必要费用的具体差异|
|GP-Refiner|GP预测修正、不确定性触发重算|不要求GP后验的轻量动作标定、精确读出/来源维护及真实取舍|

具体差异落在实际算法和执行语义，不以不同基模代替新颖性。当前WC与本地校准RA已有直接结果，AdaCorrection/GP-Refiner用于相关工作定位；忠实直接比较尚未执行，列入第10节建议，不新增近邻实现或GP/频谱模块。

来源：[WorldCache](https://arxiv.org/html/2603.22286v1)、[RA-CFGCache](https://arxiv.org/html/2609.36433v1)、[AdaCorrection](https://arxiv.org/html/2602.13357v1)、[GP-Refiner](https://arxiv.org/html/2609.05981)。

## 9. 摘要与引言：采用已完成证据的初稿

摘要五句按现有证据形成主干：

1. 视频扩散缓存减少重复深层计算，但修正后实际输出、原风险估计和费用可能失配。
2. 本文提出CFG一致缓存修正，将当前浅层变化与可靠历史结合，在真实输出空间共享修正强度。
3. 对可执行动作的guided误差与费用进行离线标定，导出可冻结部署的阶段计算安排。
4. 在Cosmos本地开发对比中，效率配置比重评WorldCache时间少13.72%、平均LPIPS失真低11.16%；在四新提示词双seed确认中，高保真配置相对Native加速1.2681×、平均LPIPS为0.0530368，构成另一个费用工作点。
5. 相同26D刷新位置下，五次修正读出令平均失真降低3.52%；来源机制与阶段重放分别支持修正设计和固定部署的解释。

可直接改写为摘要段落：

> 视频扩散缓存减少重复深层计算，而修正读出需要与实际输出、风险估计和执行费用相互对应。我们提出CFG一致缓存修正，将当前浅层变化与可靠历史的深层增量结合，在真实输出空间共享双分支修正强度。我们对可执行动作的guided误差和费用进行离线标定，并导出可冻结部署的阶段计算安排。在Cosmos本地开发对比中，效率配置相对重评WorldCache减少13.72%的时间并降低11.16%的平均LPIPS失真；在四新提示词、两个seed的冻结确认中，高保真配置相对Native加速1.2681×、平均LPIPS为0.0530368。相同26D刷新位置的消融显示，五次廉价修正使平均失真降低3.52%，来源机制和阶段重放进一步解释了方法的保真—计算取舍。

13.72%/11.16%来自420同批四CAL开发比较，1.2681×/0.0530368来自417冻结确认，3.52%来自420固定刷新消融。两种配置、两个人群与各自分母在实验部分明确，不能拼成近2×且失真低约85%的同一性能点。摘要不填SOTA、连续λ前沿、内容自适应优势、广泛模型迁移、物理能力或未测部署费用。

引言按四段：成本/应用问题→加入修正后读出、风险与费用需要协调→本方法的具体解法→两项方法设计及最强同条件结果。正文现在围绕已完成证据写作，不等待未执行的共同新测试或迁移后才填写性能句。

## 10. 证据检查与未执行建议

保留有影响的反例和拒绝分母，但不把正文写成实验流水账。Human fixed-A的退化放归因完整表；robot seed43及RA拒绝保留共同测试分布；P来源组合反转用于说明来源机制；HIGH的全视频退化放开发/敏感性材料。

最终主张—已完成证据配对：

|主张|使用的证据|保持的实际范围|
|---|---|---|
|廉价修正形成实际工作点|420同批A_NO_P/WC/RA及旧平衡测速|相对本地WC共同收益；相对RA为更低失真、略多时间，保留逐轮排序|
|高保真配置在冻结新输入上成立|417四提示词×双seed、八H1视频|单模型有限新输入确认；拒绝与robot反例保留，不称大规模泛化|
|修正本身影响完整终点|420固定A/plain，同26D位置|均改善3.52%、3/4场景，Human退化保留；局部标签不替代终点|
|当前H1可以阶段部署|四正式终态/动作/RGB与两个AV28预热144guided等价|没有内容自适应或稳定省控制税的额外收益主张|
|来源/阶段语义影响修正|16同状态点、旧参考2/8与融合8/8、E3交互|P扩展的机制证据，不归因为H1的0P收益|
|F/B已经完成的探索|F决策不变；423同首C三臂终点诊断|独立附录，不并入主方法，不把B saved速度当实际B刷新或净加速|

以下证据建议保留问题与用途，**本阶段不执行，不因余额、旧预算权限或稿件写作而自动恢复**：

|未执行建议|未来可检验的问题|当前正文处理|
|---|---|---|
|合理调参WC/RA、同口径Native少步、一个忠实修正近邻|两个工作点在强基线同费用/同保真区域是否有独立增量|使用现有已测配置，不称完整强基线前沿|
|同26D均匀/粗阶段规则|校准安排是否优于简单分配|保留fixed等价与A/plain归因，不称规则优越性|
|更广泛、全部最终对手共享的新输入/seed矩阵|冻结后优势分布与更大提示词范围|采用417现有确认，不把64提示词或其他新矩阵列为已完成/待执行承诺|
|最小部署重复测速、必要离线标定/维护/显存profile|稳定净费用与真实部署开销|列已测主时间和标定依赖，不报未测费用或回本次数|
|第二骨干、相关自动质量维度|迁移、运动/语义质量|主张限定Cosmos与Native保真，不启动第二模型或新评分实验|
|F动作收益差、真实B连续刷新与来源寿命|探索是否能成为下一版贡献|原F未执行假设与B完成诊断归档，不自动并入或续开CPU/GPU|

这些建议决定将来可扩大哪些主张和投稿范围，不成为本阶段继续实验的理由。当前完成的工作是证据、公式、算法、图表与文字之间的一致整理。

代码锚点：[原残差坐标](../cache/runtime/cosmos_predict2/_src/predict2/inference/worldcache_utils.py)、[D参考读出](../src/wcomr/cfg_guided_w1_deployment.py)、[P来源velocity融合](../src/wcomr/math_n2_source_readout_r1.py)、[真实风险表](../src/wcomr/source_phase_table_fit_r1.py)、[H1动作校准](../src/wcomr/source_phase_absolute_h1_control_r1.py)、[阶段部署控制](../src/wcomr/source_phase_fixed_mask_r1.py)。
