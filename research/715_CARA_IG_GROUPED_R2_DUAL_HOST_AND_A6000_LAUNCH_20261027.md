# 创新量增益 R2：双端复核与两卡独占启动

用户要求的双端兼容版本已通过两卡 A6000（SM86）与四卡 RTX 6000 Ada（SM89）的 GPU 隐藏 CPU 复核，每端12项检查、完整父路径/部署/B1小权重流程均通过。两端绑定同一科学源码 `3395d2ec27986a1db003e883022c81067ace6ccd`，见[双端接受](../reports/cara_IG_grouped_dual_host_CPU_acceptance_20261027.json)。这不是四卡真实模型或质量结果。

依本次用户指定优先使用两卡，R2已[单次启动](../reports/cara_IG_B1_R2_two_card_launch_20261027.json)，唯一 launch 为 `f1510940-8681-439d-9e92-77171eac5369`，GPU0为 `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`，runner PID/start ticks 为 `4060105/633742280`。物理 EXCLUSIVE_PROCESS 与唯一进程上下文已[中央确认](../reports/cara_IG_B1_R2_central_admission_20261027.json)。控制器版本 `a7bdcbdb`；独立阶段、输出盘和控制日志均为 R2 身份。

范围仍为2旧CAL的4完整父路径、12状态、72原读出位置、108附加guided重放/216 head pair。保存状态先做FULL/DEEP逐元素端点复现，再做留一prompt和全数据冻结参数的实际Phi重放。公式、alpha、样本和lambda均未改动；分组仅减少重复完整物理哈希。整卡预估1.141GPUh是工程规划值，硬上限1.5GPUh。

[原R1失败](714_CARA_IG_B1_HASH_OVERHEAD_AND_GROUPED_REPAIR_20261027.md)保留，已付0.5827235015070377GPUh与R2一并受本轮7GPUh约束。中央预算仍保留原DEV128责任和16.5GPUh未知责任；不覆盖两卡主账本，不读取DEV128部分科学指标。

下一步按本次实际启动时钟检查中点与终态，完整接受后评估局部留出收益、响应面和费用，再决定是否进入46路径的固定布局完整视频阶段。启动、CPU通过、部分状态都不是方法成功或失败，不支持并入主线。
