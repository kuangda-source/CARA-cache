# 729｜COMMON_LONG6监测进程竞态提前退出与结算

本次半程触发为18:55，但实际收件observed_unix=1793102087.2755（19:54:47），不能回填成18:48半程通过。唯一launch `33fc1816-ae18-461a-a4de-a2a0a50cfc99`已于18:25:15容器退出1；health的4完成/1运行/0失败是退出前旧快照，不是仍在运行。完整六路径未完成，CPU评分未启动，不接受科学结果或部分拼接。

## 确认原因

原监督`wc_common_long6_worker_r1.py:79`调用`production_exclusive.observe`，遍历`/proc/*/comm`判断MPS时遇到进程在读取期间退出，抛`ProcessLookupError: [Errno 3] No such process`。该循环只捕获FileNotFoundError与PermissionError，漏掉ESRCH。监督依原失败策略停止自己的runner并结算。原GPU日志没有模型异常，停止时正在首条ON的第34步；不据部分时钟或输出调整方法。

这是监测边界的工程失败；不是确认外部GPU抢占、OOM或磁盘耗尽。退出前1561样本无独占违规，最大间隔2.292秒；完整monitor accepted=false，不能把正常前缀冒充完整接受。磁盘余量约30.59GiB，原跨盘账单可读。

## 费用及资源

[失败完整终态](../reports/cara_common_long6_A6000_failed_terminal_20261027.json)与[原错误](../reports/cara_common_long6_A6000_failure_diagnostic_20261027.json)保留。原精确单调账单3384.689202470705秒 = **0.9401914451307514 GPUh**；[中央幂等结算](../reports/cara_common_long6_A6000_failure_central_settlement_20261027.json)已完成，唯一3h外部包转结算，不重复计费。中央used173.20596615932914/reserved16.5/available36.29403384067086/cap226，旧未知责任未变。

原runner、supervisor、guardian、post和容器均不活跃，UUID锁释放。guardian原件确认空闲时恢复Default。没有重派、补跑、启动评分、改原stage或追加预算。一次半程cara和旧21:10终态cara-2均已删除，因为原任务失败且完整财务收尾已完成。

## 修复方向，尚未执行新GPU

只针对/proc扫描中已消失的非GPU进程捕获ESRCH/ENOENT，不能吞掉权限不足、其他I/O错误或GPU PID身份不明。补复现ESRCH的真实观察器CPU测试，以及监督遇此竞态应继续监测、遇无法证明独占仍失败的组合测试。影响两端共享观察器，应双端受影响CPU验收、重新绑定冻结源和完整报价，再提出新完整六路径方案；原失败4条路径不拼接。原α、六对照、部署预算、累计226和IG暂停保持。
