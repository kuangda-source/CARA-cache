# CARA 主线实验概览

主线方法和范围见 [MAINLINE](docs/MAINLINE.md)。这里按证据用途组织已完成实验；原件保持原字节，具体身份和实际费用以各原回执为准。

| 实验 | 已完成证据 | 在当前主线中的用途 |
|---|---|---|
| CAL35 / F17 | [完整接受](reports/cara_f19_speed190_complete_r1_20261103/complete_acceptance.json) | 内部人工强基线 F17-A2+lightC 的来源 |
| sensitivity8 | [原协议](plans/cara_next_stage_20261104/sensitivity/PREREGISTRATION.md) | 经验终点响应和特征漂移的校准来源；不是新确认输入上的额外在线测量 |
| G17 with-nonfast | [完整结果](reports/cara_g17_minitest_nonfast_r1_20261105/COMPLETE_RESULTS.md) | 记录早期生成模型的预测偏差，保留失败/不确定结论 |
| AVSLC | [完整结果](reports/cara_avslc_minitest_r1_20261105/COMPLETE_RESULTS.md) | A/light-C 与长龄结构诊断，支持选择冻结 M0A_all；旧对照重用关系不变 |
| generator v1 | [冻结说明](plans/cara_next_stage_20261105/generator_v1_frozen/FROZEN.md) | 固定参数、MEAN 特征与 R16/R18/R21 布局，之后不重拟合 |
| confirm10 原轮 | [部分结果](reports/cara_generator_v1_confirm10_r1_20261105/PARTIAL_RESULTS.md) | C01–C04 四输入、16 原始分数；C05 文字拒绝，完整十输入终点不可评价 |
| confirm10 续跑 | [接管收尾](reports/cara_generator_v1_confirm10_continuation_r1_20261106/takeover_closeout/REPORT.md) | C06 有效产物、C07 F17 视频拒绝、原释放及唯一结算 |
| C06 补评分 + primary11 | [最终完整报告](reports/cara_primary11_r1_20261106/REPORT.md) | 现有全部 26 个有效候选/Native 配对；八输入 R18/F17 对比及五驾驶输入多预算取舍 |

最新固定九输入中 Native、F17、R18C 均成功 8/9，C07 三臂均视频拒绝；原九/十输入完整门槛未改且仍不可评价。八个完整配对输入上 R18C LPIPS 均值 0.165358，F17 0.249523，8/8 改善；去噪＋解码均值分别 130.203213 / 131.658731 秒。完整逐输入数据、完整请求时钟、费用和重用哈希均见原报告。

新增评分为 C06 四项和 primary11 六项，旧 16 项未重算。R16/R21 辅助臂仅覆盖 C01–C04、C06 五个驾驶输入。统计条件、拒绝和单种子限制持续保留。

P/S/Q、旧 source-lifecycle planner、早期策略搜索及其他分支的原始证据在 [backup](backup/INDEX.md)。它们保留历史结论与成本，不纳入当前主贡献。
