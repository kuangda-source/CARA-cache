# 少一次D三臂：完整CPU接受，GPU0已单次准入

2026-10-17北京时间。E0剩余分析、整卡设计和成本见[553](553_WC_E0_CPU_COMPLETE_CAP226_AND_DROP1_FULL18_PREREG_20261017.md)；本文件记录实际执行，**没有新视频或方法收益结论**。

## 1. 已完成的CPU与准入

[完整CPU原件](../reports/wc_drop1_full56_actual18_CPU_collection_20261017_2129.json.gz)与[独立接受](../reports/wc_drop1_full56_actual18_CPU_independent_acceptance_20261017.json)：1674份payload与原runtime核对；两个flow共56条完整数值路径（48新audit/lean、8旧前密控制），每条36更新；旧前密36guided、最终latent/actions/A历史/来源历史及Toy RGB一致，audit关闭保持数值，全部owner释放。实际生产入口、typed四请求、真实校准所有32个非D位置、预算锁五项与整卡合同四项测试全部通过。四命令退出0，共358.104秒，CUDA未初始化、无权重/GPU/账本写。

CPU21:20:38单次派发；21:23:51查收仍在第二flow，原180秒估时偏短，保存原回执后改21:29一次查收，未重启或循环查询。[只读新鲜资源](../reports/wc_drop1_full18_fresh_resource_and_budget_20261017.json.gz)：GPU0为RTX A6000/8.6、398MiB/无compute进程、自身锁可用，磁盘可用361.53GiB，足以覆盖完整18原件。

[原GPU启动](../reports/wc_drop1_full18_GPU_launch_20261017.json)于21:30:48单次派发；首次启动快照仍在监督器来源验证、未预留，保留为ADMISSION_PENDING。21:31:29完成锁内准入，后续[原准入快照](../reports/wc_drop1_full18_original_admission_20261017_ready.json.gz)和[独立接受](../reports/wc_drop1_full18_independent_admission_acceptance_20261017.json)确认原三句柄、当前source/config/CPU签名、1674源、原runtime、自身UUID锁及完整2.25GPUh预留。[CPU绑定复核](../reports/wc_drop1_full18_admission_CPU_binding_crosscheck_20261017.json)另核实际生产CPU、数值证明和同一registration/config/source。

## 2. 原任务身份与完整范围

| 项目 | 实际绑定 |
|---|---|
| 卡 | WC-DROP1-CAL4-THREEARM-FULL18-R1-20261017-A |
| run | wc-drop1-cal4-three-arm-full18-r1 |
| source | e76b4f8b934bb07bf045e6083f36eddb4711640d |
| stage | .sync/wc-drop1-production-r1-20261017 |
| launch_id | 1d847560-a411-4272-8e4c-0b07844a664c |
| supervisor | 1515148 / start_ticks 553875240 |
| worker | 1515544 / start_ticks 553879314 |
| CPU post watcher | 1515149 / start_ticks 553875241 |
| GPU | GPU0 / GPU-de9a5370-cd87-0f1c-a48e-288888777dd3 |
| config SHA | 8c2a0d512f8ccc4f8a7a57a237949fcee56f4cb8dde9bfd94cd032369669b4ba |
| registration SHA | 2532bde9cc5ba858ac3018f3bbe82e88be2e459b8e5e985734c78659f42bc134 |
| actual production CPU SHA | 2349714ee7f4ef03094fc58a986fc330436af3b68dcec1975ce9631ac011d362 |

四原CAL/seed0×三方法：**S26-C=26D10C，S25-C=25D11C，S25-A=25D1A10C**。只删除实际更新21处D，A使用冻结单位增益/共享alpha1；不调参。12正式＋6完整预热＝18条完整路径，648pairs/1296CFG、一次加载、零新教师/Native。每请求重置原始随机/缓存状态，保留原guardrail、真实D历史、年龄支持及36更新。

全部18路径实际加载/预热/采样/维护/guard/write成本计费；预计1.758860873GPUh，计费上限2.25。**累计cap226**，origin79.996377372和所有历史支出不变；实结109.394798124、当前预留2.25，可新准入余额114.355201876。预留不是实费，本卡实际费用尚空。

## 3. 已安排的两次查收

[自动化登记与本地核对](../reports/wc_drop1_full18_two_check_automations_verified_20261017.json)确认两个独立一次性heartbeat已ACTIVE，避免RRULE时间交叉造成多次调用。当前只跟踪原任务，不循环监听。

| 时点（北京时间） | 范围 |
|---|---|
| 10月17日22:46（不早于22:45:48.890315） | 仅技术半程：原PID/start/source、18分母/状态计数、错误、显存/磁盘/锁/原财务；不读取质量或方法耗时 |
| 10月18日00:01（不早于00:00:48.890315） | 原GPU/post完整终态、18分母、所有适用原件与93帧评分、实际费用和自身GPU释放 |

最终一次执行：

```bash
.venv/bin/python scripts/capture_wc_drop1_full18_r1.py --mode terminal --output reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz
.venv/bin/python scripts/analyze_wc_drop1_full18_r1.py --capture reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz --output reports/wc_drop1_full18_independent_acceptance_20261018.json
```

若GPU或CPU post仍在跑，根据该次回执的剩余工作量另约一次并结束；不能重派、补拒绝、缩卡或改原stage。连接未知不当任务终态。半程/最终各完成后删除对应自动化。

## 4. 最终必须回答的问题

三组warm各两次的36guided严格等价，四条S26-C与原N06的终态/actions/A_history/93RGB控制；全部18owner释放，真实A仅21、C/A不伪写D；所有适用正式视频与匹配原Native逐93帧LPIPS独立复算。拒绝、技术失败、缺参考均保留，不按场景拼赢家。

逐场景并列三比较：**S25-A对S25-C，S25-A对S26-C，S25-C对S26-C**。报告实际秒数、主计时边界、LPIPS、baseline秒数÷candidate秒数、真实D/A/C次数。A能否承接一次D、删掉D本身是否已够、时间差是否兑现分别解释。

每配置每场景一次正式计时属于开发诊断，不能替代N08重复clean测速，四旧CAL也不是新输入泛化。若有新的正向配置，再讨论独立确认；当前只完成原18卡，不自动开N09/N10或恢复F/B/P/历史网络。
