# CARA 问题队列 R20

2026-10-30 主线更新。现行依据为[最新总计划](cara_next_stage_20261028/01_Master_Experiment_Plan.md)、[S/Q修订](cara_next_stage_20261028/02_SQ_Method_and_Experiments.md)和[接收/两对话分工](cara_next_stage_20261028/08_REPOSITORY_RECONCILIATION.md)。原R16[逐字归档](cara_next_stage_20261028/QUESTION_QUEUE_BEFORE_R17.md)。本轮仅更新主线；S/Q 行保留所属对话原登记，最新状态以其独立回执为准。已完成执行以原接受为准，后续提案不授予新 GPU。

| 阶段 / 负责人 | 当前状态 | 下一步与边界 |
|---|---|---|
| P0 · 主线 | A32 完整32条与12对评分接受，基线已一次冻结 | 保留原32条、冻结与双时钟；GPU和费用均已闭环，旧WC73不重派 |
| F19 · 主线 | B36 完整36条、32评分位置和正式图表接受；32条单人诊断完整接收 | 使用R2原数值及760诊断记录；四旧CAL、原冻结、WC/RA FIT UNMATCHED和三条播放元数据缺口保持，不新增科学门 |
| S-FAST19 · S/Q探索 | 生产profile的170共同结构候选；尚无全支持mask | 完整风险缺口保持；BR/DIAG/CFG共同语法，见S/Q R3状态；不外推12保存状态 |
| Q0-Q1 · S/Q探索 | 双端CPU控制与源码绑定完成；原C CPU未过历史GPU逐值门 | 同硬件CUDA数值控制仅提案；当前codec评分0，固定Shared25-C及旧资产不重采 |
| A-SQ-FAST · S/Q探索 | 仅明确缺口后准备采集卡 | 绑定新父策略的108标签/56额外Dense pair与存储；解决F19 raw和Q25布局兼容问题，共同费用只计一次 |
| S-END / Q-END · S/Q探索 | 各自条件晋级，不互设成功前提 | 不同合法mask或实际同bytes读出证据后，冻结最小完整视频比较与强基线，再报价申请 |
| F18 / Q5 · 主线，S/Q提供冻结规则 | F18与Q5 Native50参考组件双端CPU通过；后者实际51更新/102次CFG调用 | GPU保持S优先；冻结S规则、50步保护/年龄映射与可辨识比较，再准备完整物理范围/生命周期/报价，组件不作整卡准入 |
| WAN / FINAL · 主线 | 迁移后置；原最终16/备用16已双端身份复核，登记范围未见执行 | 保留原池，首次使用前再做增量核查；冻结方法/checkpoint/协议、额外seed子集和完整报价后再决定 |
| B-S / B-Q / B-E · 按失败位置指定单一负责人 | 休眠；当前未启用 | 最多一个备用进入新GPU探索；不自动恢复IG/R4/GRAPH/F/B |

## 原件与停止边界

| ID | 问题 | 已完成范围 | 边界 |
|---|---|---|---|
| DONE / CAL66 | 位置/读出/少步Native筛查 | ☑ 完整66接受，冻结Shared25-C | 已曝光CAL，非独立确认 |
| DONE / DEV128 | 固定布局16新DEV | ☑ 完整128接受，主比较LPIPS改善14.82% | 已成后续选择的开发证据；不得再作A最终确认 |
| DONE / AGE3-REVIEW | A限龄版质量权衡 | ☑ 原质量/平均预算界通过，对C LPIPS改善6.68% | 事后门分析，Native26 MUSIQ区间未过；见734 |
| DONE-STOP / R4-R2 | 新状态共同项修正 | ☑ 6路径84位置完整，科学门失败 | 仅比A好1.65%、一输入退化；1.619241GPUh结算；不进E2 |
| PAUSED / IG | Scalar/Band创新量 | ⏸ 用户暂停；B1结果保留 | 不执行B2/B3，不借新名字恢复 |
| DEFERRED | 旧GRAPH102、F/B、旧在线门控、额外纯计时、单支刷新、本体量化 | ⏸ 暂停/关闭 | 旧代码和失败原件保留，不自动重开 |
| DEFERRED / 20D | 更激进配额 | ⏳ 后置 | 主线正向与完整公平基线后再报价，不取消历史计划 |

WC73已按736/738热停并结算，原完整A门未形成、B未启动，不重派原73槽。上述F19为高速可行性候选；S优先19D，Q先固定25D，原25D S方案保留。

Fidelity-v2仅用于未来逐卡冻结提案；旧质量门、原α、完整请求双预算与结果不改。DEV128已成为后续选择的开发证据，原最终输入继续保护。

B36原结算快照为cap226、used180.44611925467495、reserved16.5、available29.053880745325046 GPUh，仍不是新的准入余额。新分池不等于hard limit/预约或授权，两个对话共用中央账本；一份公共采集不重复记费。双端准备、唯一责任、硬独占和每宿主不重叠要求保持。

主线完整闭环见[756记录](../research/756_CARA_B36_COMPLETE_ACCEPTANCE_RESULTS_AND_FIGURES_20261029.md)，后续 CPU 与原视频审阅见[757记录](../research/757_CARA_B36_ORIGINAL_VIDEO_REVIEW_AND_F18_CPU_20261030.md)和[审阅承接](cara_next_stage_20261028/mainline/r2/B36_ANONYMOUS_REVIEW_R1.md)。原 A32 实际2.2557055054700728 GPUh、B36 实际2.384553982338661 GPUh均已中央唯一结算；本轮新增 GPU 和预约均为0。旧R19[逐字归档](cara_next_stage_20261028/mainline/QUESTION_QUEUE_BEFORE_MAINLINE_R20.md)，原准备、失败、范围和报价历史保留。保护输入数量不当作 GPUh。

当前论文结果入口见[清单R2](cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST_R2.json)和[758承接记录](../research/758_CARA_FAST_PAPER_RESULTS_R2_BOUND_TO_COMPLETE_B36_20261030.md)。原R1属于冻结绘图组件，保留原字节；R2不新增GPU或科学范围。

F18受影响生产CPU已按[759记录](../research/759_CARA_F18_AFFECTED_PRODUCTION_CPU_DUAL_HOST_ACCEPTED_20261030.md)双端接受；每端36成功/18预定失败仅为小张量验证，未形成真实视频或速度结论，也未冻结GPU整卡。

原32条视频的单人诊断已按[760记录](../research/760_CARA_B36_COMPLETE_SINGLE_REVIEWER_DIAGNOSTIC_20261030.md)完整接收：四条Native自比较均无明显差别，F19-C三个输入三项无明显差别，Human199三项更差，A1未显示额外改善。29条完整播放范围与三条元数据缺口一并保留；不把四旧CAL或单人记录升级为独立人类评价，也不向原规则回填CHECK评价。

Q5唯一50步的Native参考组件已按[761记录](../research/761_CARA_Q5_NATIVE50_DUAL_HOST_CPU_COMPONENT_20261030.md)双端接受，实际51更新、52个sigma，每端48成功/12预定失败；两个原容器exited/0，未重派。原36更新稀疏适配仍拒绝51更新，Q5完整方法和GPU物理卡尚未冻结。本轮GPU/预约/账本写入均为0。

[762双端身份复核](../research/762_CARA_FINAL16_RESERVE16_DUAL_HOST_IDENTITY_AUDIT_20261030.md)覆盖5,565份本地登记元数据，以及两端三个原项目输出目录的3,997份JSON。原最终16/备用16未发现执行身份，读取错误0，原池和48份输入字节保持；前16已用于DEV128，单独登记。该快照不替代首次使用前的fresh增量检查，不覆盖未登记外部存储；最终方法/物理范围/报价仍未冻结，0新增GPUh。

[763 S原生入口CPU主线承接](../research/763_CARA_S_PUBLISHED_NATIVE_CPU_HANDOFF_20261030.md)：复算发布快照双端原终态，每端123控制、20tiny路径、5生命周期控制与38源绑定一致。完整S R2十条采集卡仍待单次审批；实际风险数据和方法端点效力未形成，保持S优先。

S单次授权已接收：用户在S/Q原对话批准另一张A6000完整十条卡，硬限14GPUh；由原对话唯一派发，主线等待原启动回执，详见[授权记录](../reports/cara_fast_S_user_authorization_intake_r1_20261030.json)。不再重复申请批准。

[764 BudCache强基线源码与查询范围核查](../research/764_CARA_BUDCACHE_PRIMARY_SOURCE_AND_QUERY_SCOPE_AUDIT_20261030.md)：按A2.1补齐正式方法近邻的事前准备。官方默认控制器实际CPU替身计数302请求，双FIT适配规划上界604；须先定Cosmos同读出适配、终点查询/完整费用及双端生产CPU，不能直接引用原文搜索分钟数或NFE比作为本项目费用/速度。

[765预算搜索组件CPU接受](../research/765_CARA_BUDCACHE_BOUNDED_SEARCH_COMPONENT_CPU_20261030.md)：同36更新/19D控制器通过11项本地合成控制，原Uniform19起点保持，限额中止与失败无重试已验证。下一步接入真实Cosmos终点评价和持久化原查询恢复，再做双端受影响CPU及完整费用冻结；301查询仅为CPU夹具上限，无新GPU预算或派发。
