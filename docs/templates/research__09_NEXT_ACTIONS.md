# CARA-Cache 后续实验顺序

{{snapshot}}

研究目标是验证**可复现的校准程序是否能在实际计算预算下生成有竞争力的缓存/修正/刷新计划**。下面按依赖顺序推进；已完成旧卡与条件性扩展不混入活动队列。

{{queue}}

## 下一卡的具体准备

PG-P1两个已登记CAL_SELECT（`av_animal_dear_1_0`、`industry_057`，seed0）的本地回执及四卡项目输出身份核查已完成，范围内没有发现执行记录；首次SELECT端点前核对新增元数据。等待期还补齐了可信资产转换接口、历史失配诊断矩阵规则、少步Native纯计时选择和27项CPU控制，见[652准备记录](repo:research/652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)与[接续命令](repo:plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)。[656](repo:research/656_CARA_PG_P1_PRODUCTION_ENTRY_CPU_ACCEPTED_AND_FULL64_QUOTE_20261023.md)已补齐合法mask/alpha采样入口真实CPU接受与完整64路报价：预计8.844444、上限10.5 GPUh。下一步绑定干净价格，并完成整卡监督/评分/Native时钟/终态回调的组合接受。

[2026-10-23接续要求](repo:plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)：原1624数值/控制和动作价格分别接受；已知同卡竞争的价格不因低波动自动通过。未来GPU卡要求实际独占。冻结策略后加入小规模历史窗口诊断，PG-P2加入少步Native等实测时间对照；shadow不写回，不计为干净延迟，新增范围单独进入完整报价。

原1624资产卡已经完整接受。当前运行[独占价格刷新R1](repo:plans/cara_policy_generator_20261020/FULL1624_PRICE_REFRESH_R1_20261023.md)：10条新路径、全部区间每动作三轮正式重复，完整报价9.500278 GPUh、上限11.5；完整生产CPU与生命周期已接受，兼容入口修复后已于13:13:24在GPU3实际硬件独占运行。17:59技术半程、22:59完整验收，均绑定实际恢复启动，见[655运行与协调记录](repo:research/655_CARA_PRICE_GPU3_EXCLUSIVE_ADMITTED_AND_COORDINATED_SCHEDULE_20261023.md)。

PG-P1的Q表示用于策略选择的完整终点评价查询预算。第一个预算为0.80×Native，Q≤8、首4后4、一次CAL_SELECT冻结。基础范围最多40候选正式+6Native+18warm=64路径；额外统计采集另计。具体完整报价与准入仍按注册表执行，不挪用已完成资产卡的12GPUh批准。

PG-P2公平比较计入相同信息、查询数与校准GPUh；PG-P3沿同一程序重校准，先第二预算，再第二模型或设置；PG-P4冻结方法和对手后才选独立TEST并重复计时。旧168正式TEST矩阵是草案，warm/加载/评分另计。

## 等待期间可推进

完成冻结程序的输入接口、账本和来源核对，准备表格与图的固定比较口径，整理已接受原件；这些准备不使用运行中部分结果选择新阈值或掩码。已完成的N07/N08/N09/N10、BANK24保持原件，旧人工32路径筛查不自动恢复。

[当前生成器计划](repo:plans/cara_policy_generator_20261020/README.md) · [任务登记](repo:plans/cara_policy_generator_20261020/TASK_REGISTRY.json) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [旧计划历史](repo:docs/archive/README.md)。
