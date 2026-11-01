# CARA：缓存读写价值感知的预算化刷新规划

日期：2026-11-01
性质：研究讨论稿；未修改仓库、未调用科研服务器、未执行实验、未新增预算或推送代码。
证据基点：`ec783f2185bab38742dd22f37cf1d56f44de0235` 的研究826；预算搜索采用研究817的冻结身份。本文的新框架尚未实现、标定或验证，不是826已成立的结论。

## 0. 推荐结论

推荐只推进一个机制：**将完整刷新视为同时作用于当前求解器输入和未来缓存来源的混合控制动作，用保留缓存与求解器记忆的离散伴随，估计当前轨迹上刷新动作的终点价值，再在硬预算下生成并验证少数新计划。**

描述性名称为“读写价值感知的刷新规划”，不急于取论文缩写。核心区别不在换一个搜索器，而在改变计算资源的归因单位：从单步缓存误差，改为一次刷新造成的完整状态变化。

它可以输出离线共享、部署时固定执行的计划。第一版不是在线内容自适应，不训练Cosmos权重，也不要求使用Q压缩或A修正。

真正待验证的科学假设是：**缓存写入对后续复用的价值，提供了当前输出误差及其标量传播权重无法稳定提供的信息；保留这一价值，能提高有限校准下的计划质量。**

## 1. 最新证据及其范围

### 1.1 826端点结果

|方法|四旧CAL LPIPS|FIT|旧CHECK|T_DD秒|
|---|---:|---:|---:|---:|
|F19-C|0.249365|0.229234|0.269495|148.258|
|Uniform19-C|0.468931|0.483676|0.454186|仅历史时间，不混合|
|F19-A1|0.231499|0.213176|0.249823|149.256|
|S-DIAG|0.476871|0.491518|0.462225|148.225|
|S-CFG|0.469556|0.484507|0.454605|148.225|
|BudgetSearch19|0.306284|0.270840|0.341727|148.245|
|F19-RiskSwap|0.250091|0.226485|0.273698|148.232|

S-CFG对DIAG降低1.534%，4/4同向，但弱于Uniform、F19-A1和搜索赢家。只保留CFG机制增量，不晋级当前S。

F19-RiskSwap为D21→D35，平均退化0.291%，仅1/4改善、两个CHECK退化。它是一个有限且不稳定的交换效应，不证明D21总不可删，也不证明D35总无用。

全部是四旧CAL、seed0，CHECK多次使用。没有独立最终TEST、统计显著或跨模型结论。

### 1.2 817搜索身份

51次双FIT查询（初始1＋SA30＋HC20），112物理路径；以完整RGB MSE一次选择query39，不能改按LPIPS重选。FIT均值下降43.5819%，实耗7.197644817 GPUh；S为3.039352411 GPUh。相同14 GPUh允许上限不是实耗或信息量匹配。

赢家：`1,2,3,4,5,6,7,10,12,14,16,17,18,20,22,24,25,32,36`。

搜索确实改善其FIT目标，但LPIPS弱于F19-A1。目标差异、有限查询、初始化与结构先验都可能有关；不能仅凭FIT/CHECK均值差推断过拟合。

## 2. 这是一个什么问题？

### 2.1 增广状态

按实际执行顺序编号k=0,...,N−1，实际噪声网格为sigma_k。状态至少包含：

z_k=(x_k,H_k,C_k)。

- x_k：当前latent。
- H_k：实际求解器历史，包括UniPC保存的预测、阶数启动与校正需要的状态。
- C_k：两CFG分支的真实缓存窗口、probe历史、来源噪声位置、warp所需信息与计数。C动作可能更新部分工作状态，不能假定其缓存转移必为恒等。

固定条件、初始噪声和确定性执行后，m_k∈{0,1}控制缓存C或完整D：

z_{k+1}=F_{k,m_k}(z_k)。

这是**有限时域、带记忆状态与部分状态重置的非线性混合最优控制／组合优化问题**。在完整状态上可以Markov化；不能只用“时间步＋age”自动得到充分状态。它不是独立物品的背包，也不天然是每个D后独立重启的更新过程。

### 2.2 CFG与误差

实际两支输出经过原head/RF后，v_g=a v_c+b v_u。当前a=8,b=−7；第二模型必须读取自己的真实系数。

同状态缓存误差e_c,e_u的guided误差平方为：

q_g=a² mean(e_c²)+b² mean(e_u²)+2ab mean(e_c e_u)。

这是正确的局部目标，但不是动作的完整终点价值。

相对Native的预测差分解为：

v_hat_k^pi−v_k^N = [f_g(x_k^pi,sigma_k)−f_g(x_k^N,sigma_k)] + e_k^pi。

D使该步同状态近似误差e_k^pi为零，但不会让第一项为零，也不会把H_k替换为Native历史。因此D不是“清空所有过去误差”。

### 2.3 目标与预算

Native参考固定模型、求解器、噪声网格、输入、seed与精度：V_N=Decode(x_N^N)。部署计划pi输出V_pi。

主问题：

min_pi E_cal[ell(V_pi,V_N)]
subject to E_cal[T_DD(pi)]<=B，pi∈P_legal。

ell首版为与当前主评价一致的逐帧Alex LPIPS均值。PSNR/SSIM、参考时序和人工检查作为独立观察，不继续用未经任务标定的MUSIQ一票否决线去替代保真目标；旧合同不回写。

T_DD包含实际去噪、probe、读出、等待和解码；T_request另报。加载、预热与一次性校准费用单列。固定K次D是清楚的机制对照，不等同于精确时间预算。

### 2.4 开环与闭环

本建议离线优化一条共享序列pi_B，部署不再看teacher或求终点梯度。这是开环安排。校准时在候选自身轨迹上迭代不等于部署时在线自适应。

真正在线策略必须根据当前可获得的观测及剩余预算输出m_k；只有未来另行验证后才能这样主张。

## 3. 文献核对：哪些不能再当贡献

已读取下列论文原文HTML；SGF另核对v2摘要。链接见文末。

|工作|已有思想|这里可能新增的部分|
|---|---|---|
|WorldCache, 2026|当前probe、显著性、阶段阈值、插值和warp；C不是ZOH|固定同一个C执行器，改变刷新价值的估计与规划|
|RA-CFGCache, 2026|CFG误差相关项＋孤立扰动的传播先验＋在线联合刷新|把刷新对未来缓存和求解器状态的价值显式纳入候选自身轨迹|
|BudCache, 2026|固定预算的SA/HC端点搜索；另有缓存感知网格对齐|通过可计算的状态梯度提出少数有方向的候选，实际校准费用必须比较|
|LeMiCa, 2025|用隔离缓存区间对最终latent的影响构图，lexicographic minimax路径|不把区间端点标签当作跨历史不变的边权；用完整记忆状态的边际价值|
|CEM, 2025/2026版|离线时间×区间误差模型、累计误差与DP|不再仅累计父轨迹局部风险|
|OTCache, 2026|高预算参考＋低预算感知目标搜索＋跨预算分位插值|不以恢复F19/Shared25两个锚点并插值作为新贡献|
|L2C, 2024|可微缓存选择、输入无关而时间相关的层路由|不是“第一次给cache求梯度”；目标是全采样终点与跨步缓存写入|
|ReCache, 2026|REINFORCE学习预算条件静态计划，终点保真／质量奖励|用解析离散状态敏感度而非策略梯度，比较实际费用与计划质量|
|Self Gradient Forcing, 2026|恢复未来视频损失到历史KV写入的训练梯度|这里不训练骨干、不处理AR跨帧KV；优化跨去噪步特征缓存的二元刷新位置|
|Optimal Switching for Hybrid Semilinear Evolutions, 2016|带重置映射的切换系统、伴随和模式插入梯度|借用理论工具，不能把伴随或模式切换本身宣称原创|

结论：单独的“终点感知”“可微缓存”“缓存写入很重要”“跨预算计划”都有近邻。值得争取的是**面向冻结视频扩散推理，把缓存来源写入与求解器历史组成状态，对硬刷新动作作有符号终点归因，并在有限校准预算下生成有效计划**。是否构成足够增量，取决于因果拆分、消融和真实成本表现。

## 4. 三个实质不同的候选机制

### A. 区间更新／误差均衡规划

把刷新当作区间边界，拟合误差随当前噪声、间隔、上一个锚点跨度的增长，解分段DP或最小最大风险。

优点：简单、部署便宜、易跨预算。缺点：若把D当完整再生点就忽略latent/solver残余；跨区间交互与自轨迹错配仍可能存在。相关空间被CEM/LeMiCa/ERC式方法覆盖很多，旧GRAPH失败也要求更强理由。

可否证：同样边界和age、不同前缀造成明显不同终点收益；间隔标签无法排序自由运行候选。

### B. 低秩终点响应与交互模型

对少数合法交换做完整后缀，得到终点特征变化delta_i；以有符号内积与低秩Gram近似组合价值，而不是只用单步norm。

优点：直接面对终点方向与跨步抵消，不要求模型可微。缺点：N个动作及二阶交互参数多，少量校准难识别；大交换可能改变历史使响应失效。需要低秩/局部有效性，不能把几条标签拟合成任意全网格代理。

可否证：组合真实变化与线性响应和差异大，或跨父轨迹排序不稳定。

### C. 读写价值感知的离散伴随规划（推荐）

保留实际latent、solver与cache转移，在每条候选自身轨迹上算终点敏感度，分别归因当前输出与未来缓存写入。以少量硬候选验证控制一阶近似误差。

优点：待估量有明确计算路径，不需要拟合高维风险回归器；历史与求解器自然进入算法；每轮梯度能给所有位置评分。

代价与风险：需要可微校准适配、checkpoint/recompute和VAE／感知损失反传，存在非光滑与离散元数据问题；比纯CPU表格重，是否比51查询更省必须实测。

只推荐C为主方法候选。A作为简单对照；B作为对C的机制诊断工具，不同时开发三套主方法。

## 5. 推荐机制：一次刷新有读出价值和写入价值

令y_k=(x_k,H_k)，C_k为缓存，F_D与F_C是同一个父状态下的两个实际动作转移。

对当前完整计划pi，定义剩余后缀的终点损失函数：

V_{k+1}^{pi}(z)=ell(Decode(Phi_{k+1:N}^{pi}(z)),V_N)。

完整刷新相对复用的精确有限变化为：

Delta_k=V_{k+1}^{pi}(F_D(z_k))−V_{k+1}^{pi}(F_C(z_k))。

这是条件价值，依赖当前状态和未来计划，不是普遍V(k)。逐位置直接计算需要大量后缀，因此不将它作为免费的oracle。

### 5.1 同状态四格分解

设动作后状态为(y_C,C_C)或(y_D,C_D)，构造：

- 00: (y_C,C_C)，普通C；
- 10: (y_D,C_C)，只替换当前输出／求解器转移，不写入Dense缓存；
- 01: (y_C,C_D)，当前仍用C输出，但写入当前Dense缓存；
- 11: (y_D,C_D)，实际D。

这里C_C是实际C路径的全部工作状态，不是简单原样不动。10/01是机制干预，仍支付取得Dense真值的费用，不是声称可免费部署的新动作。

终点损失满足精确代数：

L11−L00=(L10−L00)+(L01−L00)+I_RW，
I_RW=L11−L10−L01+L00。

这个分解检验未来缓存写入价值与非线性交互，不要求D清除过去误差。

### 5.2 为什么局部误差可以为零，而D仍有价值

一个说明性两步系统：当前C与D都输出0；D将缓存写成1，C保留0；下一步复用缓存并希望得到1。当前输出误差完全相同，但D改变下一步输出。这个例子不代表Cosmos实测，它只是证明“只看当前误差”在逻辑上不充分。

### 5.3 有限消费历史

若终点损失只依赖最终视频，而某次写入之后再没有任何读取，则该写入的终点价值为零；当前完整输出仍可能有价值。

若读出依赖最近两个真实锚点，一次D不一定替换所有陈旧来源。相邻D可共同更新预测基底；但不能因此推断任何位置都应成对刷新。solver历史还可能保持更长或不同的影响。

## 6. 不把未知量藏进oracle：离散伴随的计算

在当前硬计划pi的一次真实前向上，保存或可重算z_k。对实际离散程序求：

p_N=∇_{z_N}ell，
p_k=(D_zF_{k,pi_k}(z_k))^T p_{k+1}。

这是vector-Jacobian product，不显式建立完整Jacobian。

同状态计算两动作差：

d_k=F_{k,D}(z_k)−F_{k,C}(z_k)。

定义一阶刷新分数：

g_k=<p_{k+1},d_k>。

g越负，表示在当前后缀和状态附近把C变D越有利；不是“误差越大g越大”。

把p与d按y/cache分块：

g_k = <p^y, y_D−y_C> + <p^C,C_D−C_C>
     = g_k^read + g_k^write。

p^y包括latent与solver历史。传播通过实际离散UniPC实现，不能用Euler解析步长替换，也不在已包含传播的值上再乘g_t²。

CFG通过真实v_g和后续状态自然进入梯度。不要再把64C+49U−112K额外加一次当作新的罚项，造成重复计入。

### 6.1 这不是硬动作精确收益定理

为了定义方向导数，可局部使用辅助状态插值：

F_u(z)=F_C(z)+u(F_D(z)−F_C(z))。

在u∈{0,1}处与硬执行一致，g是该辅助插值的局部导数。u在中间的混合缓存只是数学松弛，不是部署状态。有限C↔D变化、多个交换和非光滑分支会带来高阶误差。

因此g负责提出候选；真实硬计划的完整评价负责接受或拒绝。不能称全局最优，也不能把每轮g当作跨预算固定的重要性表。

### 6.2 实现前提

- 缓存用固定槽表示，记录必要来源sigma与实际工作状态，不能只对cached tensor求导而遗漏写入/移位规则。
- solver状态转移完整保留，不仅对当前x求导。
- 年龄上限等硬合法性由规划器精确执行；涉及动态离散分支的部分单列。
- clamp/相关匹配/量化等非光滑点，只能作分段导数或明确的近似，必须用方向有限差分与硬候选验证。不能静默stop-gradient后仍称完整伴随。
- 当前仓库读出函数为no_grad，旧执行成功不等于校准反向实现已经可用。未来需要单独的、硬端点前向等价的校准适配；本次没有实现。
- 不对安全检查、视频编码做反传。拟合在同帧、同尺度的未编码浮点VAE视频上算Alex LPIPS；硬候选接受还核对正式评分路径。两者的边界差异明确披露。
- 不改网络权重；这是离线计划优化，不宜称“零校准成本”。

## 7. 具体算法

### 7.1 输入输出

输入：冻结模型与读出器、实际求解器及网格、2–4个FIT输入及各自Native、目标D配额K或T_DD预算B、合法历史与边界条件、有限校准预算B_cal。

输出：共享硬D/C计划pi_B、实际费用、读写价值诊断与适用设置。首先不改变A、Q、CFG scale或求解器。

### 7.2 初始化和约束

默认由同一确定性噪声坐标均匀覆盖规则初始化。F19是强外部对照或明确的warm start，不作为新方法的隐蔽输入。若方法只能从F19微调，诚实定位为refiner。

约束包括：
- 首次缓存必须已有足够真实锚点；
- 与比较方法相同的合法保护集合；
- 最大连续复用数及实际噪声跨度；
- 需要时约束最近两个来源跨度；
- final D若属于当前执行合同则保留；
- 精确K或经测量标定的时间限制。

原D24等兼容保护可用于首轮公平对照，但必须标为历史约束，不解释为普适物理边界。迁移时由新执行器合法性和固定规则生成，不抄具体步号。

### 7.3 每轮提出最多两个计划

在当前pi上按prompt等权求g_bar。对r=1和r=2，解：

min_pi' sum_k g_bar_k(pi'_k−pi_k)
subject to pi'∈P_legal，count_D(pi')=K，||pi'−pi||_0<=2r。

时间约束版本再加入真实组件成本模型，不把K相同当作秒数严格相同。

该局部线性子问题可用有限状态DP或小型整数规划。只约束上次D年龄时，DP状态为(步号，已用D数，连续C长度，编辑数)，复杂度O(N K L r)；同时保留两个历史跨度则增至O(N K L² r)量级；离散时间预算另乘时间桶数M。以上只描述局部提案问题，不是原始非线性生成问题的复杂度。

对不超过两个硬候选运行完整FIT轨迹，以正式终点目标与预算接受最好的真正改善者。每次接受后，在新候选自身轨迹上重新求梯度。最多3轮；一次都不改善就保留原计划，不返回假赢家。

### 7.4 伪代码

```text
PLAN(model, solver, grid, readout, calibration, K_or_B, legal, Bcal):
    reference = matched_full_outputs(calibration)  # cached only when identity matches
    plan = deterministic_uniform_legal_plan(grid, K_or_B, legal)
    incumbent = evaluate_hard(plan, calibration, reference)

    for round in 1..3 while remaining(Bcal) permits the whole round:
        gradient = 0
        for sample in calibration:
            trace = checkpointed_hard_rollout(plan, sample)
            costates = discrete_reverse_actual_program(trace, reference[sample])
            for eligible step k:
                alt = same_prewrite_state_C_and_D(trace[k])
                gradient[k] += dot(costates[k+1], alt.D_state - alt.C_state)
                record_read_solver_and_write_components()
        gradient /= number_of_prompts

        proposals = deduplicate([
            constrained_linear_proposal(gradient, plan, radius=1),
            constrained_linear_proposal(gradient, plan, radius=2)
        ])
        results = full_hard_fit_evaluations(proposals)
        candidate = best_actual_feasible_improvement(results, incumbent)
        if no candidate: break
        plan, incumbent = candidate

    return plan, measured_time, calibration_cost, diagnostics
```

不在部署时执行这个循环。实现可重用同一前向中的已支付D结果和C probe；替代分支计算只作离线评分，不污染父轨迹。

## 8. 校准成本、复杂度与迁移

令n为校准prompt数、I<=3，N为实际更新数，F_D/F_C为相应前向费用，B_pi为当前硬轨迹的一次状态VJP费用，R为checkpoint重计算费用。每轮需要量级：

n [N(F_D+F_C)+B_pi+R+loss/decoder backward]

以及至多2n次真实硬候选完整生成。精确profile会随窗口复用、D结果共享、VAE和warp实现而变。

这不是O(1)免费标定；GPUh必须包括参考、shadow、反向、重计算、候选验证、读写。与51查询相比，完整候选查询更少不等于费用一定更低。

内存不必保存全部层的36步激活：用逐步／分段checkpoint及模型block重计算。但至少一个block/模型输入梯度、当前状态、缓存窗口与VAE梯度必须装得下。若真实48GB实现不可行或重算代价太高，就说明此执行方案不适合当前预算；不能只把骨干Jacobian替成identity后仍声称实现原方法。

没有对模型权重、阶段曲线或神经控制器的训练；少量校准用于求计划和费用统计。2–4个prompt是pilot设置，不保证泛化。

换预算：输入新K/B，调用同一程序；可明确使用前一预算计划作warm start，但相应标定费用必须单列。不能声称一次标定免费得到所有预算的最优计划。

换噪声网格：重新建立合法布局及离散程序，用实际sigma跨度；相同程序重新标定，不复制21/33。重新标定与无标定迁移分别报告。

换Euler/UniPC：使用各自真实状态和Native，改变的只是适配器与校准值。Euler无多步预测缓冲，UniPC保留其原阶数与历史；这本身提供机制验证。换骨干同理。

## 9. 对F19/Shared25及正负结果的对应

|已有现象|已能说的|推荐机制给出的待检验解释|
|---|---|---|
|F19明显优于Uniform|结构化布局在当前四CAL/19D有用|前段/过渡区D可能更新后续多步使用的来源；Uniform没有按这种条件价值分配|
|Shared25新输入有效|一个固定高保真布局可推广到那批输入|高预算下多处D可同时提供当前纠错和历史更新；不要求所有预算包含D21|
|S-CFG比DIAG好1.534%|CFG局部几何有小增量|只修正分支组合还没有评价写入与历史转移的终点价值|
|RiskSwap几乎打平且不稳定|父轨迹风险交换无稳定终点收益|当前输出增益和未来来源损失可能相抵，或模型局部误差方向不合适；尚未测定份额|
|搜索FIT MSE下降43.58%，LPIPS仍弱|有限搜索改善其目标，未产生强LPIPS赢家|目标、初始化、查询覆盖和泛化都可能影响；不能只归因于过拟合|
|赢家不含D21却含D22/24/25|整体结构与F19不同|刷新价值依赖周围锚点，不能把某个步号单独封为物理必需点|

理论上可以推导的结构：没有未来缓存消费者时写入价值为零；同一时刻在不同父轨迹上可以有不同价值；两个来源窗口使连续D可能具有互补性；不同预算的最优集合不一定嵌套。

不能推导的结论：所有早期D必要、所有尾部D可删、20–23普遍是相变窗口、推荐算法必然输出F19、D一定减少终点损失、局部梯度可保证有限硬交换有益。

## 10. 最少的判别实验（本次不执行）

### M1：读出/写入双作用是否真的存在

两个旧CAL，在一个预先选定、后续确有缓存读取的中间状态上做00/10/01/11四格，共8条真实后缀。保存完整latent/solver/cache/RNG，父C在D写回前计算。所有后缀保持原硬动作计划，但允许状态自由演化。

比较当前输出纠错、仅写入与完整D的终点作用及交互。可另用最后一次不再读取缓存的位置作零写入价值控制，但额外范围须另计。

若写入项始终可忽略，或者只有当前输出决定终点，这一框架的主要机制动机明显减弱。

### M2：小规模导数与有限行动预测

先在一条已选轨迹、少数状态检查辅助连续转移方向的有限差分是否与离散伴随一致；再用预登记合法swap检查排序。验证局部导数正确与硬swap排序有用是两个不同检查。

主要对照为原S局部q、同一终点伴随但删去g_write、完整g_read+g_write。使用相同初始计划、校准样本和候选预算。

若full score与read-only几乎相同，或真实swap反复与预测反向，不能宣称写入价值产生有效调度。

### M3：一次小型计划生成与留出比较

仅在M1/M2有信号后，从通用Uniform初始化，在19D或预定新预算（例如22D）用相同3轮以内程序生成计划。与F19-A1、Uniform、原S和冻结BudgetSearch比较；原预算搜索不能按LPIPS重选。为了公平评价算法效率，另行比较相同主目标、实际校准GPUh限制下的简单搜索，不能只比查询次数。

先在开发留出上判断方法价值；冻结后才扩新输入。一个第二网格或Euler验证采用自己的Native与相同生成流程。无需一次把19/22/25D、Euler和Wan全跑完。

## 11. 明确的失效与停止条件

- 找不到可复现、前向一致的实际状态VJP：当前实现路线不成立。
- cache写入价值对关键动作排序没有增量：不要把read/write当核心卖点。
- 多次硬验证表明一阶提案没有比局部风险或随机同费用搜索更好的命中率：停止扩大该规划器。
- 只能从F19出发得到微小改善，不能从通用初始化产生有竞争力安排：定位为refinement，不称通用生成器。
- 实际校准费用高于端点搜索、终点效果又不更好：没有效率贡献。
- 跨预算/网格必须手工换保护窗与步号：不能主张同程序迁移。
- 结果只在旧两个FIT成立：保留开发结果，不升格为泛化。

小但一致的真实收益可以进一步确认，不机械以5%为科学存在门；但不能通过增加大量坐标、参数、阈值来掩盖主要机制失效。

## 12. 论文主张应怎样写

当前可写为候选：

> We treat a cache refresh as a coupled intervention on the current numerical update and the memory consumed by future updates. A discrete adjoint of the augmented sampler estimates these two contributions on the candidate's own trajectory, enabling budget-constrained hard schedule proposals with bounded endpoint verification.

只有实验支持后，才进一步写低校准成本、跨预算或跨模型优势。

不要声称：首次全局缓存、首次终点优化、首次可微缓存、首次考虑未来写入、全局最优、普适阶段定律、无需校准或已验证在线自适应。

## 13. 原始证据与参考文献

### 项目证据

- 826：https://github.com/kuangda-source/CARA-cache/blob/ec783f2185bab38742dd22f37cf1d56f44de0235/research/826_CARA_ENDPOINT7_COMPLETE_ACCEPTANCE_RESULTS_AND_REGISTERED_DECISION_20261101.md
- 817：https://github.com/kuangda-source/CARA-cache/blob/4c2735d1122c6cada6f39352196e2c396959faf0/research/817_CARA_BUDGET_SEARCH_COMPLETE_ACCEPTANCE_AND_FROZEN_WINNER_20261101.md
- 当前输出融合代码（含no_grad）：https://github.com/kuangda-source/CARA-cache/blob/ec783f2185bab38742dd22f37cf1d56f44de0235/src/wcomr/cfg_guided_w1_outputs.py

### 已核对的一手文献

1. **WorldCache: Content-Aware Caching for Accelerated Video World Models**，2026。https://arxiv.org/html/2603.22286v1
2. **RA-CFGCache: From Branch-Level Criteria to Guided-Risk Control under Classifier-Free Guidance**，2026。https://arxiv.org/html/2609.36433v1
3. **Budget-Constrained Step-Level Diffusion Caching (BudCache)**，2026。https://arxiv.org/html/2606.13496v1；正式PMLR页面：https://proceedings.mlr.press/v306/lei26j.html
4. **LeMiCa: Lexicographic Minimax Path Caching for Efficient Diffusion-Based Video Generation**，2025。https://arxiv.org/html/2511.00090v1
5. **Plug-and-Play Fidelity Optimization for Diffusion Transformer Acceleration via Cumulative Error Minimization**，2025预印本／2026修订。https://arxiv.org/html/2512.23258v2
6. **OTCache: Optimal Transport for Geometry-Aware Caching in Diffusion Models**，2026。https://arxiv.org/html/2606.31026v1
7. **Learning-to-Cache: Accelerating Diffusion Transformer via Layer Caching**，2024。https://arxiv.org/html/2406.01733v1
8. **ReCache: Learning Budget-Aware Caching Schedules for Diffusion Models via REINFORCE**，2026。https://arxiv.org/html/2606.06060v1
9. **Self Gradient Forcing: Native Long Video Extrapolation**，2026。https://arxiv.org/html/2607.20368v1；v2摘要：https://arxiv.org/abs/2607.20368
10. **Optimal Switching for Hybrid Semilinear Evolutions**，2016。https://arxiv.org/html/1605.05153v1
11. **AdjointDEIS: Efficient Gradients for Diffusion Models**，2024。https://proceedings.neurips.cc/paper_files/paper/2024/hash/04badd3b048315c8c3a0ca17eff723d7-Abstract-Conference.html 。本次核对正式摘要；它研究连续伴随，不是本文离散缓存调度的直接实现。
12. **Cross-Time Directional Selection in Diffusion Sampling**，2026预印本。https://arxiv.org/html/2610.05199v1 。方向相关传播的辅助动机，不是CARA真实缓存误差的证明。
13. **UniPC: A Unified Predictor-Corrector Framework for Fast Sampling of Diffusion Models**，2023。https://arxiv.org/abs/2302.04867

检索范围内没有看到与“冻结骨干＋跨去噪特征缓存＋读写分解的离散模式梯度＋硬预算提案验证”完全相同的完整方案。但这不是不存在近邻的证明，也不是绝对原创声明。相近思想的组合必须用有辨识力的实验建立具体增量。
