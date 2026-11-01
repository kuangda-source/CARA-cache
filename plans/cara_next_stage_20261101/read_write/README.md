# 读写价值感知的刷新规划：后续主线

2026-11-01。依据用户“把这个框架更新到后续实验然后继续推进”，接收[原讨论稿](SOURCE_FRAMEWORK_20261101.md)。本目录更新后续安排；E1原预注册、原决策与旧冻结保持原字节。

## 当前执行与下一步

原M1已于18:49:24在原A6000启动完整14请求/512paired，硬1.95GPUh；只按[实际运行交接](M1_FULL14_POST_LAUNCH_HANDOFF_20261101.md)恢复和验收。下方242调用共享前缀设计是历史组件方案，实际执行以完整14 R2为准。等待期已新增[M2缓存导数实现与硬行动安排](M2_ADJOINT_IMPLEMENTATION_AND_HARD_ACTION_PLAN_R1.md)，固定源码/小权重CPU五项通过；真实Cosmos伴随与M2整卡费用尚待。

## 当前目标与唯一候选

**先建立一个可解释、可执行、可复现的主方法。** 用户明确允许效果不特别好或完美；近期验收关注机制、规则与证据能否对应。不把大幅提升、完整迁移或击败全部强基线作为开始研究的前提，也不以“高级”术语替代实际贡献。

唯一主候选是：**把一次刷新对当前输出／求解器的作用，与对后续缓存来源的作用分开，用候选自身轨迹上的终点价值指导固定预算刷新。** 输出离线共享D/C序列，部署保持固定开环执行。首版固定Cosmos、UniPC、CFG系数和原C读出；A/Q与Euler迁移后置。

采用原稿推荐C：增广状态的离散伴随＋每轮少量硬候选验证。区间DP与低秩响应只作对照或诊断。若完整状态反向代价不合适，另行登记简化估值器，披露近似；不能把它仍称为完整伴随。M1四格是机制实验，单独做出四格并不等于已有调度方法。

原有限结构化预算配方不再是主线交付，保留作简单对照。E1已完整验收，当前S仍不晋级；不重新评分、挑选搜索赢家或改写E1结论。

## 先完成的证据链

|阶段|具体问题与最小工作|达到什么才进入下一步|
|---|---|---|
|M0 状态与导数接线|显式UniPC历史；完整两CFG缓存/来源/工作状态；同父C/D与混合状态的前向；输入VJP有限差分|影响本次路径的状态恢复、硬前向等价通过。真实模型VJP另立组件验收，不用CPU合成系统代替|
|M1 真实读写四格|两旧FIT，一个由合法计划决定的位置，00/10/01/11八条完整后缀|报告有符号读、写、交互和逐输入结果；判断写入是否值得作为核心机制。M1可先于昂贵全轨迹反向运行|
|M2 值是否能指导行动|原S局部q、同一终点伴随的read-only、完整read+write；同父计划与等候选预算；完整硬swap验收|导数数值正确与硬交换有用分别判断。小而可复现的增量可继续，不设置5%机械晋级线|
|M3 最小方法证据|从通用Uniform初始化，固定K先19D；最多3轮、每轮最多2个新候选，以完整FIT终点评价接受；冻结后看开发留出|规则确实能产生新计划，关键消融可归因，完整终点收益及实际代价可解释；大规模独立确认和第二设置随后登记|

M1只依赖真实状态拆分与恢复，不要求先完成全36步LPIPS反向。这样先回答核心机制，再决定是否投入完整伴随。M2采用伴随时仍必须通过真实模型输入VJP和实际C转移验证。

## 首个M1范围已经具体化

完整机器协议见[EXPERIMENT_PROTOCOL_R1.json](EXPERIMENT_PROTOCOL_R1.json)。父计划是现有确定性sigma覆盖Uniform19-C，不从F19手填位置。

- 两个原FIT：`av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632`、`human_199`，seed0。旧CHECK和保护TEST不用于M1选点。
- 原35请求产生36实际更新。Uniform19的D为`1–7,16,19,22–29,31,36`。按“首个合法C且下步仍为C”选**第8次更新**；后续9–15均复用。选择来自动作/来源计数，无逐步科学分数输入。
- 每输入只算一个父前缀，在同一pre-write状态取得C和D的完整后状态，再完成四个原计划后缀。00=(yC,CC)、10=(yD,CC)、01=(yC,CD)、11=(yD,CD)，y包括latent和全部UniPC历史。10/01支付Dense取值，属于诊断，不当便宜部署动作。
- 7次前缀＋2次当前动作＋4×28次剩余更新＝**121次paired velocity调用/输入，242次合计**，另有8次完整解码/输出。若原Native完整身份不能复用，增加两条36更新参考，共314次；实际加载、warm、控制、复制、编码、释放与存储另计。
- 所有后缀自由演化；不把solver历史拉回Native，不固定后续cache值。完整8后缀、参考身份与释放后才统一评分，不看部分结果选下一点。
- 最后无未来消费者的零写入控制先保留在CPU；新增GPU位置必须先修订完整范围与报价。单个位置有信号只支持pilot，不夸为全局规律。

这个范围是准备协议，**不是已经可派发的GPU卡或准确费用报价**。完成真实生产入口、完整资源/存储报价与原账本权限后，按现行GPUh阈值及fresh准入推进；当前两卡限制、cap226与旧16.5责任保持。

## 方法的最小成立标准

1. 说得清：有真实缓存来源写入的终点作用，关键反事实能分辨该作用；若只支持当前输出纠错，就相应缩小主张。
2. 算得出：输入预算与校准数据能按固定规则输出计划；不用事后挑步号，也不要求一定恢复F19。
3. 验得到：full对read-only有可辨认增量，冻结计划在开发留出有可复现的实际表现；四旧CAL与多次使用CHECK保持开发口径。
4. 成本可交代：校准GPUh包含shadow、反向、重算与硬候选，部署同时报告T_DD和T_request；同K不宣称精确时间匹配。

小幅一致收益、某个清楚的速度—保真工作点或能够解释的预算取舍，都值得形成论文主线。若只在FIT有效，或写项始终无增量，记录结果并调整主张，不继续增加大量参数掩盖机制问题。

## 当前实际推进

本次已实现并通过独立CPU组件：[显式状态/四格](../../../src/wcomr/cara_read_write_state_r1.py)、[有限交换提案器](../../../src/wcomr/cara_read_write_proposals_r1.py)，以及[20项控制](../../../tests/test_cara_read_write_m0_r1.py)。真实UniPC执行36次更新，检查历史VJP；合成缓存用于检验读写导数和符号。[M0通过回执](../../../reports/cara_read_write_M0_CPU_component_r2_20261101.json)。它们不修改旧生产代码，不证明真实Cosmos缓存或视频收益。

复核命令：

```bash
PYTHONPATH=src CUDA_VISIBLE_DEVICES='' .venv/bin/python scripts/check_cara_read_write_m0_r1.py \
  --runtime .sync/wc-time-p0-runtime \
  --output reports/cara_read_write_M0_CPU_component_r2_20261101.json
```

又完成[四格后缀组件](../../../src/wcomr/cara_read_write_suffix_r1.py)和原WC/RF/UniPC函数体的[小张量集成](../../../tests/check_cara_read_write_suffix_cpu_r1.py)：flow OFF/ON各四格，00与独立Uniform19、11与独立D8计划逐值一致；完整solver/cache分组、来源、父续跑、失败恢复和禁止重复运行均通过。[M1组件通过回执](../../../reports/cara_read_write_M1_suffix_CPU_component_r3_20261101.json)。本地使用明确CPU依赖namespace和小权重，未验Linux真实import或48GB资源。

```bash
PYTHONPATH=src CUDA_VISIBLE_DEVICES='' .venv/bin/python scripts/check_cara_read_write_suffix_cpu_r1.py \
  --runtime .sync/read-write-pinned-runtime-r1 \
  --output reports/cara_read_write_M1_suffix_CPU_component_r3_20261101.json
```

上述命令的输出必须改为新的回执路径再执行；原件不可覆盖。本地M0首轮的外来类拒绝测试接线、M1的namespace/精简runtime缺文件失败均保留，未执行或重派GPU。状态归属与尚缺边界见[状态清单](STATE_AND_ACCEPTANCE_BOUNDARIES_R1.md)。

后续直接任务是**两卡的受影响Linux CPU接线、真实参数状态/内存验证和完整八后缀卡报价**，复用既有监督与评分组件。目前不重跑A32/B36/S/Q/搜索/E1，不扩大CHECK/TEST曝光，不自动复用已完成卡的账本事务权限。
