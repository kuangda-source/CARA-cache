# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)与[本卡646记录](repo:research/646_CARA_FULL1624_CPU_ACCEPTED_GPU_LAUNCH_20261022.md)。它们共用规范数据；旧长交接已完整归档。

{{snapshot}}

{{run_details}}

## 接续规则

- 上述1624 launch已于08:26完整接受，原件见[649](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)，不重复验收/提交。下一项为[独立价格刷新](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)：完整生产CPU已接受，原容器09:46:34退出、实际09:51:55观察；GPU控制器及独立终态接受已通过32项CPU检查。见[651](repo:research/651_CARA_PRICE_CPU_ACCEPTED_CONTROLLER_READY_WAIT_EXCLUSIVE_20261023.md)，四卡仍占用，没有新GPU启动，硬件独占尚未实测。
- `--launch-ref`固定上述启动原件。unknown只恢复原句柄；提前退出保留实际终态与费用。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 原资产接受后先运行完整价格审计，再按[价格/独占/历史诊断/少步Native接续方案](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)推进。原`generator_input_ready`不能覆盖同卡竞争；新GPU卡须动作价格信任通过、真实独占、自己的范围、完整成本、实际CPU和fresh准入。已用四卡私有凭据确认sudo模式修改权限，待空闲卡实际启用，不动在跑stage。长任务绑定实际启动安排半程与全程，复用自动化，完成后关闭对应一次检查。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。
- P1/P2接续准备见[652](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)及[可执行接入设计](repo:plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)。SELECT审计范围内无执行证据，首次端点前检查新增记录；先接受干净价格，再完成P1真实生产CPU/完整报价，在原64路径卡内取得干净Native预算后生成提案。历史shadow和少步Native选择成本另外完整计入P2，不能因本轮CPU控制通过就直接派GPU。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。
