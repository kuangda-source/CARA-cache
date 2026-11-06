# 104旧失败结算、磁盘保护/失败收件修复与最终恢复合同

用户授权本次完成失败费用结算、恢复前磁盘保护和终态收件修复，并给出最终恢复范围与报价；明确先不重跑。原104、72条完成原件和失败分母保留，没有科学评分、部分结果调参、新GPU预约或启动。

## 旧卡结算完成：5.48GPUh为明确标注的保守重建费用

原launch `d6351496-ee8a-4428-8ede-898f53d665cd`、source `5fc4dfe66a33a915fcc7bdf10700bae8810bb401`、原容器/句柄/UUID和锁均重新核对。主billing.json仍缺失、0字节临时文件仍保留，未伪造原账单。9008条有效监测的墙钟与单调钟偏移跨度仅0.13670秒；最后有效单调钟给出5.457539GPUh下界，容器退出减更早launch给出5.459721GPUh墙钟估计。

按容器墙钟再加60秒、向上取整至0.01GPUh，结算 **5.48GPUh**。新独立账单明确`actual_is_exact=false`、`exact_actual_GPUh=null`、`accounting_basis`及原失败身份。为兼容所有冻结版本的旧账本读者，job仍为SETTLED，旧`actual_GPUh`字段装载保守计费值，同时保存`charged_GPUh`及上述估算标记；事件为`SETTLE_FAILED_RECONSTRUCTED_CONSERVATIVE_NOT_EXACT`，不将此数作为精确科学计时。结算前账本和全部依据另存；幂等/冲突/身份/漂移/预算检查通过，其他job逐项保持。

当前账本：已用140.60066151587193、保留旧两卡未知责任16.5、可用68.89933848412807、累计上限226GPUh。旧104的11.9预约已释放；新104未预约。原始失败的科学/完整独占验收仍为false。

[原失败重新收件](../reports/cara_history104_failed_terminal_repaired_capture_20261024.json) · [独立保守结算](../reports/cara_history104_failed_conservative_settlement_20261024.json)。

## 已实际建立磁盘保护

- 在自有目录创建32GiB完整物理预分配ext4镜像，挂载到新的`outputs/cara-history-boundary104-cal4-ada-r2`；设备为独立loop文件系统，配置绑定device、镜像inode、长度及实际分配块。共享盘外部写入不能占用已分配的镜像数据块。实际卷可用约31.18GiB；不修改宿主盘保留比例。
- `/data1/gaokuangda_cara_control/history104-r2/control.journal`预分配48MiB，在与输出镜像不同的实体文件系统。6类控制记录、每类双槽4MiB，记录有代次及SHA、fsync；无需在磁盘满时扩展文件或新建临时文件。主输出/账本写失败时仍可恢复单调钟账单，坏最新槽可读取上一有效槽。
- 请求前和监督轮询检查私有输出卷4GiB、1024inode与宿主128MiB低水位。请求前检查在完整请求计时之外；所有GPU持有时间仍计整卡。未挂载、设备/镜像变化、稀疏镜像、控制日志不独立、空间或inode不足均拒绝。系统重启丢失挂载时拒绝继续，不落回普通目录。
- 账单先写独立日志，再写主账单/权威账本；主文件写失败不能绕过原子进程停止与finally中的DeviceLease释放。失败阻止CPU评分。host guardian继续只处理指定UUID，忙卡/外部进程不驱逐。

实际容器以原镜像、实际UID、GPU隐藏、只读根文件系统加精确输出/日志挂载，完成小文件写入/fsync/读回/删除及日志读写，结束时新输出卷为空。8组实际存储身份/低水位负例均拒绝。没有GPU上下文、GPU mode改变或新采样。

[32GiB与跨盘日志预分配](../reports/cara_history104_recovery_private_storage_provision_20261024.json) · [实际容器绑定和读写](../reports/cara_history104_recovery_storage_actual_container_CPU_20261024.json) · [8组存储负例](../reports/cara_history104_recovery_storage_negative_CPU_20261024.json)。

## 失败收件与新CPU组合接受

104主控制器的终态入口已对原失败实际运行：返回`FAILED_ORIGINAL_TERMINAL`，不再以ExitCode==0断言把磁盘故障误报为SSH UNKNOWN。失败入口只读技术状态、原句柄、账本和文件元数据，不调用视频评分/科学分析。完整科学接受器继续要求全104/72评分/所有控制及原件，不因费用已结算就放行。R2失败可读取注册绑定的跨盘控制日志；有效精确账单仅作为财务证据，不能将失败卡变为成功。

新冻结CPU stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-pg-p1-CPU-history104-storage-r2-20261024`；source `159aaa76ddecc78864b40fa669a32029a3a4a6e4`。容器实际13:22:06启动、13:28:12退出0，GPU隐藏。完整组合独立接受，包含：

- 原实际生产CPU入口、固定历史入口等价证据；104序列化/原件控制与72完整评分调度（CPU合成终点，不是GPU视频结果）；真实93帧LPIPS回调。
- 原6项真实CPU子进程/监督/host guardian生命周期；14项完整终态故障检查。
- 新增6组存储生命周期：真实64MiB tmpfs写满、双槽损坏恢复、正常监督、主账单/账本/监测/终态写入ENOSPC。真实CPU子进程退出、FD锁释放、独立账单可读、失败不启动评分均通过。账本或主账单失败时保留预约，等待有证据的独立结算，不静默释放责任。
- 本地40项财务、失败分类、未来精确日志身份、幂等结算、无授权拒绝重跑、完整104接受和结果分析协议检查通过。

[主控制器实际失败收件](../reports/cara_history104_main_controller_failure_capture_fixed_20261024.json) · [CPU完整原件](../reports/cara_history104_storage_combination_CPU_terminal_r2_20261024.json) · [独立CPU接受](../reports/cara_history104_storage_combination_CPU_accepted_r2_20261024.json)。

## 最终恢复：全新104，不拼32条，也不选跨会话64

保留4CAL/seed0/10角色、80正式（两轮完整40）+20warm+4诊断、3744pairs/7488CFG、单load、原alpha和固定顺序。旧72原件不用于新拟合或新验证，也不用于此报价。保持原始部署上限257.7712338712067秒与固定6秒模型余量；不根据部分结果改变策略或预算。

| 项目 | 最终值 |
|---|---:|
| 新GPU整卡forecast | 11.423207068397064GPUh |
| 新GPU硬上限 | 11.9GPUh（未放宽） |
| 释放后CPU评分 | 72组/6696帧，最多1.5h×2CPU，额外GPUh为0 |
| 累计上限 | 226GPUh |
| 新卡用满11.9后累计已用 | 152.50066151587194GPUh |
| 再保留旧两卡16.5责任后的剩余 | 56.99933848412807GPUh |

新source/CPU/存储已绑定到独立准备stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-history104-full-ada-r2-20261024`，注册SHA `73bd0dac3e1005cea6290c7e0dd93216a7020d67dd8e5811d8d44ca3181c718b`。该stage无GPU intent、launch或guardian；只是准备完成。新launch入口要求新的明确用户重跑授权文件，绑定此注册与CPU证明SHA；本次没有该授权文件，也没有GPU预算预约。

[最终完整报价](../manifests/cara_history104_recovery_full104_quote_r2_20261024.json) · [最终恢复合同](../plans/cara_policy_generator_20261020/HISTORY104_FINAL_RECOVERY_R2_20261024.md) · [新stage准备回执](../reports/cara_history104_recovery_GPU_stage_r2_20261024.json)。旧失败恢复的一次性检查已关闭；后续若获启动授权，再做fresh UUID/真实独占/账本/内存/挂载准入，按实际新launch安排检查。

[恢复准备独立汇总与SHA绑定](../reports/cara_history104_recovery_prelaunch_acceptance_20261024.json)。原科学manifest、采集/评分、历史布局、采样和时间分析源码与原5fc4dfe6逐字节一致；新增的是存储/监督/收件及新的执行身份。
