# P1完整双flow R3 CPU：唯一原运行

R1 writer后缀失败、R2 caller forward恢复失败均已退出并保留，不重启、不重评分。R2第一flow完整原件仅作已发生的CPU组件证据，不能替代本R3双flow整体验收。当前固定特征/DP/指标/数据范围均保持，修复的是生产loaded入口的调用者方法恢复及错误清理。

- source `aca025a7a51be8d134f4e2b29a3c42f25db429ca`，two_card。
- stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r3-20261102`。
- 原容器 `cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r3-20261102-cpu`，registration SHA `76edb6635326d427e06258a370b96a921498fca27882027ffbad394b59ff9e75`，1375份payload，原WC/RF runtime散列。
- 实际开始 2026-11-02T04:57:48.333867+08:00；工作3600秒、退出60秒，工作边界2026-11-02T05:57:48.333867+08:00，退出余量至2026-11-02T05:58:48.333867+08:00。工作边界保持，不延长原运行。
- 原启动 [cara_v1_P1_algorithm_Linux_CPU_launch_r3_20261102.json](../../../reports/cara_v1_P1_algorithm_Linux_CPU_launch_r3_20261102.json)，原句柄观察 [cara_v1_P1_algorithm_Linux_CPU_capture_r9_20261102.json](../../../reports/cara_v1_P1_algorithm_Linux_CPU_capture_r9_20261102.json)：Running，容器PID 3200698、启动CLI PID 3200651。恢复按原容器/registration/源，不凭PID新派。
- 单核26/4GiB/no-swap/no-network/readonly-root/no-GPU；本CPU不加载Cosmos权重、不读旧实验视频、不访问四卡或中央。

只用`scripts/cara_source_lifecycle_p1_linux_cpu_r3.py capture --source-revision aca025a7a51be8d134f4e2b29a3c42f25db429ca --output 新唯一回执`。禁止prepare、重启或改原stage/源/配置。连接UNKNOWN先恢复原句柄，不能由观测超时推定结束。

exited0与原proof齐全后，使用`scripts/accept_cara_source_lifecycle_p1_linux_cpu_r3.py`，绑定原launch_r3和新terminal capture，输出accepted/proof必须新文件。原proof字节SHA必须匹配；33控制、两flow各146语义/64同状态标签、完整93帧真实Alex合成指标、零新增回调恢复以及成功/恢复/存储拒绝的caller forward还原均须完整。原容器和全部指标子进程须退出。失败保存原终态和原因，不伪造CPU接受；不重放旧首flow或分数。

[单次检查清单](../../../reports/cara_v1_P1_algorithm_CPU_acceptance_schedule_r1_20261102.json)：半程p1-cpu在2026-11-02T05:18:00+08:00，终验p1-cpu-2在2026-11-02T05:38:00+08:00。仅运维句柄/完成计数；运行中可按计数调整同一终验，不新建重复检查。全链已收尾删除两检查；半程单次观察完成删除本半程。保持原3600/60边界。

本CPU成功仍不等于真实V1视频或完整GPU入口。宿主broker只有九项本地控制，真实Linux独立容器和完整服务接受待补，具体下一交付见[宿主probe实现承接](V1_P1_HOST_FIT_CPU_NEXT_IMPLEMENTATION_R1.md)。还需整卡原终态/释放/唯一结算后的全结果与补充指标接受、图表/冻结和正式146位置报价，之后单次>4GPUh和新卡账本事务另审。P0/M1/A32/B36/S/Q/旧搜索冻结与16保护输入/备用16保持。
