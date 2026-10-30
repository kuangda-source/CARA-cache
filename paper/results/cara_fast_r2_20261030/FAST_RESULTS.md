# Fast19 已接受结果索引

本页使用完整 B36 原回执与已接受图表。四个旧 CAL 输入等权；CHECK 是旧 CAL 内部留出。时间重复先在输入内平均，视频帧不增加独立输入数。

T_DD 从去噪循环前同步计至解码后同步，T_request 为驻留模型的完整请求。表内区间原样引用原 CSV 的 20,000 次输入簇 bootstrap，属于双侧 95% 探索性区间；未重新抽样。

| 原角色 / FIT 匹配标签 | T_DD (s) | T_request (s) | T_DD 加速比 [95%区间] | 完整请求加速比 | Alex | SSIM |
|---|---:|---:|---:|---:|---:|---:|
| NATIVE35 | 252.812242 | 318.301841 | 1.000000 [1.000000, 1.000000] | 1.000000 | 0.000000 | 1.000000 |
| SHARED25_C | 185.805542 | 251.952307 | 1.360628 [1.360224, 1.361005] | 1.263342 | 0.062266 | 0.888437 |
| F19_C | 148.447718 | 214.160169 | 1.703039 [1.702255, 1.703713] | 1.486279 | 0.249365 | 0.663106 |
| F19_A1 | 149.482379 | 215.195038 | 1.691251 [1.690807, 1.691628] | 1.479132 | 0.231499 | 0.673118 |
| UNIFORM19_C | 148.420845 | 214.557011 | 1.703347 [1.702171, 1.704137] | 1.483530 | 0.468931 | 0.531690 |
| WC_T006 [FIT UNMATCHED] | 130.013016 | 194.797263 | 1.944515 [1.922051, 1.956100] | 1.634016 | 0.464343 | 0.530523 |
| RA_T1 [FIT UNMATCHED] | 116.976452 | 181.899717 | 2.161223 [2.160698, 2.162089] | 1.749875 | 0.418125 | 0.553098 |
| NATIVE22 [FIT MATCHED] | 163.659443 | 227.645739 | 1.544746 [1.544210, 1.545516] | 1.398233 | 0.512458 | 0.478566 |

WC/RA 保留原 FIT UNMATCHED；Native-k 的 MATCHED 仅指原 FIT 时间选择。PSNR 逐输入保留 +inf，梯度分母未定义时保留 null 和输入身份，均见完整 JSON 与原 CSV。

## 原图表与可复核数据

- T_DD_speed_fidelity: [PNG](../../../reports/cara_fast_B36_figures_actual_r1_20261029/T_DD_speed_fidelity.png) · [PDF](../../../reports/cara_fast_B36_figures_actual_r1_20261029/T_DD_speed_fidelity.pdf)
- T_request_speed_fidelity: [PNG](../../../reports/cara_fast_B36_figures_actual_r1_20261029/T_request_speed_fidelity.png) · [PDF](../../../reports/cara_fast_B36_figures_actual_r1_20261029/T_request_speed_fidelity.pdf)
- Alex_frame_curves: [PNG](../../../reports/cara_fast_B36_figures_actual_r1_20261029/Alex_frame_curves.png) · [PDF](../../../reports/cara_fast_B36_figures_actual_r1_20261029/Alex_frame_curves.pdf)
- temporal_detail: [PNG](../../../reports/cara_fast_B36_figures_actual_r1_20261029/temporal_detail.png) · [PDF](../../../reports/cara_fast_B36_figures_actual_r1_20261029/temporal_detail.pdf)
- [per_member.csv](../../../reports/cara_fast_B36_figures_actual_r1_20261029/per_member.csv)
- [frame_curves.csv](../../../reports/cara_fast_B36_figures_actual_r1_20261029/frame_curves.csv)
- [prompt_equal.csv](../../../reports/cara_fast_B36_figures_actual_r1_20261029/prompt_equal.csv)
- [FIT_A_only.csv](../../../reports/cara_fast_B36_figures_actual_r1_20261029/FIT_A_only.csv)

## 原采集费用与当前范围

| 原运行 | 唯一结算 GPUh |
|---|---:|
| cara-fast-cal-a32-r2-20261028 | 2.2557055054700728 |
| cara-fast-f19-b36-r1-20261029 | 2.384553982338661 |

原 A32+B36 合计 4.640259487808734 GPUh，包含原预热、控制、校准、重复及分配开销；本索引新增 GPUh 为 0，未重新结算。

本批支持旧 CAL 上的高速布局与保真比较；新方法增量、新输入确认及人类评审不由此索引证明。25D 原 DEV128 仍为独立历史开发证据，不与本批混合计算加速比；S/Q 方法与 F18/Q5 后续结果保持待接受。

[原完整分析](../../../reports/cara_fast_B36_complete_analysis_r1_20261029.json) · [机器索引](accepted-results.json)
