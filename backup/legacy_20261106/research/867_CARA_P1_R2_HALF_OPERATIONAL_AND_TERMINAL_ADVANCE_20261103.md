# P1 R2 半程运维检查与同一终验前移

原 P1 R2 在 **2026-11-03T07:43:39.708626+08:00** 仍运行，实际墙钟 **9.0758 小时**。原 guardian、CLI、supervisor、runner 的 PID/start ticks/boot、容器和注册均与启动封存一致，原 A6000 上只有原 runner 的 CUDA 进程。[运维接受](../reports/cara_v1_P1_successor_half_operational_accepted_r1_20261103.json) · [原状态](../reports/cara_v1_P1_successor_half_original_status_r1_20261103.json) · [原账本](../reports/cara_v1_P1_successor_half_central_status_r1_20261103.json)。

- 完成 **97个物理请求／最多142**；科学语义分母146保持，不转换成97个已接受语义位置。20个内部查询意图仅是运维计数，不代表20个查询已经接受；未读取部分LPIPS、T_DD或科学计划。
- GPU 当前 **78°C、27508 MiB、40%、Exclusive_Process**；输出剩余66162495488字节，全部原主进程活跃，容器未OOM。启动前50GiB门未重跑，40/8GiB no-swap、每查询12GiB和90°C保护保持。
- 原中央115文件operator核验通过，cap250、used201.95503799855743、reserved35.5（本卡19＋旧16.5）、available12.54496200144257未变。没有新派发、预约、增额或结算。

只按97/142计数和9.07581小时墙钟作线性运维外推，完整物理上限对应约 **11:56**；剩余工作异质，不能承诺此时完成。因此把**同一个 `p1-r2` 终验从16:48前移到11月3日12:15**，留出检查余量；若仍活跃继续调整同一终验。没有新建检查，原硬19GPUh、17:39:06.791125硬截止和17:29:06.791125停止释放截止保持。[检查承接R4](../reports/cara_v1_P1_successor_acceptance_schedule_r4_20261103.json)保存原R3字节SHA和新定义SHA。

本次 `p1-r2-half` 已通过应用工具删除，quarter此前已删除；仅保留原终验ID。此次为健康运行观察，无需用户操作，尚无科学接受或主方法结论。按[原post-launch交接](../plans/cara_next_stage_20261101/source_lifecycle/P1_SUCCESSOR_R2_POST_LAUNCH_HANDOFF_20261102.md)恢复原终态和释放、唯一实耗结算，成功后才完整146/64/RGB、一次CPU全52及一次FIT冻结。旧失败、全部旧冻结和保护输入保持，不自动下一卡。
