# 动作监督对齐：原生建议已成对，局部标签仍缺终点收益与未来成本

2026-10-09。**已有完整Human数据能描述当前动作误差与当前计算量，但不能直接监督“刷新后最终改善多少、未来节省多少时间”。** 本轮把这个缺口实际核对到每一条记录，而不是因未见端到端优势就否定W3。下一步仍继续原Common整卡；联合基线、成对probe成本、终点收益／未来成本标签分别需要正确对照。

## 实际执行与完整分母

按[H-T53登记](../plans/WORLD_CACHE_EXISTING_ACTION_TARGET_ALIGNMENT_CPU_20261009.md)，先提交推送，source `f586fe9cfdcf8592ff3e08149440c515c82dda4e`执行一次本地标准库CPU，wall **0.075905秒**。输入是已完成且已曝光的Human seed2／seed3两份完整教师原件；没有读取当前Common的部分教师或评分。

全部两seed×五起点×四动作×两重复＝**80对／160事件／40严格重复组**，导出20条带重复proxy记录和10个相关状态。两次种子和四个分叉不是10个独立场景。原server已完成的各120实际张量与完整重复审计通过；本轮只读取压缩原runner、score、capture和独立审计，并核对字节SHA，不声称第二次实际张量加载。

[实际CPU结果](../reports/wc_existing_action_target_alignment_cpu_r1_20261009.json)与[原stdout](../reports/wc_existing_action_target_alignment_cpu_r1_20261009.log)保留所有细胞／重复／原pair wall。另用各可用deep配额0／26／52分别枚举最小误差，独立重建全部10个局部非支配集合、80对／160事件／40重复和缺失标签，见[独立核对](../reports/wc_existing_action_target_alignment_cpu_r1_independent_audit_20261009.json)。不拟合阈值、路由或Head，没有Torch／新GPU，费用原字节不变。

## 找到了什么

四动作和两重复的paid input／probe drift、阈值、累积量、年龄和原生建议，在各状态内**10／10实测一致**。原生两槽建议为4个CC、6个DD，没有DC／CD；这是已有历史上的诊断建议拼接。原执行先完成条件侧才获得无条件probe，所以不能把拼接结果当作当时第一次深层计算前可用的联合在线输入。

下表“局部集合”仅比较自身DD参照的guided MSE与当前deep block次数。CC、DC、CD、DD的实际deep次数分别为0、26、26、52。

| seed | 自身起点 | 原生两槽建议 | 局部误差—当前deep非支配动作 |
| --- | --- | --- | --- |
| 2 | S22 | CC | CC／DD |
| 2 | S23_after_CC | DD | CC／DD |
| 2 | S23_after_DC | DD | CC／CD／DD |
| 2 | S23_after_CD | DD | CC／DD |
| 2 | S23_after_DD | CC | CC／DD |
| 3 | S22 | CC | CC／DD |
| 3 | S23_after_CC | DD | CC／DD |
| 3 | S23_after_DC | DD | CC／DD |
| 3 | S23_after_CD | DD | CC／DD |
| 3 | S23_after_DD | CC | CC／DD |

旧seed2的after_DC中，CD相对CC的局部MSE改善8.8244%、当前只做26个deep block，仍保留为一种局部计算配额选择。新seed3相同标签的自身状态中，CD退化55.6452%，没有复现这个例外。它们是不同实际latent／缓存／solver状态，不按起点名称补认状态相同，也不抹掉旧例外。

**“原生建议10／10在局部集合内”不是路由准确率或最优策略证据。** CC当前deep最少，DD误差0又是自身教师定义，两端本来就通常保留在这个局部集合中；它没有决定在哪个去噪位置支付52个deep block更划算。这里的deep次数也不是真实秒数，原pair wall包含诊断、复制、哈希等开销，没有被转换为部署加速。

## 对后续设计的具体含义

本轮全部40个动作标签保留`L_CC-L_action`、当前deep与额外deep；**完整尾部的终点失真差、未来真实节省时间均为null**，没有用局部误差或当前调用数填充。因此不能训练一个声称预测终点刷新收益的Head，或把这10个状态当新的质量泛化确认。

下一比较至少保留当前WC、简单共同刷新，以及正确接入／校准的RA式联合基线。H-T50成对probe的Toy接口通过仍不是2B实际输出／成本通过。未来完整干预应同时记录同预算位置重分配效果与允许自适应后的质量／时间总效果；局部teacher用于机制解释，终点与未来成本用于调度目标。是否出现一个局部例外不能单独决定方向成败。

这些安排不改变当前Common身份、95运行源、全部重复、原判据、50GPUh或单次>2GPUh确认约定；不训练、不扩大稀疏、不切换OMR／DRE、不引入人评。

## 当前Common真实进展

[同原句柄只读观察](../reports/wc_other_scene_cfg_confirmation_r1_action_alignment_live_20261009.json)确认3426296／3426308／3426297三原PID仍活；source c243d30／95载荷／配置不改，模型加载101.156951秒完成，prompt guardrail通过，首OFF父实际采样到28／36。尚未完成全部两父、五起点／40对、两视频及后CPU全量审计，不能评分成功子集或宣称Common机制重现。

已结算底数27.644682758／50GPUh，第64提交在途used50仅预留，费用终态全wall结算。总体goal active：上一turn实际派发与飞书完成是progress，本轮全范围CPU目标对齐和特定活句柄核对是progress＋verified wait，不是授权受阻或方向失败。继续原完整任务，终态再做独立重建；飞书revision15已包含此前完整科学成果与Common执行状态，本轮不为重复CPU阶段追加新“成果”。
