# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)与[价格独占655记录](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。它们共用规范数据；旧长交接已完整归档。

{{snapshot}}

{{run_details}}

## 接续规则

- 原1624 launch已于08:26完整接受，原件见[649](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)，不重复验收/提交。[独立价格刷新](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)完整生产CPU已接受；修复host兼容入口后37项相关CPU检查通过。13:13:24沿原意图实际恢复并验证GPU3硬件独占，见[655](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。GMSD已释放该卡，用户授权CARA优先。
- `--launch-ref`固定价格实际恢复启动`reports/wc_policy_price_refresh_full1624_GPU_actual_recovery_launch_20261023_1313.json`。unknown只恢复原句柄；已有恢复intent/launch，不能再次launch-gpu或resume-host-entry。提前退出保留实际终态与费用，原12:59解释器前失败不能冒充实际GPU启动时间。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 原资产接受后先运行完整价格审计，再按[价格/独占/历史诊断/少步Native接续方案](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)推进。原`generator_input_ready`不能覆盖同卡竞争；完整价格须独占监测、完整原件和独立财务接受。GPU3已实际启用Exclusive_Process并验证唯一原runner，不动在跑stage；结束后仅空闲时恢复原模式。17:59半程、22:59终态绑定实际恢复启动；完成后关闭或明确改绑对应一次检查，不重复创建。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。
- P1/P2接续准备见[652](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)及[可执行接入设计](repo:plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)。SELECT审计范围内无执行证据，首次端点前检查新增记录；P1最新[656](repo:research/656_CARA_PG_P1_PRODUCTION_ENTRY_CPU_ACCEPTED_AND_FULL64_QUOTE_20261023.md)及[入口交接](repo:plans/cara_policy_generator_20261020/P1_PRODUCTION_ENTRY_HANDOFF_R2_20261023.md)已完成mask/alpha生产采样CPU与完整报价8.844444/10.5。复用原CPU接受，继续绑定整卡监督/评分/Native时钟/终态回调与干净价格，在同一64路径卡内取得干净Native预算后生成提案。历史shadow和少步Native选择成本另外完整计入P2，不能因本轮CPU控制通过就直接派GPU。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。
