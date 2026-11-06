# IG B1：双端兼容复核通过，两卡独占真实模型验证已启动

用户本轮明确要求独立验证后再决定并入主线，并要求两卡/四卡兼容、优先利用当前两卡空闲资源。两台服务器的新增B1整卡CPU控制均正常退出：[双端接受](../reports/cara_IG_dual_host_B1_CPU_acceptance_r3_20261027.json)。每端9项检查、8条原观测CPU路径、20条部署CPU路径、8条B1父路径和144次保存状态重放通过；实际冻结请求类被导入，均无CUDA初始化或真实权重。

## 原运行句柄

- [启动回执](../reports/cara_IG_B1_two_card_launch_r1_20261027.json)：`82bec7e7-c131-412a-b5e5-3e2069609ff9`；source `667afb058e155294416ff23c5f009bbd0eb2f030`；controller `5ff91439`。
- 两卡A6000 GPU0：`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`；runner PID4043801/start_ticks633415353。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-ig-b1-a6000-r1-20261027`。
- output：`/data20t/gaokuangda/worldcache_workspace/outputs/cara-ig-b1-r1-20261027`。
- [中央独占确认](../reports/cara_IG_B1_central_admission_confirmed_20261027.json)：真实EXCLUSIVE_PROCESS，唯一runner CUDA上下文，中央同一envelope已确认。
- 64GiB预分配私有输出文件系统，48MiB独立磁盘控制日志；CPU2–3；原DEV128 CPU0–1继续，未读取其部分科学指标。

## 范围、费用和判读边界

固定两旧CAL、每条OFF/ON各一条完整父路径，共4路径；12状态保留原6种读出。新增四角/中点36次、保存输入FULL/DEEP端点24次、LOPO系数24次、最终系数24次，共108次guided adapter replay。实际隔离adapter每次还支付C与候选两对head，完整登记216对；没有把这些工作当免费头部。

B1规划4410秒左右（历史4×246.852秒父路径，加模型加载600秒、原teacher/readout900秒、新head720秒、转移/哈希/写出1200秒），是保守规划而非本卡实测速率。硬上限1.5GPUh属于整轮7GPUh内，累计226不变；新阶段私有账本只记录同一中央envelope的实际费用。旧DEV128中央12h责任及16.5h未知责任保留，未覆盖两卡原账本。CPU评分不再被误认为持有GPU，但释放证据、原句柄死亡和当前设备空闲须同时成立。

目前真实模型已进入第一父路径采集，尚无B1科学结果，更没有完整视频质量增益或速度结论。下一步按原句柄进行半程/终态检查，GPU释放后核对账单并回写同一中央envelope。完成后判读LOPO与最终系数的actual-guided误差，补充保存张量的CPU raw oracle诊断；条件B2仍须按本轮费用上限执行，不自动并主线。
