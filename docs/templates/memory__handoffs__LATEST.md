# CARA-Cache 当前交接

{{snapshot}}

{{run_details}}

## 执行流程与已完成准备

[流程R3](repo:docs/EXECUTION_MODES.md)、[问题队列](repo:plans/QUESTION_QUEUE.md)和[专项交接](repo:memory/handoffs/CODEX_EFFICIENT_WORKFLOW_HANDOFF_20261025.md)已统一：按变更复用/验证、事件式文档、聊天授权有效，无新增GPU权限。固定48组本次[增量审计](repo:reports/cara_new_input_pool48_delta_r1_20261025.json)范围内清楚，首次使用前再查；[最小入口](repo:cards/README.md)仅离线规格和既有句柄收件适配，不提供启动功能。流程更新时未修改CAL66运行；其后原失败与本轮修复以顶部最新证据为准。流程详见[697](repo:research/697_CARA_WORKFLOW_R2_POOL_DELTA_AND_MINIMAL_ENTRY_20261025.md)。

## 当前用户授权

用户已明确授权完整128路径在两卡单次运行，实际启动已完成。CAL66已结算且旧四卡R2未派发；禁止恢复旧任务或双边启动。运行详情以705和当前状态唯一launch为准。

- 128=96正式+24重复+6warm+2旧CAL控制；4419pairs/8838CFG；释放后80组LPIPS和288质量位置。四卡报价12.349232超12h设计子池，两卡11.618228；本轮不调配或提高上限。
- 原CAL106入口与组合CPU接受保留，旧106不派发。旧60路径入口漏检冻结类，已由f35c826d真实参数链CPU替代；历史原件RGB及48/156评分终态组合未改部分按323bb2a1源码SHA复用；五原模型前向和93帧三指标探针均已独立接受，完整合并复核与质量绑定见695；52视频质量外推加旧LPIPS、50%余量及600秒准备约4.72小时，这些是旧CAL66的6小时上限；新DEV128另报2CPU/8GiB、预计8.56小时/10小时上限，不能沿用旧6小时，不是整批实测。
- Shared24/25全A与age3只差A34/35；当前完整能量、仅传播先验与模板同掩码。新卡不能证明能量优于模板；第二设置先做CPU可辨识性检查。
- 新输入48组已范围内曝光核查及源字节校验，16新DEV/16最终确认候选/16备用；不读新输入端点来修规则，首次执行前做增量身份审计。
- 旧104/112最大低估失败保持，新探索不再要求先通过旧2秒门；最终冻结方法仍需完整请求的0.8×新Native和257.7712338712067秒上限确认。累计226、旧两卡16.5未知责任不变。
- 新纯计时卡与GRAPH102暂缓；原P1/104/112/1624/价格卡均已结束，不重跑或重新结算。未知只恢复原句柄，不盲重派。
- 四卡私有入口、真实硬独占、磁盘保护、跨盘日志、完整分母、实际费用和来源SHA保障保留；不改忙卡模式、不触碰他人进程、不重启旧两卡实验；新卡只能使用已验隔离双端环境。

## 后续探索当前版本：E1 V2.2

[V2原始包](repo:plans/cara_predictor_refresh_scout_v2_20261026/source/01_Research_Assessment_and_Plan_V2.md)及[原绑定表](repo:plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_BOUND_V2.yaml)保持不变；未来探索以[V2.2修订说明](repo:plans/cara_predictor_refresh_scout_v2_20261026/E1_V22_AMENDMENT_AND_FREEZE_CHECKLIST.md)和[增量登记](repo:plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_PATCH_V22.yaml)为准，见[707](repo:research/707_CARA_SCOUT_V22_STRATIFIED_READOUT_PLAN_20261026.md)。

先E0已有资产与DCTA核查，再E1同状态五类/六逻辑读出（global/long两新候选），之后E2-R固定布局读出，条件满足才E2-I交互。主分母是全队列最强固定基线，不是逐prompt oracle。22/23/25/33/34/35的保存掩码/网格元数据已复算，短长各6点；新端口支持/状态恢复、精确数值及费用门、双端CPU和完整报价尚未通过，不能称完整冻结。

已有锐度/MUSIQ诊断复用，Native-relative梯度与固定轻模糊对照未做。E2-R/I各16逻辑输出，合并完全同身份可复用8条时为24唯一机制输出，否则32；warm/Native/强参考/重复/评分另报，不能沿用旧16条/2–3GPUh为完整报价。原三项质量门、α、强基线、累计226及最终部署预算保持；DEV128原自动检查和运行合同不变，未新增GPU授权/预约，不读其中途结果。

{{queue}}

[当前状态](repo:research/02_CURRENT_STATE.md) · [后续顺序](repo:research/09_NEXT_ACTIONS.md) · [实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md)

最新执行见[705实际独占启动](repo:research/705_CARA_DEV128_A6000_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_SCHEDULE_20261026.md)：两卡GPU1完整128已于13:36:59启动；双端财务兼容修复后各10生命周期、6存储、63终态检查接受。单卡12h/累计226与最终部署预算不变；仅跟踪原launch，不重复派发。

E0最新准备：[官方源审计与11组CPU用例](../../plans/cara_predictor_refresh_scout_v2_20261026/E0_SOURCE_AUDIT_AND_E1_CPU_CASES_R1.md)。DCTA Wan/FLUX裁剪差异已核对，本地8个旧视频SHA一致；生产移植、状态隔离和报价尚未接受，DEV128不变。
