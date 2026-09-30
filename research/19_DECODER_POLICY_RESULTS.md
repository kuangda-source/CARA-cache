# 局部确定性解码策略：单工程样本两新进程复现通过

2026-09-30；`LOCAL_DECODE_POLICY_REPRODUCTION_PASS`。同源33f080b，两fresh process串行官方WC AV/seed0/93帧/432×768/36点72CFG/WC70。

仅在原`model.decode`调用内部将cuDNN benchmark=false、deterministic=true；TF32及其他设置不变，离开正常/异常调用时恢复原flags。真实调用前后均记录并核对flags；参数、buffers、归一化、training和配置一致，缓存单独观察，不修改其语义。原始返回对象保持，额外逻辑无额外模型调用。

两个进程的72net输出、trace、full/skip计数、最终cache及latent/decode输入与旧stage-r2官方参考严格相同。两个fresh process的decode输出、guardrail前后、save输入、MP4以及93帧完整RGB/PTS严格相同。两MP4 SHA为`adde06cc8b3d5dc3b825b4e16869811260b40d869b3872c228799d507f3c595e`。实际VAE checkpoint为507609880字节、SHA256 `38071ab59bd94681c686fa51d75a1968f64e470262043be31f7a094e442fd981`，现场完整重算匹配content-addressed blob。

监督时长628.403564秒，费用0.174556546GPUh；两个child均exit0。旧PID均消失、锁可获取、GPU1 24MiB/noapps；监控无观察到外来计算进程，峰值25812/25804MiB。源码及产物现场重哈希通过。本机/Linux针对性22项CPU检查通过。

边界：本轮同时增加decoder状态见证与局部算法策略，不能独立证明benchmark导致旧差异，也不能证明全部场景/环境确定性。不是新近似方法、质量、部署加速或干净耗时结果。后续比较的所有路径必须共同使用同一解码策略，保留off/on实机见证；出现新场景差异仍要停止技术归因并检查。

累计1.9977743149465987/4GPUh，剩余2.0022256850534013GPUh，当前无GPU任务。继续W1-D/CAL数值机制诊断，旧工程四点负结果保持原有范围，不自动进入候选闭环或W2。

原始：[A](../reports/decoder_policy_r1_stage_a.json)、[B](../reports/decoder_policy_r1_stage_b.json)、[汇总](../reports/decoder_policy_r1_summary.json)、[监督](../reports/decoder_policy_r1_supervisor.json)、[终态审计](../reports/decoder_policy_r1_audit.json)。
