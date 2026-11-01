# V1 P1算法R2 CPU：唯一原运行承接

**终态更新：R2已于04:41:54退出1。** 首个flow完整146语义/140实际请求、64标签和82对合成真实指标完成，外层调用者`net.forward`未还原而失败，第二flow未到达。原失败/完整首flow已保存；不再prepare、重启或重评分此R2。修复后的独立R3完整CPU见[846](../../../research/846_CARA_P1_FIRST_FLOW_ORIGINAL_CALLER_RESTORATION_AND_HOST_BROKER_20261102.md)。下文保留原运行交接快照。

原R1已退出1并保存写出后缀的夹具失败；不重启。R2只修复同一夹具接口，是独立新CPU原件，非GPU卡、非P1科学结果。

- 固定源：`47a0048cbb32533095951112f172823b5dbfedc0`，two_card。
- 原stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r2-20261102`。
- 原容器：`cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r2-20261102-cpu`；CPU单核26、4GiB/无swap、无网络/只读root/无GPU。
- 实际开始：2026-11-02T04:23:13.302658+08:00；work1800/exit60，工作边界2026-11-02T04:53:13.302658+08:00，退出余量至2026-11-02T04:54:13.302658+08:00。这是上限，不是完成预测。
- 原registration SHA：`a5f43be68ae903ceffc5edc15e38f7d78aab337cfe96f1c882377d453ae425aa`，1373份payload源；原WC/RF runtime散列不变。
- 启动原件：[`launch_r2`](../../../reports/cara_v1_P1_algorithm_Linux_CPU_launch_r2_20261102.json)；最近原句柄观察：[`capture_r4`](../../../reports/cara_v1_P1_algorithm_Linux_CPU_capture_r4_20261102.json)。该观察确认Running，容器PID 3197932、启动CLI PID 3197888；PID只作观测，恢复须绑定原容器/registration/源。

只运行`python3 scripts/cara_source_lifecycle_p1_linux_cpu_r2.py capture --source-revision 47a0048cbb32533095951112f172823b5dbfedc0 --output reports/新的唯一回执.json`。禁止再次prepare、复用已存在output、改原stage/源码/容器或根据超时推定失败。连接UNKNOWN只恢复该原件。

容器完整exited0且proof存在后，使用`scripts/accept_cara_source_lifecycle_p1_linux_cpu_r2.py`对原launch和新terminal capture做本地只读接受；输出accepted/proof文件必须全新。33控制、两flow各146语义位置/64同状态标签、真实Alex权重的全93帧合成指标及零新增回调恢复均须齐全。原始CPU proof散列必须等于原字节；CPU合成费用ticks不用于GPU报价。失败则保存完整终态与原失败，不伪造CPU接受。

本CPU不读旧实验视频/最终保护输入、不加载Cosmos权重，不访问四卡或中央账本。P0/M1/标量R3旧原件保持。即使本CPU成功，宿主独立评分容器broker、原终态/释放/唯一结算后的全结果接受、完整146位置正式报价和>4GPUh/本卡账本批准仍待，不能自动新GPU。

后续设计见[845](../../../research/845_CARA_V1_P1_WHOLE_ALGORITHM_INTERNAL_FIT_AND_FAIR_SEARCH_PREPARATION_20261102.md)、[宿主broker接口](V1_P1_HOST_SCORE_BROKER_DESIGN_R1.md)与[有界物理费用草案R2](V1_P1_BOUNDED_PHYSICAL_COST_DRAFT_R2.json)。
