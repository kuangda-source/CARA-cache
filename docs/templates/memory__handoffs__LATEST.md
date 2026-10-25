# CARA-Cache 当前交接

{{snapshot}}

{{run_details}}

## 执行流程与已完成准备

[流程R2](repo:docs/EXECUTION_MODES.md)、[问题队列](repo:plans/QUESTION_QUEUE.md)和[专项交接](repo:memory/handoffs/CODEX_EFFICIENT_WORKFLOW_HANDOFF_20261025.md)已统一：按变更复用/验证、事件式文档、聊天授权有效，无新增GPU权限。固定48组本次[增量审计](repo:reports/cara_new_input_pool48_delta_r1_20261025.json)范围内清楚，首次使用前再查；[最小入口](repo:cards/README.md)仅离线规格和既有句柄收件适配，不提供启动功能。流程更新时未修改CAL66运行；其后原失败与本轮修复以顶部最新证据为准。流程详见[697](repo:research/697_CARA_WORKFLOW_R2_POOL_DELTA_AND_MINIMAL_ENTRY_20261025.md)。

## 当前用户授权

本轮只修复/验证/报价，用户明确先不重跑；见[699](repo:research/699_CARA_CAL66_FROZEN_ADAPTER_REPAIR_CPU_ACCEPTED_AND_RECOVERY_QUOTE_20261025.md)和[恢复方案](repo:plans/cara_policy_generator_20261020/CAL66_FROZEN_REQUEST_RECOVERY_R2_20261025.md)。此前一次完整CAL66授权已执行并失败，不自动授权重放。单卡8GPUh、累计226与最终部署预算不变。

- 原CAL66已失败并结算（见698），下列为保留的原范围：13正式角色×4输入、6重复、6warm、2历史桥接，共66；预计6.478451、上限8GPUh，该原授权已执行。原α、β、强基线身份不变；20D后置但新DEV正向后优先补齐。
- 原CAL106入口与组合CPU接受保留，旧106不派发。旧60路径入口漏检冻结类，已由f35c826d真实参数链CPU替代；历史原件RGB及48/156评分终态组合未改部分按323bb2a1源码SHA复用；五原模型前向和93帧三指标探针均已独立接受，完整合并复核与质量绑定见695；52视频质量外推加旧LPIPS、50%余量及600秒准备约4.72小时，CPU6小时上限不变，不是整批实测。
- Shared24/25全A与age3只差A34/35；当前完整能量、仅传播先验与模板同掩码。新卡不能证明能量优于模板；第二设置先做CPU可辨识性检查。
- 新输入48组已范围内曝光核查及源字节校验，16新DEV/16最终确认候选/16备用；不读新输入端点来修规则，首次执行前做增量身份审计。
- 旧104/112最大低估失败保持，新探索不再要求先通过旧2秒门；最终冻结方法仍需完整请求的0.8×新Native和257.7712338712067秒上限确认。累计226、旧两卡16.5未知责任不变。
- 新纯计时卡与GRAPH102暂缓；原P1/104/112/1624/价格卡均已结束，不重跑或重新结算。未知只恢复原句柄，不盲重派。
- 四卡私有入口、真实硬独占、磁盘保护、跨盘日志、完整分母、实际费用和来源SHA保障保留；不改忙卡模式、不触碰他人进程、不恢复两卡。

{{queue}}

[当前状态](repo:research/02_CURRENT_STATE.md) · [后续顺序](repo:research/09_NEXT_ACTIONS.md) · [实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md)
