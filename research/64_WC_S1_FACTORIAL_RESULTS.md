# S1真实QKV交叉控制：存在局部收益，尚无统一可用配置

2026-10-01；crossed-qkv-r1/source `de6ea8d`。本记录整理已完成的运行，不启动新任务。

来源：[预登记范围](63_WC_S1_REAL_QKV_RESULTS_AND_CROSSED_CONTROLS.md)、[部署](../reports/wc_s1_crossed_qkv_deployment_20261001.json)、[启动](../reports/wc_s1_crossed_qkv_r1_launch_20261001.json)、[终态](../reports/wc_s1_crossed_qkv_r1_terminal_20261001.json)、[审计](../reports/wc_s1_crossed_qkv_r1_fresh_audit_20261001.json)、[逐输入汇总](../reports/wc_s1_crossed_qkv_r1_summary_20261001.json)。

## 四个组合的观察

相同12个真实输入，各任务内重测dense/vanilla-full与每策略routed-full/sparse；no-PV、1warmup/3热repeat。预登记筛查是相对dense RMSE≤5%、操作wall加速≥1.1×，不是视频质量标准。两个任务共144case均finite，匹配全块控制最大RMSE0.753%。

| sim / CDF | 中位dense/sparse wall | 最大RMSE | 数值通过 | 速度通过 | 同时通过 |
|---|---:|---:|---:|---:|---:|
| 0.6 / 0.98，原public默认 | 1.019× | 1.35% | 12/12 | 1/12 | 1/12 |
| 0.1 / 0.90，原utils默认 | 2.139× | 24.04% | 2/12 | 12/12 | 2/12 |
| 0.1 / 0.98，交叉控制 | 1.286× | 6.08% | 8/12 | 10/12 | 6/12 |
| 0.6 / 0.90，交叉控制 | 1.062× | 4.47% | 12/12 | 3/12 | 3/12 |

0.1/0.98的四个数值失败都来自layer27，调用1/2/71/72的RMSE分别约5.35/6.08/5.78/5.70%。同策略layer2四个输入都同时通过；layer14晚期两个通过、早期两个速度不足。不能按这三个采样层直接制定全26深层策略，更不能事后放宽5%阈值。

降低sim后更少触发全块fallback，提高CDF后误差明显减小而节省计算减少。这支持进一步检查层/状态异质性；尚未证明某一参数的跨任务绝对时间因果效应，也未验证新调度机制。量化full控制误差小于激进mask误差，提示块选择是主要诊断对象。

## 关键覆盖缺口与下一门

12个QKV全部来自首尾强制完整计算调用1/2/71/72，只有layers2/14/27、一个已消费的开发场景/seed。候选稀疏刷新实际可能发生在中间WC miss，因此这些输入不足以证明S2可部署。

下一优先准备保持官方输出不变的中间刷新、全深层shadow诊断。冻结S0原轨迹中首调用≥17及≥35的首个完整CFG对，得到25/26与35/36；建议覆盖layers2..27，在call36完成原net.forward后提前结束。若以后采用该范围，需另冻结runner/source/hash、预算、预期partial语义与审计；本文件不将部分采样当完整视频，也不宣称300秒范围已实现或可准入。

中间状态诊断通过后，接入[最新来源与有效期分组设计](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)：先低侵入的S/D刷新对照，再验证缓存来源×复用1/2/4步，最后才少量层组C/S/D。保持shadow真值不回写，稀疏产物不升级为true dense anchor。

## 成本与审计边界

crossed任务实际监督GPU墙钟57.406171846669秒，120秒预留返还62.593828秒。原supervisor/timeout/runner/CPU PIDs已退出，global锁释放、监控见实际runner；72case覆盖与原始3repeat中位数、部署/package/input/dense来源hash和账本核对通过。输出RMSE由实际runner计算；审计没有重新执行全部输出误差计算。

累计账本3.9117525685110333/4GPUh，28jobs，余317.690753秒，无inflight。账本结算标签保留，独立审计状态见回执。没有新增预算、稀疏视频、新方法质量—时间结果或人工评审。
