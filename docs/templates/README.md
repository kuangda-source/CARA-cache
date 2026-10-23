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

P1原64位置、10.5 GPUh及半程/终态安排保持不变。P2 Native/历史R4生产入口CPU已接受；本轮整卡监督、评分与终态组合代码通过75项本地控制和15项独立接受器控制。新生产组合CPU因共享盘不足40GiB未启动，不能称为完整生产接受。最终范围和预算等P1接受、策略物理去重后确定，旧518路报价仅保留作历史上界。见[665组合检查与接续](repo:research/665_CARA_PG_P2_COMBINATION_CHECKED_CPU_STORAGE_GATE_20261023.md)。

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
