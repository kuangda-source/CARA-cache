# 双卡兼容与主线同26D接续

用户明确授权：兼容原W3，空闲卡推进同26D简单规则；原cap104.971363333、<12GPUh自主、长任务ETA一次查收不变。

先读 [449预登记](../../research/449_WC_DUAL_GPU_ACCOUNTING_AND_SIMPLE26D_COMPLETE36_PREREG_20261015.md)。完整新卡六方法×四原CAL，24正式＋12完整预热，36路径/1296pairs/1load；5.766055预测、8GPUh上限，所有26D。原fixed A/plain与uniform/frontdense A/C；A次数5/10/0必须实报，不声称同总成本。

当前source36f5583，独立stage `.sync/wc-simple26d-production-r1-20261015`，完整CPU bundle906797于2026-10-15 16:05:38启动。最早按预计600秒后一次查收，原 [CPU launch](../../reports/wc_simple26d_full96_CPU_launch_20261015.json)。全部96采样和真实入口通过后才准入GPU；新stage不可覆盖，失败保留后用fresh R2。

CPU全部通过后，本地 `scripts/launch_wc_simple26d_full36_v2_r1.py --output reports/wc_simple26d_full36_GPU_launch_20261015.json` 会先在新stage启动原W3账本桥接，再一次启动新supervisor和post watcher。新GPU0 UUID-de9a...；原W3 GPU1 UUID-cebf...。只记录原W3资源身份，无partial科学输出。

账本v2是新任务准入与费用权威：`reports/gpu-budget-v2.json`、短事务锁和逐UUID锁。原W3保留12GPUh预留，新卡8GPUh预留；原实结起点79.99637737158223不重置。桥接器将原W3实际账单仅加一次，在原CPU post终态前绝不改旧账本。镜像后旧单锁启动器通过永久inflight协议标志拒绝，后续必须走v2。

原W3 source047dcf1、supervisor876730/child876879/post876731及原stage完全不改，2026-10-16 01:00一次查收保持。本地W3 collector仅补充只读v2/桥接账单捕获，不更改原stage源码。判断W3完成看其自己的PID/原件/post和GPU1释放，GPU0并行不是W3失败。

新卡并发主计时统一 `CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY`。验收全部36原位置、12预热重复、24兼容正式全93帧LPIPS及八旧fixed端点，拒绝失败不补样。启动后将精确PID/ETA回执补入本入口与主表N06。F/B不恢复，主线强基线N05仍待，不顺带启动其他GPU卡。
