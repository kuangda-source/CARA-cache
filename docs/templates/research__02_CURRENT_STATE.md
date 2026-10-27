# CARA-Cache 当前状态

[732 WC73已启动](732_CARA_WC73_PER_HOST_ADMISSION_AND_LAUNCH_20261027.md)：用户允许两台服务器各一项独占任务；Ada GPU1于10月27日20:40:06确认唯一CUDA上下文，原73路径、12GPUh（A5/B7）。A失败即停，通过后释放/结算、CPU按预注册冻结再B；预计10月28日08:10–10:10含CPU评分完成。仅监测唯一r2 stage，不重派、不改旧门槛或部分科学解读；心跳wc73按真实起点检查。

[735 CFG mainline and checklist](735_CARA_CFG_MAINLINE_PLAN_AND_FEISHU_RECONCILIATION_20261028.md): S scheduling and Q cache compression plans registered separately. Independent confirmation/Q5 no longer wait for R4; asset/mask/codec CPU work pending. Existing WC73 unchanged; Feishu checklist updated and verified, no GPU or budget added, IG paused.

[734 DEV128 age3 secondary review](734_CARA_DEV128_AGE3_QUALITY_TRADEOFF_AND_CONFIRMATION_20261028.md): original quality bounds versus Native35/S25-A and mean time budget pass; LPIPS versus Shared25-C improves 6.68%, with MUSIQ tradeoff. Worth a separately registered independent confirmation; original main candidate unchanged, no GPU authorized, IG paused.

[733 R2 frozen analysis](733_CARA_COMMON_LONG_R2_FROZEN_ANALYSIS_AND_STOP_20261028.md): technical/financial acceptance retained; R4_COMMON_LONG fails the frozen local gate (1.65% versus A, below 5%; AV51 worsens). No E2 or new GPU; IG paused. Next: bounded saved-tensor CPU cause decomposition, no tuning.

[730 共同长龄R2已独占重启](repo:research/730_CARA_COMMON_LONG6_R2_PROC_RACE_REPAIR_AND_RESTART_20261027.md) — TERMINAL ACCEPTED: 6/6 paths, 12 states, 84 readouts; original alpha and OFF/ON parity verified. GPU ended 21:44:47, CPU 21:45:13; 1.619241 GPUh centrally settled. Handles/lock released, Default restored. Frozen mechanism analysis pending; no automatic GPU or j1 promotion, IG paused.

[729 R4共同长龄提前退出并结算](repo:research/729_CARA_COMMON_LONG6_PROC_RACE_FAILURE_AND_SETTLEMENT_20261027.md)：原六路径任务18:25因/proc进程消失ESRCH未捕获而由监督停止，完整范围未完成，未评分或科学接受。原费用0.940191GPUh已中央结算，全部句柄与锁释放、Default恢复；两次检查已删除，不自动重派。原α/强基线/226预算不变，IG暂停。

[725统一时间与七角色CPU](repo:research/725_CARA_WC_TIME_UNIFIED_SEVEN_ROLE_DUAL_CPU_AND_WHOLE_QUOTE_20261027.md)：双端各160小张量完整路径、阶段控制与真实Alex/PIQ权重CPU通过；73路径整卡工程预测Ada9.51/A6000 9.97GPUh，硬限12仅提案。GPU未授权未启动，仍需设备/中央责任/宿主监督准入和A阶段真实GPU门；原门槛不变。

[727 R4共同长龄整卡组合](repo:research/727_CARA_COMMON_LONG_WHOLE_CARD_CPU_AND_DUAL_HOST_REVIEW_20261027.md)：双端各12完整CPU路径/24状态/168重评分位置，4生命周期、6存储边界和财务终态组合独立接受。双端登记元数据曝光与资源已核查；完整6路径预计2.608114GPUh、建议硬限3，未预约未启动。两时间仍标诊断；真实GPU、新候选闭环与j1未接受，IG暂停。

[723双时间与WC公平控制P0](repo:research/723_CARA_WC_TIME_PROTOCOL_P0_CPU_AND_INCREMENTAL_SCOPE_20261027.md)：双端真实源小张量CPU通过；增量73条开发范围与评分/热环境已登记，真实GPU等价、完整生产组合和实测报价仍待完成，无GPU提交。新批T_DD/T_request并列，旧门槛与原件不变。主线预算可按用户新授权每次加24GPUh并通知，本轮未加。

{{snapshot}}

{{run_details}}

## 当前研究判断

{{research_summary}}

[创新量增益探索R1](repo:plans/cara_innovation_gain_20261027/README.md)已完成两卡真实模型B1与保存资产分析：4父路径、12状态、108附加重放。Scalar=1、Band=(1,1)，均退化DEEP，相对最强固定A_PHASE的留出局部误差高62.2%/53.2%。本轮停止这两个具体候选，不提交条件视频或范围修订，不并入主线；总1.452095GPUh含工程失败均已结算，GPU/CPU已退出。两卡/四卡生产CPU兼容均通过，四卡真实GPU未运行。见[717完整结果](repo:research/717_CARA_IG_B1_COMPLETE_BOX_ENDPOINT_RESULT_20261027.md)。

[720共同/差分CPU诊断](repo:research/720_CARA_CFG_COMMON_DIFFERENCE_MECHANISM_AND_PREDICTOR_HYPOTHESIS_20261027.md)完整接受：R4共同历史外推有用、差分历史外推逆向；实际输出只保留共同增量，原alpha下长龄6/6改善3.93%。这是已曝光CAL事后结构诊断，teacher-free参考CPU已过，真实生产/费用未过，无j1或新GPU。IG继续暂停。

[721历史WC/Native LPIPS审计](repo:research/721_WC_NATIVE_LPIPS_OFFICIAL_PROTOCOL_FORENSIC_AUDIT_20261027.md)：九对837帧CPU重评分完整接受，旧Alex分数可复算、原件配对与RGB一致；已确认UniPC/参数及Alex-VGG与论文口径不等价。保留全部历史结果和Native门槛，不称论文精确复现，不将跨批剩余因素全部归为缓存偏移；无新GPU或生成。

[722计时边界核查](repo:research/722_CARA_PAPER_LATENCY_BOUNDARY_AUDIT_AND_MINIMAL_MEASUREMENT_PLAN_20261027.md)：四卡410请求原时钟与接受复核通过，332正式路径并列分析；DEV128 Shared25-C完整请求246.675秒/1.269×，含条件准备的生成函数214.010秒/1.314×。后者不是论文“去噪＋解码”，精确边界缺失，不估算补造。优先下一张已授权卡加边界时钟，备用16路径约1.73GPUh仅提案；原预算/验收不变、无GPU。

[724准确论文时钟准备](repo:research/724_CARA_EXACT_PAPER_TIMING_DUAL_HOST_CPU_AND_METHOD_HANDOFF_20261027.md)：可选新入口已接入固定布局/少步Native，双服务器各18完整CPU路径及边界/失败检查通过，原α/输出一致。保留完整请求时间与原验收；真实GPU时钟与新读出整卡尚未接受。后续方法卡按[附件](repo:plans/cara_predictor_refresh_scout_v2_20261026/PAPER_TIMING_ATTACHMENT_R1_20261027.md)绑定，无单独GPU补测或新预算。

{{queue}}

## 本轮已完成与尚缺

- [703双端DEV128准备](repo:research/703_CARA_DEV128_DUAL_HOST_CPU_AND_CAL66_QUALITY_DIAGNOSIS_20261026.md)与[704组合接受](repo:research/704_CARA_DEV128_FULL_CPU_COMBINATION_ACCEPTED_AND_QUOTE_20261026.md)保留为准备历史；DEV128其后已按716完整接受，不应沿用旧运行或未授权状态。

- [702完整结果](repo:research/702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md)：66/48/156完整接受，4.776208 GPUh已中央结算，Shared25-C按原CAL规则冻结；后续新DEV128已按716完整接受。

- CAL66独立登记66路径：52正式、6反序重复、6warm、2历史桥接；新增Shared-all对照隔离A34/35停用效应，原α及历史强布局身份不变。
- 24/25/26D的完整能量、仅传播先验、简单模板同掩码；本轮检验位置价值，构造规则增量留给换步数设置，不重复生成别名。
- 原CAL106及其入口/组合CPU接受保留为组件复用依据。旧15角色/60路径数值CPU使用可修改夹具，冻结参数漏检现已由新真实类CPU链修复，见699。组合R1因ready快照竞态失败、R2因测试屏障位置错误失败，原件保留；R3整卡组合、五原模型CPU与93帧三指标探针均已接受；独立合并复核通过，均不是CAL科学结果。
- 原48组池已做来源组范围内审计，本轮复核源字节不变；首次DEV前增量核查，不能宣称已完成最终输入准入。

## 关键历史证据

| 证据 | 结果及边界 |
|---|---|
| [BANK24](repo:research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md) | 六DEV局部A误差改善；门控无优势，无C21端点对照 |
| [1624与价格审计](repo:research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md) | 标签完整接受；受竞争价格另卡修复，不改原件 |
| [原P1](repo:research/669_CARA_PG_P1_COMPLETE_BUDGET_ATTRIBUTION_AND_REPAIR_PLAN_20261024.md) | 原件接受但预算内策略为空；2.557833 GPUh |
| [完整104 R2](repo:research/685_CARA_HISTORY104_R2_COMPLETE_ACCEPTANCE_RESULTS_AND_COST_GATE_20261024.md) | 强历史布局超过GRAPH；24/25D有实测可行点；计时模型失败，7.395282 GPUh |
| [COST112](repo:research/690_CARA_COST112_COMPLETE_ACCEPTANCE_AND_TIMING_GATE_FAILURE_20261025.md) | 完整接受，最大低估5.006秒超过原门；8.139511 GPUh |
| [归因691](repo:research/691_CARA_COST112_CAUSE_SEPARATION_AND_P1_REPAIR_PLAN_20261025.md) | 参照、主流水线、外层流程皆有贡献；温控因果份额未识别 |

原HISTORY104 R1磁盘失败和保守5.48GPUh费用、全部失败/恢复原件保持；旧两卡16.5GPUh未知责任不挪用。旧72路径不拼接。新探索合同只调整未来研究顺序，不能把原失败改成通过。

## 状态来源

[本轮设计694](repo:research/694_CARA_CAL66_REDESIGN_MASK_IDENTIFIABILITY_AND_QUOTE_20261025.md) · [规范状态](repo:docs/project_status.json) · [实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [历史记录](repo:docs/archive/README.md)

文档时间不代替实际观测；原终态绑定其launch和SHA。只有后续明确GPU授权、完整CPU/报价和fresh独占/存储/账本准入后才能提交新GPU。

最新执行见[705实际独占启动](repo:research/705_CARA_DEV128_A6000_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_SCHEDULE_20261026.md)：两卡GPU1完整128已于13:36:59启动；双端财务兼容修复后各10生命周期、6存储、63终态检查接受。单卡12h/累计226与最终部署预算不变；仅跟踪原launch，不重复派发。
