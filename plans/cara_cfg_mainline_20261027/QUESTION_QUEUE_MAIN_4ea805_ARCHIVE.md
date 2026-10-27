# CARA 问题队列

2026-10-27 R14。执行规则以[流程](../docs/EXECUTION_MODES.md)为准，科学判断以每卡冻结合同为准。费用栏是规划提示，不构成授权。CAL66已完整接受并冻结Shared25-C；DEV128已完整接受；用户暂停IG，预测器—刷新机制线CPU完整诊断见[720](../research/720_CARA_CFG_COMMON_DIFFERENCE_MECHANISM_AND_PREDICTOR_HYPOTHESIS_20261027.md)。

| # | 问题与下一决策 | 状态 | 费用与边界 |
|---|---|---|---|
| Q1 | CAL66：过渡段删D、同Shared全A/限龄A、少步Native；完整验收后冻结一个工作点或停止 | DONE：66/48/156完整接受，冻结Shared25-C | 4.776208 GPUh已中央结算；相对S25-A LPIPS改善15.34%、4/4；原质量/预算筛查通过，见[702](../research/702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md) |
| Q2 | 冻结48组输入的新增使用记录是否触及保护组 | DONE（本次范围内增量清楚）；首次使用前再查 | 0 GPU；16新DEV/16最终确认/16备用不重选；首次使用前补全两端新增记录覆盖，见[增量原件](../reports/cara_new_input_pool48_delta_r1_20261025.json) |
| Q3 | 用最小入口复用现有收件工具，减少逐卡重复工程 | DONE（离线规格与CAL66既有句柄适配）；新卡适配按需做 | 0 GPU；无prepare/launch/retry，不接管CAL66自动检查 |
| Q4 | 冻结方法在16新DEV上是否胜过强规则和少步Native | DONE：完整接受；Shared25-C对S25-A LPIPS改善14.82%，16/16，预算与质量门通过 | 实际9.417059GPUh已结算；最终确认未做，见[716](../research/716_CARA_DEV128_COMPLETE_ACCEPTANCE_AND_FROZEN_DECISION_20261027.md) |
| Q5 | 同模型换步数后，冻结方法/规则能否迁移 | CONDITIONAL：保留CPU可辨识性准备；按V2先确认读出/布局增量再报价 | 旧4–6 GPUh仅规划；不默认批准 |
| Q6 | 20D激进档与时间对应少步Native | DEFERRED；V2先解决机制，Q4正向不自动触发 | 重新完整报价，原α和公平对照保留 |
| Q7 | RA等时间对照、WC固定工作点曲线 | DEFERRED；最终方法冻结后 | 不以不同时间点冒充等时间优势；重新报价 |
| Q8 | 第二骨干可行性与外部方法复现 | CONDITIONAL；V2候选经独立确认后再评估 | 不在当前额度内暗加实验 |
| Q9 | 自身历史shadow是否改变教师代理排序 | DEFERRED；仅方法仍依赖该代理时优先 | 原诊断设计保留，不自动恢复采集 |
| Q10 | GRAPH102可行性修复 | DEFERRED | 旧教师代理搜索未胜强规则，不等于否定全部DP/离线调度；旧报价不作为新授权 |
| Q11 | 再开纯计时卡 | DEFERRED | 原104/112失败保留；当前路线改用预登记成对预算确认，不以“都是噪声”抹去失败 |
| Q12 / E0 | 现存资产、固定sigma、DCTA commit与质量绑定 | 官方DCTA核对、旧12视频Native-relative梯度/固定模糊诊断完成；32文件SHA全集复核通过 | 不新增生成，本地资源先查；[V2.2](cara_predictor_refresh_scout_v2_20261026/E1_V22_AMENDMENT_AND_FREEZE_CHECKLIST.md) |
| Q13 / E1 | 原A与R4的同状态误差机制，是否有可部署增量 | CPU_DIAGNOSED：历史共同/差分方向分离；输出共同项诊断长龄6/6、改善3.93%；新结构仅参考CPU通过，无j1 | 无新GPU；完整成本门不能事后补冻结；[接续](cara_predictor_refresh_scout_v2_20261026/MECHANISM_REUSE_AND_PREPARATION_R1_20261027.md) |
| Q14 / E2 | 先读出验证，再有条件检验布局依赖 | BLOCKED_ON_QUALIFYING_J1：R4_COMMON_LONG是假设，真实生产/成本与新状态未验；不派视频卡 | 原R/I各16逻辑机制输出，完全同身份可合并24唯一输出；整卡参考/warm/评分另报，NOT_READY |
| Q15 / IG | 创新量Scalar/Band的增量 | PAUSED_BY_USER：B1完整结束，当前候选停止，无IG运行；不执行B2/B3 | 实际1.452095GPUh已结算，原结果保留；复用六固定读出不等于重启IG |

| 工程附件 | 后续方法卡同时保存准确去噪＋解码与完整请求时钟 | 双端各18路径CPU接受；GPU时钟未验证 | 无新GPU/预算；[724](../research/724_CARA_EXACT_PAPER_TIMING_DUAL_HOST_CPU_AND_METHOD_HANDOFF_20261027.md)，原完整请求验收保持 |

当前顺序：IG暂停 → 复用E0和完整B1六固定读出 → 原张量CPU完整诊断已完成 → 共同/差分机制已定位 → R4共同输出+A差分的受影响双端CPU已接受，6路径新状态清单/监督成本绑定准备 → 新状态验证后才决定E2。当前无j1，E2不自动启动；不使用DEV128拟合，不重采已有状态。最终确认、迁移和20D保留条件性计划。

## 2026-W43复盘（以下为2026-10-26历史快照，当前状态以上表及718为准）

- 已改变的决策：暂缓GRAPH102与额外纯计时卡，CAL66集中检验强基线、过渡段与少步Native；探索报告质量—实测延迟，最终方法仍按原部署上限确认。
- 最近完整证据：[702 CAL66](../research/702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md)已通过完整验收与原CAL筛查，选Shared25-C；新DEV已启动、尚未完整接受，最终确认未执行。旧104/112及失败不改。
- 本次流程/增量审计/最小入口：新增GPU执行0、预约0、GPUh 0。CPU检查与远端身份扫描不算GPU实验；人工工程工时未可靠计量，不填估计比例。
- 最新保存的DEV128中央准入快照：已用161.396620633628 GPUh，预留28.5（旧未知16.5+DEV128 12），未预约余额36.103379366372/上限226；不是实时或DEV128结算后余额。V2的4/12/10/10仅条件分池，无新预约。
- Q4当前执行见[705](../research/705_CARA_DEV128_A6000_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_SCHEDULE_20261026.md)。半程10月26日19:26，最终检查10月27日10:04，按实际状态调整同一自动化。

2026-10-27增量：[726](../research/726_CARA_COMMON_LONG_PRODUCTION_CPU_NEW_STATES_AND_DUAL_CLOCK_20261027.md)双端真实源CPU通过；新增状态提案6完整父路径/12状态/84位置，规划2.608114GPUh、建议硬3，无GPU授权或预约。原Q13科学门/j1与Q14阻塞状态保持。

R4_COMMON_LONG六路径准备补充：双端整卡组合CPU已独立接受，旧CAL新机制状态、2.608114GPUh规划/建议上限3，GPU未授权未提交；见[727](../research/727_CARA_COMMON_LONG_WHOLE_CARD_CPU_AND_DUAL_HOST_REVIEW_20261027.md)。IG暂停，j1不因工程接受自动产生。
