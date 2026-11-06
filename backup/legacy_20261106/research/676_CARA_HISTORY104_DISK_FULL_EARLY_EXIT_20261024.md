# 104卡磁盘满提前退出：原件保留、GPU释放、费用待恢复

实际只读观测：2026-10-24T09:09:11.001053+08:00。唯一launch `d6351496-ee8a-4428-8ede-898f53d665cd` 与source `5fc4dfe66a33a915fcc7bdf10700bae8810bb401`保持。本次未提交GPU、未修改远端文件、账本或运行stage。

## 技术终态

原容器于2026-10-24 08:49:32（Asia/Shanghai）退出1，非OOM；guardian/supervisor/runner/container四句柄均已退出。GPU3恢复Default，compute_apps为空，原UUID锁自由。health仍写RUNNING、72/104完成、1运行、0失败，这是落盘失败前的旧快照，不是当前运行状态或半程成功。完整104采集、72评分及终态协议未通过，原675中11–13点采集和12:30–15点评估的ETA失效，目前没有新的最终验收时间。

日志出现`OSError: [Errno 28] No space left on device`。文件系统对普通用户available为0；仍有约0.91TiB free blocks但bavail=0，inode充足，不能将保留块视为当前实验可用空间或擅自以root绕过。本卡输出633945754字节（约0.59GiB）。04:18还有42.14GiB可用；这些证据不能确定是谁写满共享盘，也不能据此归咎本卡。

9008条完整独占监测前缀无违规，最大采样间隔2.977539秒；最后完整样本08:49:28仍为唯一原runner。尾行损坏，完整独占终态与结算链缺失，所以不宣称全程独占验收通过。

## 费用和原件

`billing.json`缺失，`billing.json.1204839.tmp`为0字节；runner和guardian最终更新临时文件也为0字节。原11.9GPUh预约仍保留，账本未结算。容器占用墙钟约5.4597小时，只是时间估计，不是恢复出的原单调钟账单；不据此伪造精确actual_GPUh。累计226GPUh、部署257.7712338712067秒上限保持。

常规terminal capture返回UNKNOWN，实际是本地收件代码对远端容器`ExitCode==0`的断言失败；后续只读连接成功且获得原退出状态。该收件故障不代表SSH中断，更不能触发重新派发。独立失败收件保留原退出、原文件SHA、原健康快照和账本。

- [失败终态只读原件](../reports/cara_history104_GPU_failed_terminal_readonly_20261024_0912.json)
- [磁盘、空账单临时文件及日志原件](../reports/cara_history104_disk_failure_original_evidence_20261024_0910.json)
- [独占前缀与失败日志](../reports/cara_history104_failure_monitor_and_logs_20261024_0912.json)
- [技术失败汇总（不是完整接受）](../reports/cara_history104_early_failure_technical_summary_20261024.json)
- [原常规终态收件失败](../reports/cara_history104_GPU_early_exit_terminal_20261024_0907.json)

## 接续

先保全原件、核实存储空间和可审计费用，再形成恢复方案。104路径原卡不缩卡、不补跑、不重派；不启动部分评分，不用部分结果调整策略/阈值。现有671/673/674协议和原alpha保持。P1修复和P2继续等待完整证据，不能把本次72条当作104验收。后续若需新实验，必须单独完整报价和准入，失败成本保留。

一次性09:05半程检查已删除；原15:03全程检查复用改为10:30原失败句柄、存储和账单恢复检查。无需重复成功验收任务。不触碰其他用户数据/进程，不扩大此前已核验重复文件清理范围。

## 10:30后只读复查

实际观测2026-10-24T10:30:48.171774+08:00：原四句柄仍退出、空间available仍为0、原账单缺失且临时文件仍为空，账本预约未变。未改远端、未派GPU、未评分。此前已验证可清理的重复张量和两个压缩包已处理；另三个压缩包不等价，不能扩大删除。

[本次原句柄](../reports/cara_history104_failure_recheck_20261024_1030.json) · [磁盘与账单](../reports/cara_history104_disk_billing_recheck_20261024_1030.json) · [费用恢复方案](../reports/cara_history104_failed_accounting_recovery_plan_20261024_1030.json)。最后保存的单调钟至少19647.140445秒（约5.457539GPUh），不能恢复丢失的精确结束单调钟。当前保守处理仍为保留全部11.9GPUh预约，不把估计作为原账单，不清预约；待可写空间恢复后以独立重建记录和独立核验处理费用。原失败状态不变，复用同一检查移至14:30，不重复通知或创建实验。
