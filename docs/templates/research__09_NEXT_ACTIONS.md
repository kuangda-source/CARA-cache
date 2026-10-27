# CARA-Cache 后续实验顺序

[732 WC73已启动](732_CARA_WC73_PER_HOST_ADMISSION_AND_LAUNCH_20261027.md)：用户允许两台服务器各一项独占任务；Ada GPU1于10月27日20:40:06确认唯一CUDA上下文，原73路径、12GPUh（A5/B7）。A失败即停，通过后释放/结算、CPU按预注册冻结再B；预计10月28日08:10–10:10含CPU评分完成。仅监测唯一r2 stage，不重派、不改旧门槛或部分科学解读；心跳wc73按真实起点检查。

[730 共同长龄R2已独占重启](repo:research/730_CARA_COMMON_LONG6_R2_PROC_RACE_REPAIR_AND_RESTART_20261027.md) — TERMINAL ACCEPTED: 6/6 paths, 12 states, 84 readouts; original alpha and OFF/ON parity verified. GPU ended 21:44:47, CPU 21:45:13; 1.619241 GPUh centrally settled. Handles/lock released, Default restored. Frozen mechanism analysis pending; no automatic GPU or j1 promotion, IG paused.

[729 R4共同长龄提前退出并结算](repo:research/729_CARA_COMMON_LONG6_PROC_RACE_FAILURE_AND_SETTLEMENT_20261027.md)：原六路径任务18:25因/proc进程消失ESRCH未捕获而由监督停止，完整范围未完成，未评分或科学接受。原费用0.940191GPUh已中央结算，全部句柄与锁释放、Default恢复；两次检查已删除，不自动重派。原α/强基线/226预算不变，IG暂停。

[725统一时间与七角色CPU](repo:research/725_CARA_WC_TIME_UNIFIED_SEVEN_ROLE_DUAL_CPU_AND_WHOLE_QUOTE_20261027.md)：双端各160小张量完整路径、阶段控制与真实Alex/PIQ权重CPU通过；73路径整卡工程预测Ada9.51/A6000 9.97GPUh，硬限12仅提案。GPU未授权未启动，仍需设备/中央责任/宿主监督准入和A阶段真实GPU门；原门槛不变。

[727 R4共同长龄整卡组合](repo:research/727_CARA_COMMON_LONG_WHOLE_CARD_CPU_AND_DUAL_HOST_REVIEW_20261027.md)：双端各12完整CPU路径/24状态/168重评分位置，4生命周期、6存储边界和财务终态组合独立接受。双端登记元数据曝光与资源已核查；完整6路径预计2.608114GPUh、建议硬限3，未预约未启动。两时间仍标诊断；真实GPU、新候选闭环与j1未接受，IG暂停。

[723双时间与WC公平控制P0](repo:research/723_CARA_WC_TIME_PROTOCOL_P0_CPU_AND_INCREMENTAL_SCOPE_20261027.md)：双端真实源小张量CPU通过；增量73条开发范围与评分/热环境已登记，真实GPU等价、完整生产组合和实测报价仍待完成，无GPU提交。新批T_DD/T_request并列，旧门槛与原件不变。主线预算可按用户新授权每次加24GPUh并通知，本轮未加。

{{snapshot}}

## 当前探索：机制线CPU完整诊断，IG用户暂停

当前入口为[720共同/差分完整诊断](repo:research/720_CARA_CFG_COMMON_DIFFERENCE_MECHANISM_AND_PREDICTOR_HYPOTHESIS_20261027.md)和[原件复用/CPU方案](repo:plans/cara_predictor_refresh_scout_v2_20261026/MECHANISM_REUSE_AND_PREPARATION_R1_20261027.md)。原V2/V2.2历史登记不改。

- IG后续暂停；B1原件与费用保留，无运行任务，不执行B2/B3。DEV128完整接受且自动检查已删除，不重复运行。
- 两旧CAL×6状态×6固定读出已有原B1真实模型证据；独立审计核对原终态/中央结算/保存CPU/两端源码，避免重新采集。实际GPU来自A6000，四卡复用到CPU兼容证据。
- 原长龄6点R4均未胜A，聚合误差增加14.97%；无可晋级j1，不提交当前R4的E2视频卡。精确数值/费用合同缺口不事后补作预登记。
- 32文件再次SHA匹配；共同/差分CPU完整12/12已退出，无CUDA/head或拟合。R4历史共同方向有用、差分方向逆向，隐藏层已出现；只保留实际输出共同增量并保持A差分，原alpha下长龄6/6改善3.93%，仅已曝光CAL事后诊断。teacher-free参考结构CPU通过，但真实生产/费用未接受，j1仍为空。下一步先做受影响接口和双端成本，不改alpha、不追加GPU。
- E2-R/I仍按原条件与完整分母准备，不能以IG46路径CPU替代E2整卡接受。没有有效j1时完整GPU报价NOT_READY，无预约。双端兼容、默认四卡；原α、强基线、累计226与最终部署双预算保持。

[722计时边界核查](repo:research/722_CARA_PAPER_LATENCY_BOUNDARY_AUDIT_AND_MINIMAL_MEASUREMENT_PLAN_20261027.md)：四卡410请求原时钟与接受复核通过，332正式路径并列分析；DEV128 Shared25-C完整请求246.675秒/1.269×，含条件准备的生成函数214.010秒/1.314×。后者不是论文“去噪＋解码”，精确边界缺失，不估算补造。优先下一张已授权卡加边界时钟，备用16路径约1.73GPUh仅提案；原预算/验收不变、无GPU。

[724准确论文时钟准备](repo:research/724_CARA_EXACT_PAPER_TIMING_DUAL_HOST_CPU_AND_METHOD_HANDOFF_20261027.md)：可选新入口已接入固定布局/少步Native，双服务器各18完整CPU路径及边界/失败检查通过，原α/输出一致。保留完整请求时间与原验收；真实GPU时钟与新读出整卡尚未接受。后续方法卡按[附件](repo:plans/cara_predictor_refresh_scout_v2_20261026/PAPER_TIMING_ATTACHMENT_R1_20261027.md)绑定，无单独GPU补测或新预算。

{{queue}}

## 本轮授权范围与下一步

用户仅要求优先准备机制线，暂不追加GPU。原张量CPU误差分解与资产身份核查已完成，见719；共同/差分来源已由720定位，下一步准备新结构真实CPU接口与成本；当前R4无j1，后续E2需另有预登记增量依据、双端受影响生产CPU和完整报价。DEV128接受、最终确认保护组与所有历史失败/费用保留。

## 已完成历史与暂缓方案

- 原P1未选出预算内策略，原件及实际2.557833 GPUh保留。
- 完整104 R2接受，历史强布局超过原GRAPH；计时最大低估2.618秒失败，实际7.395282 GPUh保留。
- COST112完整接受，计时最大低估5.006秒失败，实际8.139511 GPUh保留。[归因691](repo:research/691_CARA_COST112_CAUSE_SEPARATION_AND_P1_REPAIR_PLAN_20261025.md)。
- 新纯计时重跑和GRAPH102暂缓；原CPU与未执行报价保留，不重新解释为成功。
- 旧两卡16.5 GPUh未知责任预约继续保留；旧两卡实验不重启；当前两卡隔离运行环境已通过CAL66迁移接受。

[新合同](repo:plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md) · [本轮记录694](repo:research/694_CARA_CAL66_REDESIGN_MASK_IDENTIFIABILITY_AND_QUOTE_20261025.md) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [历史计划](repo:docs/archive/README.md)
