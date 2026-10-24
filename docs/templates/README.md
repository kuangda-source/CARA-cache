# CARA-Cache

**用 CFG 对齐的缓存修正减少视频扩散推理误差，再由校准数据决定何时复用、修正或完整刷新。**

CARA-Cache（CFG-Aligned Readout and Cost-Aware Allocation for Video Diffusion）是一个基于 Cosmos / WorldCache 实验栈的视频扩散加速研究项目。它研究两个相连的问题：缓存读出怎样更准确，以及有限计算预算应该花在哪些时间步。历史目录 `worldcache_omr` 与 Python 包 `wcomr` 为兼容既有实验保留；本仓库当前只维护 WorldCache/CARA 主线。

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

扩散模型逐步生成视频。完整计算昂贵，直接复用旧缓存会积累误差；CARA研究一种利用当前浅层增量和历史真实锚点的低成本修正，并将修正与完整刷新共同分配到时间轴上。

{{actions}}

CFG 指 classifier-free guidance，包含条件与负条件两支。A 使用共享修正强度，保持两支融合口径一致。D 更新当前请求的真实深层锚点；A 不把近似结果冒充新的真实锚点。Native 是每个请求步均完整计算的参考推理。

目标流程是：**模型与预算 → 校准区间误差/动作价格 → 自动生成 C/A/D 计划 → 冻结选择规则 → 独立输入与实际时间验证**。现有阶段工作点、共享布局探索和最终自动生成器分别保留身份。

阅读数字时：**CAL**是校准集，**DEV**是开发验证集，**TEST**是方法冻结后才使用的独立测试集；`26D`表示26次完整刷新，`A1/A3`表示所考察窗口内修正1次/连续3次。

## 已经得到什么结果

{{headlines}}

LPIPS 越低表示越接近同输入的 Native 视频；它与局部速度 MSE、语义/物理质量、实际延迟分别报告。更多共同评价、重复时间、自动质量及失败分母见[结果概览](repo:EXPERIMENT_REPORT.md)。

![BANK24：修正机制与同配额分配](repo:paper/figures/cara_bank24_dev6_r1_20261022/mechanism_and_allocation.png)

图左展示修正的局部误差收益，图右展示刷新分配的完整比较；两者共同说明后续自动策略需要解决的问题。[完整分析](repo:research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md)。

## 当前进度

{{snapshot}}

10月24日完整终态见[685](repo:research/685_CARA_HISTORY104_R2_COMPLETE_ACCEPTANCE_RESULTS_AND_COST_GATE_20261024.md)：104路径与72评分完整接受，实际7.395282GPUh，GPU和锁已释放。历史强基线均胜原GRAPH；24/25D实测可行，但计时模型最坏低估2.618秒未过2秒门槛。下一步先修成本验证；本次不派P1/P2。

P1原件与财务已完整接受，但没有预算可行的冻结策略，P2目前不准入。保留已通过的P2组合CPU与五模型入口准备；完整离线分析确认全请求价格低估与可行性恢复搜索缺口，见[669原因分析与修复](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)。历史强基线原alpha及24/25D新旧入口148路径CPU已接受；[104路径预算边界卡](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)已完整报价11.423207/11.9 GPUh，替代未执行44路径草案。104卡组合CPU已接受，但GPU采集在08:49因磁盘满提前退出；旧health为72/104完成，GPU已释放，完整验收未通过，旧11.9GPUh预约已释放，按明确标注的保守重建值5.48GPUh结算；新完整104 R2于13:41:30在GPU3硬独占启动，现104路径/72评分已完整接受并结算7.395282GPUh，独立输出卷与跨盘日志核验通过；计时模型未过2秒最大低估门槛，先修成本验证。部署257.771秒及累计226 GPUh不变。见[676失败原件](repo:research/676_CARA_HISTORY104_DISK_FULL_EARLY_EXIT_20261024.md)。见[671实际执行](repo:research/671_CARA_HISTORY104_COMBINATION_AND_EXCLUSIVE_EXECUTION_20261024.md)。已完成旧实验约4.45 GiB实体去重，38原路径和所有SHA保持；两个压缩包经全量一致核验后清理，本次合计释放63.05 GiB，另三个差异包保留。见[668当前原件与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。

104完整结果已按预定口径分析：强历史布局优于原GRAPH，24/25D实测可行，计时模型最大低估未过门槛；先登记独立成本验证。P1修复按模型验证和真实可行性分支接续，开发曝光与下一阶段Q≤8分列。[673分析准备](repo:research/673_CARA_HISTORY104_ANALYSIS_READY_AND_P1_REPAIR_DECISIONS_20261024.md) · [674解释口径](repo:research/674_CARA_HISTORY104_INTERPRETATION_CLARIFICATIONS_20261024.md) · [681 R2接续复核](repo:research/681_CARA_HISTORY104_R2_ANALYSIS_ENTRY_AND_P1_HANDOFF_CHECKED_20261024.md) · [固定接续口径](repo:plans/cara_policy_generator_20261020/HISTORY104_ANALYSIS_AND_P1_REPAIR_HANDOFF_R1_20261024.md)。

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

磁盘增长归因已定向核对：guanwenfei的SAM区域文件约57.09GiB、user账号BeamNG采集约19.73GiB、CARA约0.80GiB；与77.62GiB空间下降基本对齐。72条/216原件SHA保持，已给出迁移和新104/跨会话64备选报价，均未执行。[677存储归因与恢复方案](repo:research/677_CARA_DISK_GROWTH_ATTRIBUTION_SAFE_MIGRATION_AND_104_RECOVERY_20261024.md)。

用户指定NuPlan数据和ConvMAE训练检查点已按清单清理约1.326TiB，579份代码/配置/日志/基础权重SHA保持一致；实测普通用户空间恢复约1358.0GiB。原104失败已按保守值5.48GPUh结算；新的完整104 R2已完成并独立验收，实际7.395282GPUh。见记录678及`reports/cara_two_targets_authorized_bulk_cleanup_complete_20261024.json`。

[679最终恢复准备](repo:research/679_CARA_HISTORY104_FAILED_SETTLEMENT_STORAGE_GUARD_AND_FINAL_RECOVERY_20261024.md)：旧失败保守结算5.48GPUh；新完整104维持11.423207/11.9GPUh，32GiB独立输出卷与跨盘日志、真实ENOSPC组合CPU通过。后续启动授权及实际执行见[680新完整104 R2](repo:research/680_CARA_HISTORY104_R2_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_20261024.md)；该新卡现已完整验收，7.395282GPUh结算，原11.9GPUh预约释放。
