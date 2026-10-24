# CARA-Cache 后续实验顺序

{{snapshot}}

10月24日14:40技术观察见[682](repo:research/682_CARA_HISTORY104_R2_TECHNICAL_PROGRESS_STORAGE_AND_THERMAL_20261024.md)：13/104完成、1运行、0失败；独占、独立输出卷和跨盘日志正常。短窗口88–89°C且有软件温控/功率限制；保持配置，19:25复核并更新ETA。未分析部分结果。

研究目标是验证**可复现的校准程序是否能在实际计算预算下生成有竞争力的缓存/修正/刷新计划**。下面按依赖顺序推进；已完成旧卡与条件性扩展不混入活动队列。

{{queue}}

## 下一卡的具体准备

P1原件与财务已完整接受，但没有预算可行的冻结策略，P2目前不准入。保留已通过的P2组合CPU与五模型入口准备；完整离线分析确认全请求价格低估与可行性恢复搜索缺口，见[669原因分析与修复](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md)。历史强基线原alpha及24/25D新旧入口148路径CPU已接受；[104路径预算边界卡](repo:research/670_CARA_HISTORICAL_BASELINE_EQUIVALENCE_AND_BOUNDARY104_20261024.md)已完整报价11.423207/11.9 GPUh，替代未执行44路径草案。104卡组合CPU已接受，但GPU采集在08:49因磁盘满提前退出；旧health为72/104完成，GPU已释放，完整验收未通过，旧11.9GPUh预约已释放，按明确标注的保守重建值5.48GPUh结算；新完整104 R2已按后续明确授权于13:41:30在GPU3硬独占启动，独立输出卷与跨盘日志生效。部署257.771秒及累计226 GPUh不变。见[676失败原件](repo:research/676_CARA_HISTORY104_DISK_FULL_EARLY_EXIT_20261024.md)。见[671实际执行](repo:research/671_CARA_HISTORY104_COMBINATION_AND_EXCLUSIVE_EXECUTION_20261024.md)。已完成旧实验约4.45 GiB实体去重，38原路径和所有SHA保持；两个压缩包经全量一致核验后清理，本次合计释放63.05 GiB，另三个差异包保留。见[668当前原件与维护](repo:research/668_CARA_STORAGE_DEDUP_AND_P1_ORIGINAL_TERMINAL_ACCEPTANCE_20261024.md)。

104完整结果分析入口已准备：固定比较历史强基线、24/25D实测预算边界与计时偏差；只接受完整终态，不读取部分结果调参。P1修复按模型验证和真实可行性分支接续，开发曝光与下一阶段Q≤8分列。[673分析准备](repo:research/673_CARA_HISTORY104_ANALYSIS_READY_AND_P1_REPAIR_DECISIONS_20261024.md) · [674解释口径](repo:research/674_CARA_HISTORY104_INTERPRETATION_CLARIFICATIONS_20261024.md) · [681 R2接续复核](repo:research/681_CARA_HISTORY104_R2_ANALYSIS_ENTRY_AND_P1_HANDOFF_CHECKED_20261024.md) · [固定接续口径](repo:plans/cara_policy_generator_20261020/HISTORY104_ANALYSIS_AND_P1_REPAIR_HANDOFF_R1_20261024.md)。

[2026-10-23接续要求](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)：原1624数值/控制和动作价格分别接受；已知同卡竞争的价格不因低波动自动通过。未来GPU卡要求实际独占。冻结策略后加入小规模历史窗口诊断，PG-P2加入少步Native等实测时间对照；shadow不写回，不计为干净延迟，新增范围单独进入完整报价。

原1624标签与独立价格补测均完整接受。PG-P1原卡已结束、实际2.557833 GPUh，64位置上界中执行30路径/16评分/4候选查询，selected_policy=null。原半程和终态一次检查已关闭，不重派原任务。

PG-P1的Q表示用于策略选择的完整终点评价查询预算。第一个预算为0.80×Native，Q≤8、首4后4、一次CAL_SELECT冻结。基础范围最多40候选正式+6Native+18warm=64路径；额外统计采集另计。具体完整报价与准入仍按注册表执行，不挪用已完成资产卡的12GPUh批准。

PG-P2公平比较计入相同信息、查询数与校准GPUh；PG-P3沿同一程序重校准，先第二预算，再第二模型或设置；PG-P4冻结方法和对手后才选独立TEST并重复计时。旧168正式TEST矩阵是草案，warm/加载/评分另计。

## 等待期间可推进

完成冻结程序的输入接口、账本和来源核对，准备表格与图的固定比较口径，整理已接受原件；这些准备不使用运行中部分结果选择新阈值或掩码。已完成的N07/N08/N09/N10、BANK24保持原件，旧人工32路径筛查不自动恢复。

[当前生成器计划](repo:plans/cara_policy_generator_20261020/README.md) · [任务登记](repo:plans/cara_policy_generator_20261020/TASK_REGISTRY.json) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [旧计划历史](repo:docs/archive/README.md)。

磁盘增长归因已定向核对：guanwenfei的SAM区域文件约57.09GiB、user账号BeamNG采集约19.73GiB、CARA约0.80GiB；与77.62GiB空间下降基本对齐。72条/216原件SHA保持，已给出迁移和新104/跨会话64备选报价，均未执行。[677存储归因与恢复方案](repo:research/677_CARA_DISK_GROWTH_ATTRIBUTION_SAFE_MIGRATION_AND_104_RECOVERY_20261024.md)。

用户指定NuPlan数据和ConvMAE训练检查点已按清单清理约1.326TiB，579份代码/配置/日志/基础权重SHA保持一致；实测普通用户空间恢复约1358.0GiB。原104失败已按保守值5.48GPUh结算；新的完整104 R2依据后续明确授权独立运行。见记录678及`reports/cara_two_targets_authorized_bulk_cleanup_complete_20261024.json`。

[679最终恢复准备](repo:research/679_CARA_HISTORY104_FAILED_SETTLEMENT_STORAGE_GUARD_AND_FINAL_RECOVERY_20261024.md)：旧失败保守结算5.48GPUh；新完整104维持11.423207/11.9GPUh，32GiB独立输出卷与跨盘日志、真实ENOSPC组合CPU通过。后续启动授权及实际执行见[680新完整104 R2](repo:research/680_CARA_HISTORY104_R2_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_20261024.md)；该新卡已单次提交并预留11.9GPUh。
