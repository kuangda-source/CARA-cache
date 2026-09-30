# Next actions — post-model reproducibility gate first

1. 最近pair任务已终态；F1/W1-P0/W1-S1全部旧身份不重启。默认scalar/shrink与decay0修订都NO_GAIN_IN_SCOPE：velocity sum-MSE比分别2.531/5.395与2.354/5.395，均2/4改善。停止无依据的第二次标量调整，不送入闭环。
2. 同版本stage-r2两个新进程exit0，latent/decode输入相同，首个差异decode_output；guardrail各自未改变输入。具体内部原因UNKNOWN。见[定位结果](17_DECODE_INTERVAL_RESULTS.md)。下一步[decoder状态/局部确定性策略](18_DECODER_POLICY_GATE.md)，准备<=900s/0.25GPUh，不改denoiser/安全检查；尚未实现或启动。
3. 累计1.823217769/4GPUh，剩余2.176782231h；含r1输出隔离问题的首进程与显式取消费用。所有旧身份终态，不重启；新提交前重核预算、锁、GPU准入与源哈希。
4. 复现区间被解释/解决后，按新证据开展F2或W1-D时间/空间分布，先诊断再选择是否W2；不无依据增加复杂度。数值结果只来自单工程场景四点，不否定整个方向，不声称质量等价。
5. 1,044本地固定提示词已清点，但无来源场景字段；CAL/DEV/CONF待自动连接来源/近模板分组，4个工程样本排除独立确认。人评非当前前置，不训练/付费评分/扩预算。代码、原始失败、数值、成本、复现缺口与handoff同步私有GitHub。
