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

## 新增后续计划：预测器—刷新探索 V2

已查收[外部V2原件](repo:plans/cara_predictor_refresh_scout_v2_20261026/source/01_Research_Assessment_and_Plan_V2.md)，仓库执行口径见[接续计划](repo:plans/cara_predictor_refresh_scout_v2_20261026/README.md)和[绑定登记表](repo:plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_BOUND_V2.yaml)。原manifest四项SHA通过，见[706](repo:research/706_CARA_PREDICTOR_REFRESH_SCOUT_V2_PLAN_INTAKE_20261026.md)。

主线DEV128及原自动检查不变。旁路顺序：E0已有资产/坐标/DCTA/质量绑定 → E1同状态五读出、路径与方向幅度诊断 → 条件E2固定布局或2×2 → 独立新输入确认/迁移。原锐度诊断已做；新增分析尚未执行。8/12、5%是待冻结建议，1/2–3/4GPUh仅规划，不是完整报价或新GPU授权。E2的16是机制正式输出上限，不含warm、缺失Native、额外强基线和评分，须完整报价。

质量原门已绑定（MUSIQ 1、主体/运动各0.01，相对S参考及Native），新E2角色映射/支持域/CPU仍待完成。保存的中央准入账目可用36.103379GPUh已扣DEV128 12h预约，不是结算后余额；实际派发前再核账。默认四卡、两端兼容、累计226及最终部署预算保持，不复活GRAPH/在线门控或读部分DEV结果。

{{queue}}

[当前状态](repo:research/02_CURRENT_STATE.md) · [后续顺序](repo:research/09_NEXT_ACTIONS.md) · [实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md)

最新执行见[705实际独占启动](repo:research/705_CARA_DEV128_A6000_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_SCHEDULE_20261026.md)：两卡GPU1完整128已于13:36:59启动；双端财务兼容修复后各10生命周期、6存储、63终态检查接受。单卡12h/累计226与最终部署预算不变；仅跟踪原launch，不重复派发。
