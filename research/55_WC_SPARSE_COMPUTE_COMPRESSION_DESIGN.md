# WC-S：受质量与行为保持约束的计算压缩

日期：2026-10-01；设计版本：v1.1；对应长程计划 v1.2。

状态：S0 CPU源码/checkpoint元数据审计通过；构建已CPU验收，动态导入/实际QKV hook/成本profile/内核仍待验收，没有运行稀疏方法或提交新GPU任务。本设计不扩充4GPUh账本，不批准训练、付费评分、人工评审或对外消息。

讨论来源：[调研两个研究方向](chatgpt-conversation://6aba8cd0-f4a8-83ee-adba-d4f960fb6dcb)最新完整轮次，用户“压缩即智能”与缓存/稀疏/模块取舍讨论。对话是研究输入，不是实验结果或额外执行权限。一手资料复核与消息身份见[来源记录](../manifests/plan_update_sources_20261001.json)。

S0实际审计与来源锁见[56_CPU审计](56_WC_S0_SOURCE_SHAPE_AND_KERNEL_AUDIT.md)，后续两扩展CPU构建与无PV接口见[57_S1结果](57_WC_S1_ISOLATED_UPSTREAM_BUILD.md)；不改变未批准GPU范围。

## 1. 当前证据与优先级

F1官方WorldCache已有3个接受配对的端到端加速约1.48–1.60×，不是新方法收益，也不是论文Euler精确复现。W1 CAL8 scalar存在机制信号，但固定轨迹后MUSIQ混合、开发VQA无一致收益，干净成本/独立确认未证；暂停增加scalar/W2复杂度。见[实验总览](../EXPERIMENT_REPORT.md)、[CAL8](21_W1D_CAL8_RESULTS.md)、[VQA](28_W1_DEVELOPMENT_VQA_RESULTS.md)。

新增优先顺序：S0剩余成本分析与资产核对 → S1真实稀疏内核门 → S2四臂固定轨迹 → S3单模块替换和计算重分配 → S4三档调度。S5增量式稀疏只做条件诊断，不要求整条路线跑完。资源受阻时保留结果并比较下一信息价值，不自动转去训练。

原W1 clean50/新4GPUh是既有成本提案，不是WC-S已获预算，也不是开展CPU核对的前置要求。下一GPU窗口需用S0/S1实测成本重新提出具体范围；不机械把旧50次计时与新分支都跑一遍。仅修改计划，不改变已冻结的运行/评分协议。

## 2. 研究问题与可检验假设

目标：在预先固定的质量与行为保持要求下，选择更便宜的计算方式。历史可预测结构与不可廉价恢复的变化分开处理，但只为真正影响结果的变化增加计算。

“压缩即智能”只提供启发：编码长度、注意力熵、GPU时间和视频质量不是同一目标。不可预测可能是噪声；静止、模糊也容易预测。注意力集中程度、模式稳定性、输出可预测性、任务敏感性分别测量，不能相互替代。

| 假设 | 对照与可观察结果 | 不成立时 |
|---|---|---|
| H-S1：WC剩余注意力仍是值得优化的成本，已有稀疏内核能净省时 | WC profile + 真实形状的dense/full-mask/sparse内核时间，含路由 | 无净收益则暂停该内核/硬件路线，不靠稀疏率宣称加速 |
| H-S2：稀疏重算可成为复用与密集刷新之间的有效中间档 | 四臂闭环；三档方案对直接叠加及简单定期刷新 | 简单组合已足够强则保留它，不强加控制器 |
| H-S3：更便宜的刷新能替代部分昂贵补偿 | 复杂补偿少刷新 vs 简单补偿多稀疏刷新，同质量/同时间 | 模块减法没有优势则恢复，不称原模块无用 |
| H-S4：模式/统计跨步复用可降低决策成本 | 每次重建、固定周期重建、廉价触发，含模式失效样本 | 模式不稳定或漏掉关键交互则提高重建/回退密集 |
| H-S5：稀疏偏差跨去噪状态的变化小于偏差本身 | 同状态直接稀疏/直接复用/稀疏增量误差及成本 | 没有稳定优势或显存/访存过大则不铺到全部层 |

WorldCache的去噪步骤复用不同于自回归视频帧的历史KV压缩；WC的latent drift也不等同于真实视频运动。新增跨模态注意力结构不是当前候选；先保持已有文本/图像cross-attention不变。

## 3. S0：先测开启WC之后的成本

复用锁定的Cosmos-Predict2.5-2B、CFG7、93帧432×768、当前UniPC/Karras与72调用/官方70计数协议。Euler或新后端单列，不与旧运行混池。

先做非GPU源码/接口审计，确认当前硬件架构、native attention backend、QKV形状/head dimension/dtype/layout、mask与RoPE位置、条件/无条件分支、深层跳过位置。实际shape需来自可信回执/真实模型hook；没有该证据时标UNKNOWN，合成shape不是性能证据。

GPU profile仅在有预算时做，Native与官方WC各取预登记的代表性CAL场景，区分：

- load/guardrail/text encoder、去噪、VAE、I/O与数据搬运；
- probe与deep分别的attention core、QKV/output投影、MLP/调制；
- drift/saliency/OSI、flow估计/warp、clone/rearrange/cache访存；
- sparse mask构建/重建、路由、同步与额外缓存。

成本不能重复相加：probe/deep是范围，attention/MLP是范围内的组件；异步重叠按trace解释。冷启动/预热/稳定运行分开，profiler与部署clean时间分开。所有诊断墙钟计入预算。

记录剩余可优化占比f与实测内核速度比k，使用T_new/T_WC约为(1-f)+f/k+新增开销占比作筛查估计；不是实测收益或质量保证。预登记继续门：预估端到端节省需明显大于重复计时波动和实现/路由成本，否则暂停稀疏接入。

## 4. S1：真实内核与数值混杂门

优先核对SpargeAttention现有Ampere接口；它结合SageAttention低精度，安装要求不证明A6000上当前形状可用或会更快。Ada与Ampere分别验收，不用H100数字预测当前机器。隔离环境与固定commit；不修改共享驱动、上游或已在运行的源码。

至少比较三项：

1. 当前优化过的dense后端；
2. 同一候选内核、所有块保留（full-mask）；
3. 同一内核、部分块跳过（sparse）。

S0实际源码核对发现公开full-mask仍默认PV阈值跳过；首轮调用同upstream no-PV binding，对照dense/full-QK-no-PV/sparse-QK-no-PV，PV另作匹配开关。full-mask对dense用于识别后端/低精度变化；在两者PV都关闭时，sparse对full-mask才隔离块稀疏收益。两种WC配置也须增加匹配full-mask控制，避免只给候选用新内核。全块保留不自动等于数值精确dense。

使用真实序列长度、head dimension、精度、布局和causal/noncausal mask；核对padding、软最大归一化、scale、RoPE、CFG分支和层映射。测输出误差、finite、峰值显存与同步计时。路由/打包/转置/编译/参考项额外计算分开记录且纳入端到端成本。

必须真正跳过块运算；dense矩阵再乘mask只能作数学参考。失败标TECH_BLOCKED；不能把CPU parity或GPU import当成真实kernel吞吐通过。

CalibAtt、LiteAttention、FastCache列为相近工作；SparsePR/Sol Engine列为额外实现/组合参考。只实现最相关且兼容的一个候选，不自动全部安装或横扫。既有工作相似不直接否定方向，但简单叠加本身不自动构成新贡献。

## 5. S2：四臂与固定跳步闭环

| 臂 | 主要目的 |
|---|---|
| N：优化后的Native dense | 统一生成参考 |
| W：官方WC dense | 缓存基线 |
| S：仅深层稀疏注意力 | 稀疏单项收益 |
| WS：WC + 同一深层稀疏注意力 | 简单组合与误差传播 |

F1仅有一个WC配置，不能称“最强WC”。进入正式曲线前给WC、S和WS相同的有限CAL调参预算，并保留原生直接少步及最相关强基线；不得只超过默认WC。

首轮沿用原CAL8/seed0，仅用于开发筛查，全部尝试/拒绝保留；如果预算不足，事前固定更小筛查集并如实命名，不按已有scalar涨分筛选。该批不承担独立确认。DEV使用未参与历史诊断/调参的样本，随后第二seed。

先保持probe密集、已有cross-attention不变；稀疏仅接deep self-attention。W/WS使用同一预登记的WC固定skip trace与完整刷新位置；它是因果部署可用性的诊断对照，不是自由调度结论。S按每步深层计算，不能伪造与W相同的工作量。full-mask控制补充于同内核的N/W路径，不只做一次孤立微基准。

重建模式按实际执行的层/CFG/模型调用识别，不按“每步必经过全部层”的全局计数猜测。WC跳过深层后也不得使sparse层计数错位。

诊断shadow的当前dense真值仅评分，不回写部署历史、模式、系数或决策。计时运行关闭shadow、profiler与tensor dump；真实过去的dense刷新才可作true anchor。

## 6. S3：一次替换一个模块，再重分配计算

按S0测得的边际成本选择warping、saliency/重复统计、稀疏模式重建或搬运，逐项变化。先固定schedule比较WS与WS-minus-one；保留probe、刷新上限、finite检查和分支隔离。

源码中的未使用warped_state是无输出依赖的优化候选，仍需检验副作用与输出等价性；即使成立也属于工程优化，不等于关闭整个warping安全。优化同样应用于对照路径。

模块减法通过后再放开刷新频率：比较“完整补偿+较少刷新”与“简单补偿+较多稀疏刷新”，至少两个重叠预算点。预登记质量容差与时间匹配范围；关闭模块变快但退化，不叫支配基线。

复用显著性统计/稀疏模式时，先共享廉价变化和触发信号；浅层saliency不当作深层attention重要性的真值。重建开销与模式年龄都记录，突变时允许独立重建和密集回退。

## 7. S4：复用—稀疏刷新—密集刷新

只有S1净省时、S2技术通过且S2/S3提示交互收益或退化机制后进入。比较固定最大cache age、固定dense刷新周期、简单直接叠加与三档策略，不先训练controller/RL。

保守初版：密集probe、定期完整刷新；稀疏刷新结果只写入明确标记的近似状态，不能升级为true dense anchor或进入仅允许真值的系数校准。

缓存元数据至少包括request/model/expert/CFG branch/condition identity、source_kind(dense/sparse/predicted)、source_step、dense_anchor_age、consecutive_reuse、mask_id/mask_age、kernel/dtype版本。分别记录复用次数、稀疏更新次数和密集刷新次数。

solver去噪step、CFG call与同分支有效调用分别标识；cache/mask age不得把另一CFG分支的调用当成同一轨迹更新，也不静默修改现有70周期/72调用的reset语义。

条件/模型/请求变化必须reset；模式变化使旧参考项失配时重建或密集回退。非finite/历史不足/达到reuse上限回退，不能用本步shadow真值选择模式。历史误差校准来自过去实际密集刷新或独立CAL，不是每个缓存命中都免费获取真值。

核心诊断：匹配相同当前状态与模式，观察一次稀疏刷新误差在随后连续复用中的传播；区分稀疏自身误差与缓存放大。只改善内部误差不解锁论文收益结论。

## 8. S5：完整参考 + 稀疏增量（条件诊断）

选少量层/固定离线CAL状态，定义同一算子、同一模式M下的dense输出A_t与sparse输出S_M(t)，历史参考s来自真实完整计算：

```text
A_hat_t = A_s + S_M(t) - S_M(s)
b_t = A_t - S_M(t)
A_t - A_hat_t = b_t - b_s
```

比较直接稀疏S_M(t)、直接复用A_s与增量近似；分析偏差变化/偏差本身、layer/head/去噪阶段/mask age分布、attention输出及下游block/velocity变化。误差恒等式成立不保证误差更小或端到端更快。

S_M(s)必须实际计算保存，不能裁切旧dense输出代替带独立softmax归一化的稀疏输出。模式、算子、精度、scale、mask语义改变时重建对应参考项；额外双计算、每层缓存、显存/访存与失效恢复计入。先比较固定模式和同算子full-mask控制，不在第一版全层加缓存。

通过同状态机制诊断后才安排固定轨迹闭环；离线A_t只作评估，不能用于部署决策。没有稳定净收益则关闭本分支。

## 9. 指标、停止条件与论文收敛

主要结果：干净端到端时间、去噪/各模块耗时、冷启动/预热、峰值显存、全部尝试与拒绝；配对质量/语义物理代理、动作完成、运动幅度、清晰度、时间一致性。运动更少不等于更好，MUSIQ/2B judge不能独自验证物理一致性，也不与论文标准评分混比。

CAL定阈值/质量容差/模式策略，DEV独立样本及第二seed确认；最终CONF冻结后不回调。开发代理与强评价分开，自动评价优先；人工评审仅在明确证据缺口与单独决策后使用，不作此分支默认前置。

| 观察 | 判断与动作 |
|---|---|
| 内核不支持或计时不快 | TECH_BLOCKED/NO_NET_KERNEL_GAIN；检查实现/硬件，不展开三档控制器 |
| 注意力在WC剩余成本中占比不足 | 暂停S，优先优化profile定位的实际瓶颈 |
| 单项可用但组合退化 | 优先来源标签、误差传播与dense刷新诊断，允许一次有根据修订 |
| 简单组合已有稳定收益 | 将其作为强基线，先独立确认；新机制必须超过它 |
| 模块替换 + 更多便宜刷新支配原曲线 | 冻结最简单候选，扩DEV/第二设置，不强行加S4/S5 |
| 内部误差降低，闭环质量/成本无收益 | MECHANISM_ONLY，停止增加复杂度 |

论文候选贡献是可解释的计算替换/联合误差处理/有效增量更新及稳定质量—时间收益，不是模块数量、熵变小或相乘的加速比。正式声称需公平调参、至少两个重叠预算点、独立样本/seed、相关强基线、机制消融与失败边界；不承诺必然成论文。

OMR仍待匹配代码/adapter/原版有效性：未来侧、均匀稀疏、梯度复用沿原J0–J3；WC+OMR须同底座四臂并处理纠正后的缓存失效。Cosmos3动作共享等待原生动作响应，不恢复第三条GPU主线。

## 10. 执行卡与成本登记

| experiment_id | 父实验/依赖 | 唯一主要变化/对照 | 输出与解锁条件 | 当前状态 |
|---|---|---|---|---|
| WC-S0-AUDIT | F1技术结果与源码锁 | WC后成本/真实shape/接口映射，非GPU先行 | 稀疏收益上限、profile方案与待核项 | PROPOSED_CPU_AUDIT |
| WC-S0-PROFILE | S0 audit + GPU窗口 | Native/WC分组件profile，固定CAL/seed | 实测f、诊断成本与clean分离 | WAIT_BUDGET |
| WC-S1-KERNEL | 真实shape/backend + 隔离环境 | dense/full-mask/sparse | finite/数值误差/真实时间/显存及路由成本 | WAIT_COMPATIBILITY_AND_BUDGET |
| WC-S2-REPLAY | S1净收益 + fixed trace | 四臂、密集probe与匹配full-mask控制 | 所有样本闭环、误差交互与净成本 | WAIT_S1 |
| WC-S3-SUBSTITUTE | S0实测昂贵模块 + S2 | 固定schedule单模块替换，随后便宜刷新重分配 | 同质量/同时间曲线收益 | WAIT_S2 |
| WC-S4-THREE_MODE | S2/S3明确机制缺口 | provenance-aware三档对简单周期/朴素叠加 | 稀疏误差传播与独立确认候选 | WAIT_SIGNAL |
| WC-S5-DELTA | S1可用 + 偏差稳定诊断价值 | 少层同状态三近似对照 | 增量误差、参考开销/显存、再决定闭环 | CONDITIONAL_DIAGNOSTIC |

每个实际运行卡必须另冻结source/config/hash、样本/seed/层列表、内核模式/阈值、比较臂、容差、warmup/repeat、输出目录、timeout/预算与失败语义。此表不授权上述运行。预算仍3.6512467238638138/4GPUh，余1255.511794秒；S0/S1不能依赖此余额“刚好够”就自动全批提交。模型加载、失败、微基准、profile、shadow与flush均计真实墙钟，一个昂贵任务同时运行。
