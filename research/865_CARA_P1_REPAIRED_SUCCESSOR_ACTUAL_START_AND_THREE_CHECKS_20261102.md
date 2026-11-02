# P1 修复后新单次 R2 实际启动与三个检查

用户明确批准新单次19GPUh及本卡原中央账本事务后，P1 R2于 **2026-11-02T22:39:06.791125+08:00** 在两卡原A6000唯一实际启动。完整146语义/最多142物理/5176pair/64同状态标签、19D22D保持，硬19GPUh。当前仅为真实执行进展，尚无完整V1科学结论。[实际启动接受](../reports/cara_v1_P1_successor_actual_start_accepted_r2_20261102.json)绑定原guardian/CLI/supervisor/runner、容器和唯一CUDA。

## 修复、来源与准备

[864完整准备](864_CARA_P1_PUBLICATION_RPC_REPAIRED_CPU_AND_SUCCESSOR_READY_20261102.md)保留了确定性旧故障复现、原子请求目录发布及RPC命名空间修复，以及实际Linux修复33、新身份56（本机另1图形控制）的原CPU接受。1473文件源、独立64GiB输出/48MiB日志均独立接受，全部原CPU/存储准备进程结束，无旧GPU/指标重放。原R1失败4.933201964GPUh已结算，三个原检查已删除。

- run：cara-source-lifecycle-V1-P1-full146-r2-20261102
- launch：498503f9cfd249f1aab929da18f04e10
- source：8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99
- registration：8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884
- GPU：GPU-cebf7119-cf03-23b9-e192-cd196332b704
- container：629379b320ee11ce938534aa7528a237cd9bee9bb923affb2e47df3a0ed867cf
- guardian3600207/692524957；CLI3600299/692525281；supervisor3600355/692525330；runner3600402/692525518。

## 授权、完整准入和一次预算

[用户新批准](../reports/cara_v1_P1_successor_direct_approval_r2_20261102.json)和[授权原件](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SUCCESSOR_SINGLE19_AUTHORIZATION_R2.json)仅覆盖本新单次与本卡原账本读/唯一预约/实际结算，不增cap、不迁账本、不在四卡做实验。原持久化115源operator已准备，缓存位于原账本同机.sync；禁止再次central-prepare。

[完整资产admit](../reports/cara_v1_P1_successor_fresh_admission_r2_20261102.json)校验20个生产资产共19.88194GiB真实内容。初次fresh回执年龄56.56秒触发本机55秒预检查停止，未预约；随后原refresh成功，在60秒窗内[唯一预约19](../reports/cara_v1_P1_successor_central_reservation_r2_20261102.json)。cap250保持，旧责任16.5、used201.95503799855743保持，预约后available12.54496200144257。

首个dispatch在再次现场内存门中拒绝，发生于GPU-intent写入前，未产生GPU运行或费用。status重新确认原意图/容器均不存在后，refresh回读50.07317GiB、中央同一envelope恢复且无账本写入，再由同一原dispatch通过其新鲜资源门并写出唯一GPU意图。全程没有降50GiB门、重复预约、源修改或重启旧卡，批准持续有效。此拒绝/恢复与真正GPU失败分开保存，不把它计为第二次实验。

## 运行观察和实际开始绑定的检查

[当前原句柄快照](../reports/cara_v1_P1_successor_original_running_status_r4_20261102.json)：新原进程活跃，唯一runner CUDA、GPU100%/84°C/15908MiB、完成1个物理请求、内部查询意图0。运维记录不读取部分T_DD/LPIPS或选择科学计划。

[三个检查定义及SHA](../reports/cara_v1_P1_successor_acceptance_schedule_r2_20261102.json)已实际创建并逐项核验：

| 角色 | 北京时间 | 原自动化 |
|---|---|---|
| 1/4程 | 2026-11-03 03:10 | p1-r2-quarter |
| 半程 | 2026-11-03 07:41 | p1-r2-half |
| 完整验收 | 2026-11-03 16:48 | p1-r2 |

按原guardian实际开始和18.05067GPUh工程预测计算，quarter/half向上取整到分钟，终验在预计结束后约5分钟。**硬截止2026-11-03T17:39:06.791125+08:00，停止释放截止2026-11-03T17:29:06.791125+08:00**；19GPUh、90°C、40/8GiB no-swap和每查询新鲜12GiB保持。运行中不重新应用初始50GiB准入门。无变化/不可行动安静，quarter/half只运维计数，可前移同一个终验，不创建重复监控。完整成功或真实失败收尾后删除所有剩余检查。

## 后续只恢复本原运行

按 [新post-launch交接](../plans/cara_next_stage_20261101/source_lifecycle/P1_SUCCESSOR_R2_POST_LAUNCH_HANDOFF_20261102.md)，仅`cara_p1_successor_control_r2.py status/central-status`恢复；UNKNOWN不重派、不换源/卡/配置。成功失败均原完整终态/释放后唯一guardian全段实耗结算。

完整GPU成功释放和结算后才完整146/64/RGB门、一次至多32新CPU并复用本卡封存FIT组成52、原FIT一次冻结、完整原字节导出/本机绘图。原CPU活跃只recover。保留原R1失败与费用、所有A32/B36/S/Q/旧搜索冻结、四旧CAL/曝光CHECK、WC/RA FIT UNMATCHED和最终/备用16；不自动P2/V2或下一GPU卡。
