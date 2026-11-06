# 814 — 预算搜索原14GPUh半程检查

2026-10-31 23:24:49（Asia/Shanghai），原 run `cara-budget-calibration-14gpuh-r2-20261031` 已完成 **104/112** 路径，105条已尝试。完整目标仍为112路径/51次双FIT查询，尚未进入终态接受。

原 launch `323ef0d5e8eb4a91a1c8a4ba47c24b18`、源 `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`、stage及四个PID/start ticks均与启动回执一致。原A6000为Exclusive_Process，唯一CUDA PID为2371944，温度76°C，显存25614MiB。容器正常运行、无OOM，2CPU/40GiB且MemorySwap等于Memory；实际占用23.49GiB，宿主可用内存30,668,432KiB，输出私盘剩余28,436,410,368字节。

原中央账本只读核验通过：cap226GPUh、已用183.78654345747375、预约30.5（本卡14及旧未知责任16.5）、可用11.713456542526245；本卡只有一条预约事件，尚无结算。四卡本卡stage/容器不存在。这里的6.66254193小时为截至观察的墙钟，不是最终实测账单；最终仍按原guardian全段实耗唯一结算。

仅用104完成/8剩余及实耗墙钟线性估计23:55:35完成，额外留约15分钟后，将**同一个14h-2终验前移到11月1日00:10**。这是运维估算，不能保证完成时间，也不作为科学性能指标。原14GPUh硬限、06:45:04.590671硬截止、600秒停止释放余量、90°C阈值不变。一次半程自动化14h已删除，没有新增重复检查。

本轮新增GPU提交0、账本写入0、部分科学结果读取0。终验继续恢复原句柄；完整终态、释放和唯一结算通过后，才用固定源完整接受入口进行一次CPU接受及冻结。A32冻结、B36/S/Q接受记录、WC/RA FIT UNMATCHED和旧CAL范围保持。

证据：

- [半程汇总](../reports/cara_budget_successor_halfway_summary_r1_20261031.json)
- [原句柄与计数](../reports/cara_budget_successor_halfway_capture_r1_20261031.json)
- [原中央账本只读回执](../reports/cara_budget_successor_halfway_central_r1_20261031.json)
- [原容器资源](../reports/cara_budget_successor_halfway_resources_r1_20261031.json)
- [检查清理与前移](../reports/cara_budget_successor_halfway_check_cleanup_r1_20261031.json)
