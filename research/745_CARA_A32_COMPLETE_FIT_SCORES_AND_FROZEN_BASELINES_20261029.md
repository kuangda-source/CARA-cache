# 745：A32完整验收及真实基线一次冻结

A32已完成GPU、费用、释放、12对真实CPU评分和一次冻结的完整链。原GPU于00:33:01结束，完整32/32，原实际2.2557055054700728GPUh已中央唯一结算；原句柄/锁释放、Default恢复。CPU评分于00:55:16启动、01:01:26正常退出0、无OOM，12/12配对的93帧、92时序对、PTS、实际参数/权重/源码、完整曲线与汇总及2CPU/8GiB无GPU边界均接受。[原GPU完整接受](../reports/cara_fast_A6000_release_accepted_20261029_0053.json) · [原CPU终态](../reports/cara_fast_A6000_CPU_scores_terminal_20261029_0107.json) · [评分独立接受](../reports/cara_fast_A6000_CPU_scores_accepted_20261029_0108.json)。未重派或重评。

## 冻结选择与时间匹配边界

[原一次冻结文件](../plans/cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json)严格执行已登记规则：每个FIT目标为该输入Native35的T_DD/1.5；两个FIT的最坏相对误差不超过5%才进入Alex排序；无合格点时选择最邻近者并保留UNMATCHED。不扩大网格、改阈值或换参考。

| 家族 | 冻结候选 | 最坏目标时间误差 | Alex均值 | 时间匹配 |
|---|---|---:|---:|---|
| WC | WC_T006（本地PaperPort，tau0.06） | 23.2983% | 0.482825 | UNMATCHED |
| RA | RA_T1（原校准倍数1） | 30.6229% | 0.412405 | UNMATCHED |
| 少步Native | NATIVE22（请求22、实际23更新） | 2.9514% | 0.538501 | MATCHED |

这些均是两个旧CAL内FIT输入、seed0、同卡同生产入口相对本次干净Native35的全93帧保真；不是新DEV或F19比较。WC与RA不匹配的方向是**比目标更快**：两FIT的T_DD倍率分别1.910–1.956、2.160–2.162，Native22为1.544–1.546。不能把三个家族都称为同时间比较；T_request另存，不能用T_DD倍率代替请求倍率。[全部12个校准位置与原双时钟](../reports/cara_fast_A6000_frozen_calibration_analysis_20261029_0110.json)。没有据此宣布F19收益或扩展搜索。

## 实际A到B承接已核对

在真实六份完整原件上运行已通过双端CPU控制的 `read_handoff` / `bind_handoff`，验证原决定与原评分/费用/释放链完全一致、14个共享源码及同一物理GPU。[实际承接文件](../plans/cara_next_stage_20261028/mainline/r2/A32_TO_B36_BOUND_HANDOFF.json)已生成，`CPU_fixture_only=False`，但 `authorizes_phase_B=False`、`GPU_dispatch_ready=False`。本步仅核对metadata，不运行B36；保留WC/RA的UNMATCHED。

半程检查`a32`和原最终检查`a32-2`均已完成删除，无剩余A32后台检查。B36仍为独立完整36条，原A6000报价约5.022GPUh、建议硬5.5，需要独立授权和新的实际宿主/资源准入；不能据GPU空闲、CPU承接或已冻结基线自动启动。历史60行科学记录保留，A32校准结果在本独立记录中报告。
