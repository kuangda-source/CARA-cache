# Next actions — scalar固定重放在跑，继续原任务

1. 2026-10-01 00:29:13实机核验：source31a797d，supervisor2471255/timeout2471260/runner2471262均live，GPU1仅此runner；official14项和scalar OFF/ON18项检查全真。首候选完成1/8，第二common场景生成。接续`outputs/w1-replay-r1`，不重启CAL8或重复提交/部署。
2. [部署](../reports/w1_replay_r1_deployment_20261001.json)Linux63项CPU通过及hash匹配；[启动](../reports/w1_replay_r1_launch_20261001.json)记录唯一身份；[实时快照](../reports/w1_replay_r1_live_observation.json)为非终态。后续文档commit不改变实机source31a797d。
3. 单batchcap3000秒/原4GPUh不变。结算2.995044843356h另有0.218519319h在途；旧ledger余额未扣在途，不能准入第二任务。全8样本保持原顺序/参数/full位置；misc恶化不替换，拒绝保留，未知/parity/非有限/位置异常停止。
4. 只读观察原handles到终态；确认PIDs消失/锁释放，审计源码与视频hash、监控GPU归属并按监督实际wall更新账本。归档runner/supervisor/audit后执行`scripts/summarize_w1_replay.py`；完整summary重核hash绑定原CAL8 reference和两门，partial必须NO_QUALITY_DECISION，不凑全或自动重跑。
5. 首AV视频与WC明显不同且帧间变化较小，但仅是完整RGB差异描述；诊断时间不作clean speed、距离/平滑不作物理质量。终态后按覆盖和成本评估clean重复计时/标准质量/独立确认资源缺口。完整技术通过不是质量收益；当前不先加W2，不要求人评。
6. 保留[CAL8机制结果](21_W1D_CAL8_RESULTS.md)：scalar7/8联合改善、velocity/postwarp均比0.759185/0.893679，MECHANISM_ONLY_CAL8；shrink0/8 velocity改善不送闭环。CAL仅开发数据。代码/回执/总览/handoff同步GitHub；不扩预算/训练/付费评分，重大资源或方向决策交用户。
