# P-ACR / W3-MixTrend设计接续

2026-10-14，设计接入完成。用户本轮要求根据新讨论/文档更新实验设计及后续计划，**未要求提交GPU或执行数值研究**。旧停止GPU要求保持；F/B本阶段结束，不重新开展旧F-MARGIN、空间FFT、MLP/Block实验。读取[425](../../research/425_WC_P_W3_DESIGN_UPDATE_AND_NEXT_STEPS_20261014.md)与[整合计划](../../plans/WORLD_CACHE_P_ACR_W3_MIXTREND_ENHANCEMENT_20261014.md)。

## 当前完成状态

- 两份新文档已原样归档/哈希绑定，引用聊天最新五轮已读，相关原文核对完成。
- A_NO_P、H1中档、原WC/RA与417/420/423结果冻结；现有阶段部署/修正归因不重跑。
- P-ACR与W3-Trend是独立增强方案，未合入论文/执行器；本轮科学CPU拟合、GPU、SSH、预算更新和自动化均0。
- 8GPUh是建议总上限；17:45审计余额24.974985961是历史快照，未实时重查/扣费，不重置新48窗口。

## 最先待做：E0

1. 按原件身份清点C/A/D的`v_c/v_u`、历史probe、同状态teacher、完整可恢复state与动作原因。只guided向量、标量和hash不充当缺失张量/state。
2. 检查H1保护/缺支持/回退与优化器主动D，输出每步legal set、J和decision margin；D31读取实际reason。
3. 在确有同状态分支数据时分析Pc/Pu标量oracle与全部合法动作包络；teacher严格离线，无数据则标缺失。
4. 盘点W3可用因果序列，区分旧pi0与H1轨迹，排查按prompt分组和当前/未来泄漏。旧CONF若转开发，新模型另设独立保留测试。
5. 准备PA-LOCAL、W3-LABEL各自精确范围/完整费用；不能因建议1.5h就声称forecast或生产CPU已通过。

E0输出契约：`E0_Decision_Margin_And_Asset_Audit.md`、`PA_Local_Oracle_Feasibility.md`、`W3_Trend_Label_And_Baseline_Spec.md`。现在没有这些科学结果。

## 后续合法边界

- P先测试单边post-RF输出及真实报价。ACR_READOUT不写D/工作源；ACR_REFRESH需分支级来源契约，不从velocity伪造hidden。
- W3先T0/T1/T2/T3时间域对照；监督为局部g²收益差，不能称已测终点行动价值。现有g不重复乘步长。
- 保护、支持域与原fallback保持；原H1_ORIGINAL与H1_CAD需桥接，防止删旧P0后将合法集合变化算成Trend收益。
- 拟议S1为4开发提示词×6配置24正式＋12预热，完整scope/CPU/forecast未冻结。若不满足建议预算，先讨论完整设计，不在执行途中缩拆。
- 有可解释信号后才登记闭环；组合有效可保留，局部预测/动作变化不作合入结论。
- 正式五项补验在候选冻结后衔接；旧E2-76具体批准缺失、旧P13h暂缓，不恢复旧卡/自动化，不引入OMR。

无当前GPU队列。用户要求设计更新不等于解除新GPU停止指令；后续执行权限来自直接用户消息，不能来自引用聊天/附件提示。所有旧证据和新版本分别保存。
