# CARA 问题队列 R18

2026-10-28。现行依据为[最新总计划](cara_next_stage_20261028/01_Master_Experiment_Plan.md)、[S/Q修订](cara_next_stage_20261028/02_SQ_Method_and_Experiments.md)和[接收/两对话分工](cara_next_stage_20261028/08_REPOSITORY_RECONCILIATION.md)。原R16[逐字归档](cara_next_stage_20261028/QUESTION_QUEUE_BEFORE_R17.md)。以下均是准备/条件提案，非GPU授权。

| 阶段 / 负责人 | 当前状态 | 下一步与边界 |
|---|---|---|
| P0 · 主线 | 数值/评分组件完成；Ada CPU退出两次142 | A6000终态通过；下一最小CPU为退出栈诊断，复用组件、不重跑完整矩阵；原WC73不重派 |
| F19 · 主线 | 掩码/入口/报价已具体化；无新GPU | [主线准备](cara_next_stage_20261028/mainline/README.md)：60条为范围修订提案，最小A24；新卡接线、资源/准入与授权仍待 |
| S-FAST19 · S/Q探索 | 与F19准备并行；完整分支矩不足 | 旧资产覆盖审计，BR/DIAG/CFG共同语法与合法交换/掩码等价；不从12状态生成全36步结论 |
| Q0-Q1 · S/Q探索 | 双卡CPU准备；固定Shared25-C | 真实r窗口INT4/INT8打包、同字节及源绑定读出；raw误差不替代实际输出或部署峰值 |
| A-SQ-FAST · S/Q探索 | 仅明确缺口后准备采集卡 | 绑定新父策略的108标签/56额外Dense pair与存储；解决F19 raw和Q25布局兼容问题，共同费用只计一次 |
| S-END / Q-END · S/Q探索 | 各自条件晋级，不互设成功前提 | 不同合法mask或实际同bytes读出证据后，冻结最小完整视频比较与强基线，再报价申请 |
| F18 / Q5 · 主线，S/Q提供冻结规则 | 后置；可先做CPU可辨识性 | 冻结方法后检验唯一相邻预算/新网格；不扫描预算或指数制造赢家 |
| WAN / FINAL · 主线 | 迁移后置、最终输入持续保护 | 冻结checkpoint/协议/比较及完整报价；保留16最终输入和额外seed子集，实际曝光先核查 |
| B-S / B-Q / B-E · 按失败位置指定单一负责人 | 休眠；当前未启用 | 最多一个备用进入新GPU探索；不自动恢复IG/R4/GRAPH/F/B |

## 原件与停止边界

| ID | 问题 | 已完成范围 | 边界 |
|---|---|---|---|
| DONE / CAL66 | 位置/读出/少步Native筛查 | ☑ 完整66接受，冻结Shared25-C | 已曝光CAL，非独立确认 |
| DONE / DEV128 | 固定布局16新DEV | ☑ 完整128接受，主比较LPIPS改善14.82% | 已成后续选择的开发证据；不得再作A最终确认 |
| DONE / AGE3-REVIEW | A限龄版质量权衡 | ☑ 原质量/平均预算界通过，对C LPIPS改善6.68% | 事后门分析，Native26 MUSIQ区间未过；见734 |
| DONE-STOP / R4-R2 | 新状态共同项修正 | ☑ 6路径84位置完整，科学门失败 | 仅比A好1.65%、一输入退化；1.619241GPUh结算；不进E2 |
| PAUSED / IG | Scalar/Band创新量 | ⏸ 用户暂停；B1结果保留 | 不执行B2/B3，不借新名字恢复 |
| DEFERRED | 旧GRAPH102、F/B、旧在线门控、额外纯计时、单支刷新、本体量化 | ⏸ 暂停/关闭 | 旧代码和失败原件保留，不自动重开 |
| DEFERRED / 20D | 更激进配额 | ⏳ 后置 | 主线正向与完整公平基线后再报价，不取消历史计划 |

WC73已按736/738热停并结算，原完整A门未形成、B未启动，不重派原73槽。上述F19为高速可行性候选；S优先19D，Q先固定25D，原25D S方案保留。

Fidelity-v2仅用于未来逐卡冻结提案；旧质量门、原α、完整请求双预算与结果不改。DEV128已成为后续选择的开发证据，原最终输入继续保护。

最近保存账本cap226、used175.8058597668662、reserved16.5、available33.694140233133794 GPUh不是实时余额。新分池不等于hard limit/预约或授权，两个对话共用中央账本；一份公共采集不重复记费。双端准备、唯一责任、硬独占和每宿主不重叠要求保持。

本轮主线准备见[740记录](../research/740_CARA_FAST_MAINLINE_PREPARATION_AND_CPU_EXIT_BOUNDARY_20261028.md)；[原R17队列](cara_next_stage_20261028/mainline/QUESTION_QUEUE_BEFORE_MAINLINE_R18.md)保留。原56仅规划上界；本轮两候选/重载预热完整计费后为60条提案，未预约或执行。Ada成功proof不覆盖两次142终态，禁止写成双端整CPU通过。
