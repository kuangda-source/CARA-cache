# B36 完整验收、参考保真与正式图表

B36原运行完整36/36、0失败；技术、原件、双时钟、独占热界、真实释放、原费用和完整32位置评分均已接受。原GPU于10:40:41退出，评分CPU于13:44:46退出；实际 **2.384553982338661 GPUh** 已中央唯一结算，硬5.5GPUh、cap226及旧16.5责任保持。两个自动检查均已删除。

4个旧CAL输入等权结果显示：在同19D预算与几乎相同去噪时间下，F19-C的Alex LPIPS为0.249365，比Uniform19-C的0.468931降低 **46.82%**，4/4输入同向。F19-A1进一步降至0.231499，相对F19-C降低 **7.16%**，同样4/4同向，去噪时间增加 **0.70%**。F19-C的注册T_DD速度为 **1.703×**，完整请求单独报告 **1.486×**。Shared25-C具有更低的参考误差（Alex0.062266），对应1.361×去噪速度，保留25D与19D之间的取舍。

| 方法 | T_DD秒 | 去噪加速 | 完整请求加速 | Alex↓ | SSIM↑ |
|---|---:|---:|---:|---:|---:|
| Native35 | 252.812 | 1.000× | 1.000× | 0.000000 | 1.000000 |
| Shared25-C | 185.806 | 1.361× | 1.263× | 0.062266 | 0.888437 |
| F19-C | 148.448 | 1.703× | 1.486× | 0.249365 | 0.663106 |
| F19-A1 | 149.482 | 1.691× | 1.479× | 0.231499 | 0.673118 |
| Uniform19-C | 148.421 | 1.703× | 1.484× | 0.468931 | 0.531690 |
| WC_T006（FIT UNMATCHED） | 130.013 | 1.945× | 1.634× | 0.464343 | 0.530523 |
| RA_T1（FIT UNMATCHED） | 116.976 | 2.161× | 1.750× | 0.418125 | 0.553098 |
| Native22（FIT MATCHED） | 163.659 | 1.545× | 1.398× | 0.512458 | 0.478566 |

正式与登记重复先在输入内取均值，再对输入等权；速度为Native均时与角色均时之比。T_DD与T_request分别报告，FIT原A来源的敏感性保存在独立CSV。93帧曲线、逐视频PSNR（包括自对照无穷）和梯度未定义身份均原样保留；统计抽样单位为输入，20,000次原种子prompt bootstrap仅作探索区间。

这是4个原CAL、seed0的比较，2个CHECK仍属于原CAL内部留出。WC_T006和RA_T1保持原FIT的UNMATCHED，不能形成三个家族都时间匹配的结论；Native22保持FIT MATCHED。完整结果不改变原A32十二对评分、一次冻结、alpha、mask或阈值，也不新增独立DEV/部署或端点竞争结论。

## 原件与接受链

- [最终本地重验](../reports/cara_fast_B36_complete_final_revalidation_r1_20261029.json)：五份原件重建、原source和launch/settlement/manifest/A冻结字节、两个检查删除均通过；没有重算指标。
- [完整机器摘要](../reports/cara_fast_B36_complete_summary_r1_20261029.json)
- [原GPU终态](../reports/cara_fast_B36_original_terminal_r1_20261029.json)、[原中央结算](../reports/cara_fast_B36_original_central_settlement_r1_20261029.json)、[原释放接受](../reports/cara_fast_B36_original_release_accepted_r1_20261029.json)
- [CPU原终态](../reports/cara_fast_B36_original_CPU_score_capture_r3_20261029.json)、[32位置接受](../reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json)、[完整分析](../reports/cara_fast_B36_complete_analysis_r1_20261029.json)
- [图表CPU真实接受](../reports/cara_fast_B36_figures_actual_CPU_acceptance_r1_20261029.json)、[图面与PDF/CSV检查](../reports/cara_fast_B36_figures_actual_visual_QA_r1_20261029.json)、[检查清理](../reports/cara_fast_B36_complete_acceptance_cleanup_r1_20261029.json)

## 正式导出

四组PNG/PDF和四CSV由未修改的原图表实现生成。独立CPU导出目录复制原source与已接受汇总/图表组件，1129文件逐项同SHA；1CPU/4GiB/禁swap/无GPU网络/root只读，正常退出，GPU/评分原stage均未改。图表入口重新验证五份原接受回执。

- [T_DD速度与保真](../reports/cara_fast_B36_figures_actual_r1_20261029/T_DD_speed_fidelity.png) · [PDF](../reports/cara_fast_B36_figures_actual_r1_20261029/T_DD_speed_fidelity.pdf)
- [完整请求速度与保真](../reports/cara_fast_B36_figures_actual_r1_20261029/T_request_speed_fidelity.png) · [PDF](../reports/cara_fast_B36_figures_actual_r1_20261029/T_request_speed_fidelity.pdf)
- [全部93帧Alex曲线](../reports/cara_fast_B36_figures_actual_r1_20261029/Alex_frame_curves.png) · [PDF](../reports/cara_fast_B36_figures_actual_r1_20261029/Alex_frame_curves.pdf)
- [时序与细节](../reports/cara_fast_B36_figures_actual_r1_20261029/temporal_detail.png) · [PDF](../reports/cara_fast_B36_figures_actual_r1_20261029/temporal_detail.pdf)
- [32行输入明细](../reports/cara_fast_B36_figures_actual_r1_20261029/per_member.csv) · [2976行帧曲线](../reports/cara_fast_B36_figures_actual_r1_20261029/frame_curves.csv) · [24行输入等权](../reports/cara_fast_B36_figures_actual_r1_20261029/prompt_equal.csv) · [6行FIT原A敏感性](../reports/cara_fast_B36_figures_actual_r1_20261029/FIT_A_only.csv)

连接经本机隔离代理和原SSH主机密钥恢复后完成全部取证；共享FRPC、TUN、SSH全局配置及原实验未重启。临时通道仍偶发断线，额外最后一次账本重读未成功；原中央结算快照按其观测时点保留，不能作为下一张卡的fresh准入。原GPU/CPU终态、费用与正式结果均已完整接受。后续新输入确认应另行登记完整范围与报价，本次不派发新卡。
