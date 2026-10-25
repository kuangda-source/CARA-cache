# CAL66技术检查：冻结请求参数异常，提前退出并结算

用户只要求技术状态，本次未分析视频质量或部分科学结果。原launch `54eeebc7-00bb-4951-96cf-e2f66a85e344` 于2026-10-25 18:19:39启动；容器实际18:49:06.827747退出1。本次19:59:31首次实测发现退出，后续原件补齐；文件名2000/2002等为标签，不替代各自observed_unix。此前运行描述是18:21/18:26保存快照，不是持续在线确认。

## 进度与直接原因

完整分母66保留：0完成、1失败、其余未到达，模型加载后第一个请求入口失败。原GPU日志指向 `exploration_requests.py:16` 的 `sample.seed=slot['seed']`，真实Cosmos `InferenceArguments` 是冻结实例，Pydantic抛出 `ValidationError: Instance is frozen`。未进入后续采集和释放后的评分。容器OOMKilled=false；没有磁盘耗尽证据。这是生产请求适配错误，不是科学假设的负结果。

原件：[技术观察](../reports/cara_CAL66_progress_technical_20261025_2000.json)、[失败终态](../reports/cara_CAL66_failed_terminal_20261025_2002.json)、[错误/存储/监测](../reports/cara_CAL66_failed_storage_monitor_error_20261025_2005.json)。不改原stage，不重派、不补跑或重新评分。

## 独占、释放与磁盘

- 774个监测样本完整，无坏行，最大间隔3.310秒；授予上下文后的734个样本均通过唯一原runner检查，无外部进程/MPS混入。
- 两个授予前过渡样本按idle规则得到GPU_ALREADY_OCCUPIED，核实是原runner PID1635470/start970865687/UID1000刚建立上下文，非外人进程；[原始过渡样本](../reports/cara_CAL66_failed_monitor_transition_20261025_2006.json)保留，不删除样本。原exclusive-monitor-final的accepted=false原样保留，不能称完整成功独占接受。
- 末样本至账单结束2.201秒。四个原句柄全部退出，设备锁已释放；18:49:07 GPU2空闲恢复Default。19:59观察到的外部进程是在释放后，不能归因为本卡干扰；未触碰。
- StorageGuard当前复查通过，32GiB独立卷可用31.18GiB，host可用约1.16TiB；48MiB跨盘日志完整，supervisor/billing/guardian/telemetry/failure/accounting六槽均有有效记录。独立账单与原billing.json及权威账本SHA一致。

## 费用与检查安排

[独立财务核验](../reports/cara_CAL66_failed_financial_audit_20261025_2006.json)接受精确单调时钟1745.851328秒，即 **0.484958702187 GPUh**。权威账本已经自动SETTLED，本次不再写账或重复结算；原8GPUh预约已释放。累计used156.62041309731035、reserved16.5旧两卡未知责任、available52.87958690268965、cap226。

科学整卡接受=false，财务接受不替代完整实验接受。原预计00:48采集完成、05:50验收已失效；已删除 `cara-cal66` 与 `cara-cal66-2` 两个一次性检查，避免继续将失败任务当运行中轮询。当前没有可提供的完成ETA。

下一步应修复真实冻结参数的构造/复制方式，并以真实InferenceArguments补验少步Native与缓存请求入口；原α、强基线和66完整分母保持。先完成修复证据与恢复方案，再决定新的执行；本次没有代码修复、GPU重跑或新预算授权。
