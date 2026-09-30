# Next actions — CAL sparse W1-D next

1. 默认/recent scalar与shrink仅在旧AV四点NO_GAIN_IN_SCOPE，不送闭环、不继续无依据参数调整，也不否定整个方向。
2. [局部解码门](19_DECODER_POLICY_RESULTS.md)两个fresh进程通过：72net/latent与旧参考相同，权重/状态见证相同、flags恢复、decode至93帧RGB/MP4一致。不是全数据集确定性或独立根因证明；所有新对照必须共用该策略并再做off/on。
3. [CAL24清单](../manifests/cal_v1.json)按官方reference_video+词法近重复组冻结，前8涵盖7域+第2AV；4工程组排除。原recording/session语义独立性未证明，CAL仅校准，DEV/CONF未冻结。
4. 实现[CAL前8 W1-D](20_CAL_AND_W1D_PREPARATION.md)：预测先于truth、过去full anchors独立、每样本off trace选择稀疏点后冻结；显式布局的时间/空间/通道分布与velocity排序、off/on原轨迹/解码一致、安全拒绝/技术失败保留。提议单batch6000秒/1.666667GPUh，尚未实现或启动。CPU/源码部署后，重核预算/锁/准入。
5. 当前累计1.997774315/4GPUh，剩余2.002225685；全部旧身份终态，不重启/不修改共享源码/不扩预算。完整F2多点12–24场景成本超现余额，不能以小子集冒充完成。后续按机制证据和实际成本决定新局部假设或报告资源缺口。
6. 不训练/付费评分/引入非必要人评。所有代码/配置/原始失败/结果/成本/实验总览/handoff同步私有GitHub。
