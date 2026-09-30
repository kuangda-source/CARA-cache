# Next actions — CAL sparse W1-D running

1. 默认/recent scalar与shrink仅在旧AV四点NO_GAIN_IN_SCOPE，不送闭环、不继续无依据参数调整，也不否定整个方向。
2. [局部解码门](19_DECODER_POLICY_RESULTS.md)两个fresh进程通过：72net/latent与旧参考相同，权重/状态见证相同、flags恢复、decode至93帧RGB/MP4一致。不是全数据集确定性或独立根因证明；所有新对照必须共用该策略并再做off/on。
3. [CAL24清单](../manifests/cal_v1.json)按官方reference_video+词法近重复组冻结，前8涵盖7域+第2AV；4工程组排除。原recording/session语义独立性未证明，CAL仅校准，DEV/CONF未冻结。
4. [CAL前8 W1-D](20_CAL_AND_W1D_PREPARATION.md)已实现并运行，部署源62f1c0d，Linux44项CPU检查通过。原身份outputs/w1d-cal8-r1，supervisor2461004/timeout2461009/runner2461011；先查原进程/日志/回执，不重新提交或修改运行源码。23:09北京时间只读快照5/8 PAIR_PARITY_PASS，各8点、17项一致性检查通过；physics_045 OFF运行。见[启动](../reports/w1d_cal8_r1_launch_20260930.json)、[实时快照](../reports/w1d_cal8_r1_live_observation.json)、[部分汇总](../reports/w1d_cal8_r1_live_partial_summary.json)。LIVE_PARTIAL_NO_DECISION，不调候选、不据部分结果进入闭环。
5. batch硬上限6000秒/1.666667GPUh；启动前结算1.997774315/4GPUh，23:09在途另计0.668417GPUh，旧账本余额不能用于新准入。终态后核验原PIDs退出/锁可用、全程GPU归属、产物重新哈希、源码、监督器退出与wall成本，将runner/supervisor/audit/预算归档。完整终态仅执行scripts/summarize_w1d_cal.py生成固定8样本screen；随后scripts/analyze_w1d_cal.py生成分布/排序descriptive结果，scripts/plot_w1d_cal.py作图（新11项CPU检查通过，未改变原screen）；任何技术失败/超时按实际覆盖报告，不能重启或挑替补补齐。全部旧身份保持终态，不扩预算。完整F2多点12–24场景成本超现余额，不能以小子集冒充完成；终态后按机制证据和实际余额决定下一局部假设或报告资源缺口。
6. 不训练/付费评分/引入非必要人评。所有代码/配置/原始失败/结果/成本/实验总览/handoff同步私有GitHub。
