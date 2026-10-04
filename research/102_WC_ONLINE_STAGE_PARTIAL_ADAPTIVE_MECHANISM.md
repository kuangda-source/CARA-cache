# 在线阶段已实际执行：稀疏次数与缓存影响范围不同

2026-10-04。原[100八输出卡](100_WC_ONLINE_STAGE_EIGHT_OUTPUT_EXECUTION_CARD.md)仍运行。以下仅为已完成common三个测量的结构/来源证据，人物候选和整卡费用、完整四候选指标待完成；不是候选质量或速度接受。

[首个候选部分审计](../reports/wc_online_stage_r1_partial_phase_audit_20261004.json)和[common完整三臂审计](../reports/wc_online_stage_r1_partial_phase_audit_r2_20261004.json)各自保留原回执SHA。原frozen source3ad34e1、每臂完整93帧/36更新/72CFG/prepare1、实际attention metadata、来源/CFG/epoch/true-D历史及native70/尾dense独立通过。这里的S是实际GPU稀疏核，不是旧CPU toy的10/6配额。

| common已完成臂 | 实际S CFG调用 | S算子数 | 实际deep CFG调用 |
|---|---|---:|---:|
| 官方自适应WC | 无 | 0 | 35 |
| 窗口every1 | 45/46、49/50、53/54 | 138 | 35 |
| 窗口every2 | 45/46、53/54 | 92 | 36 |

every1实际去噪step23/25/27双CFG使用S，每CFG三个窗口内eligible full；every2选择其第1/3个eligible full，实际step23/27双CFG。全部固定23层，6/23/27 dense回退、S不入true-D历史，当前步骤和过去计数选择，不读取未来mask或deep truth。36 deep是合法原生反馈，不违反本卡未承诺固定deep数的范围。

## 两个值得纳入后续比较的现象

[实际决策差异](../reports/wc_online_stage_r1_common_adaptive_decisions_20261004.json)逐call比较原common官方与两个候选：every1的deep/cache决策与官方相同；every2在call70（实际去噪step35、CFG1）将原官方cache变为full，累计35→36。其余call判定相同。两个策略虽只改S频率，但会通过各自latent/cache轨迹影响后来原生判定，不能把4次S当成必然比6次S更省实际计算。

两个候选在call47/48、51/52和57/58都读取近似来源；57/58为step29，已经在窗口23–27之外。**限制新增S的位置不等于立即清空原生forecast窗口中的近似来源**。窗口外full用D，而官方cache保持，允许其已有forecast来源继续影响后续计算；目前不能从“停止S”推断误差立即消失或安全寿命。

这些是同曝光CAL/seed0的完整策略轨迹差异，不是同一个实际状态上的单步full/cache反事实，不能生成RV标签、分解瞬时与传播贡献或声称额外full改善多少。也不证明所有输入均有同样的call70反馈。

common三臂完整pipeline wall198.348480/197.230562/200.564102秒仅单次固定顺序描述，首次S与必要选择/来源开销保留；不作稳定加速归因。参数/输入没有为通过此审计改动，失败和负结果不会被替换。

## 下一步

现场1791072802.997635原任务7/8，人物官方WC/every1已完成208.100152/205.948581秒，最后cadence候选生成中；原三PID存活，3600全cost/3570child/kill5、原12h含预付10.136838727254782h、43jobs保持。继续原卡至终态，再统一独立八输出、逐臂在线来源/核/窗口与频率、费用/释放、全部四候选视频指标。整卡不完不得改成第一场景成功或减四候选分母。

后续评价以实际完整wall和保真为准，同时记录native full/cache反馈及窗口后approximate引用。先完成现有任务，有可用信号才进入Native/少步/调过WC强前沿；没有训练、人工评审或新的GPU卡选择。科学goal active。
