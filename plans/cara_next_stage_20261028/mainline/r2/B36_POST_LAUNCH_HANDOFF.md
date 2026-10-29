# B36 原运行与完整验收交接

用户于2026-10-29明确批准：**“批准单次 B36，硬限 5.5 GPUh，资源和预算核验通过后就启动，安排半程检查和全程验收。”** [授权原件](B36_USER_AUTHORIZATION_20261029.json)。实际已于 **08:17:37 Asia/Shanghai** 单次开始，禁止重派、重启、换卡或修改运行源/配置。

## 唯一身份和费用

- run：`cara-fast-f19-b36-r1-20261029`；launch：`b684eb05c8674a94ad3dad8187f1c6b9`。
- 实际运行源码：`249aadcb2f33e360520560fea83059293ac77fed`，A基座仍为 `9eaa5eb30c5509810c99a55002b51d6b71da1ef6`，52个执行CPU关键源字节未变。registration SHA：`b72083573f35e2eb653bb2dde0c36b9572e469f1c56c4728eb8659375614c5f7`。
- 主机 `two_card_lan` 经 `four_card`；GPU：原A6000 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
- 项目 `/data20t/gaokuangda/worldcache_workspace`；stage为项目下 `.sync/cara-fast-f19-b36-a6000-r1-20261029`；容器 `cara-fast-f19-b36-a6000-r1-20261029-gpu`。
- 原句柄 PID/start ticks：guardian `878084/652796038`；Docker CLI `878097/652796192`；supervisor `878142/652796209`；runner `878186/652796350`、UID1004。PID必须与start ticks同核对，连接未知只恢复这些原件。
- [原始GPU launch字节](../../../../reports/cara_fast_B36_GPU_actual_launch_r1_20261029.json)；[实际派发](../../../../reports/cara_fast_B36_actual_dispatch_r1_20261029.json)；[原独占上下文观测](../../../../reports/cara_fast_B36_original_context_startup_r1_20261029.json)。该首次观测证明EXCLUSIVE_PROCESS下仅确切runner，仍处于加载/预热阶段，不是完整技术或科学接受。
- 完整20资产/21,348,071,882字节重新核验通过，见[实际准入](../../../../reports/cara_fast_B36_actual_admission_r1_20261029.json)；[32GiB私有SSD及48MiB跨盘journal](../../../../reports/cara_fast_B36_actual_storage_r1_20261029.json)。2CPU/40GiB、禁swap、cores24,25、无网/只读root；90°C保护与释放180秒界限不变。
- [中央唯一5.5GPUh预约](../../../../reports/cara_fast_B36_actual_central_reservation_r1_20261029.json)，four_card为唯一账本，cap226和旧16.5责任保持；预约后可用25.93843472766372GPUh。旧未知财务hold不是设备锁，不删除或重复计为新卡。不得写两卡旧副本、再reserve或按监督器区间二次收费。

原宿主guardian的 `stage/B-billing.json` 是唯一费用依据，按实际单调分配墙钟，包含其准入、容器和释放处理。`B-supervisor-billing.json` 只用于监测连续性；成功失败均结算原实测费用。缺文件、UNKNOWN或没有完成路径不能当作零费用。

## 实际开始后的两个检查

原guardian `started_unix=1793233057.4184854`；原GPU写出的 `B-check-schedule.json` 是计划，外部自动化回执另存，不回写运行文件。

| 事件 | 2026-10-29 Asia/Shanghai |
|---|---|
| 实际开始 | 08:17:37 |
| 预计半程 / 安排检查 | 10:48:16 / **10:49** |
| 预计结束 / 安排验收 | 13:18:54 / **13:19** |
| 原硬截止 | **13:47:37**，不自动延长 |

实际自动化id及初始配置见 `reports/cara_fast_B36_acceptance_schedule_r1_20261029.json`，同一检查的运维跟进策略见 `reports/cara_fast_B36_check_followup_policy_r1_20261029.json`。半程只查原句柄、36分母进度、温度、资源、独占和中央账本，不读或发布部分科学分数。若已经结束，立即按下文收尾，不等预测ETA；无变化保持安静。半程可仅依据原路径计数与已耗墙钟提前同一个终验检查，避免实际提前结束后等待旧预测；不读取部分T_DD或科学分数。终验若仍运行，把同一个检查移到下一次15至30分钟后的可行动终态检查，最晚覆盖原硬限后13:51的释放/验收边界；不能创建新GPU意图、重复检查或修改原硬限。CPU评分仍活跃时，恢复其原句柄并调整同一终验检查继续接受，不重复评分。

## 原终态、唯一结算与CPU评分

本地工作目录 `/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr`。用现有 `scripts/cara_two_card_transport_r1.py` 的ssh/four_ssh；秘密只读既有0600读取器并走stdin，不打印或入Git。不再调用 prepare/provision/reserve/launch。

运维状态使用 `scripts/cara_fast_b36_dispatch_r2.py status --output <新的唯一reports路径>`。终态捕获使用：

```sh
python3 scripts/capture_cara_fast_b36_terminal_r1.py --launch reports/cara_fast_B36_GPU_actual_launch_r1_20261029.json --output reports/cara_fast_B36_terminal_<唯一时间>.json
```

捕获绑定原launch字节和入场源码；原GPU仍活跃时只返回运维信息。真正结束后按原 `B-terminal-capture-intent.json` / `B-terminal-capture.json` 的唯一读者恢复，1CPU/1GiB、900秒界限；超时先查原读者PID/start ticks、intent和回执，不重开。全部原进程/容器终态及关闭证据确定后，成功失败均在 **four_card中央** 调用原 `settle_original`，仅用原guardian的实测bill并保存同一原settlement文件。连接中断先恢复中央原job/回执，不能重复reserve或用新快照替换manifest绑定的原settlement。

四卡已接受的CPU stage为 `/data20t/gaokuangda/worldcache_workspace/.sync/cara-fast-B36-dispatch-CPU-ada-r23-20261029`，其52关键源仍与实际B一致。可将捕获复制到新的私有输入目录，用固定原CPU环境和 `scripts/postprocess_cara_fast_b36_r1.py settle` 在该中央主机结算；实际source要逐项比对。禁止在Mac或两卡副本结算。`release` 必须验证36完整分母、原参数/精度/源码、干净双时钟、全程独占与热界、所有原件SHA和真实释放/模式恢复。技术失败保留失败与费用，不能进入科学评分或后续GPU。

技术接受后用原 `postprocess_cara_fast_b36_r1.py manifest` 派生恰好32逻辑位置；完整manifest字节放在原B输出 `B-score-CPU/manifest.json`，其SHA不得改变。32位置＝24个新B产物＋8个原A产物；只执行26新评分，六份已接受A指标/93帧曲线原样复用。原A32的12对评分与真实一次冻结不得重做。

唯一CPU评分入口：

```sh
python3 scripts/dispatch_cara_fast_b36_score_cpu_r2.py --launch reports/cara_fast_B36_GPU_actual_launch_r1_20261029.json --capture <原B捕获> --settlement <原中央结算> --manifest <同字节完整manifest> --output <新的唯一CPU启动回执>
```

先核对 `B-score-CPU-intent.json`、`B-score-CPU-launch.json` 及 `<原stage名>-B-score-cpu`；已有句柄仅恢复。固定2CPU/8GiB、禁swap、cores26,27、无GPU/网络、root只读、四小时上限；原A/B视频与源码只读、仅评分目录可写。原scorer无修改，只计算26对，禁止重评六份A指标。

CPU退出后，用原捕获器附加 `--score-manifest` 读取原评分句柄，再由 `postprocess_cara_fast_b36_r1.py accept-scores` 独立接受完整32、原26输出与六原A行、93帧/92时序对/PTS、逐帧曲线、资源和真正退出。随后运行[完整汇总](B36_ANALYSIS_READINESS.md)及[图表导出](B36_FIGURE_READINESS_R1.md)；不得由部分结果调规则。按输入内正式＋登记重复均值、再输入等权，保持T_DD/T_request及FIT原A敏感性独立。

## 结论和完成清理

WC_T006、RA_T1保持原FIT的 **UNMATCHED**，Native22为MATCHED；不重新冻结、补扫或强称三个家族同时间。两个CHECK属于旧CAL内部留出，不能升级为独立DEV或部署结论。完整结果、费用和科学解释分别接受，更新canonical状态、WORKSTREAMS及新的研究记录后生成导航，精确提交owned路径并推送，保留并行S/Q工作。

只有原B完整链接受后才删除剩余两项检查；真实失败则唯一结算并通知、删除多余检查，不重派。整个监控/验收不启动任何其它GPU卡，也不改变现有预算、输入、mask、alpha或阈值。

## 2026-10-29 半程连接中断交接

见 [原句柄UNKNOWN运维回执](../../../../reports/cara_fast_B36_halfway_connection_unknown_r1_20261029.json)。原FRP端口拒绝、office_tailscale超时，直连及临时独立visitor也未取回远端；共享FRP与SSH配置未更改。09:18的14/36、0失败只是最后已知计数，当前温度/独占/资源/账本/终态均UNKNOWN。不得将未知升级为结束、失败或零费用，原5.5GPUh责任与身份保持。半程b36已删除；只保留同一个b36-2，13:35先恢复原连接和句柄，若仍未知则同一检查续至13:51覆盖原硬截止后边界。原13:47:37硬截止不变，无GPU或CPU重新派发。

## 连接恢复及原GPU已接受，当前只续验CPU

[755最新记录](../../../../research/755_CARA_B36_CONNECTION_RECOVERED_GPU_ACCEPTED_CPU_SCORE_20261029.md)与[恢复回执](../../../../reports/cara_fast_B36_original_connection_recovered_r1_20261029.json)取代上节UNKNOWN当前状态。原B36已于10:40:41正常退出，完整36/36、0失败、3797次监测、最高88C，原四句柄全退出、Default恢复及原件/源码/精度/双时钟接受；原guardian实际2.384553982338661GPUh已中央唯一结算。原settlement见 `reports/cara_fast_B36_original_central_settlement_r1_20261029.json`，保持同字节，不再产生另一份结算快照。

原连接现在通过独立的本机隔离代理恢复；共享FRPC、TUN与全局SSH配置未改。执行现有scripts时只给该子进程PATH前置 `.sync/b36-original-transport-recovery-20261029/bin` 的绝对路径，包装器继承原已固定主机密钥。私有通道core PID16947、FRPC PID16948、SSH localhost22619；配置和日志仅在忽略目录，不能入Git。可恢复这些连接进程，禁止触碰原实验。

CPU已于13:32:19**单次**启动，见 `reports/cara_fast_B36_original_score_CPU_launch_r1_20261029.json`。原CLI PID969049/start_ticks654684263、容器init PID969093/start_ticks654684280、容器 `cara-fast-f19-b36-a6000-r1-20261029-B-score-cpu`，2CPU/8GiB/禁swap、cores26,27、无GPU/网络/root只读均已观测。manifest为 `reports/cara_fast_B36_original_score_manifest_r1_20261029.json`，SHA057277a410b602f64c83df800b07bb50f33b291987cb6e837f246808231903fa。只恢复原评分，不可重派；26新对＋六原A组成完整32，A32十二对/冻结不重做。仅保留同一个b36-2于13:55续验原CPU，完整后按上文接受、汇总、导图、canonical和提交推送，再删除终验。
