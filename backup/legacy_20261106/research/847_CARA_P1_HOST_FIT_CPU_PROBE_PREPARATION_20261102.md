# P1 宿主评分接口：真实 CPU 探针准备

原 Tailscale/ProxyJump 已恢复可用。原 R3 算法 CPU 于 04:57:48 开始，本轮半程原句柄仍运行，完整源码与运行时一致；未重派、未改原源、未读取中途指标。半程检查已删除，原终验保持。原 R1/R2 失败与 R2 完整首 flow 继续保存。

新的宿主探针独立于原 R3：父进程及服务限定 CPU26/27、地址空间4GiB、CPU/墙钟1200秒，它们是宿主进程。媒体生成和三个评分任务使用实际 Docker，分别2核/8GiB/无额外 swap、无网络、无GPU、只读源和唯一可写输出；不给模型容器 Docker socket。所有媒体为明确的合成93帧64×64夹具，不加载 Cosmos 权重或旧实验视频，不访问四卡或中央账本。

前两个完整两FIT请求验证真实 Alex/PIQ 指标、客户端回执和重复请求复用。第三个完整请求的第二个视频预设为编码失败，检验保留两FIT分母、拒绝部分均值、原服务退出及不重复派发。服务终态后只读恢复前两份原接受，要求字节不变。此处记录的是执行前设计，实际 Linux 接受仍待原终态。

本轮还修复了客户端在读取 response 与服务活性之间的竞态：服务可能刚封存终态回执并退出，客户端应再读已存在的原回执。新的针对性控制连同原broker和探针共12项通过；不改变评分核、D/C合法空间或选择规则。

- [12项本地CPU回执](../reports/cara_v1_P1_host_FIT_probe_local_CPU_r2_20261102.json)
- [原R3半程记录](../reports/cara_v1_P1_algorithm_CPU_halfway_r1_20261102.json)
- [宿主实际CPU设计](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_HOST_FIT_CPU_NEXT_IMPLEMENTATION_R1.md)
- [完整P1范围及费用草案](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_BOUNDED_PHYSICAL_COST_DRAFT_R2.json)

下一步完成原R3和本宿主探针接受，再组合原guardian与宿主服务、释放后全146语义位置接受和完整报价。P1 GPU与本卡中央事务尚未获批；当前12项本地控制、合成视频或已有P0结果均不构成真实V1方法效果。
