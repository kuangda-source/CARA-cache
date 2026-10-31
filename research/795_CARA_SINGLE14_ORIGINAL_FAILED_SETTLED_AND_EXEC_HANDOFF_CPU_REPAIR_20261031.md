# 795 — 单次14GPUh原失败、唯一结算与exec承接CPU修复

单次14GPUh已于16:00:22在两卡按原授权唯一启动，runner在exec身份检查处退出，0/112路径、无CUDA就绪或科学结果。原8.335秒/0.002315298GPUh已唯一结算，容器和四原进程退出、锁释放、Default恢复；余额25.71345654，旧16.5保持。真实Linux CPU复现命令哈希随exec变化；候选修复及8项实际进程控制通过，原失败源不改、不自动重跑。

原完整112路径/51双FIT查询、硬14GPUh的批准已执行。launch_id `2b8058a77c7248f181acffddd399c257`，源 `8a4eb813e5122cc450d980be45d4c3816ad9b4ae`，两卡原A6000。实际guardian起止为 2026-10-31T16:00:22.729488+08:00 → 2026-10-31T16:00:31.064562+08:00，容器退出1、无OOM。GPU切为独占后已恢复Default，四个原PID/start ticks均退出，设备锁与模式锁均释放。未进入模型加载或任何物理路径，没有部分赢家、CPU科学评分或布局冻结。

启动前81项实际Linux增量、1182文件完整源、20资产哈希/戳、64GiB卷和独立日志及实时资源通过。第二次资产准备在CPU0亲和性下错误拒绝24/25核心，保留原失败和完整资产摘要后，仅重新核验资源阶段完成准入。中央首次请求传输中断且只读证明未预约；缓存原已验证中央操作源码后，fresh核验与唯一预约完成。cap226及旧4.5+12责任不变。

实际runner错误是把bootstrap记录的身份字典与exec后的重新绑定作全字段相等比较。真实Linux CPU使用同一原bootstrap执行exec，证明PID、start ticks、boot/namespace不变，但命令SHA改变。候选修复保留原命令SHA作为来源，单独验证稳定身份、原grant、活guardian与冻结命令；8项真实进程控制通过，包括PID/start ticks/boot/namespace/grant/guardian/command篡改拒绝，另7项原runner绑定本地回归通过。候选仅本地代码与CPU夹具，未覆盖原已派发源，也未重绑为可派发整卡。

原实测费用 0.002315298004800247 GPUh 已中央唯一结算。结算回包超时后只读恢复到SETTLED及唯一事件，余额 25.713456542526245 GPUh；未重复提交结算。此次单次权限已消耗，后续只能准备修复后的新卡与新审批，不能重派原launch/run。原控制日志、容器、存储和失败保留。

启动状态取回时已经结束，因此直接完成终态/释放/费用验收，没有创建已无意义的半程或未来终验自动化。A32原冻结及B36的62项保护源码重新核对一致；科学总表行与映射条目不变。

[完整回执](../reports/cara_budget_single14_failed_settled_closeout_r1_20261031.json) · [原终态](../reports/cara_budget_single14_original_startup_r1_20261031.json) · [结算恢复](../reports/cara_budget_single14_central_settlement_recovery_r2_20261031.json) · [CPU复现](../reports/cara_budget_single14_exec_identity_CPU_reproduction_r1_20261031.json) · [候选修复CPU](../reports/cara_budget_single14_exec_handoff_CPU_repair_r1_20261031.json) · [原句柄交接](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14_POST_LAUNCH_HANDOFF_20261031.md)
