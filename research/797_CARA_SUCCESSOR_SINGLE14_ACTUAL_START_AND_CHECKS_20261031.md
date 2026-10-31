# 797 — 修复后的新单次14GPUh实际启动与检查

修复后新单次14GPUh获批，113项Linux CPU、20资产及实时资源/中央准入通过；10月31日16:45:04两卡A6000唯一启动，原四进程存活、runner独占CUDA通过。完整112路径/51双FIT查询，硬截止11月1日06:45:04；23:16半程、06:01终验已绑定。原失败与0.002315298GPUh结算保留，无部分科学结果。

用户明确批准“批准新单次 14 GPUh 及该卡原账本预约、结算”。run `cara-budget-calibration-14gpuh-r2-20261031`，launch `323ef0d5e8eb4a91a1c8a4ba47c24b18`，源 `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`，原独立阶段和A6000 UUID见实际接受回执。guardian实际起点 2026-10-31T16:45:04.590671+08:00，硬截止 2026-11-01T06:45:04.590671+08:00；原14GPUh及600秒停止释放余量不变。

准入20资产校验和原有界CPU退出已核验。中央源码两次传输中断后只读恢复；最终从原已校验缓存复制到独立新目录，仅补一个中央操作文件并核对全部118文件，旧源不改。中央实时可用25.71345654GPUh，通过后唯一预约14，余11.71345654；cap226和旧16.5保持。两卡资源再次刷新后派发一次。

启动接受确认guardian、CLI、supervisor及runner原PID/start ticks均活跃；runner2371944独占CUDA，读取时52C、24514MiB、0/112，处于模型加载。此处只是实际启动接受，不是实验完整技术接受或科学结果。后续仅按112分母检查计数，不读取部分T_DD、目标分数或候选赢家。

半程14h：10月31日23:16；全程14h-2：11月1日06:01。均按实际起点安排，若提前完成前移同一个终验，状态无变化不通知。终态成功失败均唯一结算guardian整段实耗并验证释放；只有完整112/51接受后才原入口一次CPU汇总/冻结，不自动派发下一卡。原卡0/112和0.002315298GPUh费用及A32/B36/S/Q原结果保持。

[启动与检查汇总](../reports/cara_budget_successor_launch_summary_r1_20261031.json) · [原句柄交接](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14_POST_LAUNCH_HANDOFF_20261031.md) · [实际启动接受](../reports/cara_budget_successor_actual_start_accepted_r1_20261031.json) · [检查清单](../reports/cara_budget_successor_acceptance_schedule_r1_20261031.json)
