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
