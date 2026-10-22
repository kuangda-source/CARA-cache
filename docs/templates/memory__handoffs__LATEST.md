# CARA-Cache 当前交接

先读[当前状态](repo:research/02_CURRENT_STATE.md)、[实验顺序](repo:research/09_NEXT_ACTIONS.md)与[本卡646记录](repo:research/646_CARA_FULL1624_CPU_ACCEPTED_GPU_LAUNCH_20261022.md)。它们共用规范数据；旧长交接已完整归档。

{{snapshot}}

{{run_details}}

## 接续规则

- 唯一提交者只跟踪上述launch。半程使用`capture --mode gpu-halfway`，终态使用`capture --mode gpu-terminal`后`accept --kind gpu`；控制器为`scripts/wc_four_card_policy_assets_r1.py`。每次输出新文件，已有原件先复用，不重复验收/提交。
- `--launch-ref`固定上述启动原件。unknown只恢复原句柄；提前退出保留实际终态与费用。原R1 CPU失败、BANK24原ffprobe失败和后续恢复均保留。
- 使用已授权四卡私有入口；不恢复两卡、不触碰他人任务、不更改在跑stage。完整范围/预算/冻结门控不变，DEV不回流调阈值。
- 资产接受且`generator_input_ready`后按PG-P1→P2→P3→P4准备与执行；每卡仍须自己的范围、完整成本、实际CPU和fresh准入。长任务绑定实际启动安排半程与全程，复用自动化，完成后关闭对应一次检查。
- 有意义的进度、完成、失败或需用户行动时才通知；文档整理不构成新的实验观测。

后续修改规范数据和模板，再运行`python3 docs/tools/render_repository_docs.py`及`--check`；有意义的代码、配置、结果须同步私有GitHub。完整历史见[归档入口](repo:docs/archive/README.md)。
