# 104路径完整结果分析

仅由完整终态与独立接受生成；四CAL、seed0，两轮先按prompt合并。LPIPS表示相对Native的保真。

| 布局 | 两轮均时/s | LPIPS | 验证轮均时/s | 验证轮预算余量/s | 预测加6s可行 |
|---|---:|---:|---:|---:|---|
| NATIVE | 295.309 | — | 296.016 | -59.770 | — |
| PG_ALL_D | 296.974 | 0.000000 | 298.343 | -62.096 | False |
| GRAPH_DIVERSE_ORIGINAL | 241.010 | 0.071628 | 240.979 | -4.732 | False |
| S26_C | 239.185 | 0.060588 | 239.880 | -3.633 | False |
| S26_A_PHASE | 240.355 | 0.058537 | 240.790 | -4.543 | False |
| SHARED26_C | 239.652 | 0.050738 | 240.390 | -4.143 | False |
| S25_C | 233.246 | 0.082546 | 233.871 | 2.375 | False |
| S25_A_PHASE | 235.058 | 0.074504 | 235.289 | 0.958 | False |
| S24_C | 228.144 | 0.114207 | 229.472 | 6.774 | True |
| S24_A_PHASE | 229.216 | 0.095841 | 230.042 | 6.205 | False |

| 预登记比较（左减右） | 时间差/s | LPIPS差 | 四prompt改善数 | 描述性关系 |
|---|---:|---:|---:|---|
| GRAPH_DIVERSE_ORIGINAL − S26_C | 1.825 | 0.011041 | 0/4 | RIGHT_DESCRIPTIVE_PARETO |
| GRAPH_DIVERSE_ORIGINAL − S26_A_PHASE | 0.655 | 0.013092 | 0/4 | RIGHT_DESCRIPTIVE_PARETO |
| GRAPH_DIVERSE_ORIGINAL − SHARED26_C | 1.358 | 0.020891 | 0/4 | RIGHT_DESCRIPTIVE_PARETO |
| SHARED26_C − S26_C | 0.467 | -0.009850 | 4/4 | TRADEOFF_OR_TIE |
| S26_A_PHASE − S26_C | 1.171 | -0.002051 | 2/4 | TRADEOFF_OR_TIE |
| S25_A_PHASE − S25_C | 1.812 | -0.008041 | 4/4 | TRADEOFF_OR_TIE |
| S24_A_PHASE − S24_C | 1.072 | -0.018366 | 4/4 | TRADEOFF_OR_TIE |
| S25_C − S26_C | -5.939 | 0.021958 | 0/4 | TRADEOFF_OR_TIE |
| S24_C − S25_C | -5.102 | 0.031661 | 0/4 | TRADEOFF_OR_TIE |
| S25_A_PHASE − S26_A_PHASE | -5.297 | 0.015967 | 0/4 | TRADEOFF_OR_TIE |
| S24_A_PHASE − S25_A_PHASE | -5.843 | 0.021336 | 0/4 | TRADEOFF_OR_TIE |

| 24/25D布局 | 第一轮/s | 第二轮/s | 实测≤B | 预测+6≤B | 跨轮越界 |
|---|---:|---:|---|---|---|
| S25_C | 232.621 | 233.871 | True | False | False |
| S25_A_PHASE | 234.828 | 235.289 | True | False | False |
| S24_C | 226.815 | 229.472 | True | True | False |
| S24_A_PHASE | 228.390 | 230.042 | True | False | False |

| 冻结计时检查 | 实际值 | 原门槛 | 通过 |
|---|---:|---:|---|
| mean_absolute_relative_error | 0.0036121775019036517 | 0.01 | True |
| maximum_underestimate_seconds | 2.6179079333581967 | 2.0 | False |
| no_false_feasible | True | True | True |

冻结计时判据：TIMING_MODEL_VALIDATION_FAILED；平均绝对相对误差0.361%，最坏低估2.618s；B=236.246823s，余量固定6.0s。

表中全部布局保留。相同D数不能替代同实测时间；每项prompt差值、描述性区间、顺序漂移和组件闭合见同名JSON。诊断时钟不用作速度证据；年龄因果、独立感知质量和泛化需后续受控实验。

P1准备分支：`NEW_COST_CALIBRATION_AND_INDEPENDENT_VALIDATION_REQUIRED`。本报告不选择最终策略，不派GPU，不修改预算；新合同、曝光核查、完整报价与生产CPU通过后方可准入。

固定掩码的最大复用年龄（当前步减最近真实D步）：

| 布局 | 最大复用年龄 |
|---|---:|
| NATIVE | 0 |
| PG_ALL_D | 0 |
| GRAPH_DIVERSE_ORIGINAL | 2 |
| S26_C | 2 |
| S26_A_PHASE | 2 |
| SHARED26_C | 5 |
| S25_C | 3 |
| S25_A_PHASE | 3 |
| S24_C | 4 |
| S24_A_PHASE | 4 |

年龄表是布局描述，不是有效阈值：短年龄已有正证据，不等于只有年龄≤3才有效；SHARED26_C的最大年龄为5。年龄、位置、状态与alpha尚未单独隔离。
同D数用于消融，同实测时间用于方法竞争力比较。不同D/A组合也可构成有效优势，不能只以同D数胜负裁定贡献。少步Native按实测时间配平，并补独立质量指标。
固定6秒只加在预测提案上，实际时间门槛仍为B；不要求实测≤B−6。超预算3.89秒只描述时间差，不能由历史某次删D推断保真损失或修复难度。
增加重复可改善均值估计，不能自动消除系统偏差或缩减余量；当前余量不变，未来修改须独立校准验证。
接续诊断：`COST_MODEL_NOT_VALIDATED`。若模型通过而布局实测超B，优先研究更低成本候选；若实测可行但预测缺余量，单列提案保守性，不改写实测失败。
