# 共享规划与自身历史诊断：独立判断包的接续

本文件记录本次用户决定。共享规划和实际历史采集仍由原PG-P1/P2唯一执行链完成，分析结论单独保存于本目录。没有第二个runner或新训练卡；本聊天仅新增验收证据接续自动任务，见下文。

## 2026-10-24原P1终态后的具体接续

原P1已经验收，但selected_policy=null、PG_P2_input_ready=false。此次重新运行原接受器再次确认该结果。[机器门槛回执](p1_gate_status_20261024.json)保存原件SHA及本轮独立核验。以下“原P1完整终态”步骤已经完成，不再等待或重复派发原P1。

当前唯一活动GPU任务是104路径计时/预算边界卡，launch `d6351496-ee8a-4428-8ede-898f53d665cd`、source `5fc4dfe66a33a915fcc7bdf10700bae8810bb401`、上限11.9 GPUh。复用主线原句柄及其半程/终态安排；本目录不改该卡、不从部分输出调参。完整104接受后，先完成主线的成本桥接与修复P1，再按通过实测预算的冻结CARA/SIMPLE接入原P2历史诊断。原257.7712338712067秒、0.80×新Native和累计226 GPUh不变。104卡本身不采集本诊断的shadow D标签，不能据其名字含history就宣布历史失配实验已执行。

这一依赖未满足属于既定判断合同S1/S2的预先约定，不是临时新增审批要求，也不需要用户重新确认。用户已授权没有重要问题就自行推进；保留原唯一执行链，不创建重复提交或监控。新策略/卡仍需各自完整范围、CPU、报价和fresh准入，旧P1验收不能代替新卡准入。

本聊天已创建“CARA 自身历史诊断接续”（automation id `cara`），Asia/Shanghai每日16:30、20:30检查已保存的验收结果。主线原09:05半程和15:03终态检查保持不变。本任务不重复主线实时GPU监控，优先消费其完整原件；仅在依赖完整、没有现存提交或owner且原整卡准入通过时接续执行。状态未变保持安静，完成独立分析后删除自动任务。[自动接续回执](continuation_schedule_20261024.json)记录核对结果。

## 1. 等待原PG-P1完整终态

原launch：`39b4481a-79a7-4dff-92aa-0498a03c3e78`；source：`170c50e6c289a93cb60d13ead918fdb258177746`。原[实际启动回执](../../reports/cara_PG_P1_full64_GPU_actual_launch_20261023_2030.json)与[661接续](../661_CARA_EXCLUSIVE_PRICES_ACCEPTED_PG_P1_ACTUALLY_ADMITTED_20261023.md)保留。遵循主线的原句柄恢复/半程/终态程序，不因本目录存在再次派发，不读取部分终点调阈值。

必须获得绑定原capture SHA的完整独立接受；核对全部位置、候选、拒绝/失败、冻结SELECT、视频评分、独占时钟、费用及资源释放。复用原CAL选择，不按本次解释另选“更适合诊断”的策略。

## 2. 绑定实际历史诊断

复用[既有历史合同](../../plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)、`history_matrix`和`p2_history_sampling`。

- 输入为原CAL_FIT前两条、seed0；角色为最终CARA与按原SELECT顺序确定的可行SIMPLE。相同策略指纹物理去重但保留两个角色。
- 每个唯一策略1warm+2formal，最多6路径。最近两个真实D间隔按2–4、5–8、≥9分组，每组只取最早合法跳步；空组不补点。
- 同自身状态比较真实[p,s]与邻接影子[s−1,s]两窗口的C/A(.5)/A(1)，共用shadow D参照；A(1)必须对较早锚点逐位不变。
- 记录逐步guided、终态latent与93帧OFF/ON控制，以及输入/solver/cache/anchor/condition/RNG不干扰。原双支张量由`p2_history_analysis.audit_record`核验，不只相信保存标量。
- 诊断路径有shadow，不能进入干净部署速度表。所有shadow、读出、保存及评分进入实际费用。

主线已有[P2生产CPU R4接受](../../reports/cara_PG_P2_native_history_CPU_accepted_r4_20261023.json)及[完整capture](../../reports/cara_PG_P2_native_history_CPU_complete_r4_20261023.json)，本目录只复用它们；不得重跑已通过的CPU或独立改动其stage。`scripts/prepare_cara_pg_p2_after_p1_r1.py`是主线的P1→P2原件绑定入口，以[663生产交接](../663_CARA_PG_P2_NATIVE_HISTORY_PRODUCTION_CPU_ACCEPTED_AND_WHOLE_QUOTE_20261023.md)和其冻结版本为准，本目录不复制实现。生产入口CPU接受仍不等于完整P2 GPU生命周期已验，也不等于真实历史诊断已完成。

既有CPU矩阵接口（在输入已按原P1终态冻结后）：

```sh
python3 scripts/prepare_cara_pg_continuation_r1.py history-matrix \
  --input <原P1最终策略与SIMPLE及前两CAL_FIT绑定.json> \
  --output <新的历史矩阵回执.json>
```

矩阵生成不是GPU准入。诊断保留在既定P2完整范围中，原完整报价、生产入口/整卡生命周期CPU、fresh独占/账本/资源准入通过后执行。若P1无可行SIMPLE或策略缺失，明确记录依赖未满足，不按诊断结果补选。

## 3. 单独写出判断

在完整接受后新增唯一的本目录结果文件，绑定P1接受、P2接受与原张量审计SHA，不覆盖`results.json`中的旧CAL分析。

建议每行保留：policy role/fingerprint、CAL/seed、history bin、p/s/t、两窗口动作MSE、教师表MSE、动作并列集合、后悔值区间、原件SHA、shadow调用数及控制状态。先逐prompt汇总，再等权汇总；帧/格/动作不增加独立样本数。

判读依照[decision_contract.json](decision_contract.json)的S1–S4。没有合法点记NOT_APPLICABLE；技术控制失败不作科学归因；资料不足记PENDING。两prompt机制诊断不产生一般化优劣或3%等价结论。

本包允许提出下一项机制问题，但不会自动启动敏感度采集、在线校准、L2/L3、调度器训练或DAgger，也不会重新打开662关闭的研究线。
