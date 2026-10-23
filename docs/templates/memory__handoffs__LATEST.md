# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)和[668原终态与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。历史原件全部保留；P1已终态接受但没有可交给P2的冻结策略。

{{snapshot}}

{{run_details}}

## 接续规则

- 原1624 launch已于08:26完整接受，原件见[649](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)，不重复验收/提交。[独立价格刷新](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)完整生产CPU已接受；修复host兼容入口后37项相关CPU检查通过。13:13:24沿原意图实际恢复并验证GPU3硬件独占，见[655](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。GMSD已释放该卡，用户授权CARA优先。
- `--launch-ref`固定价格实际恢复启动`reports/wc_policy_price_refresh_full1624_GPU_actual_recovery_launch_20261023_1313.json`。unknown只恢复原句柄；已有恢复intent/launch，不能再次launch-gpu或resume-host-entry。提前退出保留实际终态与费用，原12:59解释器前失败不能冒充实际GPU启动时间。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 原资产与独占价格继续保持接受。PG-P1原终态已独立接受，但未选出预算可行策略；原两次检查已关闭。见[668原终态](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。完整分析与修复方案见[669](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)；历史/边界入口148路径CPU已接受，104卡组合CPU已接受，GPU3已实际独占启动，完整结果待终态验收，不能直接接P2。见[670](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。
- P1/P2历史准备见[652](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)、[657](repo:research/657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)和[整卡交接](repo:plans/cara_policy_generator_20261020/P1_FULL_CARD_COMBINATION_HANDOFF_R3_20261023.md)。这些是已经执行的原P1入口和报价，不得将旧接续命令作为再次派发授权。历史shadow和少步Native仍属P2独立范围。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。

## P2并行准备

P1原件与财务已完整接受，但没有预算可行的冻结策略，P2目前不准入。保留已通过的P2组合CPU与五模型入口准备；完整离线分析确认全请求价格低估与可行性恢复搜索缺口，见[669原因分析与修复](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)。历史强基线原alpha及24/25D新旧入口148路径CPU已接受；[104路径预算边界卡](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)已完整报价11.423207/11.9 GPUh，替代未执行44路径草案。104卡采集、释放GPU后评分与终态组合CPU已接受，GPU3已实际独占运行；等待完整104采集及72配对评分验收，部署257.771秒及累计226 GPUh不变。见[671实际执行](repo:research/671_CARA_HISTORY104_COMBINATION_AND_EXCLUSIVE_EXECUTION_20261024.md)。已完成旧实验约4.45 GiB实体去重，38原路径和所有SHA保持；两个压缩包经全量一致核验后清理，本次合计释放63.05 GiB，另三个差异包保留。见[668当前原件与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。

104完整结果分析入口已准备：固定比较历史强基线、24/25D实测预算边界与计时偏差；只接受完整终态，不读取部分结果调参。P1修复按模型验证和真实可行性分支接续，开发曝光与下一阶段Q≤8分列。[673分析准备](repo:research/673_CARA_HISTORY104_ANALYSIS_READY_AND_P1_REPAIR_DECISIONS_20261024.md) · [674解释口径](repo:research/674_CARA_HISTORY104_INTERPRETATION_CLARIFICATIONS_20261024.md) · [固定接续口径](repo:plans/cara_policy_generator_20261020/HISTORY104_ANALYSIS_AND_P1_REPAIR_HANDOFF_R1_20261024.md)。

P2 CPU原件与绑定命令见[生产接续方案](repo:plans/cara_policy_generator_20261020/P2_NATIVE_HISTORY_PRODUCTION_HANDOFF_R1_20261023.md)。不重复已接受CPU。78.5 GPUh仍是历史未去重上界，非已批预算；无预算可行的冻结P1策略时不能生成最终P2报价或派发。
