## 2026-10-15 23:52完整CPU接受，同26D修复R2已准入

[453 CPU接受与GPU启动](../../research/453_WC_SIMPLE26D_MEMORY_FULL144_ACCEPTED_AND_COMPLETE36_GPU_R2_LAUNCH_20261015.md)：source0795a00/1658源、144完整CPU及实际生产入口接受（544.245326秒），96修复请求owner全释放；原CPU1037920已终态。完整R2于23:54:49锁内准入，supervisor1040857/runner1040918/post1040858，GPU0/新run wc-simple26d-memory-cal4-full36-r2，24正式+12warm/1296pairs/1load不缩，旧28全作等价控制不拼接。原失败卡及451不改。完整预测5.766055、计费上限8<12，v2实结86.864053599/cap104.971363333，预留8、可准入10.107309734。新卡无科学结果，真实显存稳定仍待完整验收。**10-16 04:55一次查收**（最早04:54:11），不持续监听；用项目venv执行capture新launch-ref和独立R2分析。原W3原源/GPU1/01:00科学验收不改，未读其partial。F/B关闭。以下保留历史。

## 2026-10-15 显存修复与同26D完整R2 CPU在途

用户已明确授权修复并在验证后继续完整同26D。旧“待讨论、不自动重跑”为历史。[452完整修复预登记](../../research/452_WC_SIMPLE26D_MEMORY_LIFECYCLE_REPAIR_FULL36_PREREG_20261015.md)：故障在36步/VAE后的视频安全encoder移入GPU。新source0795a00、独立stage wc-simple26d-memory-production-r2-20261015，CPU1037920于23:36:27派发；原W3源/stage/01:00科学查收不改。请求边界GC及owner弱引用检查的本地4控制通过，完整144 CPU与实际生产入口待验；23:52一次收原CPU。通过后沿v2/GPU0 fresh准入完整36重跑，24正式+12warm/1296pairs/1load，预测5.766055、上限8<12。旧28全作等价控制、不拼接；原失败36分母保持。实结86.864053599/cap104.971363333、预留0/余18.107309734未重置。新GPU预计3至5小时，启动后5小时另约一次收，不持续监听。F/B保持关闭。

# 双卡兼容与主线同26D接续

**23:00本卡已一次收终态，禁止再运行launch或持续查旧进程。** [451](../../research/451_WC_SIMPLE26D_PARTIAL_RESULTS_OOM_TERMINAL_AND_PAPER_IMPLICATIONS_20261015.md)：36分母保留，12warm/16正式完成并评分、1 OOM/7未到达，整卡未接受；九CPU负控制及部分原件审计通过。新卡2.292842043GPUh、GPU0锁释放，新池实际86.864053599/104.971363333、预留0余18.107309734。原W3科学验收仍01:00，财务条目不当科学完成。worldcache-26d暂停，无补样或新卡；显存定位和完整收尾仅待讨论。下面在途/CPU段落保留历史。

**最新：完整CPU已接受，新卡GPU已准入。** source36f5583于16:18:09取得GPU0 UUID-de9a...锁和8GPUh完整预留；supervisor909867、runner910056、post909868、bridge909859。全部1644源/两flow96采样/真实生产通过，60个非D计划步真实calibration支持也已核对。原W3 source047dcf1/876730/876879/876731和GPU1不变，旧账本SHA未变。

按[450](../../research/450_WC_DUAL_GPU_SIMPLE26D_RUNNING_AND_ACCOUNTING_ACCEPTANCE_20261015.md)于**10-15 23:00**一次查收，自动化`worldcache-26d`；原W3`p-acr-cpu`仍10-16 01:00。新账本实结起点79.996377372、总预留20、可准入4.974985961，cap104.971363333不变。新卡并发秒数只诊断，不作clean加速。结果尚待，不继续SSH看partial，不自动重派/追加卡。下面CPU启动安排保留历史，不能再执行一次launch。

用户明确授权：兼容原W3，空闲卡推进同26D简单规则；原cap104.971363333、<12GPUh自主、长任务ETA一次查收不变。

先读 [449预登记](../../research/449_WC_DUAL_GPU_ACCOUNTING_AND_SIMPLE26D_COMPLETE36_PREREG_20261015.md)。完整新卡六方法×四原CAL，24正式＋12完整预热，36路径/1296pairs/1load；5.766055预测、8GPUh上限，所有26D。原fixed A/plain与uniform/frontdense A/C；A次数5/10/0必须实报，不声称同总成本。

当前source36f5583，独立stage `.sync/wc-simple26d-production-r1-20261015`，完整CPU bundle906797于2026-10-15 16:05:38启动。最早按预计600秒后一次查收，原 [CPU launch](../../reports/wc_simple26d_full96_CPU_launch_20261015.json)。全部96采样和真实入口通过后才准入GPU；新stage不可覆盖，失败保留后用fresh R2。

CPU全部通过后，本地 `scripts/launch_wc_simple26d_full36_v2_r1.py --output reports/wc_simple26d_full36_GPU_launch_20261015.json` 会先在新stage启动原W3账本桥接，再一次启动新supervisor和post watcher。新GPU0 UUID-de9a...；原W3 GPU1 UUID-cebf...。只记录原W3资源身份，无partial科学输出。

账本v2是新任务准入与费用权威：`reports/gpu-budget-v2.json`、短事务锁和逐UUID锁。原W3保留12GPUh预留，新卡8GPUh预留；原实结起点79.99637737158223不重置。桥接器将原W3实际账单仅加一次，在原CPU post终态前绝不改旧账本。镜像后旧单锁启动器通过永久inflight协议标志拒绝，后续必须走v2。

原W3 source047dcf1、supervisor876730/child876879/post876731及原stage完全不改，2026-10-16 01:00一次查收保持。本地W3 collector仅补充只读v2/桥接账单捕获，不更改原stage源码。判断W3完成看其自己的PID/原件/post和GPU1释放，GPU0并行不是W3失败。

新卡并发主计时统一 `CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY`。验收全部36原位置、12预热重复、24兼容正式全93帧LPIPS及八旧fixed端点，拒绝失败不补样。启动后将精确PID/ETA回执补入本入口与主表N06。F/B不恢复，主线强基线N05仍待，不顺带启动其他GPU卡。
