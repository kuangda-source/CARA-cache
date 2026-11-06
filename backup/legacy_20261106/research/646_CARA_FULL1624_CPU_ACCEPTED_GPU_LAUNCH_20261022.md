# 完整1624采集：CPU已接受，四卡GPU任务已启动

**当前进度：完整生产CPU已独立接受；10月22日22:13在空闲GPU3启动原完整采集卡。** 这批实验采集自动策略所需的真实区间误差和动作成本。它接续已完成的BANK24修正机制与冻结门控分析；自动生成策略的收益由后续PG-P1至P4检验。

| 阶段 | 当前结果 |
|---|---|
| BANK24六新DEV | 全24视频和12评分已接受；[科学结果](644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md) |
| 完整1624 CPU R2 | 三条命令均退出0，28路径/4060重载格/26040试验、4真实请求/12拒绝及FD锁证明通过 |
| 完整1624 GPU | 已启动；22:19:22原runner已进入warm_1_CONTROL实际采样，GPU3约13661 MiB/100%利用率，0/14完成、1在运行，无日志错误 |
| 自动策略比较 | 等完整原件、参照相等与费用接受后，接既定PG-P1→P2→P3→P4 |

## 本卡范围与时间

原4CAL、1624正式格、14完整路径（12正式+2warm）、2030含warm总格、13020成对读出试验、504普通pairs/1008CFG、单次模型加载保持。已具体批准整卡上限12 GPUh；完整规划9.956389 GPUh，实际费用由终态账单给出。

实际启动：2026-10-22 22:13:05.114752 Asia/Shanghai。半程最早2026-10-23 03:11:46，安排03:12；全程最早08:25:28，安排08:26。半程只查原任务技术进度；若提前退出，保留真实完成/失败状态与实际费用，按实际证据接验收。未知只恢复原句柄，不重派。

四卡现场GPU0/1有任务，选无compute进程、24 MiB的GPU3；磁盘余354302070784字节、MemAvailable 77053779968字节通过整卡准入。GPU启动后自身UUID锁持有、supervisor/runner/原容器均活，原单写账本预留本卡12 GPUh。池used118.746008291427/reserved28.5/available78.753991708573；reserved含旧两卡16.5未知责任预约，不充已发生费用。

## 原件与复现入口

- [CPU终态](../reports/wc_policy_assets_full1624_fourcard_CPU_r2_terminal_20261022_2212.json)：实际22:12:06收件；原容器22:02:40退出0，CPU总耗时922.819849秒，未OOM、未调用GPU。
- [CPU独立接受](../reports/wc_policy_assets_full1624_fourcard_CPU_r2_accepted_20261022.json)：1840件注册源与固定runtime一致；原R1失败保留在[645](645_CARA_FULL1624_CPU_ENTRY_REPAIR_20261022.md)。
- [实时资源](../reports/wc_policy_assets_full1624_fourcard_fresh_GPU_preflight_20261022.json)、[唯一GPU启动](../reports/wc_policy_assets_full1624_fourcard_GPU_launch_20261022.json)、[首次准入观察](../reports/wc_policy_assets_full1624_fourcard_GPU_admission_20261022.json)、[实际CUDA加载观察](../reports/wc_policy_assets_full1624_fourcard_GPU_load_observation_20261022.json)。
- [控制器](../scripts/wc_four_card_policy_assets_r1.py)：半程`capture --mode gpu-halfway`；终态`capture --mode gpu-terminal`后`accept --kind gpu`。`--launch-ref`始终使用上述唯一GPU启动原件，输出使用新文件。

运行身份：`wc-policy-interval-assets-cal4-full1624-ada-r2`；launch `37ab7e89-952b-4ddb-acde-5b20a0fc1295`；source `94fe08832b8feb92ae6235c5b569d615950cf491`。stage `/data20t/gaokuangda/worldcache_workspace/.sync/wc-policy-assets-fourcard-full1624-r2-20261022`。GPU3 UUID `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`；supervisor811837/start946344871，runner811944/start946345336。

旧CPU终态自动化`cara-bank24-2`已改绑本GPU全程；新一次半程为`cara-1624-gpu`。保持正常运行静默、完成/失败/需要行动时通知，避免重复验收。后续PG-P1仍需真实资产接受、CAL_SELECT曝光核对、任意合法mask生产CPU和整卡报价；六DEV不回流调阈值。

22:19:22有界[初始采样观察](../reports/wc_policy_assets_full1624_fourcard_GPU_initial_sampling_20261022.json)确认已越过模型加载、进入首条预热CONTROL完整路径。仅技术状态，未据部分结果调参。
