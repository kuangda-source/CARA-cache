# P0 第20步：唯一原运行与完整验收承接

原通路已恢复，实时资产、资源、原句柄、独占和中央余额核验通过。唯一P0于 **2026-11-02 01:24:19.536402 Asia/Shanghai** 实际开始。以下覆盖启动前连接等待快照；禁止再prepare、预约或派发GPU。

## 原身份与硬限

- run：`cara-source-lifecycle-P0-point20-full14-r1-20261101`
- launch：`94ad4122aab5401b834643a84868d417`
- 固定GPU source：`3263bdfe0eb93fa7c93daefd34ce892855a5a4b3`
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-P0-point20-GPU-a6000-full14-r1-20261101`
- two_card A6000：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`
- scope SHA：`0b61ea4937e71724ad1c781a3adca36a3839a4d8e3212a971747a0579da5a766`
- registration SHA：`d5df9d66c521bd0ffba6ae190f395c0daac22f79dc72f1ecbf3a9033b306b9f8`
- 容器：`cara-source-lifecycle-P0-point20-GPU-a6000-full14-r1-20261101-gpu`，完整id见原开始接受。
- host boot：`13495735-f30b-47a2-af0a-2496f5206a0b`，PID namespace inode `4026531836`。

| 原进程 | PID | start ticks |
|---|---:|---:|
| guardian | 3110195 | 684876234 |
| container CLI | 3110286 | 684876474 |
| supervisor | 3110345 | 684876512 |
| runner / 唯一CUDA进程 | 3110391 | 684876645 |

完整14请求、504真实更新、512物理成对计算、1024 CFG分支调用、8新评分、93帧432×768，目标第20次真实更新。预计1.6047625 GPUh；硬限 **1.95 GPUh**，主工作停止/释放截止 **03:11:19.536402**，最终硬截止 **03:21:19.536402**，600秒释放余量及90°C阈值保持。不得改源、改配置、换卡、重启或迁移。

[原实际开始接受](../../../reports/cara_v1_P0_point20_actual_start_accepted_r1_20261101.json)与[原运维状态](../../../reports/cara_v1_P0_point20_actual_start_status_r1_20261102.json)已核对launch SHA、四原句柄、容器镜像/设备/manifest与独占唯一CUDA PID。原01:28:41快照为0完整/1运行/13未到达、81°C；这是保存的运维快照，不能当作后续实时进度或科学结果。guardian的`ADMITTING`标签本身不代表尚未开始，以原单调时钟、句柄和CUDA上下文为准。

## 只恢复原运维与账本

使用 `scripts/cara_source_lifecycle_p0_control_r4.py status --output 新文件`；四卡仅本卡原账本的`central-status`或`central-recover`，不得在四卡运行实验或迁移账本。R4在每次串行RPC前做一次有界原Tailscale peer probe，并使用原任务QOSnone SSH配置和目标60秒连接等待；原两层公钥/host key不变，无系统路由、服务或Clash配置修改。间歇断连根因没有证实，UNKNOWN只恢复原句柄，不能因此再派发。

中央原operator缓存为 `/tmp/source-lifecycle-P0-point20-central-operator-94ad4122aab5401b834643a84868d417`；115份源码已与原CPU proof一致。不要再次central-prepare。若缓存因重启真实丢失，仅恢复同一launch的原字节与原事务；不能新造GPU身份或账本。客户端可更新连接方式，但central源码闭包须继续匹配原proof。

唯一预约已接受，见[原中央预约](../../../reports/cara_v1_P0_point20_actual_central_reservation_r1_20261102.json)：cap226、已用195.54048154808925、总保留18.45（本卡1.95与旧16.5）、可用12.009518451910754 GPUh。它是预约时快照，不能代替下一张卡实时准入。当前实际费用待原guardian终态，不填0。成功失败均唯一结算原guardian全段单调时钟实耗，禁止把supervisor时间重复计费。

## 已建立的实际开始检查

[原调度回执](../../../reports/cara_v1_P0_point20_acceptance_schedule_r1_20261102.json)绑定原实际开始；当前状态见[更新调度r2](../../../reports/cara_v1_P0_point20_acceptance_schedule_r2_20261102.json)。半程已完成并删除，仅原终验p0-20仍活跃。

| 检查 | 自动化id | 本次时间（Asia/Shanghai） |
|---|---|---|
| 半程（完成，已删除） | `p0-20-2` | 2026-11-02 02:13 |
| 全程验收 | `p0-20` | 2026-11-02 03:03 |

半程只读14分母计数、句柄、温度、资源、独占和账本。仍运行保存一次运维回执；只能按完成/剩余计数和实耗墙钟前移同一个终验，不读取部分T_DD、LPIPS、RGB或latent。半程处理后删除自身；全链结束则同时删除多余终验。终验若仍运行或CPU活跃，调整同一id继续接受，原硬截止不变，不新建重复检查。状态无变化或不可行动保持安静，只在有意义进展、完成、失败或需要用户行动时通知。

## 原终态、释放、结算与一次CPU验收

1. 使用R4恢复原terminal status，保存固定 `reports/cara_v1_P0_point20_final_original_r1_20261101.json`。日期为冻结卡标识，文件内必须保留真实时间。完整核对14分母、原进程终态、容器、锁释放、Default恢复、原billing；失败同样保留。
2. `scripts/cara_source_lifecycle_p0_control_r4.py settle --input reports/cara_v1_P0_point20_final_original_r1_20261101.json --output reports/cara_v1_P0_point20_final_settlement_r1_20261101.json`。原事务UNKNOWN先central-recover/central-status，禁止重复收费。只有原释放和唯一结算均接受，才能读完整科学工件。
3. 完整14成功才用 `scripts/cara_source_lifecycle_p0_accept_transport_r2.py artifacts --output 新回执` 恢复固定stage的原释放读者，要求四个完整latent/93RGB等价控制、两份与原第8步Native的桥接全部通过。读者已启动只`capture`，不得重复读者。客户端R2仅改变SSH连接设置，原REMOTE/WORKER与固定source逐字相同；[七项本地客户端控制](../../../reports/cara_v1_P0_point20_client_transport_CPU_r1_20261102.json)通过，不构成CPU或科学执行结果。
4. 原工件接受后，原`score`只派一次8新对CPU评分，之后只`capture`恢复。不能重评旧M1八对、重跑旧Native、改旧冻结；真实失败不能自动重试。保存原packet、manifest、scores的完整字节与SHA，依据固定stage的原接受器接受全部8对。
5. 全8接受后使用 `scripts/analyze_cara_source_lifecycle_p0_complete_r1.py --point20-accepted 原8对接受文件 --point20-packet 原完整packet --output 新汇总`，合并原已接受第8步八行，完整16科学位置。输入等权、全93帧，报告W_C、W_D、读出、总收益、交互及直接来源消费/替换记录，导出完整曲线与图表。第20步预期C21消费/D23替换在此前只是设计，必须由完整原history确认。
6. 保存完整成功或真实失败记录，更新canonical、精确提交推送，然后删除本卡剩余自动化。

P0只检验两个预登记状态的写入机制。当前无第20步科学结论；V1真实拟合和自动计划视频仍待。P1完整预算另审，不自动启动；原A32/B36/S/Q/搜索冻结、WC/RA FIT UNMATCHED、四旧CAL范围及最终16/备用16保持。

## 已完成半程

[02:14半程接受](../../../reports/cara_v1_P0_point20_halfway_accepted_r1_20261102.json)及原状态/中央回执：7/14完成、0失败、四原句柄活跃，独占唯一CUDA PID3110391，63°C。账本原预约仍RESERVED_OR_RUNNING，cap226、旧16.5和1.95硬限保持。仅使用运维计数与墙钟，原终验03:03及硬截止均未变；半程p0-20-2已删除。P0运行期间新增的V1标量采集CPU准备另有独立stage，不运行GPU，不替换原stage或P0验收。
