# CARA-Cache 后续实验顺序

{{snapshot}}

{{queue}}

## 本轮授权范围与下一步

用户已授权新的完整CAL66 R2独占执行及半程/最终验收。新R2身份、真实参数链和监督/存储CPU、stage与磁盘保护已接受，当前等待空闲GPU；每30分钟检查准入，见[700](repo:research/700_CARA_CAL66_R2_BOUND_CPU_STORAGE_AND_IDLE_GPU_ADMISSION_20261025.md)。原R1失败已结算，不重放；新卡预计6.880951GPUh，上限8，累计226和最终部署预算不变。

空闲卡通过fresh源码/资源/账本核验后单次启动。已有intent或UNKNOWN只恢复原句柄，不重复prepare/provision/launch。半程与全程检查绑定新launch实际起点；完整接受后按原冻结合同选一个主工作点，首次DEV前做增量曝光审计并重新报价128请求；不承诺其必然装入12GPUh规划池。

若新DEV正向，新增工作点优先20D；构造规则迁移优先同模型换步数，并包含仅传播先验与缩放模板。WC保持官方工作点，RA在预登记CAL有限阈值网格对齐时间。所有新卡独立报价，不放宽累计226和最终部署预算。

## 已完成历史与暂缓方案

- 原P1未选出预算内策略，原件及实际2.557833 GPUh保留。
- 完整104 R2接受，历史强布局超过原GRAPH；计时最大低估2.618秒失败，实际7.395282 GPUh保留。
- COST112完整接受，计时最大低估5.006秒失败，实际8.139511 GPUh保留。[归因691](repo:research/691_CARA_COST112_CAUSE_SEPARATION_AND_P1_REPAIR_PLAN_20261025.md)。
- 新纯计时重跑和GRAPH102暂缓；原CPU与未执行报价保留，不重新解释为成功。
- 旧两卡16.5 GPUh未知责任预约继续保留；退役两卡不恢复。

[新合同](repo:plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md) · [本轮记录694](repo:research/694_CARA_CAL66_REDESIGN_MASK_IDENTIFIABILITY_AND_QUOTE_20261025.md) · [完整实验总表](repo:paper/EXPERIMENT_MASTER_TABLE.md) · [历史计划](repo:docs/archive/README.md)
