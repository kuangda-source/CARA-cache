# CARA-Cache 后续实验顺序

{{snapshot}}

## 后续探索当前版本：E1 V2.2

[V2原始包](repo:plans/cara_predictor_refresh_scout_v2_20261026/source/01_Research_Assessment_and_Plan_V2.md)及[原绑定表](repo:plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_BOUND_V2.yaml)保持不变；未来探索以[V2.2修订说明](repo:plans/cara_predictor_refresh_scout_v2_20261026/E1_V22_AMENDMENT_AND_FREEZE_CHECKLIST.md)和[增量登记](repo:plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_PATCH_V22.yaml)为准，见[707](repo:research/707_CARA_SCOUT_V22_STRATIFIED_READOUT_PLAN_20261026.md)。

先E0已有资产与DCTA核查，再E1同状态五类/六逻辑读出（global/long两新候选），之后E2-R固定布局读出，条件满足才E2-I交互。主分母是全队列最强固定基线，不是逐prompt oracle。22/23/25/33/34/35的保存掩码/网格元数据已复算，短长各6点；新端口支持/状态恢复、精确数值及费用门、双端CPU和完整报价尚未通过，不能称完整冻结。

已有锐度/MUSIQ诊断复用，Native-relative梯度与固定轻模糊对照未做。E2-R/I各16逻辑输出，合并完全同身份可复用8条时为24唯一机制输出，否则32；warm/Native/强参考/重复/评分另报，不能沿用旧16条/2–3GPUh为完整报价。原三项质量门、α、强基线、累计226及最终部署预算保持；DEV128原自动检查和运行合同不变，未新增GPU授权/预约，不读其中途结果。

{{queue}}

## 本轮授权范围与下一步

CAL66已完整接受并结算，Shared25-C被冻结为唯一新DEV主候选；用户已授权并实际启动两卡DEV128，旧四卡R2不得派发。

16DEV六角色128路径、原α和强基线保持。两端生产CPU与财务修复补验接受，首次使用前双端曝光复核通过；本次按用户指定两卡执行，报价11.618228GPUh、硬12h。新执行stage、中央单次意图、fresh独占和磁盘准入均已完成。

DEV128完整接受后仍按原三分支合同判断；新的机制探索采用V2.2的E0→E1→E2-R→条件E2-I顺序。20D、换步数及第二骨干均为条件后续，不因DEV结果正向自动启动。WC固定工作点和RA公平对照保持；RA固定掩码可提前登记为E2布局，不无条件另开重复卡。所有新卡独立完整报价，累计226和最终部署预算不变。

## 已完成历史与暂缓方案

- 原P1未选出预算内策略，原件及实际2.557833 GPUh保留。
- 完整104 R2接受，历史强布局超过原GRAPH；计时最大低估2.618秒失败，实际7.395282 GPUh保留。
- COST112完整接受，计时最大低估5.006秒失败，实际8.139511 GPUh保留。[归因691](repo:research/691_CARA_COST112_CAUSE_SEPARATION_AND_P1_REPAIR_PLAN_20261025.md)。
- 新纯计时重跑和GRAPH102暂缓；原CPU与未执行报价保留，不重新解释为成功。
- 旧两卡16.5 GPUh未知责任预约继续保留；旧两卡实验不重启；当前两卡隔离运行环境已通过CAL66迁移接受。

[新合同](repo:plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md) · [本轮记录694](repo:research/694_CARA_CAL66_REDESIGN_MASK_IDENTIFIABILITY_AND_QUOTE_20261025.md) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [历史计划](repo:docs/archive/README.md)

最新执行见[705实际独占启动](repo:research/705_CARA_DEV128_A6000_EXCLUSIVE_LAUNCH_AND_ACCEPTANCE_SCHEDULE_20261026.md)：两卡GPU1完整128已于13:36:59启动；双端财务兼容修复后各10生命周期、6存储、63终态检查接受。单卡12h/累计226与最终部署预算不变；仅跟踪原launch，不重复派发。
