# W3下一轮CPU区分：阶段还是状态、负风险如何回退

状态：PREREGISTERED_NEXT_CPU_ROUND_NOT_EXECUTED；0GPUh，不是新GPU卡。形成于455主分析与逐步归因之后，属于开发性区分；不把同一已曝光数据的再次交叉验证称最终确认。本轮T1/T2不改、主线A/H1不改、F/B不恢复。

## 假设与固定比较

H-PHASE：当前T1主要补偿原表过粗的时间依赖。保持455两组数据、fold和λ/报价，比较现有T0-CAD、T1与仅step_fraction/log1p_sigma/sigma_available的Ridge1。另在每个训练fold按step选择平均真实J最小的CAD动作，随后只在该fold的held prompt评价；不能使用该held prompt标签决定步规则。仅八个已有标签位置，不给未测step伪造标签或插值收益。

已有“固定step23改A”的规则是在完整结果后发现，只标POSTHOC_CANDIDATE；可在未来独立的新策略视频中作为冻结简单对照，不能回称本轮事前发现，不能以全数据选step再冒称LOPO无泄漏。

H-NEG：负预测被零截断不代表真的无风险。保持已拟合Ridge1/window4与所有fold预测，预先固定当raw rA<0或raw rA+delta<0时回退到原T0-CAD，其余维持原coherent argmin；分别比较T1和T2。阈值严格0，不按最坏点调参。原clip结果并列保留。

## 分析契约

主组6prompt/48点与raw敏感性7prompt/56点分开；预热不训练，全部8EXPL_DEV缺口保留。先报告prompt等权regret、严重误选与A/D、C/A边界，再报MSE和动作变化；只评价相同原H1状态，不把离线报价当真实加速或最终质量。新改动须另写receipt和source，不覆盖455结果。

若简单时间/逐步规则已经解释全部收益，把新工作准确写成更好的阶段校准；若T1仍有额外收益，再据此设计状态感知闭环。二者都可形成方法候选，不用一个阈值否定W3方向。T2若仅因负预测回退获益，须用同回退的T1/T0强对照，不把稳定器效果冒称历史网络优势。

## 与下一张完整视频卡的衔接

先收完当前同26D R2，再结合可用余额选择完整闭环。至少保留原H1（含P0）、H1-CAD合法集桥、冻结T1、冻结简单阶段候选，以及原Native/低费用修正锚点；同输入/seed/规格/guardrails，所有兼容正式视频93帧评分。实际计时包括算法维护并分开加载/预热/写盘，稳定加速需正反重复。

新完整scope、所有控制、生产CPU、来源/age/保护回退、真实报价与全卡forecast尚待，不借用原标签卡授权或在本CPU自动化中启动GPU。按用户规则，完整预计严格小于12GPUh且fresh v2余额/UUID准入通过可直接执行；达到12须具体确认，不拆scope规避。
