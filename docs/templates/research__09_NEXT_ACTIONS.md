# CARA-Cache 后续实验顺序

{{snapshot}}

研究目标是验证**可复现的校准程序是否能在实际计算预算下生成有竞争力的缓存/修正/刷新计划**。下面按依赖顺序推进；已完成旧卡与条件性扩展不混入活动队列。

{{queue}}

## 下一卡的具体准备

P1原64位置、10.5 GPUh及半程/终态安排保持不变。P2 Native/历史R4生产入口CPU已接受；本轮整卡监督、评分与终态组合代码通过75项本地控制和15项独立接受器控制。新生产组合CPU因共享盘不足40GiB未启动，不能称为完整生产接受。最终范围和预算等P1接受、策略物理去重后确定，旧518路报价仅保留作历史上界。见[665组合检查与接续](repo:research/665_CARA_PG_P2_COMBINATION_CHECKED_CPU_STORAGE_GATE_20261023.md)。

[2026-10-23接续要求](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)：原1624数值/控制和动作价格分别接受；已知同卡竞争的价格不因低波动自动通过。未来GPU卡要求实际独占。冻结策略后加入小规模历史窗口诊断，PG-P2加入少步Native等实测时间对照；shadow不写回，不计为干净延迟，新增范围单独进入完整报价。

原1624标签与独立价格补测均完整接受。当前已进入PG-P1整卡独占运行：4 CAL_FIT/2 CAL_SELECT、最多64路径/40评分、Q≤8、B=.80，forecast8.844444/上限10.5 GPUh。见[661实际接续](repo:research/661_CARA_EXCLUSIVE_PRICES_ACCEPTED_PG_P1_ACTUALLY_ADMITTED_20261023.md)；半程10月24日00:52、终态05:32绑定唯一PG launch，不重派已完成资产卡或CPU。

PG-P1的Q表示用于策略选择的完整终点评价查询预算。第一个预算为0.80×Native，Q≤8、首4后4、一次CAL_SELECT冻结。基础范围最多40候选正式+6Native+18warm=64路径；额外统计采集另计。具体完整报价与准入仍按注册表执行，不挪用已完成资产卡的12GPUh批准。

PG-P2公平比较计入相同信息、查询数与校准GPUh；PG-P3沿同一程序重校准，先第二预算，再第二模型或设置；PG-P4冻结方法和对手后才选独立TEST并重复计时。旧168正式TEST矩阵是草案，warm/加载/评分另计。

## 等待期间可推进

完成冻结程序的输入接口、账本和来源核对，准备表格与图的固定比较口径，整理已接受原件；这些准备不使用运行中部分结果选择新阈值或掩码。已完成的N07/N08/N09/N10、BANK24保持原件，旧人工32路径筛查不自动恢复。

[当前生成器计划](repo:plans/cara_policy_generator_20261020/README.md) · [任务登记](repo:plans/cara_policy_generator_20261020/TASK_REGISTRY.json) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [旧计划历史](repo:docs/archive/README.md)。
