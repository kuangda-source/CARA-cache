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

[766查询日志CPU接受](../research/766_CARA_BUDGET_SEARCH_QUERY_JOURNAL_CPU_20261030.md)：14项本地控制通过，原返回重放0新增评价，真实子进程中断保持UNKNOWN，额度不重置。原765控制器源码保持；下一步真实Cosmos评价、原物理终态读者和专用存储，再双端生产CPU与整卡报价。

[767完整RGB评价与四卡CPU终态](../research/767_CARA_BUDGET_RGB_ENDPOINT_AND_PENDING_PRODUCTION_CPU_20261030.md)：原CPU退出/0，31项组件控制、54成功路径/8预定失败、12完整目标完成。实际swap边界不符，验收器拒绝；保留原终态，先修正后续资源绑定，两卡保持S内存优先。双端生产CPU未接受。

[768资源修订与RGB存储](../research/768_CARA_BUDGET_CPU_RESOURCE_REPAIR_AND_RGB_STORAGE_20261030.md)：R2资源控制通过8项本地测试，四卡原CPU退出/0、完整数值及1CPU/4GiB/零swap已核验；两卡因56GiB门拒绝且stage不存在，保留S优先。默认604份RGB NPY约208.28GiB，3项容量控制通过；该默认仅作容量示例，未冻结GPU范围或报价。

[769同步CPU原端点恢复](../research/769_CARA_ORIGINAL_ENDPOINT_CALLBACK_RECOVERY_CPU_20261030.md)：9项本地/Linux控制、四组原生产CPU工件副本复核和4项接收器控制通过。原值一致、原件SHA保持，0新增生成；只补最后一个完整但缺失返回的原意图。GPU物理终态、双端端点验收与整卡费用仍待。

[770原S启动、Q1完整承接与校准成本](../research/770_CARA_S_ORIGINAL_START_Q1_COMPLETE_AND_CALIBRATION_COST_BASIS_20261030.md)：S原卡及既有双检查已承接，Q1原完整费用0.29875649GPUh；主线不重派或重记。完整RGB成本实测及10+2Q校准草案已补齐，14GPUh适配或默认301方向待用户选择，尚未冻结整卡费用或授权新GPU。

[771原进程身份CPU组件](../research/771_CARA_ORIGINAL_PROCESS_IDENTITY_CPU_COMPONENT_20261030.md)：7项本地/Linux控制、四个真实子进程、6项接收器控制通过；错误boot/命名空间保持UNKNOWN，全部退出不授予执行或结算。后续仍需原容器/设备/锁/费用联合终态、双端端点CPU与完整报价，预算方向未冻结。

[772生命周期回执CPU控制](../research/772_CARA_CALIBRATION_LIFECYCLE_RECEIPT_CPU_CONTROLS_20261030.md)：14项本地控制核验原启动/容器/锁/实耗和临时账本唯一结算；失败与超限不能报告成功。真实采集入口、完整监控/搜索验收和双端生产CPU待接通，旧原件及预算方向保持。

用户已选择[14GPUh完整SA+HC设计方向](../reports/cara_budget_14GPUh_design_direction_20261030.json)，替代此前待选状态；实际查询数、完整报价与单次GPU启动审批仍待。

[773十四GPUh完整SA+HC草案](../research/773_CARA_14GPUH_SA_HC_BUDGET_DESIGN_20261030.md)：提出初始1+SA30+HC20共51次双FIT查询、整卡112路径；五种原控制器CPU情形通过。规划12.53GPUh、余量1.47GPUh，非已接受报价；下一步完整生产组合、双端CPU和单次启动审阅。

[774完整校准CPU入口](../research/774_CARA_COMPLETE_CALIBRATION_ENTRY_AND_FOUR_CARD_CPU_20261030.md)：原112路径/51双FIT查询已组合，四卡原CPU18:46启动、18:56仍运行；完整两flow矩阵待原终态接受。只读采集与接收器本地控制通过，GPU组合及pre-lock失败见证仍待，未新派GPU。

[775完整校准CPU验收](../research/775_CARA_COMPLETE_CALIBRATION_CPU_ACCEPTANCE_AND_FAILURE_BOUNDARY_20261030.md)：四卡原CPU19:04退出/0，224设计路径、102双FIT目标及6预定失败通过，原发布源e31cc212明确绑定。失败结算修订及验收器27项本地控制通过，受影响Linux与GPU组合待验；64GiB存储额度待实施，双端CPU/报价和单次GPU批准仍待。

[776生命周期Linux与存储](../research/776_CARA_LIFECYCLE_LINUX_DELTA_AND_STORAGE_GUARDS_20261030.md)：R1缺依赖失败保留；修订R2四卡22项通过且退出/0，5项验收器控制通过。存储边界接入完整校准并通过13项本地控制；实际硬配额和GPU生产组合、双端CPU/整卡报价仍待，0新增GPU。

[777原尝试日志与存储组合](../research/777_CARA_GUARDIAN_DURABLE_ATTEMPTS_AND_STORAGE_CPU_20261030.md)：独立日志持久化尝试/原费用及原账单恢复已实现；四卡原CPU19:35:45退出/0，48项及资源/源绑定接受。连接超时仅恢复原stage，另5项验收器控制通过。生产GPU监督器/硬配额组合、双端CPU与报价仍待，0新增GPU。

[778原runner监督](../research/778_CARA_ORIGINAL_RUNNER_SUPERVISION_LINUX_CPU_20261030.md)：四卡原CPU19:53:07退出/0，12项Linux进程控制通过，11场景/8实际CPU runner；原硬限、热停、上下文/存储失败仅停止原子进程，旁侧哨兵保持，另6项验收控制通过。外层guardian/硬配额、双端CPU和报价仍待，0新增GPU。

[779原guardian控制链CPU](../research/779_CARA_HOST_GUARDIAN_ALLOCATION_CHAIN_CPU_20261030.md)：原R1/R2失败保留；R3原CPU20:30:45退出/0，13项Linux及7项验收控制通过，12场景/7个真实CPU runner。启动回执前失败采用原父进程身份见证，UNKNOWN不结算；SSH异常仅恢复原stage。实际Docker空容器兼容、64GiB硬配额、完整入口/科学验收、双端CPU/报价与14GPUh单次审批仍待，0新增GPU。

[780双端Docker观察与容器入口](../research/780_CARA_DOCKER_OBSERVATION_AND_CALIBRATION_CONTAINER_ENTRY_20261030.md)：两个原SSH入口均完成真实Docker空容器只读验证；26项本地观察/参数/worker/验收控制通过。原R3按发布源复核、不重跑。下一步连接真实校准runner、完整验收/once入口、64GiB硬配额及双端整卡CPU/报价；容器实际执行尚未验收，14GPUh未启动。

[781校准运行器与原CPU终态待恢复](../research/781_CARA_CALIBRATION_PRODUCTION_RUNNER_AND_AFFECTED_CPU_20261030.md)：14GPUh拟议完整51查询/112路径运行器已接通；32项本地控制通过，唯一四卡CPU见运行后终态读取受跳板间歇超时影响，仅恢复原句柄。ProxyJump原已配置，userspace曾双层认证通过但未稳定，Windows同期日志待回；不重派、不新增GPU。完整验收/once、64GiB实际配额及双端整卡CPU/报价仍待。

[782原CPU差量接受与完整验收器](../research/782_CARA_CALIBRATION_CPU_ACCEPTED_AND_COMPLETE_READER_20261030.md)：原781四卡CPU已退出0/无OOM并完整接受；无重跑。新完整112路径/51查询验收和一次冻结入口11项本地CPU控制通过，先原释放/唯一结算后科学读。剩整卡once、64GiB实际存储和双端整卡CPU/报价；生产端末次全量回读须计入GPU报价，14GPUh仍待启动批准。

[783单次宿主入口与旧责任账本兼容](../research/783_CARA_CALIBRATION_ONCE_DISPATCH_AND_CENTRAL_LIABILITY_20261030.md)：56项本地CPU回归通过；已有意图只恢复，原guardian句柄与启动序列化已连接。修正4.5+12GPUh责任保留的中央核算兼容，旧费用不改。源打包/中央预约连接、64GiB实际存储与当前源双端整卡CPU/报价仍待，0新GPU。

[784发布源包与中央单次事务](../research/784_CARA_PUBLISHED_SOURCE_AND_CENTRAL_TRANSACTIONS_20261030.md)：58项本地CPU控制通过，两端301文件覆盖包已绑定发布源；原两笔责任保留不改。双端原stage只读观察再次SSH握手超时，未远端prepare或提交CPU/GPU；继续原入口恢复，补实际Linux/双端整卡CPU、64GiB硬配额和完整报价。

[785跳板诊断与宿主传输](../research/785_CARA_WINDOWS_SSH_DIAGNOSTIC_AND_HOST_TRANSPORT_20261030.md)：Windows监听/认证正常，原ProxyJump曾双端成功但后续观察仍超时；根因未定，Clash/TUN日志待回。修正宿主解释器路径，未提交新CPU/GPU；安装前还需统一完整源包及实际整卡CPU。

[786当前完整CPU源与S完整承接](../research/786_CARA_CURRENT_COMPLETE_CPU_SOURCE_AND_S_ACCEPTED_INTAKE_20261031.md)：1174文件双端一致；本地109项通过、25项Linux跳过。两端原R3 stage/容器均不存在，传输尚未恢复，新CPU/GPU未启动。S完整接受且三目标同mask，后续合并；同14GPUh上限不冒称相同实耗，完整CPU/存储/报价后再审阅启动。

[787原R3 CPU失败与连接边界](../research/787_CARA_R3_CPU_ORIGINAL_FAILURE_AND_TRANSPORT_RECOVERY_20261031.md)：原两卡00:43:36→00:48:09退出/1，133/134执行控制通过、完整数值矩阵未开始；原源/资源及失败保留。就绪/采样顺序修复已发布，Linux回归待验；四卡仅源文件部分传输，未启动CPU。直接入口仍间歇重置，根因未证，不改全局服务，不重启原任务。

[788两卡限定与完整R4 CPU运行](../research/788_CARA_TWO_CARD_ONLY_READINESS_ACCEPTED_AND_FULL_CPU_RUNNING_20261031.md)：四卡维护期间按用户指令仅两卡推进；26项Linux回归接受，原R4于01:02:21开始，01:23/01:44检查。完整矩阵未接受；中央唯一账本仍在四卡，后续GPU不得用历史快照绕过fresh准入。

[789两卡完整CPU接受与费用草案](../research/789_CARA_TWO_CARD_R4_CPU_ACCEPTED_AND_COMPLETE_COST_DRAFT_20261031.md)：仅两卡推进。原R4 CPU于01:17:53正常退出并完整验收：两种flow各112设计路径，134执行+3规格控制通过；两项检查删除。完整93帧RGB读写组件接受，五项整卡费用草案13.03253GPUh/硬限14，尚含未实测余量。实际派发链、私有存储、唯一中央账本fresh准入及GPU审批仍待。

[790两卡限定与实际子进程CPU](../research/790_CARA_TWO_CARD_POLICY_AND_ACTUAL_DISPATCH_CHILD_CPU_20261031.md)：两卡限定已绑定准备/派发的源码、授权、CPU与报价；43项实际Linux增量控制通过，原CPU容器01:47:45退出0。真实子进程/私有管道/原身份发布及失败账单、不重派已验证；原R4完整数值复用。实际64GiB存储、GPU生命周期和完整费用准入仍待，中央唯一账本与原句柄去重门不变，14GPUh未批准。

[791两卡私有存储实际接受](../research/791_CARA_TWO_CARD_PRIVATE_STORAGE_ACCEPTED_20261031.md)：两卡64GiB私有卷及独立48MiB控制日志已实际创建并复核，原进程结束，输出为空。六项本地控制通过，首次部署导入失败原件保留；未使用GPU、未访问四卡。下一步补私有卷完整RGB读回与报价；中央唯一账本fresh准入及14GPUh批准仍待。

[792两卡私有RGB读写与费用](../research/792_CARA_TWO_CARD_PRIVATE_RGB_IO_AND_COMPLETE_QUOTE_20261031.md)：两卡私有卷完整93帧RGB读写已接受，原CPU容器正常退出；清除文件及镜像缓存后两数组读回校验4.27秒、MSE0.55秒。六个合成文件按SHA清理，输出恢复为空，独立日志未写入。完整费用仍预计13.03253GPUh/硬限14；继续整卡CPU证据组合，中央fresh准入和实际批准仍待。
