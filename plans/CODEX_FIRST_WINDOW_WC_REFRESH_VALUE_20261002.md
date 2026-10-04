# W3首窗口接续入口（2026-10-04更新）

当前详细计划：[WorldCache全帧保真与同配额位置干预 v1.6](WORLD_CACHE_W3_NEXT_WINDOW_20261004.md)。先读[当前状态](../research/02_CURRENT_STATE.md)、[队列](../research/09_NEXT_ACTIONS.md)、[真实恢复](../research/112_WC_RV0_REAL_RESTORE_RESULTS_AND_NEXT_GATE.md)及[118实际CPU](../research/118_WC_RV0_AUTHORIZED_SYNC_AND_ACTUAL_CPU_RESULTS.md)。已完成104点/S-H/阶段/FAIR14/恢复/CPU同步不重跑，W1只复用兼容既有视频分析。

1. 已有FAIR14十组Native比较及W1兼容性表，全93帧CPU LPIPS；复用现有计量检查，补实际不同输入/轻扰动，不新生成填缺失。
2. 重估新小卡完整父/参考/因果控制/两臂/编码/退出成本；原8父24后缀18输出仍未选且不缩身份。累计13h只余7119.663527秒，0.30h不是经测可执行cap。
3. 两CAL各一处合法checkpoint/CFG各一对自适应C/D：测有符号终点与后续成本，不能报同预算收益。
4. 新固定mask接口通过后，两CAL各至多两次合法C/D位置交换：每CFG完整配额匹配，两臂状态独立演化，保护不可移除；无合法点在新卡冻结前登记，不按结果替换。
5. 有空间才冻结phase/age/已支付probe的简单规则并用新seed或新场景确认；hindsight优势不作在线结果，同prompt新seed不作场景CONF。

本轮仅计划更新，无实际LPIPS评分、新C/D、交换或训练。此前CPU限定同步已完成；CPUproject-view不作GPU账本/锁目录。下一执行沿用具体权限、真实根目录/来源绑定与live资源/完整对预算；不从文档建议扩大授权，亦不重复索要已完成事项的许可。

## 历史首窗口记录（下文为各时点快照，非当前续跑指令）

<!-- Latest real restoration: ../research/112_WC_RV0_REAL_RESTORE_RESULTS_AND_NEXT_GATE.md; full causal RV0 and signed benefit remain incomplete. -->
<!-- Current execution evidence: ../research/111_WC_RV0_RESTORE_EXECUTION_CARD.md; full RV0 remains incomplete. -->
# WC-RV首窗口：先验证刷新收益空间，不先训练Head

> 最新恢复与成本准备：[110](../research/110_WC_RV0_FROZEN_CONDITION_RESTORE_AND_COST_CARD.md)。官方frozen条件恢复已修复并CPU验证；两场景/四条未干预后缀入口及3900秒费用预案已具体化，真实模型恢复、完整C/D因果RV0和收益仍待证。下一先独立执行器/冻结部署与实际门，配置未选择GPU；累计预算保持10.713586944446/12h。

> 2026-10-04动作CPU更新：[109](../research/109_WC_RV0_ONE_ACTION_CPU_CONTROLS.md)。一次当前CFG C/D干预加原自适应后缀的Toy CPU控制通过；尚无真实模型标签、等预算验收或已选择GPU卡。账本仍10.713586944446/12GPUh，以当前状态文件为准。下面旧接口缺口保留其当时阶段。

> 2026-10-04最新：原冻结科学工作已完成，[107](../research/107_WC_FAIR_CAL_RESULTS_AND_DIRECTION_GATE.md)未支持稀疏净收益；本轮完成[108 CPU未干预后缀控制与成本准备](../research/108_WC_RV0_CPU_SUFFIX_CONTROLS_AND_COST.md)，R3四组/交换顺序/完整父轨迹复现与来源独立审计通过。仍无真实GPU分叉、C/D路由/收益标签/拟合/训练，下一先CPU动作与保护合同及开销包络。现累计10.713586944446/12h、44jobs无inflight，余1.286413055554h；两拟cap仅算术草案，未选择GPU卡。下文旧状态为历史。

最新补注：[r3最短技术门](../research/73_WC_MIDDLE_R3_PARITY_RESULTS.md)在后续独立授权下通过并结算，但没有正式C/D分叉或GPU恢复后续推，不验收完整RV0。先完成当前科学卡的因果门及成本提案，RV仍无标签/拟合/训练授权，禁止自行r4。最新4.390463858430222/12GPUh、余7.609536141569778h；以下r2/旧4h条目为历史。

2026-10-03接续补注：[r2终态](../research/71_WC_MIDDLE_R2_RESULTS.md)未通过跨阶段输入/完整状态门，原数据只用于局部算子诊断，不验收RV0。先CPU全RNG、命名输入/状态与条件闭包预案，再具体卡和实际门；无第三窗口或RV采集/拟合授权。累计4.255375150608726/12GPUh，余7.744624849391274h，以下旧4h/317秒是历史快照。引用对话新增总规划只更新研究分工，不改变当前执行顺序。

[2026-10-03累计12GPUh新授权](../research/BUDGET_AUTHORIZATION_20261003.md)：原建议/未拨款为历史，具体卡仍须资源与停止门，禁止重复旧任务。

2026-10-02；DESIGN_ONLY。按[68完整设计](../research/68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)接续W3，当前冻结WC-S/H工作先完成，执行顺序以[09队列](../research/09_NEXT_ACTIONS.md)为准。

## A. 可准备内容

1. 阅读现有回执、运行适配与WC代码图，列清probe后/deep前的决策点、CFG两槽位、完整UniPC状态。先给恢复检查与Head-off等价检查的接口预案；未实际实现或运行不能报PASS。
2. 逐项标注在线特征何时已产生、张量大小、归约/clone/同步成本；当前deep真值/未计算attention/未来视频严禁作为输入。
3. 提议q的branch-call或solver-step单位、强制D预留与两臂可行条件；分开固定后缀边际标签和预算匹配标签，保存完整σ版本。
4. 给RV1成本表：FIT8×1seed、3个合法位置交换候选、最多24分叉状态、K4/8及预选8终点。样本上限仅用于估价，先根据成本缩范围，不据余317.690753秒直接提交。
5. 新场景按源/首帧/prompt/seed成组，旧CAL8只开发；确认标签未来去向、失败和缺失规则、Native参考兼容性，保持现有collector/runtime/配置不改。

## B. 具体成本窗口通过后才执行

先RV0实际恢复/因果检查，再RV1同刷新数位置交换与短/终点分叉。只改变合法刷新位置、共用原近似器；实测时间不匹配时不称等时比较。没有可信标签或收益空间，不训练Head；仅有限候选hindsight优势不能认定可部署收益。

正式Head需要RV2预算匹配标签、拟合范围与新数据划分。训练主干冻结，比较时间/年龄/预算规则、线性/树、小MLP和局部误差Head；闭环及分布补采分别登记。LoRA、第三动作、逐层token门控不在此窗口。

## C. 输出与边界

输出接口/状态清单、特征因果表、预算和后缀定义、完整成本提案及下一张最有信息的卡；实际运行后再补PID/日志/退出、source/输入hash、全部样本与预算。

原4GPUh与new4h/clean50提案不改变。当前没有RV collector、标签、拟合、训练、GPU或新方法结果；不启动或取消现有服务器任务，不默认人评或付费。

## 2026-10-02 文档包 alias 适配

新增原包作为参考，[编号与证据适配](../docs/portfolio_20261002/ADAPTATION.md)和[文档短接续](../docs/portfolio_20261002/RESUME.md)登记最新入口、未决门槛和来源。原实验卡、冻结合同和执行状态保留；本次没有执行或追加额度。
