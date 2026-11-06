## 最新执行状态

累计50h实际生效；完整GPU任务3313447/3313516及绑定CPU等待3313629已启动，source12bc430保持，完整scope未缩。见[157实际执行](157_WC_CFG_FACTORIAL_50_GPUH_EXECUTION.md)。下文“尚未GPU/预算待答复”保留为历史，不再适用。

## 2026-10-08 最新：累计50h已获直接批准并写入服务器，完整卡接续

用户直接批准24→50，原用量22.314242424/59jobs与失败费均保留，余27.685757576h。原子更新、原预算存档与授权SHA见[实际回执](../reports/wc_cumulative50_authorization_receipt_20261008.json)。单次≤2h自主规则保持；下文24→25请求/blocked均为历史，已不待回复。

[新selected配置](../configs/wc_w3_cfg_factorial_selected_r1_20261008.json)只改变原CPU允许的五项动态字段；全部277载荷、完整scope、生产静态绑定与已通过的CPU源9c69152不变。下一实际selected绑定验证与fresh准入唯一执行1父10后缀6视频；当前尚未GPU提交，没有新四组合质量结果。

# 补齐 CFG 四组合：CPU 已通过，完整执行等待累计预算

2026-10-08。本轮首先完成已获准的联合CFG原卡，完整结果见[155](155_WC_CURRENT_CARD_FIXED_REFERENCE_RESULTS.md)：联合刷新修复单分支退化约2.397%，但比原WC失真仍高0.453%；当前加2/未来省2，全程同为35次。旧两项历史验收失败保留，评分是卡内共享状态、固定参照的探索性诊断。

依[事前计划](../plans/WORLD_CACHE_CFG_FACTORIAL_WINDOW_20261008.md)和[冻结登记](../manifests/wc_w3_cfg_factorial_r1_preregistration_20261008.json)，下一卡用同一新快照补齐BASE、只D45的CFG0、只D46的CFG1、D45+D46的PAIRED，区分单槽净作用和两槽的自适应总效果交互。旧三细胞不拼成新四细胞因果对照。

## 完整范围与实际 CPU 证据

`WC-W3-CFG-FACTORIAL-R1-20261008-A` / `wc-w3-cfg-factorial-r1`：1原WC父、10完整后缀、6新视频、1旧Native参照、4细胞全93帧损失、4预定对比及1交互量。保留五组严格重复、共享pre45/当前输入、BASE/CFG1及CFG0/PAIRED两个pre46桥、原生各自继续、70reset和71/72完整尾。实施只请求登记的D，不强制其他C；原生D/no-op也保留分母。

| 检查 | 实际结果 | 证据性质 |
|---|---|---|
| 新核心 source c686ce9 | CPU264.922637秒/exit0；4成功父、40完整后缀、24 mock输出，4故障恢复、92项破坏拒绝 | 实际固定源码采样器/CPU Toy接口，无模型权重、真实视频或GPU质量结论 |
| 核心独立重建 | 原组件/总指纹/配置原值、五组重复、实际deep动作和两个分支前缀均通过 | 从原始记录重算，不只读PASS汇总 |
| 新生产 source 9c69152 | CPU54.484379秒/两步骤exit0，277份载荷保持，27本地依赖、7项合同拒绝通过 | 实际延迟导入、guardrail缓存/Blocklist、原生请求及CPU LPIPS资源实例化；零评分/零CUDA |
| 评分算术 | 实际嵌套PTS格式/原三损失加mock缺失槽检查、15项拒绝 | 算术与格式检查，缺失CFG0没有新科学结果 |
| 原监督器预算表达式 | 拒绝当前余额、在途、错误cap和非有限费用；虚拟25h只有算术通过 | 未写账本、未获得预算批准、未选择/提交GPU |

实际核心两个PID3303780/3303781与生产三个PID3304431/3304432/3304536均退出；各CPU新stage唯一提交，不重启原身份。全部CPU禁止CUDA和下载，根预算前后字节不变。

原CPU部署后的本机launch回执文件名未同步，因旧文件已存在而拒绝覆盖；远端CPU已经唯一启动。保存该[本机捕获失败](../reports/wc_w3_cfg_factorial_core_cpu_r1_local_capture_failure_20261008.json)，只读取新stage原始launch补存，没有重复提交。早期评分算术夹具只用标量PTS，未覆盖实际嵌套列表；原回执保留，后续源单独覆盖实际PTS格式。

新源记录scheduler `_internal_dict`实际完整值、保留默认参数名字原排列，再分列数值字段和已知元数据；实际完整状态指纹仍严格绑定。这个记录修补证据缺口，不改变旧配置或追认历史失败。

## 完整预测与唯一待决事项

原联合完整预测5979.545582秒保持；增加两个后缀各475.162955秒（保留原保守代理，高于本次实测最大362.718424），一条额外视频49.837106秒（本次最大完整解码/guardrail/编码），新增项继续乘1.2。全卡7179.741201秒=**1.994372556 GPUh**；原加载、准备和释放余量不删。这是预测，不是新增秒数截止。

现已结算**22.314242424/24 GPUh**、59jobs，无在途，余**1.685757576 GPUh**。完整预测比余额多0.308614980h；预测完成后总额24.308614980h。单次小于2h的自主约定保持，但不能据此越过累计24h预算。

当前[277份生产草案](../configs/wc_w3_cfg_factorial_production_r1_20261008.json)选择false、GPU UUID空、预算扩展权威空；原监督器已实际CPU验证会拒绝当前余额。全部必要CPU准备完成，**没有提交新GPU，也不删对照或重复以挤入余额**。

建议提报一次具体问题：是否把累计上限从24增加到**25 GPUh**，执行上述完整卡？已有用量和失败费不清零、不转移；单次≤2h自主规则不变。得到直接答复后仅绑定预算权威/账本、所需selected配置与实际CPU绑定检查，再fresh GPU/共享锁/余额准入唯一执行。若不增加预算，保存本轮全部成果并讨论用现有结果收敛或其他方向，不自动启动训练/稀疏/人评。

## 原件入口

- [核心终态原件/SHA](../reports/wc_w3_cfg_factorial_core_cpu_r1_20261008_terminal_capture.json)、[独立重建](../reports/wc_w3_cfg_factorial_core_cpu_r1_independent_audit_20261008.json)。
- [生产终态原件/SHA](../reports/wc_w3_cfg_factorial_production_cpu_r1_terminal_capture_20261008.json)、[独立源/资源绑定](../reports/wc_w3_cfg_factorial_production_cpu_r1_independent_audit_20261008.json)。
- [完整预算表达式检查](../reports/wc_w3_cfg_factorial_budget_gate_cpu_20261008.json)、[实际PTS评分算术](../reports/wc_w3_cfg_factorial_score_arithmetic_cpu_r2_20261008.json)。

这一配置尚无真实新结果；CPU准备不能当新方法通过。当前W3有条件性机制信号，原WC净保真优势与推广仍待。原正/负/no-op例、原判据和费用全部保留。
