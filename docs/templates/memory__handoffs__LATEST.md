# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)与[本卡646记录](repo:research/646_CARA_FULL1624_CPU_ACCEPTED_GPU_LAUNCH_20261022.md)。它们共用规范数据；旧长交接已完整归档。

{{snapshot}}

{{run_details}}

## 接续规则

- 上述1624 launch已于08:26完整接受，原件见[649](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)，不重复验收/提交。下一项为[独立价格刷新](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)：完整范围、报价已登记，生产collector/生命周期/实际CPU尚待；没有新GPU启动。
- `--launch-ref`固定上述启动原件。unknown只恢复原句柄；提前退出保留实际终态与费用。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 原资产接受后先运行完整价格审计，再按[价格/独占/历史诊断/少步Native接续方案](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)推进。原`generator_input_ready`不能覆盖同卡竞争；新GPU卡须动作价格信任通过、真实独占、自己的范围、完整成本、实际CPU和fresh准入。已用四卡私有凭据确认sudo模式修改权限，待空闲卡实际启用，不动在跑stage。长任务绑定实际启动安排半程与全程，复用自动化，完成后关闭对应一次检查。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。
