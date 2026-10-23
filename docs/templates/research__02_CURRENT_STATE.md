# CARA-Cache 当前状态

{{snapshot}}

## 当前跟踪实验

{{run_details}}

## 已完成的前置

BANK24完整24视频、12组LPIPS、原控制和实际1.845248657494 GPUh已接受，[科学分析](repo:research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md)已完成。完整1624 CPU R2的3条命令、28路径/4060重载格/26040试验、真实请求与FD锁证明通过。CPU R1缺少`output_dir`的原失败保持，不重写为成功。[修复记录](repo:research/645_CARA_FULL1624_CPU_ENTRY_REPAIR_20261022.md)。

P1/P2等待期准备已完成SELECT范围内曝光核查、价格/标签到生成器的转换接口、历史诊断矩阵与少步Native计时选择规则、27项局部CPU控制及真实UniPC调度网格。详见[652准备与接续](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)。最新[657](repo:research/657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)已完成整卡监督/评分/Native时钟/终态复算组合CPU接受，保留18条采样控制，新增真实全93帧LPIPS和6种生命周期，12项终态检查；本地92项相关检查通过。64路完整报价仍为8.844444/10.5 GPUh。原价格完整接受后，PG-P1已按661实际启动；P2新增GPU提交仍为0。

P1原件与财务已完整接受，但没有预算可行的冻结策略，P2目前不准入。保留已通过的P2组合CPU与五模型入口准备；完整离线分析确认全请求价格低估与可行性恢复搜索缺口，见[669原因分析与修复](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)。历史强基线原alpha及24/25D新旧入口148路径CPU已接受；[104路径预算边界卡](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)已完整报价11.423207/11.9 GPUh，替代未执行44路径草案。下一步补齐104卡采集、GPU释放后评分与终态组合CPU，部署257.771秒及累计226 GPUh不变。已完成旧实验约4.45 GiB实体去重，38原路径和所有SHA保持；两个压缩包经全量一致核验后清理，本次合计释放63.05 GiB，另三个差异包保留。见[668当前原件与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。

## 科学判断与下一步

{{research_summary}}

{{queue}}

技术半程只核查原句柄、容器、UUID锁、错误、进度、预算和磁盘；完整终态再核对全部原件、Native/off/on参照相等、动作价格、费用及释放。若仍运行，按实测进度更新检查；未知只恢复原句柄，不盲目重派；提前退出按真实完成或失败处理。保持原卡范围，不用部分视频调参，不以六DEV拟合门控，不恢复两卡任务。

## 状态来源

本页由[规范状态数据](repo:docs/project_status.json)、[实验索引](repo:paper/experiment_master_table.json)和已保存回执生成。新观察覆盖规范状态指针，旧观察保留原文件。文档更新时间不能代替实验观测时间。[维护规则](repo:docs/MAINTENANCE.md) · [历史记录](repo:docs/archive/README.md)。
