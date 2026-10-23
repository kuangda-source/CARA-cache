# 共享规划与自身历史诊断：独立判断包的接续

本文件记录本次用户决定。共享规划和实际历史采集仍由原PG-P1/P2唯一执行链完成，分析结论单独保存于本目录。没有第二个runner、自动化或新训练卡。

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
