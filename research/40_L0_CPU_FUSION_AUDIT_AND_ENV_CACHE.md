# L0两臂CPU终态审计与隔离环境缓存缺项

2026-10-01；最终状态以实际receipt为准。

## 两臂完整审计准备

真实fusion-r1/sourcec69e492的CFG-only与few-step+CFG两臂均已有825张量/300目标/525未目标、3分片的融合与序列化检查，完整任务还需监督终态和原输入后hash，不能仅据分臂PASS称可推理。

新 [audit_l0_cpu_fusion.py](../scripts/audit_l0_cpu_fusion.py)准备完成/语法检查通过，当前尚未执行。原3PIDs全部消失、fusion锁释放且exit0/完整runner/source/账本成立后，独立CPU-only审计新identity、GNU timeout900秒、CUDA为空。先写PID/阶段，再全18输入官方digest重算并核对融合前后记录；全6输出分片digest、1650实际serialized tensor字节/shape/dtype/有限性、1050实际未目标原始weight字节、新config/index/auxiliary链接；完整runner矩阵公式记录保留，源码固定。审计结束再复核receipt/source/账本，不能把exit0或CPU产物当模型/任务/GPU结果。

新审计阶段不改原融合程序/原3600秒cap，不重跑融合，不计GPU成本。任务观察超时只查同PID/输出，不能重复audit。

## 隔离环境元数据

已在本项目 `.sync/l0-native-env-r1` 新建Python3.11.15 virtualenv，尚未装runtime包，不修改原Cosmos/Wan环境，也没有在融合期间进行大环境复制/import。

第一次cache dry-run的only-binary/no-build参数互斥、未进入解析，记录为COMMAND_ARGUMENT_CONFLICT。修正后新metadata-r2真实offline/no-build dry-run发现指定Torch2.4.1+cu121无法在当前索引缓存解析；该证据仅为离线获取缺项，不是依赖数学冲突/完整网络资源不存在/模型不兼容。

[拟定独立环境pins](../manifests/l0_native_environment_proposed_pins_20261001.json)/[原命令问题](../reports/l0_native_environment_metadata_r1_20261001.json)/[修正后真实缓存检查](../reports/l0_native_environment_metadata_r2_20261001.json)。下一从官方PyTorch/PyPI与官方FlashAttention匹配binary补资源或核对现有本地wheel，固定实际release/hash/全部resolved依赖，再新环境安装与唯一600秒CPU probe。不能改共享包/源码以忽略缺项。

原生Wan requirements要求Transformers4.49–4.51.3；同一native common pipeline的A/B/C必须使用同一固定环境。既有环境元数据/历史PhysCache结果不作为新模型load或GPU证据。新4GPUh WorldCache clean50仍待决定，L1余额不足不自动提交。

## 实际融合终态

CPU fusion-r1/sourcec69e492已exit0/1960.417015秒终态，peak RSS30.8287GiB；两臂各825tensor/3分片/300目标/525未目标完整，18原输入融合前后官方digest一致，3PIDs退出/CPU锁释放/source与GPU账本不变。完整独立fresh产物审计尚未执行，不能称模型/任务/GPU就绪。

[监督完整终态](../reports/l0_cpu_fusion_r1_supervisor.json)/[全两臂逐tensor runner](../reports/l0_cpu_fusion_r1_runner.json)。下一独立audit-r1/hash部署新程序/CPU900上限，仍不重跑融合。
