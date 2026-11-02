# P1 R2 四分之一程运维检查

原 P1 R2 在 2026-11-03T03:08:03.204840+08:00 仍运行，实际墙钟 4.4823 小时。原 guardian、CLI、supervisor、runner 的 PID/start ticks/boot 和容器均与启动封存一致，原 A6000 上只有 runner 的 CUDA 进程。此次仅保存运维信息，没有读取部分科学结果。[检查接受](../reports/cara_v1_P1_successor_quarter_operational_accepted_r1_20261103.json) · [原状态](../reports/cara_v1_P1_successor_quarter_original_status_r1_20261103.json) · [原账本](../reports/cara_v1_P1_successor_quarter_central_status_r1_20261103.json)。

- 完成32个物理请求，物理上限142；科学语义分母保持146，不能把32转换成已接受语义位置。内部查询意图0，完整64标签与全52最终评分仍待后续完成。
- GPU 当前67°C、29612 MiB、利用率7%、Exclusive_Process；输出剩余66749550592字节。所有原进程活跃、容器未OOM。此次未重新应用启动前50GiB内存准入门，40/8GiB no-swap及每查询12GiB保护不变。
- 原中央115文件operator验证通过；cap250、used201.95503799855743、reserved35.5（本卡19＋旧16.5）、available12.54496200144257保持。没有新预约、增额或结算。

仅凭当前物理计数不足以确认更早的完整终态，保留同一半程 **11月3日07:41** 和终验 **16:48**，没有创建新检查。硬19GPUh和 **17:39:06.791125** 截止不变，停止释放截止 **17:29:06.791125**。已通过应用工具删除本次 `p1-r2-quarter`，并验证另外两个定义原SHA及ACTIVE均保持。[新检查承接](../reports/cara_v1_P1_successor_acceptance_schedule_r3_20261103.json)保留原计划字节引用和删除事实。

这是健康运行中的运维观察，尚无新的科学接受或主方法结论。后续仍按[原post-launch交接](../plans/cara_next_stage_20261101/source_lifecycle/P1_SUCCESSOR_R2_POST_LAUNCH_HANDOFF_20261102.md)只恢复原句柄；完整终态释放后唯一结算，成功后才完整146/64/RGB、一次CPU全52接受与一次FIT冻结。原R1失败、全部旧冻结和保护输入保持，不自动下一卡。
