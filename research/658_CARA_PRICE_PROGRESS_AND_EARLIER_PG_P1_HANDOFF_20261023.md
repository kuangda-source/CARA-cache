# 独占价格补测实际进度与提前接续PG-P1

2026-10-23 **16:56:36–16:58:04 Asia/Shanghai**只读检查原launch `895d66c7-5e95-42b3-bbff-0f78766eb424`。原guardian/supervisor/runner/container均存活，GPU3为Exclusive_Process、唯一原runner950782/start951747898/UID1000、UUID锁保持，0失败/错误。没有修改在跑源码、配置或提交新GPU。

## 实际进度与估计

- 5/10路径完整结束，正在formal_1_PRICE，完成254/406格；另4路径未到达。正式格660/1624，含warm总格1066/2030（52.5%）。这些是技术完成量，不是价格接受或科学结果。
- 两条完整PRICE分别75.36、76.50分钟；两个正式CONTROL分别5.33、5.45分钟。按剩余2条完整PRICE、当前152格和2条CONTROL计算，剩余点估计3.185小时，对应20:08:38完成采集。
- 合理工作估计：**20:00–20:30采集完成，20:30–21:00完成验收及PG-P1准入启动**。后者为预留收件、独立接受、曝光复查、stage准备和fresh资源检查的估计，不是实测保证。若后处理或资源准入失败，应保留原件并按实际证据处理。
- 独占前缀6167样本、最大间隔2.8153秒、0违规；仍须终态覆盖至结算才能接受价格。剩余盘92.40GiB、MemAvailable24.24GiB；P1启动须重新检查（当前内存只是略高于24GiB准入线，原价格退出会释放其资源，不能据此提前准入）。
- 单卡自13:13:24运行约3.74小时，上限11.5小时；账本仍预留11.5，尚未结算。原标签保持，不读取运行中部分价格调参。

## 接续安排

原17:59技术半程保持；把既有`cara-bank24-2`从22:59提前至**20:20**，已读回确认。20:20若尚运行，仅技术检查后按实测更新同一任务；若已退出，则立即完整收件及独立接受。旧launch里的22:58:25来自原报价forecast，不是提前结束后必须等待的门槛。

PG-P1整卡生产CPU及组合验收已在[657](657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)完成，不重派CPU。价格完整接受、账单结算和原卡释放后，执行新曝光审计、绑定旧标签与新价格、fresh资源准入并单次启动已授权P1。P1完整报价8.844444 GPUh、上限10.5；按20:30–21:00启动估计，预计次日05:20–05:50左右运行结束，实际排程以新launch返回为准。

## 原件

- [原任务实时收件](../reports/wc_policy_price_refresh_GPU_user_progress_20261023_1655.json)。
- [技术路径与格进度](../reports/wc_policy_price_refresh_GPU_technical_eta_snapshot_20261023_1658.json)。
- [正确独占前缀汇总](../reports/wc_policy_price_refresh_GPU_exclusive_prefix_20261023_1659.json)：技术快照中monitor_max_gap_seconds=0因错读字段层级无效，其空bad_records也不是有效独占检查；原件保留，本独立前缀汇总明确更正为最大间隔2.8153秒、按实际PID/start/UID检查0违规。
- [推算方法、范围与排程读回](../reports/wc_policy_price_refresh_progress_eta_and_schedule_20261023_1700.json)。文件名时刻仅命名标签，实际观测以原件observed_unix为准。
