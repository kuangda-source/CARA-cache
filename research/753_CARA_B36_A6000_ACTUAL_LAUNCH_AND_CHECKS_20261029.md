# B36原A6000单次启动与实际开始检查

用户明确批准单次B36、硬5.5GPUh，并要求资源/预算通过后启动及半程/全程验收。2026-10-29 **08:17:37 Asia/Shanghai** 已在原A6000实际开始；当前属于运行与预热状态，没有完整技术或科学结果。[原启动字节](../reports/cara_fast_B36_GPU_actual_launch_r1_20261029.json) · [原句柄交接](../plans/cara_next_stage_20261028/mainline/r2/B36_POST_LAUNCH_HANDOFF.md)。

## 授权、来源和新鲜准入

- [直接用户授权](../plans/cara_next_stage_20261028/mainline/r2/B36_USER_AUTHORIZATION_20261029.json)：完整36条、同原A6000、硬5.5；不授权重派、换卡或其它GPU卡。
- launch为 `b684eb05c8674a94ad3dad8187f1c6b9`；实际运行source为已发布 `249aadcb2f33e360520560fea83059293ac77fed`，原A基座仍为 `9eaa5eb30c5509810c99a55002b51d6b71da1ef6`。52个执行关键源、4个汇总关键源及原A共享实现字节未改，沿用已接受双端CPU与固定runtime。与S/Q的后续Git父提交共存，不改变它的独立范围。
- registration SHA `b72083573f35e2eb653bb2dde0c36b9572e469f1c56c4728eb8659375614c5f7`；原stage `.sync/cara-fast-f19-b36-a6000-r1-20261029`，原容器同名加`-gpu`。GPU为 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，不得迁移到另一张卡。
- [实际准入](../reports/cara_fast_B36_actual_admission_r1_20261029.json)重新读取并核对全部20文件、21,348,071,882字节及快照指针；源码、runtime、英语资源、固定image、UUID/显存/apps/锁、内存与存储均核对。准入时GPU0%/24MiB/45°C，无compute PID，主机可用内存约47GiB。
- [私有存储](../reports/cara_fast_B36_actual_storage_r1_20261029.json)实际全分配32GiB SSD image并挂载、跨盘48MiB journal，原输出低水位4GiB。容器2CPU/40GiB、禁swap、cores24,25、无网络/只读root，仅确切runner开放CUDA；90°C及释放180秒界限保持。

## 唯一预算和实际原进程

[four_card中央唯一预约](../reports/cara_fast_B36_actual_central_reservation_r1_20261029.json)绑定该新launch及原A冻结，预约5.5GPUh；[启动后只读预算](../reports/cara_fast_B36_live_budget_after_launch_r1_20261029.json)为cap226、used178.06156527233628、reserved22.0、available25.93843472766372，旧16.5责任原样保持。旧未知财务hold不是新设备租约，不清除、不另计或写两卡副本。

只有宿主guardian的单调实际分配墙钟作为唯一费用；当前账单未终结，不将预约或部分路径计时当成最终GPUh。成功失败均按原真实bill唯一结算，监督器区间仅作独占监测审计。

原guardian `878084/652796038`、Docker CLI `878097/652796192`、supervisor `878142/652796209`、runner `878186/652796350`（PID/start ticks，runner UID1004）。[实际原上下文观测](../reports/cara_fast_B36_original_context_startup_r1_20261029.json)确认四句柄存活、EXCLUSIVE_PROCESS且仅确切runner，容器资源与固定UUID一致。[后续启动观测](../reports/cara_fast_B36_runtime_observation_r1_20261029.json)已记录真实模型构造、1/36完成/0失败、GPU100%/88°C及原独占通过；这些只证明运行进展，不给出部分保真、速度或方法结论。 [09:18原运维检查](../reports/cara_fast_B36_precommit_status_r1_20261029.json)进一步记录14/36完成、0失败，原guardian/supervisor仍运行；未读取部分科学分数。

## 已创建的实际开始检查

[外部检查回执](../reports/cara_fast_B36_acceptance_schedule_r1_20261029.json)绑定原guardian `started_unix=1793233057.4184854`、source、UUID及launch。已创建两项当前线程heartbeat，均COUNT1；无GPU再派发。

| 项目 | 2026-10-29北京时间 | 自动化id |
|---|---|---|
| 预测半程 / 检查 | 10:48:16 / **10:49** | `b36` |
| 预测终点 / 验收检查 | 13:18:54 / **13:19** | `b36-2` |
| 原硬截止 | **13:47:37** | 原guardian/监督器执行，不延长 |

半程只检查原句柄、36进度、温度、资源、独占和账本；若已结束直接按原终态收尾。半程可依据原路径计数与实际已耗墙钟提前同一个终验检查；终验仍活跃时，仅将该同一检查移到15至30分钟后的下一可行动终态检查，最晚覆盖原硬限后的释放边界，绝不创建重复检查、重派或改源。[跟进策略回执](../reports/cara_fast_B36_check_followup_policy_r1_20261029.json)记录原两项自动化的提示更新，没有新增检查或改变GPU源/硬限。完整技术/释放及原账单接受后，仅单次计算26新对、复用六份原A指标，完整32接受，再做输入等权双时钟/原A敏感性汇总和图表；CPU仍活跃只恢复原句柄，不重复评分。完成或真实失败唯一收尾后删除多余检查。

原A32十二对评分及真实一次冻结保持。WC_T006/RA_T1仍是FIT UNMATCHED，Native22为MATCHED；四输入都是旧CAL，两个CHECK不升级为独立DEV。原历史60行科学记录不增加运行中成绩，当前没有新的F19质量、加速或部署结论。
