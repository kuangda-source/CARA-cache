# N07半程：独立只读健康入口准备

2026-10-16。原N07完整查收器只有admission/terminal两种入口，原最终ETA前不能用于半程。新增独立技术入口，六项标准库CPU控制和CLI冷检查通过；原完整终态脚本与已冻结源均未改。本轮尚未查看服务器健康或科学结果。

## 到时执行

北京时间10月16日21:30及之后、原最终最早时间10月17日05:26:04之前，执行一次：

```sh
.venv/bin/python scripts/capture_wc_paper_N07_midpoint_health_r1.py --output reports/wc_paper_N07_midpoint_health_20261016_2130.json
```

命令绑定原launch/admission/schedule：source140d0a6、launch798d9047，原supervisor1115797/start542326777、runner1115898/start542330755、CPU post1115798/start542326783及原GPU0 UUID均保持。早于半程不SSH；到原最终ETA后使用原终态工具。

同一launch已有回执时只离线读取；进行中的同名`.attempt`防止并发重复查询。连接失败保留UNKNOWN，不当成任务结束或授权重派；只检查任务拥有的本地FRPC连接，修复后必要的再次观察另用新回执，仍查原句柄。

## 仅收技术信息

核对原PID/start_ticks/命令行、registration与config身份、总体180/20预热/160正式分母下的已结束/在执行/未到达及错误计数，读取指定GPU利用率/显存/进程归属、磁盘、原UUID锁及本任务账本状态。RUNNING和拒绝分别计数，不用`len(runs)`充作完成数。

GPU/post日志各最多读取尾64KiB，只返回固定技术错误标签与文件元信息，不输出日志原文、逐方法质量或时间。CPU-final-results仅stat，不打开内容；不读取视频或张量。快照区分原句柄缺失、PID复用、读取未知、GPU进行中、CPU后处理和技术流程已结束；技术信号由代理继续诊断，不新增人工评审。

六项本地控制覆盖真实原绑定、半程/最终时间门、已有与在途回执去重、连接超时未知、状态分母及科学字段过滤、PID复用/CPU失败。SSH、进程与GPU观察使用测试替身；这是入口准备，不是运行正常证明。

完成半程后不持续监听，不暂停仍承担明早05:30完整验收的原自动化。即使提前技术终态，也保留原完整验收；不因此启动N08或其他GPU卡。正常仅留回执，重要异常或阶段变化再通知。原cap113、严格少于12GPUh自主与N07→N08→N09/10保持。

本轮0SSH/新GPU/服务器或预算写，没有更新或重置自动化的两个时点。N09完整监督/终态接受等准备仍可独立推进，F/B关闭。

原件：[CPU与原句柄绑定](../reports/wc_paper_N07_midpoint_health_entry_local_CPU_20261016.json)、[514原时间安排](514_WC_N07_MIDPOINT_HEALTH_CHECK_AND_FINAL_COLLECTION_SCHEDULE_20261016.md)。代码：[技术筛选](../src/wcomr/frozen_shared_health_r1.py)、[一次查收](../scripts/capture_wc_paper_N07_midpoint_health_r1.py)、[本地控制](../tests/test_frozen_shared_midpoint_health_r1.py)。
