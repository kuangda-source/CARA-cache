# 固定刷新对照已完成 CPU 接线，下一优先人物保真诊断

2026-10-04。[87 轻量十输出结果](87_WC_LIGHT_OUTPUT_RESULTS_AND_FIDELITY_NEXT.md)显示 common 的两轨动作相同，人物两轨则有9次 full/cache 差异、deep CFG38/35。因此下一步先区分固定动作位置下的稀疏近似与原 adaptive 调度反馈，不先训练 Head。

## 对照接口及来源

[不可变掩码](../src/wcomr/fixed_refresh_mask.py)绑定 sample/model/condition、72个 Boolean CFG 动作及原回执 SHA，强制前14次与最后2次 dense、原生70周期。掩码从已独立审计的原十输出两次官方 trace 派生，重复 trace 必须相同；[草案清单](../manifests/wc_fixed_exposed_masks_draft_20261004.json)保留 common35、human38。源为原终态 SHA `29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae`，不是未来新样本的线上决策特征。

[FixedRefreshDiagnosticAdapter](../src/wcomr/fixed_refresh_diagnostic.py)在固定官方源码的原 threshold 判断位置替换结果，保留后续 resume_flag、误差累积、probe 历史、skip 计数以及 cache/full 分支状态转移。只在 Execution Branching 前改 skip 会漏掉这些关联更新，故没有采用。SimpleRefreshAdapter 默认新增钩子为恒等变换；现有线上路径仍使用原 predicate。未改固定 upstream 文件或已经结束的 GPU stage。

该掩码使用之前曝光的完整官方轨迹，**只能作为离线解释性对照**；两臂共同获得这些固定动作，不声称线上 teacher 路由、刷新收益学习或部署算法。事件分别记录固定选择与本臂状态上原 predicate 会给出的选择；后者不是原官方父轨迹上的反事实真值。强制缺少 cache 的复用、错误请求/模型/条件/CFG/horizon/warm 分配均拒绝。

## 实际 CPU 验证

服务器现有 Torch2.7.1+cu128、禁止 CUDA 初始化，无模型权重或真实稀疏核。固定官方 Inference/WC/UniPC/sampler 函数体仍由明确的 toy 网络、prepare、kernel、decoder、writer 边界支撑。

- [固定刷新 r2](../reports/wc_fixed_refresh_cpu_r2_20261004.json)：87.789秒，旧轻量接口15控制及新固定调度12控制通过，flow OFF/ON。包含相同掩码 D/D 九项与 pipeline、跨参考配对的共同入口 RNG、共同改变动作掩码的实际计数、D/S 来源隔离、70失效/尾dense、缺历史和 nonfinite 失败分母与清理。
- [本地掩码控制](../reports/wc_fixed_masks_cpu_20261004.json)：两份实际掩码的原件绑定、28项长度/类型/SHA、warm/tail、身份与 CFG 越界拒绝通过。[CPU原件审计](../reports/wc_fixed_refresh_cpu_audit_20261004.json)保留 r2 冻结 payload 身份。
- [四输出组合 r2](../reports/wc_fixed_four_output_cpu_r2_20261004.json)：65.142秒，原十输出组合4控制及新四输出组合6控制通过，flow OFF/ON。实际执行每臂真实 prepare/36 solver/72 CFG；D/D 九门/完整 pipeline、三份 dense artifact 相同、无测量诊断 hooks、真实来源成本保留，以及控制失败阻止测量/候选失败保留前三产物和四分母通过。[当前 source 审计](../reports/wc_fixed_four_output_cpu_audit_20261004.json)绑定全部当前 payload，并覆盖后来可选 dense factory 的共享模块变更。

两次早期 CPU 失败完整保留，不追认为 PASS：

1. 固定刷新 r1 在跨配对比较时未共同恢复入口 RNG，toy prepare 的随机 fps/Python/NumPy 元数据不同。修复测试的跨配对初始状态，未改生产路由。
2. 四输出组合 r1 误要求 D/S mock 视频不同；toy tanh 解码可饱和，使不同 latent 得到相同 mock 文件。修复测试为直接观察 sampler 返回改变，同时保留 D/D 与三份 dense artifact 等价要求。候选编码视频“必须不同”本就不是科学验收条件。

全部 CPU 费用0，实测账本保持7.407626319933526/12GPUh、38jobs，无新 reservation。CPU通过不证明实际人物 fixed-mask D/D、真实稀疏核、编码视频保真或加速。

## 下一张四输出卡的具体草案

[生产组合](../src/wcomr/fixed_output.py)已实现，拟议仅 human_199/seed0、原35请求/36实际更新/72CFG、93帧768×432/16fps、共享 eval/decoder/guardrail 及 sim0.1/cdf0.98/no-PV/6、23、27 dense 回退。

| 阶段 | 输出 | 决策与作用 |
|---|---|---|
| 严格 D/D1 | 原官方 adaptive WC | 真实准备、九门/五检查点与完整 pipeline 控制；不用于速度 |
| 严格 D/D2 | 固定38次 deep 的 dense | 与上一臂逐项及最终文件等价，否则停止 |
| 轻量 D | 同固定掩码 dense | 完整普通生成；必要来源/掩码开销计入 wall |
| 轻量 S | 同固定掩码 sparse refresh | 两臂实际 trace 相同，真实 S 来源进入后续 cache；之后独立四产物/费用/指标审计 |

在 D/D 与轻量配对之间恢复同一入口 RNG，每臂仍独立调用真正 prepare，不共享 prepared batch，不复用上臂 cache。固定 D 三份文件必须相同。测量部分不携带 D/D shadow 哈希/五处诊断观察，首次 S 和全部失败仍保留。四个产物全分母不删；D/D不通过则不生成候选。

主问题是 fixed-S 相对官方/fixed-D 的人物编码保真，以及 fixed-S 与旧 adaptive-S 的差异。旧视频仅在模型资产、输入/seed/grid、mode、decoder、guardrail/source 协议绑定后作曝光开发参照。三项损失不能被解释为独立可加因果贡献；仍无 Native/少步/调过 WC 前沿和 CONF。单个轻量 D/S 配对只能给描述性成本，不能替代速度重复或质量确认。

## 完整成本与执行边界

[成本草案](../reports/wc_fixed_human_four_output_cost_draft_20261004.json)保留全部四输出：诊断每臂以既有完整控制与人物 debug 最大381.750898秒规划，轻量每臂以八测量最大214.334779秒规划，加载95.915549秒；前次未分配整卡 wall44.888082秒，预留 bookkeeping50秒。合计1338.086904秒×1.2，再加结束结算30秒，**1635.704284秒**。

拟议独立单次1800秒全cost/1770秒child/kill5、预付0.5GPUh，现余额4.592373680066474h可覆盖。这里还没有选定 GPU 卡、冻结新 source/payload 或创建 reservation，也不复用已消耗的104点单次1800授权。下一先完善唯一 runner/scope、source/费用/资产/import/package/真实prepare/mode/metadata门，再新卡及 fresh UUID/VRAM/compute/无inflight/全局锁/磁盘准入；不重复旧任务，不自动批量参数扫描、训练或新增人评。

[68 刷新收益设计](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)保持后置。本次固定动作控制不是同状态预算匹配反事实标签；低相似度或9次动作差异都不解锁 Head。强基线与独立确认仍是最终研究目标的缺口，goal保持 active。
