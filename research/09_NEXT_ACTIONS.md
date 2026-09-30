# Next actions — scalar CAL8机制信号，固定重放闭环下一步

1. 阅读[完整CAL8结果](21_W1D_CAL8_RESULTS.md)：8/8全技术通过，scalar7/8联合改善、平均velocity/postwarp比0.759185/0.893679，MECHANISM_ONLY_CAL8。misc恶化必须保留；shrink0/8 velocity改善，仅本冻结收缩线不送闭环。旧四工程点NO_GAIN_IN_SCOPE保持旧范围，不以新结果倒改。
2. w1d-cal8-r1全部原PIDs退出，锁可用、GPU1释放；[终态audit](../reports/w1d_cal8_r1_audit.json)/runner/supervisor/summary/analysis/figure已归档。累计2.995044843/4GPUh，余1.004955157h，旧live/partial快照不再是当前状态。不重启旧任务。
3. [固定schedule准备卡](22_W1_REPLAY_PREPARATION.md)的完整generation runner及监督模式已实现，19项本地CPU检查通过；下一步Linux/hash部署与fresh准入。CPU fixed_replay模块24项针对性检查通过，[协议](../manifests/w1_fixed_replay_protocol.json)冻结全部8官方trace/receipt hash与scalar-recent参数。firstAV新official replay必须严格复现旧OFF，scalar OFF/ON自身轨迹parity通过才继续原其余7 scalar OFF。自己当前latent/probe/真实full anchors，不回放旧latent、不注入shadow truth。
4. 本轮拟单batch cap3000秒/0.833333h，从原预算余额扣除；forecast2224.619秒（+30%=2892.004），不是实测候选成本或完成保证。runner已本地CPU验收/未Linux部署/未GPU。源码commit/hash及LinuxCPU通过后，重查预算/锁/原handles/GPU准入并记录唯一新身份；未知/parity/非有限/位置不符停止，安全拒绝保留，不能补样本/扩额。
5. 闭环终态后按实际成本与8样本覆盖、候选自身诊断/视频差异判断是否值得clean计时/质量评估。诊断时间不作clean speed、相对WC距离不作物理质量；当前无必要人评。组上没有平均局部有效而其他无效模式，不先加W2。完整F2多点12–24场景/重复clean计时/独立确认超现余额时报告资源缺口，不能以小子集冒充完成。
6. 不训练/付费评分/引入非必要人评；代码、冻结配置、原失败/终态/成本、实验总览和handoff同步私有GitHub。重大预算/训练/方向决策交用户；无重要问题则自主推进。
