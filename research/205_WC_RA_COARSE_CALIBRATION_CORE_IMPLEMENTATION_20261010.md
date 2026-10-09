# RA 粗校准核心实现与完整CPU入口（2026-10-10）

新增[同状态采集核心](../src/wcomr/cfg_ra_calibration.py)与[原始张量校准表](../src/wcomr/cfg_ra_calibration_table.py)，将共同锚点、真实CC/DD动作与完整dense UniPC续推接起来。固定共同D6父策略，六起点分别提供两分支误差相关性和终点latent传播gain；每臂完毕恢复父的物理状态及新增执行器history。对故障执行器不清除poison后继续运行。

[独立首版设计](../plans/WORLD_CACHE_RA_COARSE_CALIBRATION_R1_20261010.md)明确六点范围、年龄／阶段混合、undefined值与缺表回退，插值grid标作估计。该实现尚未生成真实Cosmos表、部署RA策略、获得质量或速度结果；MF-00 R2原进程和冻结源不修改。

[CPU实际源码测试](../tests/check_cfg_ra_calibration_full_sampler_cpu.py)覆盖两flow、两场景OFF／ON各全36父、12起点与24完整子后缀，共624solver／1248net。只验证本次采集与表生成的受影响行为，不重跑无变化的旧16路矩阵。完整实际执行和原件验收回执随后追加；本节初始状态为实现及语法检查完成，非CPU通过。

单次完整4GPUh门槛与48GPUh窗口已经在权威执行约定中落实。下一批真实模型校准仍需完整生产batch／CPU、费用预测、源与实际资源准入；符合门槛就自主推进。

首个CPU实际运行source7b9d1f6／152载荷，3692520／3692521退出1，driver234.415227秒／核心0.947386秒，完整失败范围与原件已保存。新history指纹调用既有tree_digest时未将PaidProbe dataclass规范化，第一父12步检查点报`Uncovered state type: PaidProbe`。这是新指纹实现错误，未完成采集，不是校准或方法负结果。修正只在指纹中将last／base_last的paid_probes转为asdict；动作、张量、求解器和六起点范围不改，新R2独立stage重新执行完整CPU。

CPU期间账本原字节变化来自原MF-00 GPU终态结算；CPU未写账本也未新增GPU。不能把变化解释成CPU费用或CPU失败原因。

独立R2已完整通过：[原件验收](../reports/wc_ra_calibration_core_cpu_r2_terminal_20261010_capture_and_independent_audit.json)sourcec94ab4a／152载荷，3710289／3710290均退出0消失，driver92.332007秒。两flow实际8完整父、24完整子、624solver／1248net；四个父OFF/ON逐张量相同，全部12起点的物理状态与新增共同history恢复、每步实动作、首guided复用一次及全dense后缀通过。原始Toy分支与终点张量真实重读、表可重建、缺起点／改先验／Toy表进入真实部署均拒绝；临时Toy文件不作为长期原始数据，结果原件保留。CUDA未初始化，GPU提交0、预算SHA前后相同；仍非真实Cosmos校准。

生产[完整batch](../src/wcomr/cfg_ra_calibration_sampling.py)及[独立CPU卡](../manifests/wc_ra_calibration_sampling_cpu_r1_preregistration_20261010.json)已准备：两flow各成功与最后父tensor写出失败四完整路径，合计16执行父／48完整子、1248solver／2496net，成功8父及96个子张量实际重读，16项证据破坏／2实际子文件截断／2最后写出失败。真实guarded准备／采样／解码／写出源码配合Toy权重，新增生产batch的作用域与原始artifact审计需要这次完整验证；不重跑已经不变的旧接口矩阵。当前仅准备及CPU派发，未称生产batch通过或启动新的GPU。
