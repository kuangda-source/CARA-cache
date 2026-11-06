# Codex 首批执行说明：WorldCache

**仓库分工（2026-10-02）：本库只推进WorldCache。** OMR文档、独立队列与Wan/LongLive支持准备已迁至[omr-experiments](https://github.com/kuangda-source/omr-experiments)。当前WC-S/H冻结工作先完成，预算、运行配置和回执不变。拆分不启动或取消实验。


**执行顺序约束（用户2026-10-02）：当前工作不取消，先按原范围完成并审计，再考虑本轮新增设计。** 保留已冻结运行的配置、source、预算、失败和输出；当前S1结果归档/中间刷新覆盖准备优先，v1.3的寿命与分组卡后置。本次不终止进程、不重置运行或以新候选替代未完成工作。

2026-10-01后续内核结果：S1实际A6000合成QKV8case完成，full-mask数值技术门通过，静态稀疏mask误差大；下一真实模型QKV与WC剩余成本profile，不解锁视频四臂或三档。GPU11.726698秒在原4h内结算，详见[59结果](../research/59_WC_S1_REAL_KERNEL_RESULTS.md)。

2026-10-01后续执行：完整upstream两sm86扩展CPU构建/独立fresh审计通过，无PV wrapper同3CPU契约本地与实际Cosmos Torch通过；下一动态导入/ABI及有界GPUrunner准备，实际kernel/profile/质量尚待。见[构建终态](../research/57_WC_S1_ISOLATED_UPSTREAM_BUILD.md)。

2026-10-01执行更新：S0实际CPU checkpoint/source接口审计通过，构建/直接QKV/profile未通过；公开full-QK默认仍PV跳过，S1首轮改为dense/full-QK-no-PV/sparse-QK-no-PV并另列PV因子。详见[实际审计](../research/56_WC_S0_SOURCE_SHAPE_AND_KERNEL_AUDIT.md)。GPU预算不变。

**日期：** 2026-09-29；2026-10-02更新至v1.3
**对应总计划：** `LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_20260929.md`  
**用途：** 把下面正文交给当前项目主线程。它要求接续现有项目，不要求先重建科研自动化框架。本文本不是已运行的实验报告。

---

请先阅读长程实验计划，再从当前项目状态接续执行。不要从零重新设计全部方向，不要自动跑完整路线图。

## 一、长期目标

在已有 WorldCache 上，形成可重复的质量—时间改进：同质量更快，或同时间质量更好。先尝试实现门槛低的增量方法，允许借鉴和深化已有思想；不要因为存在相似论文就直接否定候选。


**v1.3接续入口（第八节覆盖第七节）：** 下文F0/F1/W1为原首批设计，不要求重跑；最新状态见实验总览/回执，新增顺序见第七节/research/55。更新设计不自动扩GPU额度。

## 二、本批次范围

依次处理 F0-ASSET、F1-SMOKE，并根据实测成本和既有权限提出 F2-FRONTIER / W1-SHADOW。资源核实可以与非 GPU 工作并行；同时最多一个昂贵 GPU 任务。

### F0-ASSET

读取：

- `AGENTS.md` 和现有项目规则；
- `research/GOAL.yaml`、`02_CURRENT_STATE.md`、`09_NEXT_ACTIONS.md`；
- 最近实验报告、预算账本、未完成任务与 `memory/handoffs/LATEST.md`；
- WorldCache 当前代码和所用模型/推理入口。

先检查 git status 和运行中作业。保留现有修改，不覆盖原始结果，不重复已经完成且配置兼容的实验。

输出一份简短资产表，说明模型、权重、上游 commit、推理入口、配置、硬件、已用预算与尚未确认项。定位 probe/deep residual、缓存状态、CFG/条件分支和真实 full-compute anchor 的代码路径。不要根据论文符号猜测变量和函数。


Cosmos3 只核对 P0–P2 的已有证据与剩余预算；本批次不自动恢复原 P3–P5 全部任务。

### F1-SMOKE

只有项目中存在明确的 GPU 执行授权，且批次成本不超过剩余预算时，才运行 Native 与官方 WorldCache 的 4 场景 × 1 seed smoke。

保持相同 checkpoint、条件、seed、尺寸、帧数、采样器、精度和卸载策略。第一选择是官方支持的原始配置；若降规格，明确标为资源适配设置。

记录生成是否成功、输出规格、缓存命中、显存、原生单视频时间与主要开销。技术错误不计作科学负结果。

若没有明确授权，完成非 GPU 检查与实验卡，停在 NEEDS_GPU_APPROVAL。不要把总计划中的 4/12/20 GPU·h 建议值当成已有授权。

## 三、首个候选 W1 的实现要求

先实现三个模式：原始 WorldCache、简单增量收缩/一阶外推、在线标量浅深层增量校准。

在源码确认 probe residual 与 deep residual 的定义和维度可比后，再实现：

`r_hat_t = r_s + beta_t * (p_t - p_s)`

`s` 必须是当前分支历史上真实完整计算的 anchor，而不是无条件使用 t−1/t−2。beta 只来自当前之前实际完整计算步的成对增量，使用小规模正则化与裁剪；数据不足时回退官方 WC。

第一轮不同时加入分组、可学习 controller、warp 改动和多阈值搜索。

诊断版可在预测之后额外计算真实 deep output，但真值只能记录误差，不得更新本次预测、缓存、统计或决策。部署版关闭所有额外真值计算。原生轨迹离线收益之后仍需实际加速轨迹的闭环验证。

至少测试：

1. 缓存关闭时与原生路径一致；候选关闭时保留官方行为。
2. 当前步真值不泄漏到预测和在线决策。
3. 不同 prompt、条件分支、expert 和重启任务不会误用缓存。
4. 小分母、NaN/Inf、anchor 不足时安全回退。
5. 诊断 hook 不改变生成状态；干净测速不包含 profiler/特征 dump。

## 四、预算与自动化

服从现有工作流已经验收的权限，不默认升级成长期无人值守。

等待、轮询、计账、基础结果提取使用确定性程序。GPU RUNNING 期间不为检查状态调用模型；一个完成事件至多触发一次主要分析。

已有批准窗口内才能提交下一任务。最多 3 个自主轮次、单个昂贵任务，以及项目内更严格的 GPU/金额上限均须遵守。429 时保存状态并停止，不循环重试。

三次不减少不确定性的实验触发方向审查；不能将“三次没有涨分”机械等同于无进展。INCONCLUSIVE 不写成 FAIL，技术失败不写成科学失败。

## 五、完成后报告

更新现有 CURRENT_STATE、HYPOTHESIS_LEDGER、EVIDENCE_MAP、DECISION_LOG、NEXT_ACTIONS 和 handoff；不要重复创建另一套记忆目录。

交付一份报告，包含：

- 本批次实际执行与未执行的任务；
- 运行配置、样本清单、全部结果与真实成本；
- 基线是否可信，主要瓶颈与现有混杂；
- W1 的初步证据属于 TECH_BLOCKED / INCONCLUSIVE / MECHANISM_ONLY / PROMISING / NO_GAIN_IN_SCOPE 的哪一种；
- 一个最值得执行的下一任务及原因、预计预算、依赖和停止条件。

本批次不要自动启动新模型训练、全量 benchmark、付费评分、大规模 Cosmos3 探索或多算法组合。出现明确收益后优先小复验，不为了让方法复杂而增加模块。

## 六、2026-09-30补充执行顺序（与总计划v1.1一致）

## 七、2026-10-01最新讨论补充（v1.2，覆盖历史优先顺序）

目标为受质量与行为保持约束的计算压缩。完整设计见[WC-S执行卡](../research/55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)，来源见[记录](../manifests/plan_update_sources_20261001.json)。前文暂缓多算法组合不排除本次有界两项对照，但不自动叠加量化/少步/物理纠正。

1. F1/W1证据复用；W1机制改善但质量收益未证，暂停scalar/W2复杂化。下一非GPU准备是S0源码/真实shape/成本方案。
2. 有预算时先测WC后的成本，再检验内核：native dense / 同内核full-mask / sparse，隔离低精度/后端混杂；真实routing/shape/mask/显存计入，不用dense乘mask声称省算。
3. 四臂：优化Native、官方WC、仅deep稀疏、WC+deep稀疏；probe密集/cross-attention不变，W/WS同skip trace，匹配full-mask控制。CAL8仅开发，不冒充独立确认。
4. 先单模块替换，再同质量/同时间比较复杂补偿少刷新与简单补偿多稀疏刷新；不先删probe/刷新保护。实际profile决定改哪项。
5. 有机制缺口才做三档调度；稀疏状态标源，不作true dense anchor。S5完整参考+同模式稀疏增量仅少层同状态诊断，参考计算/缓存与显存计费。
6. 保持4GPUh上限/已用3.6512467238638138，原新4GPUh/clean50待决策；未执行GPU、不扩额。下一窗口按最有信息的成本卡提议。自动评价优先，不默认人评/付费/训练；Cosmos3按原依赖门接续。

## 八、2026-10-02最新层级讨论（v1.3，当前接续顺序）

详细设计见[65来源与有效期](../research/65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)，来源见[一手核对](../manifests/plan_update_sources_hierarchy_20261002.json)。RAPID³/SADA等已覆盖计算方式组合，当前待证问题是参考创建误差如何影响后续复用长度，不凭三档/免训练宣称创新。

1. 复用S0成本及S1四组合144case审计，先补中间实际刷新/全深层覆盖；首尾12QKV不足以部署所有层。只准备有界诊断，不重跑已完成控制。
2. 最小基线保留WC浅层probe/skip/强制dense位置，重算处比较S/D；核对残差与输入兼容，计全部组/路由费用。
3. 优先诊断dense/同候选full/sparse三来源×复用1/2/4步，完整恢复solver历史/RNG/CFG缓存；同状态诊断与最终视频分开，真值只评分。
4. 有信号才两组，三组另作复杂度控制；增加静态分组、无来源动态、来源/计划寿命消融及相近动作数量的位置控制。不同时独立控制所有MLP/cross/head/token。
5. 特征与mask失效分别记录，成本明显才加模式复用；PSA表示精度后置，S3模块替换由边际成本驱动。局部dense不恢复Native轨迹，稀疏参考不是true anchor。
6. 账本3.9117525685110333/4GPUh、余317.690753秒；此次设计更新无新GPU/扩额/训练/人评/付费。新4GPUh/clean50仍待决策，完整寿命/视频曲线另冻结范围和成本。


## 九、2026-10-02刷新收益讨论（v1.5，条件后置）

当前冻结WC-S/H范围先完成，保持第八节队列；新增[WC-RV首窗口](CODEX_FIRST_WINDOW_WC_REFRESH_VALUE_20261002.md)只登记因果恢复/在线可见特征、CFG决策与预算单位、固定后缀及同预算标签区别、RV1具体成本。新[68设计](../research/68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)按收益空间→廉价可预测性→闭环推进，不立即训练Head。

保留原4GPUh/new4h-clean50未分配状态，不动runtime/已有collector或输出；采标签、CPU拟合、Head训练/部署等均未执行。无新增人评/付费/LoRA，也不将对话中“继续W1”的旧阶段描述当本库当前任务。
