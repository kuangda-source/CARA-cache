# CAL12终态查收连接未知，保留原任务并安排一次恢复查收

2026年10月19日18:06按原计划调用完整collector，但SSH在密钥交换前被重置，未取回服务器原件。此次状态为 `SCOUT_OBSERVATION_UNKNOWN_NOT_TASK_TERMINAL`，不能判断原GPU或CPU post是否已经结束，也不能接受质量、费用或锁释放。BANK24尚未派发。

## 本次原件和连接边界

- 原失败捕获：`reports/wc_scout_CAL12_full12_terminal_collection_20261019.json.gz`。保留原字节，不覆盖，也不把它送入科学终态analyzer。
- 只读诊断：`reports/wc_scout_CAL12_terminal_connection_unknown_local_FRPC_readonly_20261019.json`；独立边界核对：`reports/wc_scout_CAL12_terminal_connection_unknown_independent_assessment_20261019.json`。
- 本任务本地FRPC原PID17525仍持有33620监听和控制TCP；日志在18:06:50记录远端visitor服务不存在。该现象解释了本次连接失败，但不能据此判断服务器实验进程的状态。
- 未重启FRPC或远端服务，未改变网络配置、原stage、GPU任务、CPU post、锁或账本；新增GPU派发为零。

原CAL12身份保持：launch_id `f3c235ac-1b69-45e5-81cc-4d1cdbd92b08`，source `2bd41dc8fa19f42353e03a7c78b7264b4b2695c6`，实际entry source `c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9`；supervisor2729092/start569156045、runner2729134/start569156584、post2729096/start569156053。完整12位置、8正式及4预热、432pairs、一次加载和所有原验收控制均不变。

## 当前能确认的状态

最近一次成功远端观察仍是16:54技术半程：11 COMPLETE、1 RUNNING、0未到达，原句柄一致、错误标签为空。该历史快照不代表18:06仍在运行，也不代表12视频已完整科学接受。

最近核对的池账实际115.83511083569408/cap226、完整预留2.5同样只是历史快照；本卡实际费用、当前活动预留、GPU和锁释放均未知。本次没有写任何服务器账本，也没有把预留记成实费。

## 一次恢复查收

通过应用工具更新原 `worldcache-cal12-bank24` 自动化，安排今天18:30再次读取原同一句柄一次；最早unix1792405800。不循环重试，不重复派发原实验。实际自动化核对保存在 `reports/wc_scout_CAL12_connection_recovery_once_schedule_20261019.json`。

恢复使用新文件名 `reports/wc_scout_CAL12_full12_terminal_recovered_collection_20261019_1830.json.gz`，原unknown完整保留。取得真实完整终态原件后，才离线调用原analyzer并冻结四CAL gate；若仍运行则按实际剩余量另约，若连接仍未知只保留新失败和自身本地TCP诊断，不推断任务成功或失败。

CAL12原件、全部适用93帧、observer OFF/ON、同状态前缀/probe/inputhash、实际费用和本UUID释放按原标准接受前，不启动BANK24。通过后沿[原就绪手册](../plans/WC_SCOUT_GPU_READY_CONTINUATION_20261019.md)接其自身R2已验CPU、固定四CAL gate和fresh UUID/v2准入；不重复CPU、不用DEV重拟合。原N10及Window24已接受结果不重查，F/B保持关闭。
