# N07完整180修复卡已获批并启动，09:24／17:24查收

2026-10-17。**用户已明确回复“批准完整180修复卡”；完整新卡已经在GPU0准入，原监督、运行器、CPU后处理守候进程及整卡预算预留均已独立核对。** 本卡用于完成冻结方法与强基线的新输入、双seed共同测试，核实开发集观察到的保真—费用优势能否推广。当前是运行与准入结果，正式质量和速度结果仍待完整原件验收。

## 本次执行范围与实现

卡号`WC-PAPER-N07-REFUSAL-REPAIR-FULL180-R2-20261016-A`；原8个提示词×seed17/43×10方法，**160正式＋20完整预热，共180路径**。方法为Native35、Native26、WorldCache半阈值、RA半阈值／默认／双阈值、A_NO_P、TABLE_PHASE_H1、FRONT_DENSE_C、FRONT_DENSE_A。完整6318pairs／12636CFG、一次模型加载、零在线教师，保持原提示词、输入、参数、36步完整采样mask和guardrail。

修复只处理零步文本拒绝的边界：合法拒绝如实留在完整分母中，不再误要求它完成36步。原失败R1所有拒绝／失败／未到达和实际费用均保留，新卡不拼接旧partial。源版本为`6e10aa31197b4c137705b9117090c3a4e538e863`，实际服务器九命令CPU和1750源SHA已接受；本轮没有更改在途stage。

[具体整卡批准](../reports/wc_paper_N07_refusal_repair180_R2_direct_human_authority_20261017.json)绑定用户回复、完整范围、source／CPU／config SHA和独立launch_id。旧R1批准不复用，累计113GPUh窗口不重置。

## 原任务身份与初次准入

- 实际派发：**2026-10-17T01:23:40.791354+08:00**，北京时间。
- 原run：`wc-paper-n07-refusal-repair180-r2`，launch_id：`bbdd6983-8dd3-4572-a2dc-05bb365c4ea9`。
- GPU0：`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`，A6000。
- supervisor：1212464／start_ticks546632431；runner：1212599／546636405；CPU post watcher：1212465／546632437。
- 独立stage：`.sync/wc-paper-n07-refusal-repair-production-cpu-r1-20261016`。

第一次快照在派发后18.5秒取得，当时原supervisor仍做启动校验，未写准入结果；其原回执保留。事前登记启动后三分钟以后仅复核一次原句柄，得到[ready快照](../reports/wc_paper_N07_refusal_repair180_R2_ready_admission_capture_20261017.json.gz)及[独立接受](../reports/wc_paper_N07_refusal_repair180_R2_ready_admission_acceptance_20261017.json)：1750payload SHA、三个原PID/start_ticks、完整授权、v2预留及自身UUID锁全部通过；观察时显存24889MiB。没有重复派发，也没有读取科学partial。

[原启动回执](../reports/wc_paper_N07_refusal_repair180_R2_GPU_launch_20261017.json)、[原CPU接受](../reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_independent_acceptance_20261016.json)、[准入复核与两次时点](../reports/wc_paper_N07_refusal_repair180_R2_admission_followup_and_two_collection_times_20261017.json)均保留。

## 已安排的查收

| 查收 | 北京时间 | 仅在该时点核对 |
|---|---|---|
| 半程技术检查 | **10月17日09:24** | 最早09:23:40.791，核原句柄／源码／显存／锁／技术错误和全部180分母；不报告科学partial |
| 完整原件验收 | **10月17日17:24** | 最早17:23:40.791，一次收原件、全部有效兼容视频93帧RGB／LPIPS、分组统计、真实费用和自身锁／GPU释放 |

新heartbeat为`worldcache-180`，以实际派发时间＋8h／16h设门，取整到下一分钟。已将半程入口绑定ready准入原件。[应用后的自动化核验](../reports/wc_paper_N07_repair180_R2_admitted_automations_verification_20261017.json)保留实际设置，期间不持续监听。若到时未完，按剩余工作量另约一次；若观察失败，只检查本任务连接，不重启服务器任务。

原失败R1的`worldcache-26d`仍按**05:30**做原卡完整失败验收，与本R2分开。拒绝、技术失败和缺失均保留，CPU后处理退出0不能单独算整卡科学接受。

## 预算与后续主线

| 项目 | GPUh |
|---|---:|
| 累计cap | 113.000000000 |
| 实际已结算 | 96.278971908 |
| 本卡完整预留／计费上限 | 15.055555556 |
| 本卡预留后可新准入 | 1.665472537 |

以上来自原准入时的服务器v2账本。**预留不是实际支出**，结束后按原监督真实全wall费用加法结算；原origin79.99637737158223及历史job保持。

完整R2验收后按原主线进入N08独占重复clean测速，再接N09部署测量／N10完整自动质量。N08完整40路径预计3.6275GPUh，届时必须按本卡实结后的fresh余额准入，当前预留余额不能承诺覆盖。严格少于12GPUh且余额足够可按既定计划自主；达到12GPUh或余额不足时确认完整卡，不拆缩。重CPU评分模型避免与本GPU／clean测速并发；F/B关闭，未新增训练、人评或OMR。

## 独立资源任务的已到时技术检查

N10固定ViCLIP直连R4的[一次半程技术回执](../reports/wc_paper_N10_direct_R4_midpoint_health_20261017.json)已保存：原进程消失、registration与两worker SHA一致，writer记录**204／204段、1710545812字节、零HTTP失败**。这次没有重新做完整权重哈希或加载模型；原**01:54完整独立大小／SHA验收**仍由`p-acr-cpu`查收，不能把writer摘要当资源或模型接受。

本轮新增一张完整GPU卡，原失败R1、原资源stage及历史审计均保持；论文结果栏仍等待完整视频与质量／费用接受。
