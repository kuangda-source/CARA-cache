# DEV128：两卡A6000独占启动与验收安排

2026-10-26。用户明确授权完整128路径在两卡服务器单次执行；本记录为实际启动和技术准入，不是新DEV结果。

## 唯一执行身份与范围

- 实际启动：2026-10-26 13:36:59.839347+08:00。launch `61587bb0-0e0d-4379-973b-d5502158fcd2`，run `cara-shared25-dev128-r1`。
- 冻结执行源码 `f273eefceef4fe88ab75edc74eaf714081126550`，stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-dev128-full-a6000-r1-20261026`。后续文档提交不改变运行stage。
- GPU1 A6000 UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；guardian3845133/start628792336，supervisor3845191/start628792481，runner3845233/start628792670/UID1004。真实idle及active硬独占握手通过；四卡未提交本卡。
- 16新DEV、六角色，96正式+24重复+6warm+2诊断=128，4419pairs/8838CFG/单load、26控制；原α和强基线不变。释放GPU后80LPIPS/7440帧与96×3=288独立质量位置，2CPU/8GiB、最多10小时。

## 启动前修复与证据

发现旧16.5GPUh未知责任预约的GPU UUID被旧通用账本当作活跃占卡，可能拒绝两卡新预约。仅对精确退休责任类型、无真实launch/PID、费用未知且未确认GPU提交的记录，区分财务责任和活跃设备身份；旧原始行与16.5费用一字不变，真实占用仍拒绝。没有修改旧全局账本模块，也没有移除责任预约。

修复后两端完整CPU重新接受：各10生命周期、6真实ENOSPC、63终态/财务/评分检查；本地77检查通过，包含同UUID责任保留与重复提交拒绝。真实质量模型沿已接受源码/权重SHA复用。传输中断发生在远端stage建立之前，只结束自有传输后确认不存在stage，随后两端R3各一次完整通过。所有旧CPU收件保留。

双服务器首次使用曝光审计无远端已执行命中；本地两项命中是冻结清单和既有无推理审计的角色元数据，按精确路径/SHA/结构复核通过，原宽审计保留。没有更换16输入。执行源码已推送并核实公开HEAD后绑定。

## 资源和预算

32GiB完整物理预留ext4输出卷与系统盘48MiB跨盘日志已核验；StorageGuard持续监测。13:38:08原件为模型加载中、0失败；29独占样本无违规，最大间隔2.336秒，输出可用31.18GiB、跨盘遥测新鲜度2.312秒。完整终态独占尚未接受。

- GPU预测11.618228467131088h，硬上限12h；累计226与最终部署min(257.7712338712067秒,.8freshNative)不变。
- 中央used161.39662063362806、reserved28.5（旧16.5+本次12）、available36.10337936637194GPUh。两卡子账本与中央外部包是同一次费用，不重复计费。实际费用待原单调账单形成并中央结算。

## 实际启动后的检查

| 环节 | Asia/Shanghai时间 | 说明 |
|---|---|---|
| 技术半程 | 10月26日19:26 | 不早于19:25:32，自动化cara-dev128-a6000 |
| 采集预测 | 10月27日约01:14 | 按整卡报价外推，实际可提前或延后 |
| CPU评分预测结束 | 10月27日约09:48 | GPU释放后评分，预测8.56449h、最多10h |
| 完整验收检查 | 10月27日10:04 | 自动化cara-dev128-a6000-2，未完成则原任务改期 |

半程只查身份、独占、存储/跨盘日志、完成量和错误。终态必须全部128、26控制、80/288评分、SHA、原布局α、完整独占/末次结算间隔≤45秒、原进程容器锁释放、原单调账单及中央结算全部通过后独立接受。CPU评分中不能重派GPU，失败保留费用与原件。UNKNOWN只recover此stage。完整接受后才按冻结DEV合同分析，不从部分结果调参或自动追加GPU。

## 原件

- [reports/cara_DEV128_A6000_GPU_actual_launch_20261026.json](../reports/cara_DEV128_A6000_GPU_actual_launch_20261026.json)
- [reports/cara_DEV128_A6000_technical_admission_20261026.json](../reports/cara_DEV128_A6000_technical_admission_20261026.json)
- [reports/cara_DEV128_A6000_central_admission_20261026.json](../reports/cara_DEV128_A6000_central_admission_20261026.json)
- [reports/cara_DEV128_A6000_acceptance_schedule_20261026.json](../reports/cara_DEV128_A6000_acceptance_schedule_20261026.json)
- [reports/cara_DEV128_A6000_storage_20261026.json](../reports/cara_DEV128_A6000_storage_20261026.json)
- [reports/cara_DEV128_prelaunch_dual_exposure_reviewed_20261026.json](../reports/cara_DEV128_prelaunch_dual_exposure_reviewed_20261026.json)
- [reports/cara_DEV128_full_four_card_CPU_accepted_r4_20261026.json](../reports/cara_DEV128_full_four_card_CPU_accepted_r4_20261026.json)
- [reports/cara_DEV128_full_two_card_CPU_accepted_r4_20261026.json](../reports/cara_DEV128_full_two_card_CPU_accepted_r4_20261026.json)
- [reports/cara_DEV128_dispatch_controller_CPU_20261026.json](../reports/cara_DEV128_dispatch_controller_CPU_20261026.json)
- [reports/cara_DEV128_A6000_direct_authorization_20261026.json](../reports/cara_DEV128_A6000_direct_authorization_20261026.json)
- [reports/cara_DEV128_A6000_preflight_20261026.json](../reports/cara_DEV128_A6000_preflight_20261026.json)
- [reports/cara_DEV128_CPU_transfer_cancelled_before_stage_20261026.json](../reports/cara_DEV128_CPU_transfer_cancelled_before_stage_20261026.json)

13:45技术补充：[原件](../reports/cara_DEV128_A6000_technical_followup_20261026.json)确认首条路径RUNNING、0失败，222独占样本无违规、最大间隔2.362秒，跨盘遥测新鲜度1.397秒；不读取部分科学结果。

## GMSD并发协调：采集阶段继续等待

依据冻结执行源码，96条QUALITY路径同样提供完整请求时钟，不只有24条重复路径计时；计时包括方法安装、guarded pipeline、视频写入及清理。EXCLUSIVE_PROCESS只隔离本GPU上下文，不隔离主机CPU、内存带宽和I/O。固定顺序没有外部作业的暂停/窗口握手，因此不能把warm、两路径之间或诊断间隙承诺为安全加载窗口。

GMSD线程报告主机MemAvailable约30.5GiB、其T5构造转换瞬时模型张量约23.12GiB，原准入门槛40GiB；这些数值仅归因于对方报告，本轮未重新测量。近期PSI为0与另一张GPU空闲均不能证明新增加载不会影响本卡或满足原40GiB门槛。

协调结论：CARA采集计时期间，GMSD保持等待，不新增T5加载和标签任务；不暂停或改变CARA。原GPU子进程退出、账单形成并本地结算、锁释放后，才可重新评估非计时阶段并发。届时仍须fresh满足GMSD原40GiB准入，保留CARA评分8GiB/2CPU资源与系统余量，读取实际post子进程CPU affinity以免重叠，并核验共享内存/IO可承受；不能只靠绑核或单次快照保证没有干扰。不能确认则等CPU评分结束。GPU释放后评分不再测推理延迟，但有10小时上限，不能忽略评分资源。

本条只记录本任务的协调条件，不新增GMSD授权、不降低任何门槛、不修改运行stage，也不主动跨对话发消息。原始机器记录：[协调原件](../reports/cara_DEV128_GMSD_shared_host_coordination_20261026.json)。

## 17:41–17:42技术进度（非半程替代）

2026-10-26 17:41–17:42实际技术观察：DEV128已完成55/128、1运行、0失败。两卡GPU1原runner仍为唯一EXCLUSIVE_PROCESS上下文，原guardian/supervisor/runner/container与锁正常；6627独占样本无违规，最大间隔3.501秒。输出卷可用30.73GiB，跨盘日志新鲜度1.56秒。最近20完成文件间隔均值259.02秒，仅技术预测今晚23点前后完成采集，释放后CPU评分原预测8.56449h/最多10h，暂估明早7:30–9:30具备完整收件条件。原19:26半程和明日10:04终态保持，半程按新节奏再调整；未读取部分科学结果。

文件名1742/1743/1744为标签，实际时间以observed_unix为准。原件：[cara_DEV128_A6000_technical_progress_20261026_1742.json](../reports/cara_DEV128_A6000_technical_progress_20261026_1742.json)、[cara_DEV128_A6000_progress_capture_20261026_1743.json](../reports/cara_DEV128_A6000_progress_capture_20261026_1743.json)、[cara_DEV128_A6000_progress_pace_20261026_1744.json](../reports/cara_DEV128_A6000_progress_pace_20261026_1744.json)。采集节奏仅来自已完成request文件mtime，不读取分角色时钟、视频或评分；未启动CPU评分。运行约4.09小时是墙钟，不冒充已结算GPU账单。

## 独立四卡窗口协调（2026-10-26 20:17）

GMSD线程提出在独立four_card主机的GPU1或GPU3执行原900秒标签采集、阶段间CPU验收、原600秒配对测量。本聊天fresh只读中央CARA账本：有效执行预约仅为两卡DEV128外部包12GPUh，另保留旧两卡16.5责任；所询四卡两UUID没有CARA优先预约。E1仅本地准备、无GPU授权或预约。

从CARA资源协调侧，同意本轮在上述四卡UUID中仅选一张的窗口；不是新GMSD执行授权或预算，执行线程须核对自己的直接用户授权、原累计范围与账本，并fresh核验UUID/PID/锁/RAM/磁盘/资产/hash。未把对方20:15空卡报告当作本方实际准入；未读取或改写GMSD账本。CARA余额不能转给GMSD。

两卡DEV128的禁加载条件不变，本次不得使用两卡传输/计算。两技术阶段累计GPU不超过原25分钟，不重置已用量；按原阶段边界退出上下文、释放锁、结算费用，空闲时才恢复模式。阶段间CPU验收失败或资源变化则不能继续。若下一阶段前CARA有新的明确授权，阶段边界优先交还，不驱逐运行中的进程；没有授权的E1准备不抢占该窗口。

[只读预约核对与协调原件](../reports/cara_GMSD_four_card_window_reservation_check_20261026.json)。本轮没有GPU操作、跨对话发送消息或更改DEV128验收。
