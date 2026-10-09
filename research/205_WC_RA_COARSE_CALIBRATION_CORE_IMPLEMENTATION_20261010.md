# RA 粗校准核心实现与完整CPU入口（2026-10-10）

新增[同状态采集核心](../src/wcomr/cfg_ra_calibration.py)与[原始张量校准表](../src/wcomr/cfg_ra_calibration_table.py)，将共同锚点、真实CC/DD动作与完整dense UniPC续推接起来。固定共同D6父策略，六起点分别提供两分支误差相关性和终点latent传播gain；每臂完毕恢复父的物理状态及新增执行器history。对故障执行器不清除poison后继续运行。

[独立首版设计](../plans/WORLD_CACHE_RA_COARSE_CALIBRATION_R1_20261010.md)明确六点范围、年龄／阶段混合、undefined值与缺表回退，插值grid标作估计。该实现尚未生成真实Cosmos表、部署RA策略、获得质量或速度结果；MF-00 R2原进程和冻结源不修改。

[CPU实际源码测试](../tests/check_cfg_ra_calibration_full_sampler_cpu.py)覆盖两flow、两场景OFF／ON各全36父、12起点与24完整子后缀，共624solver／1248net。只验证本次采集与表生成的受影响行为，不重跑无变化的旧16路矩阵。完整实际执行和原件验收回执随后追加；本节初始状态为实现及语法检查完成，非CPU通过。

单次完整4GPUh门槛与48GPUh窗口已经在权威执行约定中落实。下一批真实模型校准仍需完整生产batch／CPU、费用预测、源与实际资源准入；符合门槛就自主推进。
