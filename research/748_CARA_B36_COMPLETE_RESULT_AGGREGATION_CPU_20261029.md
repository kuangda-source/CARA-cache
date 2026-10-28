# B36 完整结果汇总的双端 CPU 验证

B36正式结果汇总工具已完成，双端各6项CPU控制通过。当前仍等待用户明确批准预计5.021509、硬5.5GPUh的单次B36；没有B GPU派发、预算预约、新指标计算或正式B科学结果。[独立CPU接受回执](../reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json) · [执行审批卡](../plans/cara_next_stage_20261028/mainline/r2/B36_GPU_REVIEW_R2.md)。

原执行入口的双端22项CPU接受、20个实际资产核验及52个执行源码字节均保持；本次新增汇总代码独立于这52个文件。未重跑A32或其12对评分，原一次冻结SHA仍为 `56e1eb84fed0a459ae8fdeb6598680009226dced9529052cabc57cf11cef2be8`，历史科学表保持60行。B的实际基线继续为WC_T006、RA_T1、Native22，WC/RA的UNMATCHED不变。

## 实际控制证据

| 项目 | four_card | two_card |
|---|---|---|
| 最终CPU容器 | analysis-CPU-ada-r25 | analysis-CPU-a6000-r25 |
| 实际时段，2026-10-29北京时间 | 03:06:49–03:07:00 | 03:07:02–03:07:11 |
| 汇总控制 | 6项全通过，无跳过 | 6项全通过，无跳过 |
| 实际终态 | exited / 0 / Pid0 / 无OOM | 同左 |
| 资源 | 1CPU/4GiB、禁swap、core27、无GPU/网络、只读root | 同左 |

两端16个runtime源码摘要一致；实际源码包与容器注册摘要一致。测试使用完整A元数据和合成B元数据，GPU/引擎观测沿用既有显式模拟夹具；没有载入Torch、权重或度量网络。生产汇总入口拒绝此类CPU夹具，不会将其写成B结果。

首轮R24在测试初始化时因打包清单缺少夹具引用的 `dispatch_cara_fast_b36_score_cpu_r2.py` 退出1，执行了0项测试。已补齐CPU打包清单，用全新R25目录验证并接受；原R24失败回执及目录保持，不重启或覆盖它们。

## 原规则的具体实现

- 先重新验证原B完整终态、唯一中央结算、释放、32位置manifest、原26新评分加6份未改A评分，以及已接受32位置回执的一致性。运行中、UNKNOWN、缺行、混源、变更冻结或未接受数据均不能进入汇总。
- 对每个输入与角色，先平均其正式计时及登记的干净重复，再按输入等权汇总。全部32正式位置加6个重复，共38个互异计时来源；预热及A诊断不参与。`T_DD`、`T_request`分别报告，组速度比为输入等权Native均值除以对应角色均值，同时保留逐输入速度比。
- 分别保存ALL四输入、FIT两输入、CHECK两输入的结果。三个冻结基线另外报告FIT仅使用原A正式计时的敏感性结果，Native分母不加入B重复；它不重新选择基线。
- 原32位置的93帧Alex/SSIM曲线、q95、首次最差帧、视频PSNR、时序残差和梯度统计原样保留。PSNR保留逐输入原值及 `+inf`，不另作有限子集平均；梯度比任一输入未定义时，组值为null并列出输入，不丢弃该输入。
- WC/RA始终标注原FIT冻结的UNMATCHED，Native22为MATCHED。两个CHECK仍是旧CAL内的留出角色；不新增质量门、统计显著性、独立DEV或部署结论。

## 实际执行边界

汇总入口为 `scripts/analyze_cara_fast_b36_complete_r1.py`，读取显式指定的capture、settlement、manifest、score-capture及accepted-scores，只向新的output路径写入一次。输入按单次读取的原字节计算SHA，输出记录完整原件和汇总代码身份，已有输出拒绝覆盖。

只有B完整接受并释放、26新评分完成且完整32位置接受后才运行这个入口。它不会调用模型、指标网络、GPU派发、预算操作或重新冻结。见 [汇总交接](../plans/cara_next_stage_20261028/mainline/r2/B36_ANALYSIS_READINESS.md)。
