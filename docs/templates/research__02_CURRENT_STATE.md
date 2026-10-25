# CARA-Cache 当前状态

{{snapshot}}

10月24日完整终态见[685](repo:research/685_CARA_HISTORY104_R2_COMPLETE_ACCEPTANCE_RESULTS_AND_COST_GATE_20261024.md)：104路径与72评分完整接受，实际7.395282GPUh，GPU和锁已释放。历史强基线均胜原GRAPH；24/25D实测可行，但计时模型最坏低估2.618秒未过2秒门槛。COST112于10月25日完整接受，实际8.139511GPUh；计时最大低估5.006秒未过2秒门槛，新P1不准入，P2仍等待冻结策略。见[690](repo:research/690_CARA_COST112_COMPLETE_ACCEPTANCE_AND_TIMING_GATE_FAILURE_20261025.md)。

## 当前跟踪实验

{{run_details}}

## 已完成的前置

BANK24完整24视频、12组LPIPS、原控制和实际1.845248657494 GPUh已接受，[科学分析](repo:research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md)已完成。完整1624 CPU R2的3条命令、28路径/4060重载格/26040试验、真实请求与FD锁证明通过。CPU R1缺少`output_dir`的原失败保持，不重写为成功。[修复记录](repo:research/645_CARA_FULL1624_CPU_ENTRY_REPAIR_20261022.md)。

P1/P2等待期准备已完成SELECT范围内曝光核查、价格/标签到生成器的转换接口、历史诊断矩阵与少步Native计时选择规则、27项局部CPU控制及真实UniPC调度网格。详见[652准备与接续](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)。最新[657](repo:research/657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)已完成整卡监督/评分/Native时钟/终态复算组合CPU接受，保留18条采样控制，新增真实全93帧LPIPS和6种生命周期，12项终态检查；本地92项相关检查通过。64路完整报价仍为8.844444/10.5 GPUh。原价格完整接受后，PG-P1已按661实际启动；P2新增GPU提交仍为0。

P1原件与财务已完整接受，但没有预算可行的冻结策略，P2目前不准入。保留已通过的P2组合CPU与五模型入口准备；完整离线分析确认全请求价格低估与可行性恢复搜索缺口，见[669原因分析与修复](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)。历史强基线原alpha及24/25D新旧入口148路径CPU已接受；[104路径预算边界卡](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)已完整报价11.423207/11.9 GPUh，替代未执行44路径草案。104卡组合CPU已接受，但GPU采集在08:49因磁盘满提前退出；旧health为72/104完成，GPU已释放，完整验收未通过，旧11.9GPUh预约已释放，按明确标注的保守重建值5.48GPUh结算；新完整104 R2于13:41:30在GPU3硬独占启动，现104路径/72评分已完整接受并结算7.395282GPUh，独立输出卷与跨盘日志核验通过；计时模型未过2秒最大低估门槛，先修成本验证。部署257.771秒及累计226 GPUh不变。见[676失败原件](repo:research/676_CARA_HISTORY104_DISK_FULL_EARLY_EXIT_20261024.md)。见[671实际执行](repo:research/671_CARA_HISTORY104_COMBINATION_AND_EXCLUSIVE_EXECUTION_20261024.md)。已完成旧实验约4.45 GiB实体去重，38原路径和所有SHA保持；两个压缩包经全量一致核验后清理，本次合计释放63.05 GiB，另三个差异包保留。见[668当前原件与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。

104完整结果已按预定口径分析：强历史布局优于原GRAPH，24/25D实测可行，计时模型最大低估未过门槛；COST112独立验证已完整结束，最大低估门槛失败。P1修复按模型验证和真实可行性分支接续，开发曝光与下一阶段Q≤8分列。[673分析准备](repo:research/673_CARA_HISTORY104_ANALYSIS_READY_AND_P1_REPAIR_DECISIONS_20261024.md) · [674解释口径](repo:research/674_CARA_HISTORY104_INTERPRETATION_CLARIFICATIONS_20261024.md) · [681 R2接续复核](repo:research/681_CARA_HISTORY104_R2_ANALYSIS_ENTRY_AND_P1_HANDOFF_CHECKED_20261024.md) · [固定接续口径](repo:plans/cara_policy_generator_20261020/HISTORY104_ANALYSIS_AND_P1_REPAIR_HANDOFF_R1_20261024.md)。

## 科学判断与下一步

{{research_summary}}

{{queue}}

技术半程只核查原句柄、容器、UUID锁、错误、进度、预算和磁盘；完整终态再核对全部原件、Native/off/on参照相等、动作价格、费用及释放。若仍运行，按实测进度更新检查；未知只恢复原句柄，不盲目重派；提前退出按真实完成或失败处理。保持原卡范围，不用部分视频调参，不以六DEV拟合门控，不恢复两卡任务。

## 状态来源

本页由[规范状态数据](repo:docs/project_status.json)、[实验索引](repo:paper/experiment_master_table.json)和已保存回执生成。新观察覆盖规范状态指针，旧观察保留原文件。文档更新时间不能代替实验观测时间。[维护规则](repo:docs/MAINTENANCE.md) · [历史记录](repo:docs/archive/README.md)。

磁盘增长归因已定向核对：guanwenfei的SAM区域文件约57.09GiB、user账号BeamNG采集约19.73GiB、CARA约0.80GiB；与77.62GiB空间下降基本对齐。72条/216原件SHA保持，已给出迁移和新104/跨会话64备选报价，均未执行。[677存储归因与恢复方案](repo:research/677_CARA_DISK_GROWTH_ATTRIBUTION_SAFE_MIGRATION_AND_104_RECOVERY_20261024.md)。

用户指定NuPlan数据和ConvMAE训练检查点已按清单清理约1.326TiB，579份代码/配置/日志/基础权重SHA保持一致；实测普通用户空间恢复约1358.0GiB。原104失败已按保守值5.48GPUh结算；新的完整104 R2已完成并独立验收，实际7.395282GPUh。见记录678及`reports/cara_two_targets_authorized_bulk_cleanup_complete_20261024.json`。

[679最终恢复准备](repo:research/679_CARA_HISTORY104_FAILED_SETTLEMENT_STORAGE_GUARD_AND_FINAL_RECOVERY_20261024.md)：旧失败保守结算5.48GPUh；新完整104维持11.423207/11.9GPUh，32GiB独立输出卷与跨盘日志、真实ENOSPC组合CPU通过。后续启动授权及实际执行见[680新完整104 R2](repo:research/680_CARA_HISTORY104_R2_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_20261024.md)；该新卡现已完整验收，7.395282GPUh结算，原11.9GPUh预约释放。
