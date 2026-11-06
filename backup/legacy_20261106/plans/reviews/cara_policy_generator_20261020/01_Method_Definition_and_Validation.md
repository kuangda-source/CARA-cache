# CARA：读出条件化区间策略生成器（提案 v1）

## 文档状态

这是针对“由固定步数配置升级为可复现算法”的新方法设计，不是已完成的实验结果、仓库实现或 GPU 执行授权。依据为用户最新问题及已提供 CARA v5；用户提及的 v6 未在本轮逐文件核对。本文件不覆盖原计划，不更改已冻结候选、已批准实验范围或原始记录。

## 1. 核心判断

当前缺口不是把 Cosmos 的几个位置解释得更漂亮，而是一个明确算子：

`GeneratePolicy(model_adapter, sampler_profile, hardware_profile, calibration_data, inference_budget, calibration_budget) -> policy`

策略至少包括：真实完整刷新位置、各区间的 C/A 覆盖、共享 CFG 修正强度、合法性和回退规则、适用配置以及标定开销。

跨模型允许重新计算误差与费用、输出不同掩码；不允许读取新模型 TEST 后修改候选规则、搜索流程或挑选参数，再称相同方法迁移。可复现生成流程是必要条件，但不是自动构成创新；还需超过同预算强简单规则和合理的自动计划基线。

已有证据的职责：

- 四格 G00/G10/G01/G11 支持修正持续范围有终点作用；不证明当前已存在全局优化算法。
- D33→D22 支持位置的独立作用；不证明该位置适用于其他模型。
- H1/RA/Efficient 的旧独立表不替新区间策略提供独立验证。
- 四格正的 LPIPS 交互量表示在该损失尺度上的次加性，不解释成超加性，也不直接证明所有区间间的相互作用。

## 2. 推荐算法：读出条件化区间图 + 完整终点闭环选择

第一层以小代价构造完整合法候选；第二层用少量真实完整输出决定保留哪个候选，并做有限的联合修订。第一层不是终点损失定理，第二层不是在线 teacher。

### 2.1 输入与两类预算

| 输入 | 定义 |
|---|---|
| 模型适配器 | 检查点、输入模式、合法 shallow/deep 边界、原生 warp/head/RF、实际 CFG 组合和缓存更新接口 |
| 求解配置 | 实际更新数 N、真实时间/噪声网格、求解器历史与保护规则 |
| 硬件配置 | 精度、batch、attention 后端、offload、分辨率与帧数；费用与这些条件绑定 |
| CAL_FIT | 用于局部统计和候选搜索的开发提示词与 seed |
| CAL_SELECT | 少量未参与搜索拟合的开发选择输入；选一次候选，不在此继续产生新设计 |
| B | 目标部署平均延迟，或相对本配置 Native 的目标时间比例；不是默认等于 D 次数 |
| Q | 最多允许见到终点评分的不同计划数，另有 GPUh 上限；两者取先到者 |
| 合法性元数据 | 必须 D 的位置、支持的最大年龄、最少真实锚点数、来源类型及确定回退 |

最终 TEST 不参与上述过程。早期只有四个 CAL 时可以用提示词级留一作开发筛查，但不能把反复迭代后的留一结果叫独立终测。

### 2.2 输出

`policy.json`：

- `dense_mask[1:N]`
- `readout_mask[1:N]`，每步 C/A/D
- `alpha[1:N]`，两 CFG 分支共享；D 或纯 C 位置为空或约定值
- `intervals`，真实边界与各区间修正窗口
- `fallback_policy`，与质量/费用评价一致
- `profile_identity`，模型、采样、条件、硬件、费用表及标定身份
- `budget_predicted`、`budget_observed`、`budget_status`
- 标定和候选评分成本、失败/拒绝和可用队列

若预算下没有已验证可行计划，返回 `BUDGET_NOT_VERIFIED` 和最接近的已验证点，不悄悄放宽预算。

## 3. 以区间为搜索对象，不以具体步数为规则

设实际更新为 1…N，额外增加终端节点 N+1（它不执行模型）。一条边 s→r 执行：

- 在 s 执行 D；
- 在 s+1…r−1 执行 C 或 A；
- r 为下一条边的 D 起点；r=N+1 时为终端，不收费 D。

一条从 1 到 N+1 的路径即完整计划。这样每次 D 和每次读出只计费一次。

每个区间的读出候选：

1. 全 C；
2. 一个连续的 A 窗口 [u,v]，s<u≤v<r，其余为 C；共享强度 alpha∈{0.5,1}。

此语法自动包含当前-only、later-only、full-interval，也能生成从中间开始或提前结束的窗口。它不硬编码 21、22、23、25、33。零强度由全 C 表示，避免重复配置。

若区间含 l 个可复用位置，候选数为 `1 + 2*l*(l+1)/2`。l=6 时为 43；这是小规模离散候选集合，不需要拟合高维网络。真实系统最大 l 必须来自该配置合法支持域，不默认跨模型都为 6。

过滤规则：

- 任意必须 D 的位置不能被边内部跨过；
- 历史和来源支持不足的边不进入候选图；
- 不把预测写成真实 D；
- D 与 A 不重叠；
- 边界一旦改变，就重新构建受影响的完整区间和读出窗口；
- 固定掩码的在线回退若改变了预算，最终按实际动作报告。

## 4. 第一层：低成本、明确有偏的区间提案表

### 4.1 标签与实际读出对齐

基线和提案必须使用实际 WC/GCR 路径：当前 probe、真实来源定义、warp、head/unpatchify、RF、实际 CFG 权重。不能用 raw hidden 差代替部署 velocity 并声称完全等价。

对于同一假设来源 s 和当前校准状态 t，保存：

- `v_C`
- 修正提案 `v_Phi`
- 同状态 `v_D`

均为实际 guided 输出。定义 e=v_C−v_D，d=v_Phi−v_C，则

`q(alpha) = mean(e^2) + 2*alpha*mean(e*d) + alpha^2*mean(d^2)`。

这个公式在实际输出空间线性融合时精确。只需保存三个二阶统计，就可比较多个 alpha，不必为每个 alpha 重跑完整模型。

参考轨迹提供的 teacher 状态可以复用于提案计算，但必须标为 `TEACHER_CONDITIONED_PROPOSAL`：实际新计划的 latent、旧 D 序列及插值窗口可能不同。它不是该新计划自由运行误差的真值。

不能从 MP4 或标量日志复原未保存的 probe/velocity。若缺资产，记录必要的新采集；教师推理、额外 head、搬运和评分全部计入校准费用。

### 4.2 区间误差代理

初版使用：

`E_hat(s,r,m) = average_CAL sum_{t=s+1}^{r-1} w_t*q_hat(s,t,m(t))`。

w_t 使用预先固定的权重规则。若沿用传播幅度标定，则用与平方误差一致的 g_t²，且归一化尺度也必须对齐；新模型按照相同标定程序重新获取。不重复乘一次已经包含在 g 中的求解器步长。

为了比较提案器的价值，应保留无传播加权或原 H1/CEM 式提案作为消融，但不能根据 TEST 逐模型挑权重规则。

### 4.3 时间代理

选择一种统一边界：

`T_hat(pi) = T_shared + sum_e c_hat(e)`。

`T_shared` 只包含未在边上收费的编码/解码/固定工作。边 c_hat(e) 包含 D_s 和区间全部 C/A。如果使用“probe 已付”报价，必须把所有 probe 统一加入且只加一次。

共享强度为 1、中间值和 C 的实际 head 路径可能不同，不能把 A 时间当作与 alpha 无关。所有必要状态维护、分支同步和回退都计费。

B 约束的是特定配置的平均延迟，除非另有验证，不声称每个请求都满足严格实时上界。

## 5. 区间图求解：有预算的最短路径

将边费用按固定分辨率 Delta_c 向上离散：

`cbar_e = ceil(c_hat(e)/Delta_c)`，`Bbar=floor((B−T_shared)/Delta_c)`。

定义 F(r,b) 为到达节点 r、使用离散费用 b 的最小代理代价，F(1,0)=0：

`F(r,b) = min_{s<r,m} [ F(s,b-cbar(s,r,m)) + E_hat(s,r,m) ]`。

回溯得到 D 位置与读出窗口。对可用预算范围一次求解可产生多档计划；允许不同预算的计划不嵌套。

- DP 对这个有限、可加代理图成立。
- 不宣称对真实视频的全局最优。
- 向上取整只保守控制预测费用，不保证实测时间。
- 原 WC 可能使用最近多个 D、UniPC 有多步历史，因此真实过程不是只由节点 s 决定的马尔可夫过程。若日后扩充图状态，必须显式增加所需历史；初版不要假装已经精确解决。

保存少数不同拓扑、满足预算的候选，而不只是一个标量最优。预先固定候选多样性规则，例如端点 D 集合的差异优先。不得看到终点后手工加入一个特定有利步数而仍称自动生成。

## 6. 第二层：完整终点评价与有限联合修订

### 6.1 真实评价

`L_CAL(pi) = average_prompt average_seed LPIPS(V_pi, V_Native)`。

每条 pi 使用自己的 latent、缓存、真实 D 历史和求解器历史自然继续。未读取的未来状态不能从 Native 或旧计划拼接进来。

只有完全相同的实际前缀和完整状态能复用检查点；后缀仍运行到终点。不能只恢复 latent，不能重置高阶求解器历史。

主选择为：实际时间满足 B 的候选中，终点主损失最小者；尾部、拒绝、质量守卫按预定规则单列。若时间边界不稳定，先按保守候选筛查，再重复测最终点，不把 0.1 秒的波动当调度收益。

### 6.2 默认有限开发档

- 一个待验证预算 B；
- CAL_FIT 为 4 个既有开发提示词、固定 seed；
- 至多 Q=8 个不同计划的完整终点评分，分两批；
- 第一批四个槽：两个由同预算规则生成的强简单计划（C/A），一个最低代理图计划，一个拓扑不同的图计划；
- 第二批四个槽：围绕真实评分较好的 1–2 个候选，按固定邻域生成并用代理排序的联合变体；
- 全部槽、去重顺序、tie-break、费用/合法性处理在看结果前确定；
- 额外随机同语法计划作为对照时，在自己的等额基线预算内评分，不偷加到本文方法预算。

邻域只有三种操作：

1. 合并相邻区间，即删去一个非保护 D，并重新选择合并后的 A 窗口；
2. 拆分/移动区间边界，同时重建两侧的读出；
3. 固定 D，仅调整区间 A 的覆盖或 alpha。

读出和边界在同一个邻域内联合更新，不是先各自选最好再固定拼接。

若候选因显式支持规则无效，记录 INVALID 并按固定顺序取下一个；若出现技术故障，处理为工程失败，不悄悄用“更容易成功”的科学样本替代。

Q 与 GPUh 先到即停。已经评分过的相同计划可复用，但必须区分“没有新的计算费用”和“算法已经看过该计划的终点信息”。公平对照须获得同等可用初始信息。

### 6.3 选择与冻结

在 CAL_SELECT 上一次性评价少数入围计划，用事先固定规则选最终候选。不能根据 CAL_SELECT 发明下一轮规则再称它独立。

输出完整策略及预算状态。最终 TEST 不参与选系数、窗口或新增候选。部署时不执行 teacher、DP、完整计划搜索或 LPIPS 评分，只执行已编译的计划和必要合法性处理。

## 7. 为什么这不是把单个区间代价机械相加

各区间会通过 latent、缓存和求解器历史发生依赖。当前四格结果只证明区间内两段修正在 LPIPS 尺度上有非加性，不直接证明所有跨区间关系。

本提案把可加表仅用作高性价比候选生成器，真正入围与更新使用完整终点。这一两层设计要被实验验证：若局部表与终点排序完全一致，则第二层增量可能很小；若表无法提出有效候选，也要面对同预算随机或直接邻域搜索。

不能把“用了 DP”或“跑了终点”作为单独首创；研究增量在于读出条件化的可行区间、联合边界/覆盖选择，以及在有限校准预算下的真实效果。

## 8. 与近邻的具体关系

| 工作 | 可借鉴部分 | 必须用对照建立的增量 |
|---|---|---|
| CEM | 时间/区间误差与 DP 计划 | 相同 GCR 下，固定读出后仅选边界 vs 同时选覆盖、强度与边界 |
| Golden Path Hypothesis | 共享计划、完整终点评价 | 同额终点查询/计算下，只搜索刷新掩码 vs 读出条件化区间搜索 |
| ReCache | 预算输入、完整结果驱动计划学习 | 本方法不必用 RL；小样本校准成本、实际时延而非仅重算数、联合读出设计 |
| AlignCache | 阶段、guided 误差反馈与修正 | 不把校准/CFG 修正本身称首创；区别是离线联合区间配置与独立验证 |

这些都是直接近邻；不需要为了避免相似性改成另一个不相干的问题。

## 9. 实验重排：先算法生成闭环，后大规模最终主表

### P0：规格与 CPU 原型

- 从本轮规范生成 grammar、边合法性、费用计算与 DP；
- 小型合成图用穷举核对 DP，不宣称模型性能；
- 不同 N 的合法掩码都能生成，且不内置 21/22/23/33/25 的分支；
- 原有四格与位置移动只作为该语法能表达的示例和开发观测；
- 明确模型适配器，而不是当前权重/历史被错误抽象成通用接口。

### P1：Cosmos 单预算完整生成器

在 4 CAL 上、Q≤8 的开发档检验整个流程，允许一轮有依据的修订。输出终点选择结果，不再只输出最好的局部 q 或手工挑选的一组步数。

约 220 秒/路径下，8计划×4提示词的主生成量级约为 1.96 GPUh；这不含误差表采集、Native参考、预热、评分、失败和选择集，不得把整轮报价写成“2 GPUh必完”。重新读取实际报价与许可。

### P2：算法贡献对照

优先四种对照：

1. 同预算前密 C/A；
2. 仅按刷新位置搜索，读出规则固定；
3. 同一搜索空间，但使用局部代理做最终选择，不做终点重排；
4. 本方法联合区间配置。

增加同等 Q 的随机/简单局部搜索，判断是否仅仅多给了优化机会。比 CEM 时尽可能使用同一个 GCR，以免把预测器差异记成调度贡献。

“先优化 D 后优化 A”与“联合优化”使用相同语法、数据、终点查询数和预算。模块可以协同有效，不要求每个模块先独立显著。

### P3：第二预算与流程迁移

沿用同一候选语法、权重标定程序、搜索预算规则及选择流程。在另一模型或采样设置只重新采集合法表与代价。输出不同位置是预期行为，不是失败。

最好报告两类迁移：冻结参数直接运行，以及相同流程重新校准。后者可以是主张，不必伪装零样本。

### P4：最终独立确认

衔接既有审稿修订方案，不改名挪用已经冻结的卡。新算法冻结之后，新主表评估它本身；旧 H1、A_NO_P、N08/N10 不自动代替新策略。未见 TEST 的定义按当前项目真实使用历史核对。

## 10. 同一方法、不同模型允许改变什么

保持不变：目标定义、区间语法、合法性处理原则、统计标签口径、候选生成/搜索流程、停止规则、选择/测试隔离。

允许经同一流程改变：实际步数和噪声网格、模型适配器的结构对齐、实际 CFG 权重、g/误差/费用表、支持区间、选出的 D/A 窗口和 alpha。

仅换硬件且数值执行经过核验时，可优先重测费用并重规划；换采样器、精度、分辨率、条件模式等可能同时改变误差，不能默认只改费用。

## 11. 论文主张与停止边界

候选主张：在有限校准费用下，读出条件化的区间选择与全轨迹验证，优于固定读出后的计划优化或手工前密，并能通过相同流程迁移。

需要实测：同真实时间的保真增量、同保真的时间节省、校准样本/查询效率、迁移后是否仍无需手工改规则。

不提前声称：首个联合方法、全局最优、真正物理误差上界、所有输入硬时延保证、零标定或已完成跨模型收益。

如果最终仅靠相同 GCR、自动搜索就超过强简单基线，仍是值得研究的结果；是否达到投稿创新层级需与同额自动计划近邻比较。若联合过程没有超出简单搜索，收敛到最简单有效规则，不用新增名字掩盖这一点。

F/B 保持结束，旧 P 大卡保持用户暂缓；不把它们作为本算法必备。工程预算、权限和正在运行的卡都要由原 Codex 读取最新状态，不继承旧时点余额。

## 12. 伪代码

```text
GeneratePolicy(profile, CAL_FIT, CAL_SELECT, B, Q):
    grammar = BuildIntervalReadoutGrammar(profile)
    stats = CollectOrReuseLegalProposalStatistics(profile, CAL_FIT)
    costs = MeasureOrReuseCompatibleCosts(profile)
    graph = MakeBudgetedIntervalGraph(grammar, stats, costs)
    shortlist = BudgetedPathsPlusSimpleControls(graph, B, fixed_rules)
    archive = empty

    while unique_endpoint_plans(archive) < Q and calibration_budget_allows:
        plan = NextUnseenLegalPlan(shortlist, fixed_order)
        result = RunCompletePlanOnCalibration(plan, profile, CAL_FIT)
        archive.add(plan, result, actual_cost, trace, missingness)
        shortlist += JointIntervalNeighbors(
            measured_feasible_incumbents(archive), grammar, graph, fixed_rules)
        # Source/solver state evolves naturally. No teacher is used online.

    finalists = FeasibleNondominatedPlans(archive, B, fixed_rules)
    if finalists is empty:
        return BUDGET_NOT_VERIFIED
    chosen = SelectOnceOnCalibrationHoldout(finalists, CAL_SELECT, B)
    return CompileFrozenPolicy(chosen, profile, provenance=archive)
```

## 参考依据

- 用户提供 CARA-Cache v5（2026-10-19），第2–5页：具体 GCR、四格终点、旧主表、显式位置干预；v6本轮未逐文件获取。
- Shao et al., *Plug-and-Play Fidelity Optimization for Diffusion Transformer Acceleration via Cumulative Error Minimization*, arXiv:2512.23258v1. https://arxiv.org/html/2512.23258v1
- Wang et al., *The Golden Path Hypothesis: Reusable Schedules in Diffusion Caching*, arXiv:2609.39343v1. https://arxiv.org/html/2609.39343v1
- Aliev et al., *ReCache: Learning Budget-Aware Caching Schedules for Diffusion Models via REINFORCE*, arXiv:2606.06060v1. https://arxiv.org/html/2606.06060v1
- Jiang et al., *Heuristics are Not Enough: Calibrated and Corrected Caching for Video Diffusion Acceleration*, arXiv:2610.16545v1. https://arxiv.org/html/2610.16545v1

外部论文支持相关路线与差异定位，不证明本提案已经有效。正文中的 DP、代价模型、候选语法和实验范围为本轮新设计。
