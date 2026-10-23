# CARA独占价格补测已在GPU3准入：调度与检查安排

**独立价格补测已在GPU3实际运行，硬件独占和唯一原runner验证通过。** 实际恢复启动为2026-10-23 **13:13:24.179586 Asia/Shanghai**；13:19:01的最新技术快照已进入首条`warm_1_CONTROL`，0失败。本卡仍需完整终态接受，不是PG自动策略的质量/速度结果。

## 优先级与GMSD协调

已读取GMSD源对话`01a0f8c7-2f9c-7372-87e3-bd77f830f9f2`并核对用户消息`01a16728-7cb3-7350-91b8-9ffbeec1fbd6`：GPU优先CARA-cache。GMSD对话报告原28F诊断已完成、后续暂不派GPU；本侧[实时复查](../reports/wc_policy_price_refresh_GMSD_release_fresh_resources_20261023_1313.json)也确认其PID942555和容器均已退出、共享GPU3 UUID锁释放，GPU3只有24 MiB且无计算进程。没有中断或改动GMSD任务。

[协调回执](../reports/wc_policy_price_refresh_CARA_priority_coordination_20261023.json)记录授权、资源与范围；仅在本对话和仓库记录，未发送跨对话消息。当前安排如下：

| 资源 | 本次实际状态 | 后续可用条件 |
|---|---|---|
| GPU3 `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934` | CARA价格补测独占 | 原runner/容器/共享UUID锁实际释放后再准入；不要按预计时间抢占 |
| GPU0 | BeamNG占用 | 后续fresh确认空闲，满足独立准入后才可使用 |
| GPU1、GPU2 | 其他Python任务占用 | 同上；当前没有可承诺给GMSD的空闲卡 |
| GMSD当前可推进 | 原结果CPU验收、文档和代码准备 | 未来另有空闲GPU0–2时，可在自身预算、共享UUID锁及主机内存/磁盘足以保留CARA运行空间的前提下独立准入；GPU3仍优先CARA |

价格卡forecast9.500278 GPUh，上限11.5；约22:43的预计完成与22:59验收都不是保证释放时间。价格完整接受后，CARA待接PG-P1/P2；这些后续卡还需要各自真实CPU与完整报价，不在本次11.5 GPUh中。

## 唯一实际运行身份与准入

[实际恢复启动原件](../reports/wc_policy_price_refresh_full1624_GPU_actual_recovery_launch_20261023_1313.json)保持原launch ID `895d66c7-5e95-42b3-bbff-0f78766eb424`。原12:59裸Python解释器前失败及0 GPU费用原件见[654](654_CARA_PRICE_HOST_ENTRY_REPAIRED_WAIT_GMSD_RELEASE_20261023.md)，没有重写或重跑科学卡。

- run：`wc-policy-price-refresh-cal4-full1624-ada-r1`。
- source：`cecba6647fcc626887761961fc7215c6fe1afa8b`；stage：`/data20t/gaokuangda/worldcache_workspace/.sync/wc-policy-price-refresh-fourcard-full1624-r1-20261023`。
- guardian PID950505/start951746754；supervisor PID950689/start951747277；runner PID950782/start951747898/UID1000。
- 容器`wc-policy-price-refresh-fourcard-full1624-r1-20261023-gpu`；只暴露指定GPU3 UUID。
- [实际idle独占核验](../reports/wc_policy_price_refresh_GPU3_exclusive_idle_actual_20261023_1314.json)和[实际active核验](../reports/wc_policy_price_refresh_GPU3_exclusive_active_actual_20261023_1316.json)均通过。硬件`Exclusive_Process`，无MPS，唯一CUDA上下文为原runner；共享UUID锁持有。
- [准入与安排回执](../reports/wc_policy_price_refresh_exclusive_admission_and_schedule_20261023.json)绑定启动、收件、独占proof和原身份；[初期连续监测](../reports/wc_policy_price_refresh_monitor_and_resources_20261023_1316.json)56条记录、最大间隔2.612秒。持续监测和末次到结算间隔仍必须不超过45秒，最终才可接受干净价格。
- [13:19:01技术进度](../reports/wc_policy_price_refresh_full1624_GPU_initial_progress_20261023_131859.json)：0/10完成、1运行、9未到达、0失败，`warm_1_CONTROL`运行，原四个句柄均存活、无错误行。文件名131859是本地命名时刻，实际远端观测以`observed_unix`为准。

完整scope保持4CAL、10路径（8正式+2warm）、1624正式格/2030总格、每格1warm+3正式轮×3动作、24360读出、360pairs/720CFG、单load。复用原4Native与原误差标签，未改变生产配置。原1624的6.900543598864 GPUh已结算保持；本卡新预留11.5后，池已用125.646551890291、总预留28（含旧未知16.5）、可用72.353448109709、cap226。新实际费用终态结算。

## 检查与接续

| 检查 | 按实际恢复启动的最早时刻 | 已安排 | 自动化 |
|---|---|---|---|
| 技术半程 | 17:58:24.679586 | 10月23日17:59 | `cara`，一次性 |
| 完整终态验收 | 22:58:25.179586 | 10月23日22:59 | 复用`cara-bank24-2` |

旧13:30资源检查已改绑22:59终态。已存在恢复intent和恢复launch，接续只能capture/recover，绝不能再次launch-gpu或resume-host-entry。统一`--launch-ref reports/wc_policy_price_refresh_full1624_GPU_actual_recovery_launch_20261023_1313.json`。

半程只记录技术状态、进度、独占/UUID/锁/预算/磁盘和错误，不以部分价格或视频调参。提前退出按实际终态和费用处理。完整终态用同控制器capture `--mode terminal`后独立`accept-gpu`，核对全部10路径/24360读出、原36步/final/93帧参照、三轮一致、原标签不变、完整独占监测、财务与释放、恢复身份双SHA、新bundle绑定；通过后才分析全1624重复波动/顺序漂移/聚合放大并接PG-P1。

PG-P1/P2非GPU准备见[652](652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)。冻结策略后的历史窗口shadow不写回、少步Native等实测时间对照保持；新增范围各自完整报价。仅意义进度、完成、失败或需要用户行动时通知。
