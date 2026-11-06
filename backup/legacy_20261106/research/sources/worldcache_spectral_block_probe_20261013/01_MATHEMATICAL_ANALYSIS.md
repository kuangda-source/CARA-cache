# 频域调度与部分 Block 刷新：数学可行性与边界

日期：2026-10-13。状态：研究分析与候选设计，不是新增真实模型实验结果。

## 0. 结论与材料范围

两条路线都有合理数学基础，适合先进入轻量探索。

- **F：频率条件的动作判断**。合理之处在于改变误差度量或对原有标量统计进行分解，而不是 FFT 本身提高了信息量。优先使用共享线性滤波／Haar 统计、小规模空间 FFT，保持原生成器和基线策略不变。
- **B：部分 Block 更新执行器**。可以减少真正执行的矩阵乘法，但必须明确缓存对象和上下文。优先比较更多层的部分 MLP、少数完整 Block 的残差保持，以及“当前完整 K/V＋活跃 Q 和 MLP”。陈旧 K/V 是更进一步的近似，不是第一版必须引入的前提。
- 两者分别改善决策信息和动作成本；先分别筛查，再做一个小型组合，不能要求每个模块在第一次试验中达到最终论文门槛。

项目事实依据是用户提供的 380 N2 报告及此前 10 月 9—11 日说明。当前强锚点为 A_NO_P/P_OFF；N2 H1/H2 未使用 A，D 都由保护／支持域回退触发。当前 P 只对四层约一半 token 的 MLP 做部分更新，attention 仍全算。频域与 Block-v2 均不是当前已经验证的算法。

当前请求是分析与设计。本方案不启动 GPU、不改主线、不改 E2、不启用用户已经暂缓的完整 P 参考卡。旧报告预算不是实时余额。

## 1. 符号与索引

- n：实际去噪更新的顺序；tau_n：真实噪声／solver 时间。
- f：视频 latent 的时间坐标；(x,y)：空间坐标。**f 与 n 不是同一个时间轴。**
- l：Transformer block；h_l：当前整段视频 token 表示。
- p_c,p_u：两 CFG 分支当前已经计算的浅层 probe。
- s：合法缓存来源，可能是 D 或 P；p_s 和其他元数据必须指向同一来源。
- e_c,e_u：相对同一个实际状态上的 dense teacher 的输出误差。当前模型 e_g=8e_c-7e_u。
- L：深层 block 数，当前为 26；N：实际 token 数；d：hidden width；r：MLP expansion ratio；eta：活跃 token 比例。

除直接比较同状态 teacher 外，旧 native 轨迹上的输出不能冒充当前状态的 teacher。

## 2. F：FFT 为什么可能有价值，又为什么不是充分条件

### 2.1 纯正交变换不会改变 L2 距离

令 F 为单位化 Fourier 变换，F*F=I。对任意差分 Delta p：

    ||F Delta p||² = ||Delta p||².

因此，FFT 后原样求全部频点平方和，只是重新表达原距离。没有新增判别信息。相对于只保留一个原始标量的方案，保留多个频带统计可能增加可利用的信息；但它们仍是原张量的确定性函数。

频带加权定义：

    d_W² = (Delta p)* F* W F (Delta p),   W=diag(w_f), w_f>=0.

它是一个半正定二次型。全部权重相同退化为原 L2；有权重为零时是半范数，不应说能识别所有变化。要有效，W 必须更接近实际任务敏感度，而不是仅使训练样本上的某项指标变小。

### 2.2 为什么 Fourier 可能近似任务相关的二次型

在小扰动、固定线性化点下，把从当前预测扰动到最终感知特征的映射记为 G，则零基准附近的局部敏感度代理为：

    D_sens(delta) ≈ delta* G*G delta.

若 G*G 近似空间平移不变，其 Fourier 表示接近对角，频率加权便是一种廉价近似。Transformer 的内容相关 attention 通常不严格平移不变，因此这只是可检验的建模假设。

更一般地，当前轨迹已有参考误差 e，动作带来 delta 时：

    D(e+G delta)-D(e) ≈ 2<e,G delta>+||G delta||².

频带能量主要刻画二次项，不能自动表达方向相关的一次项。故频谱改善局部误差预测后仍须小规模终点验证，不能宣称已预测最终动作价值。

### 2.3 Wiener 模型提供什么、不提供什么

在 x_tau=a_tau x_0+b_tau eps、信号与单位白噪声不相关、采用线性平移不变估计器的假设下，对干净信号的线性 MMSE 响应是：

    G_tau(omega) = a_tau S_x(omega) / (a_tau² S_x(omega)+b_tau²).

SeaCache 将这一类谱先验用于阶段相关的输入滤波与复用距离。[R1]

这能解释某些数据和去噪阶段为何适合不同频率响应，但不能推出：

1. Cosmos 的浅层 residual 也满足同一个 signal/noise 模型；
2. 高频总是噪声，低频总是语义；
3. 最优去噪滤波器就是最优缓存动作判据；
4. 模型请求步数可直接替代实际 solver tau；
5. 提高滤波相似度必然改善最终 LPIPS。

SenCache 本身侧重 latent 和 timestep 的敏感性，而非 FFT 核心算法；本探索中傅里叶参考为 SeaCache，敏感性解释另引 SenCache。[R1,R2]

### 2.4 时间变化的滤波器会产生额外“变化”

SeaCache 比较不同阶段各自滤波后的表示，这是它的方法定义，不是错误。但在我们区分来源变化时，要注意：

    G_n F p_n - G_s F p_s
      = G_n F(p_n-p_s) + (G_n-G_s) F p_s.

即使 p_n=p_s，第二项仍可能非零。它编码了滤波器／阶段变化，而不全是特征漂移。

探索对照：

- 主要候选使用同一个当前 G_n 作用于 p_n 和来源 p_s；
- SeaCache 式双时间滤波作为后续一个指定对照；
- 基线保留真实 tau、Delta tau、source、age，以排除频谱仅重学阶段规律。

### 2.5 不能丢掉相位

信号循环平移不改变幅度谱，但会改变相位和空间位置。正确的源差分统计优先使用：

    |F p_n - F p_s|²,

而不是：

    (|F p_n|-|F p_s|)².

CFG 交叉项也必须保留复内积的实部。两分支使用同一线性算子 T：

    T(8e_c-7e_u)=8T(e_c)-7T(e_u).

对频带 b：

    q_b=64||T_b e_c||²+49||T_b e_u||²
        -112 Re <T_b e_c,T_b e_u>.

完整正交分带且同权时，sum_b q_b 就是原 guided L2。新价值来自条件权重或保留频带差异，而不是发现新的 CFG 公式。[R7]

真实 e 只用于离线标签。在线的 8 Delta p_c - 7 Delta p_u 是 probe 代理，不是实际 guided 输出误差；hidden 到输出经过非线性映射，必须校准。

### 2.6 更便宜且更适合局部选择的备选：Haar

对不重叠 2×2 空间单元 (a,b;c,d)，定义：

    LL=(a+b+c+d)/2
    LH=(a-b+c-d)/2
    HL=(a+b-c-d)/2
    HH=(a-b-c+d)/2.

这是正交变换，四系数能量之和等于四原值能量。几次加减即可获取空间低频／方向差分，且保留空间位置。

使用不重叠正交 Haar 是为了避免把一般低通与高通残差误说成正交分解；普通高斯低通 Lx 和 x-Lx 通常存在交叉项。

全局 FFT 的 band energy 能判断“变化属于哪类频率”，但不能直接定位“刷新哪些 token”。需要位置时，先看 Haar／局部差分图，不要自动把全球频谱能量用于 Top-K token。

### 2.7 张量处理与真实成本

首版使用固定 8–16 个预登记通道，保留相同索引；不先跨 channel 求均值，以免相消。固定子采样不保证代表所有通道，所以和全特征 raw 统计、同子采样 raw 统计分别对照。只有必要时才加入随机投影，投影本身计费。

空间 FFT 只沿真实 H/W token 网格，不对展平后 token 顺序或 hidden 通道做“空间 FFT”。视频 latent 的帧轴不能默认为原始 93 帧。

可先低通／Haar 后降采样到不大于原形状的 <=64×64 网格；被删掉的高频能量须在降采样前计算，不能拿降采样频谱声称保留了原始高频。

L2 可以在频域直接求和，不需要 iFFT。rFFT 只保存半谱时，要对非 DC、非 Nyquist 的共轭成对频点补权；先与完整单位化 FFT 做一致性测试。若采用窗函数，窗函数本身改变度量；原始／窗化不得混成同一结果。

成本包括 gather、布局转换、滤波、FFT、聚合、来源频谱写回、同步，不能只记录 FFT kernel。

## 3. B：部分 Block 刷新的三种精确定义

### 3.1 扩大部分 MLP 覆盖

保留完整 attention，在更多层仅更新部分 token 的 MLP。当前四层一半更新，若各层 MLP 费用相等，只省约 4×0.5/26=7.69% 的深层 MLP 计算，不是整个深层的 7.69%。这与已有整组省时很小相容，并不证明执行器失败。

更多层可能提高可省比例，同时增加缓存和误差；不保证层越多越好。先测试 8 层一个配置，不展开所有层数和比例笛卡尔积。

### 3.2 层级／整 Block 残差复用

将真实 block（含必要条件和时间参数）抽象为：

    h_{l+1}=h_l+R_l(h_l,tau,c).

刷新集合为 S 时：

    hat h_{l+1}=hat h_l+R_l(hat h_l,tau,c),             l∈S
    hat h_{l+1}=hat h_l+R_l^cache,                      l∉S.

复用对象是残差／创新项，不是用旧 h_{l+1} 整体覆盖当前输出。后者会把当前 identity path 的变化一起删除。

缓存误差的来源：

    R_l(h_n,tau_n)-R_l(h_s,tau_s)
      ≈ J_h Delta h + (partial_tau R_l) Delta tau.

因此即使 hidden 变化不大，时间条件／调制变化也不能忽略。真实 block 可能有多个 residual、AdaLN/RMSNorm、gate、cross-attention，具体缓存位置需要按源码定义，不把普通残差网络示意当作现有 API。

令同当前近似输入上的局部复用误差为 delta_l，有：

    ||e_{l+1}|| <= (1+L_l)||e_l||+||delta_l||.

在线层的 L_l 未知，此式用于解释误差如何传播，不能拿松上界宣判每个跳层都不安全。后层全算不能保证把早层误差清零。

BWCache 提供 block 特征缓存先例，但它不证明我们任意层子集刷新或跳层都有效，不能把其结果直接当作本地先验结论。[R3]

首版仅跳 2 个预登记 block，其他 block 保持当前计算；必要时扩到 4 个。不要全 26 层同时建立并优化复杂策略。

### 3.3 活跃 token 的 Block 更新：先用 fresh K/V

选活跃行 M，计算当前完整 K,V，但只计算 Q_M、活跃输出投影和 MLP：

    O_M=softmax(Q_M K_t^T/sqrt(d_k)) V_t.

**在同一层、同一完整当前输入、相同 mask/位置编码/精度下，它在精确算术上就是 full attention 的 M 行。**GPU kernel 改形状后，浮点结果可能有小差异；不是要求无依据的 bitwise 一致。

这提供一个很有价值的中间方案：不先引入陈旧上下文，就测试少量 query 与 MLP 计算能省多少。

对非活跃行保留当前 residual skip input，复用合法旧 attention／MLP residual，而不是覆盖为旧完整 hidden。两次 residual 写回分别定义。涉及 cross-attention、条件 token、位置编码与调制时保留其真实语义，未测部分保持 dense 并计费。

当输入已受上游近似影响时，“active attention 对该输入精确”不等于“相对原生整网精确”。

### 3.4 再增加 stale K/V：收益更大，误差源也增加

RAS 一类方法使用：

    tilde O_M=softmax(Q_M [K_M,tilde K_I]^T/sqrt(d_k)) [V_M,tilde V_I].

未更新 token 仍以缓存 K/V 提供完整上下文；不能把它们从 softmax 分母与 value 集合中删除。[R4]

在 Q_M 固定、同一有效 mask 下，令 Delta K、Delta V 是缓存偏差，可得一个保守界：

    ||tilde O_M-O_M||_F
      <= ||Q_M||_2 ||Delta K||_F ||V||_2/(2 sqrt(d_k))
         +||tilde P_M||_2 ||Delta V||_F.

推导：softmax Jacobian 为 diag(p)-pp^T；最大行绝对和 2p_i(1-p_i)<=1/2，因此其 2-norm 不超过 1/2。再对 (tilde P-P)V+tilde P Delta V 使用矩阵范数界。

该界通常不紧，但清楚区分 key 引起的权重偏移和 value 内容偏移。**token 自己变化小，不代表它对其他 query 不重要。**局部频率或低更新分数不能自动证明可删除其上下文。

### 3.5 计算量不是 eta²

忽略小算子，一个标准 block 可近似为：

    F_D ≈ (4+2r) N d² + 2 N² d.

fresh K/V 的活跃行版本：

    F_fresh ≈ [2+eta(2+2r)] N d² + 2 eta N² d + F_state.

stale K/V 版本：

    F_stale ≈ eta(4+2r) N d² + 2 eta N² d + F_state.

所有 query 仍访问 N 个 key，因此 attention 项按 eta 缩放，不是 eta²；eta² 对应只剩 eta N 个 key 的不同算子。融合 QKV kernel 若仍全量计算 Q，必须按实际路径计费。

真实时间不能按 FLOPs 比例直接推断。选择、gather/scatter、状态读写、布局、kernel 利用率和完整上下文读取都可能限制收益。[R4,R6]

### 3.6 显存与缓存税

k 个层、两 CFG 分支各保存一个 N×d residual，以每元素 b 字节计，至少：

    M_res=2kNdb.

若另存每层 K/V、attention residual、MLP residual，费用按实际张量求和；有 GQA 等实现时不能机械使用同一 hidden width。

初始化与维护必须由真实历史填充，计入 dense 或 P 的实际成本。不能在待跳步骤先全算再生成“旧缓存”，也不能将 host 诊断快照内存与部署工作缓存内存混为一谈。

## 4. F 与 B 怎样结合，什么不能假定

两者都可看成对不同子空间分配预算：F 表示观测／度量空间，B 表示执行选择。

但一般有：

    F M_token != M_frequency F.

全局 Fourier 权重不等于空间 token mask，非线性 Transformer 更没有自动可分离性。因此首轮分开测试 F 的判别能力和 B 的执行收益；有信号后再做一个小 2×2 组合，不声称必然相加。

CFG 两分支优先采用同一 mask／同一滤波坐标，保留不同数据和来源。共享选择是合理的稳定起点，ToCa 已有直接先例，不单独作为创新。[R5]

局部 Haar 图比全局频谱更适合后续 token 选择；仍须超过同配额随机／轮换。DuCa 已给出随机选择很强的证据，不能隐藏这一对照。[R6]

## 5. 成本条件与可证伪命题

F 值得部署的最低经济条件：

    被替代／减少的真实计算费用 > 所有新增特征与控制费用。

若只希望从现有 P 替代 D 取得约 0.08089 秒／次的微小节省，每步都付几十毫秒可能就不合算；若能避免一次完整 D，空间会不同。不能孤立说“FFT 只有 1% 所以忽略”。

新 P 值得替换旧 P 的条件是端到端费用与保真的可接受折中，而不是必须每个局部 MSE 都更好。若插入原本 C 的位置，应计算：

    新增当前成本 = c_P'-c_C,

并与未来节省和质量收益一起比较。

本探索分别验证：

- F-H1：给定 source、tau、age 和现有 raw/RA proxy，频带特征仍改善动作判断。
- F-H2：其净收益超过特征开销，且并非只学到阶段规律。
- B-H1：至少一种部分 Block 执行在真实设备上形成更好的动作成本—误差点。
- B-H2：该来源在后续自然或明确受控的使用中不产生抵消全部节省的频繁重算。
- X-H1：两者组合的优势是否超过原部件的朴素串接。

## 6. CPU 代数检验

随包提供 math_sanity_checks.py 和结果。已在 NumPy CPU 合成数据上检查 Parseval、Haar 能量守恒、相位丢失反例、不同滤波器的虚增距离、CFG 交叉项、fresh-KV 活跃行等价、stale-KV 保守界、旧输出覆盖反例。

这些检查只防数学／实现概念错误，不证明 Cosmos 效果、GPU 速度或论文贡献。

## 7. 一手资料（2026-10-13核对）

[R1] Chung et al., SeaCache: Spectral-Evolution-Aware Cache for Accelerating Diffusion Models. arXiv:2602.18993v1，§4、附录7/8。`https://arxiv.org/html/2602.18993v1`

[R2] Haghighi and Alahi, SenCache: Accelerating Diffusion Model Inference via Sensitivity-Aware Caching. arXiv:2602.24208v2，§4。`https://arxiv.org/html/2602.24208v2`

[R3] Cui et al., BWCache: Accelerating Video Diffusion Transformers through Block-Wise Caching. arXiv:2509.13789v1，§3。`https://arxiv.org/html/2509.13789v1`

[R4] Liu et al., Region-Adaptive Sampling for Diffusion Transformers (RAS). arXiv:2502.10389，§3.2–3.4。`https://arxiv.org/html/2502.10389`

[R5] Zou et al., Accelerating Diffusion Transformers with Token-wise Feature Caching (ToCa). arXiv:2410.05317v4，Appendix A.1.2–A.1.3。`https://arxiv.org/html/2410.05317v4`

[R6] Rethinking Token-wise Feature Caching: Accelerating Diffusion Transformers with Dual Feature Caching (DuCa). arXiv:2412.18911v3，§IV。`https://arxiv.org/html/2412.18911v3`

[R7] Liu et al., RA-CFGCache: From Branch-Level Criteria to Guided-Risk Control under Classifier-Free Guidance. arXiv:2609.36433v1。`https://arxiv.org/html/2609.36433v1`

本文件中的新公式、候选、成本模型与实验解释是本次推导，不是声称上述论文已经验证了当前 Cosmos 组合。
