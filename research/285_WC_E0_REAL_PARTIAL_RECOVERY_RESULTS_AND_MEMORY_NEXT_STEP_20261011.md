# E0实际回收结果：组合出现新增终点正信号，下一修复检查点容量

2026-10-11。依据[284事前CPU登记](284_WC_E0_PARTIAL_RECOVERY_AND_NUMERICAL_PAIRING_PREREGISTRATION_20261011.md)实际运行，不新增GPU或视频。原完整64仍是技术失败，14完整／1部分失败／49未开始及原1.507741092GPUh费用保持。

## 发现与研究价值

**AV28已保存的八方法提供了新的单场景开发正结果：P闭环比RA更接近Native，阶段A与P组合进一步改善。** 已验证的14条路径全部文件／tensor／视频有效；六条Human缺原始prepare证据，继续不评分。新结果支持推进组合与P执行器完善，不能代替阶段A新输入确认或完整64结果。

| AV28方法 | 全93帧平均LPIPS | 相对RA失真降低 | 真DD对数 | PP对数 |
|---|---:|---:|---:|---:|
| SOURCE_RA／DYNAMIC_NO_P | 0.395027411 | — | 14 | 0 |
| CPD／REF_CPD／A_CPD_OFF | 0.345738431 | 12.4774% | 13 | 4 |
| A_CPD_W1_ONE_PHASE | 0.285459909 | 27.7367% | 12 | 5 |
| A_CPD_BETA1_ONE_PHASE | 0.298508513 | 24.4335% | 13 | 3 |
| DENSE_CONTROL | 0 | Native文件完全相同 | 36 | 0 |

三种P候选相对RA均为93／93帧改善。阶段W1／β=1相对CPD分别改善17.4347%／13.6606%，也是93／93帧。与旧32卡同一Native／指标的阶段A保真参照相比，阶段W1＋P再降低4.9107%（92好／1坏帧），β=1＋P再降低0.9393%（67好／26坏帧）。保留全部坏帧；跨批次参照仅比较保真，原64缺少匹配的阶段A无P同卡对照。

这些结果是闭环组合总效果：P、A以及后续动作均可能参与。**P不是已证明更快的动作**：CPD的DD＋PP为17对，RA为14对；阶段W1＋P为17对、β=1＋P为16对。当前P实测费用又接近D，不能只看到真DD减少就称省钱。原记录时间含检查点／hash等取证开销，不能作为clean速度。E4同P时机真D、匹配A无P和生命周期费用仍必要。

## 实际执行与独立验收

CPU独立stage为`.sync/wc-full64-partial-recovery-cpu-r1-20261011`，源b2ce44a45761487a70d5d096b51daa0203bd05a8，监督4039038／子4039039，均已exit0且PID消失。监督wall244.790746秒，子审计／评分区间227.153436秒；CUDA未初始化、GPU提交0、账本hash前后不变。

- 全64位置保持：14 PATH_VALIDATED、1 PARTIAL_FAILED_NOT_ELIGIBLE、49 NOT_WRITTEN，无完整路径无效。
- 重读14×（36 guided＋final）＝518实际tensor，核形状／FP32／有限值／文件与tensorhash；14新视频和4匹配Native完整解码。
- 两场景共六实际轨迹控制：RA／无P和CPD／OFF严格相等；CPD／full-GEMM参考按原容差相等。AV28对应视频及全93评分也完全相等。
- AV28 all-D与Native文件完全相同，LPIPS为0；新SOURCE_RA与旧32的RA文件及全部93分数相同。
- 合格八视频全部评分，744距离／PTS／均值独立重建。一个场景仍是一个场景，不以帧、重复控制扩充样本量。

[原字节捕获](../reports/wc_full64_partial_recovery_cpu_r1_terminal_20261011_capture.json)、[独立结果重建](../reports/wc_full64_partial_recovery_cpu_r1_independent_result_20261011.json)、[可重跑的独立审计入口](../scripts/audit_wc_e0_partial_recovery_result.py)保留终态身份、资源、分母、逐帧对照和所有缺失。完整结果原件为压缩保存的JSON，未修改旧runner／supervisor／score gate。

## 配对边界保持

旧严格字段判据仍为0／14。评分前登记的新数值合同在实际冻结源码数据流验证后，允许仅忽略全零mask下不参与计算的有限gt_frames以及solver默认字段取证顺序；其他活跃条件／prepare／数值solver／前七dense guided必须一致。AV28八行通过；Human六行缺prepare仍拒绝，未补造或借RA桥接来取消此要求。新数值等价验收与旧严格字段结果同时保留。

没有完成原64的第二来源规则、Human后两方法、misc和AV51，也没有独立seed确认、clean计时、物理／语义收益结论。原顺序技术停止造成缺失，不能对现有14平均后称跨场景P有效。

## E1已定位的容量线索与下一步

原dynamic checkpoint在physical snapshot已建立后，再以此前physical headroom门槛加两倍own_state逻辑字节检查GPU，然后对own_state作GPU deepcopy；恢复又作一次deepcopy。已完成路径step12／30的附加own_state逻辑量约1.900GiB。失败点原physical gate的逻辑复制约2.634GiB，原门槛约13.270GiB；这些是取证容量，不等同部署缓存大小。

目前只说明潜在额外峰值／重复保守预留，**未证明泄漏、碎片、CUDA OOM或具体GPU根因**。下一新版本将先按唯一storage与逻辑字节分列，检查别名、CPU独立快照、完整restore／RNG／installation／poison控制；仅在等价成立后考虑CPU保存附加状态，保留逻辑cap和workspace安全余量。随后冻结失败方法冷启动＋预先指定短前序后的真实GPU区分卡，不重投旧完整64或放宽原保护冒充修复。

阶段A确认仍保持四新提示词×二seed×五版本40路径、32计时路径完整72范围；不因为本场景P正例改候选或替代确认。预算仍39.183807748／77.895246590，新48余额38.711438842；本轮GPU增加0。完整≤4GPUh自主、严格>4具体确认，原32／64授权不复用，无新增人工评审。
