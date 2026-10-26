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

### 四卡窗口释放回报（20:39收悉）

GMSD线程报告原标签阶段30编码/60场、298.964秒，阶段间CPU182场/91context通过；测量阶段四臂8step/48F/16 backward/512重算/4checkpoint、444.418秒。报告两阶段成功退出、容器不存在，四卡GPU1无计算进程、共享UUID锁无持有者，其自身中央账本已结算且预约为空，总费用0.20649492322156826GPUh；秒数求和换算一致。

本条是对方执行线程的完成/释放回报，不是本聊天重新核验设备空闲或独立接受GMSD实验；不把该费用计入CARA账本。GMSD仍在四卡以2CPU/4GiB完成checkpoint字节/结构及报价终验，因此不能称其全部CPU验收已完成。该GPU协调窗口关闭；新的GPU任务须按原授权范围与fresh准入另行判断，不能复用本次窗口。两卡DEV128及半程/终态安排不变，未发送跨对话消息。

[释放协调原件](../reports/cara_GMSD_four_card_window_release_reported_20261026.json)。

### GMSD RA1新的正式四卡窗口（2026-10-26T21:30:02.277774+08:00）

对方报告新增直接用户授权并请求RA1四臂各240步/总960步。本聊天fresh只读四卡：GPU1为23MiB、GPU3为24MiB，均无compute app；MemAvailable 79.08GiB，/data20t普通用户可用约1025.92GiB。CARA中央活跃预约仍仅两卡DEV128外部12h包加旧16.5h责任，四卡GPU1/3没有CARA优先预约；E1仍未授权GPU。共享锁本轮未独立检查，由执行方fresh准入。

从CARA资源协调侧明确放行本次新的单GPU四臂窗口，优先GPU1以沿用其先前测量设备；GPU3也没有CARA保留，但切换仍须自己的主机/设备绑定。4CPU/32GiB容器、host至少40GiB和磁盘48GiB的准入门保持。3617秒/约1.005GPUh只是对方报价预测，实际hard cap须在GMSD原剩余额度内登记；原RA1总10800秒/每臂2700秒及历史测量费用继续计入。未复用旧25分钟窗口，也没有转移CARA预算或代替执行线程核实用户授权。

两卡DEV128继续不受GMSD加载/传输/计算影响。若下一臂前CARA获得新的明确执行授权，在注册的臂/checkpoint边界优先交还，暂缓下一臂；不驱逐或强行中断当前进程。全部完成或原安全预算触发后释放GPU/锁并结算，不能自动追加后续科学训练。本聊天不派发、不改账本、不发送跨对话消息。

[四卡只读观察与新窗口协调原件](../reports/cara_GMSD_RA1_four_card_window_readonly_20261026.json)。

## GPU采集结束、CPU评分与CAP-1窗口申请复核（2026-10-26T23:39:01.384480+08:00）

fresh只读原句柄：128/128完成、0失败，原GPU runner退出；15335独占样本无违规、最大间隔3.501秒。原单调账单33901.4129568秒/9.417059154666GPUh已形成，本轮未执行中央结算，不称完整科学或财务接受。CPU post实际2026-10-26T23:02:05.475115+08:00启动，PID3966891/start632182898，affinity为0–1，原2CPU/8GiB/10h不变。80组LPIPS与40/288质量评分文件已存在；只数文件，不读取分数。GPU1仍Exclusive_Process，由原guardian负责后续恢复，本次不改模式。原10月27日10:04终态检查不变。

主机MemAvailable52.14GiB，内存PSI近期0，IO PSI avg60约0.31%；这是时点观察，不是并发无影响证明。GMSD新请求为CAP-1原20层182forward、900秒帽、GPU0、4CPU/32GiB、不加载T5、不训练；来自对方消息，非本方新增授权。允许继续本地准备原生入口CPU验证方案与同机报价，并在完成后重新申请协调窗口；当前不授予双卡GPU或高负载CPU启动窗口。须先证明避开CARA评分0–1核、完整8GiB评分包和系统余量、原40GiB准入及加载I/O边界；不能确认则等评分结束。两台独立主机的旧GMSD窗口不自动延续到本次。

原件：[技术观察](../reports/cara_DEV128_A6000_GMSD_window_technical_20261026_2340.json)、[评分资源](../reports/cara_DEV128_GMSD_CPU_scoring_resource_review_20261026.json)、[协调结论](../reports/cara_GMSD_CAP1_two_card_preparation_review_20261026.json)。不分析DEV部分结果，不改运行stage，不新增预约或跨对话发送。

### CAP-1改用独立四卡窗口（2026-10-26T23:53:05.518522+08:00）

GMSD报告35项CPU检查通过，双卡缺244项约200MiB输入未传输，四卡247项已有；这些准备结果由对方负责独立验收。本聊天fresh四卡只读：CARA中央预约无四卡GPU1/3，E1尚无GPU执行授权/预约；GPU1 23MiB、GPU3 24MiB且无计算进程，RAM约81.68GiB，磁盘约990.75GiB。锁仍由执行方fresh核验。

从CARA资源协调侧允许四卡独立CPU验收准备及随后原CAP-1单GPU窗口，优先GPU1；仅原20层182forward、900秒累计帽，4CPU/32GiB和主机40GiB门保持。原生入口、同机完整报价及对方直接用户授权/原账本必须先通过，不能重置此前CAP费用，也不续用旧RA1窗口。本条不授予新GPU权限或预算。

两卡评分期间本次不安排200MiB补齐、CPU验证或GPU加载：既有独立四卡可用，优先避免同机I/O与CPU竞争，而不是断言200MiB传输必然有害。保留CARA CPU0–1及其SMT兄弟40–41的保护建议（SMT拓扑来自GMSD报告，本轮未独立核实）。两卡DEV128不改变、不读取部分分数，10月27日10:04终态检查保持。

[四卡资源与协调原件](../reports/cara_GMSD_CAP1_four_card_window_readonly_20261026.json)。本聊天无GPU提交、账本修改或跨对话发送。
