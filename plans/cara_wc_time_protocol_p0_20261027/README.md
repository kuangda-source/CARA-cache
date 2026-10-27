# CARA × WorldCache 双时间口径 P0 增量包

日期：2026-10-27。状态：**CPU组件验证通过；真实GPU等价未验证；完整生产组合与实测报价未完成；不具备派发资格。** 本包是增量方案，不替换已完成合同，不启动GPU。

## 明确判断

历史Native参考LPIPS仍衡量计算保真；独立生成质量、官方论文GT指标与它不能相加或互相替代。继续保留原门槛。新批同时记录连续去噪至decode的 `T_DD`、原完整请求 `T_request`，保留 `T_generate`。旧T_DD一律N/A；DEV128、IG、CAL66、721/722原件和结论不改。

## 已核验与交付

- 基线main：`f8bb36e545659870deffc1ba220a145020db26fc`，开始时与origin/main一致；精确文件清单见 [SHA清单](REFERENCE_SHA_INVENTORY.json)：376个保护原件、421个本轮显式引用、39个历史直接SHA断言均通过。不是声称扫描全部Git历史或远端所有文件。
- [配置映射](WC_PORT_PARAMS.md)、[控制身份和73条物理路径](CONTROL_IDENTITY_MATRIX.yaml)、[时间埋点](TIME_BOUNDARY_DESIGN.md)、[CPU验收](TIME_BOUNDARY_TESTS.json)、[实际GPU最小验证设计](FULLD_GPU_MINIMAL_VALIDATION.md)。
- [CAL预注册](CAL_PREREGISTRATION.md)、[费用统一汇总](PRICE_QUOTE.md)、[资源机器清单](COST_AND_RESOURCE_ENVELOPE.json)、[评分绑定](SCORING_BINDINGS.json)、[热环境与评分](THERMAL_AND_SCORING.md)、[缺失统计](MISSINGNESS_PLAN.md)。
- 两服务器各完成14条小张量CPU路径；实际原生forward与WC全D、三臂计时开关输出相等。不是完整Cosmos权重/真实视频/GPU等价结论。七角色生产监督器与评分生命周期尚需组合CPU验证，不能凭本组件测试放行。

## 完整范围为何从参考方案50变为73

参考50依赖跨选参阶段复用2条候选输出，并未覆盖12条计时开关数值诊断。现有流程要求先释放GPU再评分。为保证最终CAL七角色同一新批驻留模型/热环境，采用A校准26条、释放评分冻结、B完整比较47条，两次加载。A的候选与锚点不混入B主表。共73条、13warm、12诊断、8校准与锚点、28正式、12时间重复；这是尚未执行的完整范围提案，不是已经获批的GPU任务。

## 账本、任务与权限

初始只读快照：中央上限226 GPUh，已用172.2657747141984、保留16.5、不含保留可用37.234225285801614。两卡镜像落后，不能当第二份额度或覆盖中央账本。两项RESERVED_OR_RUNNING是未确认提交的财务不确定保留，不等于活跃GPU任务。扫描未见本项目运行任务；四卡GPU0有他人BeamNG上下文，两卡无compute app。快照不是未来准入。

用户本轮新增授权：主线总GPUh上限可由助手按每次24 GPUh提高，每次告知调整前后与用途。本轮未调整；此授权不替代新卡执行授权、完整报价、独占与身份恢复。本包不改既有卡硬限，不增加最终16实验范围。

## 同源去重与19D

本轮检索已登记本地plans/configs/manifests/src/scripts及相关主线讨论，未找到可合并的已冻结19D完整执行身份。不能据此宣称所有并行工作都不存在。19D完全排除本包；若出现，另建增量范围，以checkpoint/source/runtime/scheduler-sigma/prompt-seed/config/action policy/thermal-round/role/purpose完整身份去重，重新汇总双方费用。仅同D掩码或同名称不足以复用；warm、时间重复和诊断不能按科学样本去重。

[用户附件原文副本](USER_PLAN_REFERENCE.md)仅作来源；实际用户请求及后续预算授权优先，附件中的执行建议不是GPU启动指令。
