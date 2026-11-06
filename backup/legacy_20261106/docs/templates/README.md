# CARA-Cache

{{next_stage_notice}}

**通过选择完整刷新的时间位置，在加速视频扩散时尽量保留完整模型的输出。**

CARA-Cache（CFG-Aligned Readout and Cost-Aware Allocation for Video Diffusion）是一个基于 Cosmos / WorldCache 实验栈的视频扩散加速研究项目。它研究两个相连的问题：缓存读出怎样更准确，以及有限计算预算应该花在哪些时间步。当前冻结的新DEV候选Shared25-C采用完整刷新D与缓存复用C，不包含修正A；A保留为机制对照。CARA为沿用的项目名。历史目录 `worldcache_omr` 与 Python 包 `wcomr` 为兼容既有实验保留；本仓库当前只维护 WorldCache/CARA 主线。

## 第一次阅读

| 想了解什么 | 从这里进入 |
|---|---|
| 做了什么、主要结果怎样 | [研究与结果概览](repo:EXPERIMENT_REPORT.md) |
| 现在在跑什么、下一次何时验收 | [当前状态](repo:research/02_CURRENT_STATE.md) |
| 每项实验是否完成、支持什么结论 | [{{row_count}}项实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) |
| 下一步解决什么问题 | [后续实验顺序](repo:research/09_NEXT_ACTIONS.md) |
| 如何复核代码、原件和统计 | [复现与证据指南](repo:docs/REPRODUCIBILITY.md) |
| 从项目开始到现在的完整记录 | [历史入口](repo:docs/archive/README.md) |

## 方法直觉

扩散模型逐步生成视频。完整计算昂贵，复用旧缓存会积累误差；当前研究重点是在固定刷新次数下，保留过渡区间的完整计算、减少末段刷新。CAL66的Shared25-C采用这一布局，DEV128已完成冻结继续验证，当前将它保留为高保真参照，并准备高速F19与S/Q机制。历史修正A利用当前浅层增量和真实深层锚点，在新DEV中作为机制对照。

{{actions}}

CFG 指 classifier-free guidance，包含条件与负条件两支。A 使用共享修正强度，保持两支融合口径一致。D 更新当前请求的真实深层锚点；A 不把近似结果冒充新的真实锚点。Native 是每个请求步均完整计算的参考推理。

当前流程是：**公平基线与评价/时钟 → F19可行性及S/Q独立准备 → 冻结规则 → 第二预算/网格 → 第二骨干与独立确认**。当前网格上能量规则与简单模板给出相同掩码；自动规则的额外价值留给可区分两者的新设置检验。历史GRAPH搜索与C/A/D生成器单独保留。

阅读数字时：**CAL**是校准集，**DEV**是开发验证集，**TEST**是方法冻结后才使用的独立测试集；`26D`表示26次完整刷新，`A1/A3`表示所考察窗口内修正1次/连续3次。

## 已经得到什么结果

{{headlines}}

LPIPS 越低表示越接近同输入的 Native 视频；它与局部速度 MSE、语义/物理质量、实际延迟分别报告。更多共同评价、重复时间、自动质量及失败分母见[结果概览](repo:EXPERIMENT_REPORT.md)。

![BANK24：修正机制与同配额分配](repo:paper/figures/cara_bank24_dev6_r1_20261022/mechanism_and_allocation.png)

图左展示修正的局部误差收益，图右展示刷新分配的完整比较；两者共同说明后续自动策略需要解决的问题。[完整分析](repo:research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md)。

## 当前进度

{{snapshot}}

历史研究阶段：[原P1](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)未选出预算可行策略；[104](repo:research/685_CARA_HISTORY104_R2_COMPLETE_ACCEPTANCE_RESULTS_AND_COST_GATE_20261024.md)与[COST112](repo:research/690_CARA_COST112_COMPLETE_ACCEPTANCE_AND_TIMING_GATE_FAILURE_20261025.md)完成采集，但原最大低估计时门均失败。该路线暂缓，失败与费用保持；当前按[CAL66完整结果](repo:research/702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md)保留Shared25-C已完成的DEV128结论；未来工作按顶部新计划推进。

## 仓库结构与使用

| 目录 | 内容 |
|---|---|
| `src/wcomr/` | 缓存读出、来源管理、调度与实验实现 |
| `scripts/`、`tests/` | 运行、采集、验收、分析及相应控制 |
| `configs/`、`manifests/`、`plans/` | 冻结配置、资产/源码身份、实验登记 |
| `research/`、`reports/` | 解释性研究记录与机器回执；历史原件持续保留 |
| `paper/` | 实验总表、术语映射、图表及论文材料 |
| `docs/` | 新读者指南、统一状态数据、文档生成器及归档 |

仅检查阅读层（Python标准库，无模型、无服务器连接、无GPU提交）：

```bash
python3 docs/tools/render_repository_docs.py --check
```

运行实验需对应卡的固定资源、生产CPU验证、完整成本与准入条件，见[复现指南](repo:docs/REPRODUCIBILITY.md)。日常文档更新只改规范数据和模板，再统一生成，见[维护规则](repo:docs/MAINTENANCE.md)。

历史存储维护和失败恢复记录：[677空间归因](repo:research/677_CARA_DISK_GROWTH_ATTRIBUTION_SAFE_MIGRATION_AND_104_RECOVERY_20261024.md)、[679恢复方案](repo:research/679_CARA_HISTORY104_FAILED_SETTLEMENT_STORAGE_GUARD_AND_FINAL_RECOVERY_20261024.md)、[680执行](repo:research/680_CARA_HISTORY104_R2_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_20261024.md)。它们描述当时状态；当前运行与准备以本页快照为准。
