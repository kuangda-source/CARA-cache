# 下一项：宿主评分接口真实CPU probe

2026-11-02终态更新：本probe已按固定source `7c48488afdd7426a64ec9884737e606bcaada990`完整执行并结束接受，见[848](../../../research/848_CARA_P1_ALGORITHM_AND_ACTUAL_HOST_FIT_CPU_ACCEPTANCE_20261102.md)及[原接受](../../../reports/cara_v1_P1_host_FIT_CPU_accepted_r1_20261102.json)。两成功/一预设失败cohort、全部CPU终态与原字节恢复通过；不要再prepare或评分。以下为原执行前设计，下一交付为下文完整P1 outer入口。

当前`cara_source_lifecycle_fit_broker_r1.py`、原CLI和九项本地控制已实现；尚无真实Linux服务/容器接受。本交付不等待P1算法R3空转：继续实现新的宿主CPU probe，再冻结其源并单次执行。原R3运行只恢复，不改源或重派；本probe不运行GPU、模型权重或中央事务。

## 实现和资源

1. 新独立host-CPU stage，先复用已终态R2的完整源payload/runtime身份，再仅从新published source复制新增broker/CLI/探针代码。旧R2输出不复制、不重算。prepare意图先落盘；连接UNKNOWN或stage已有原意图只恢复原PID/start ticks/boot/namespace，禁止重复Popen。
2. 宿主probe/服务只使用stdlib和固定源，父进程固定CPU26/27、RLIMIT_AS4GiB、CPU/wall1200秒、无GPU可见；宿主有Docker组权限。它只构造固定CPU命令。无需给模型容器Docker socket。每次worker仍执行真实2核/8GiB/no-swap、26/27、无网络/只读root/固定镜像和唯一可写输出；实际MemAvailable至少12GiB、磁盘余量实时核验。父进程和服务都要保存原句柄/终态。
3. 一次额外的受限CPU媒体生成容器，使用原PyAV合成93×64视频，避免依赖宿主的编解码环境。相同项目/源码只读、唯一合成工件目录可写，原CLI/CID/源码/镜像/完整命令与真实资源均保存和核验。视频明确标为CPU夹具，不是Cosmos视频。
4. 固定三个不同合法策略：Uniform19、Uniform22，以及同一profile的一个预定合法19D交换。完整两FIT、seed0、Native合成参考；proof必须CPU_fixture_only、同context/source/launch，实际D/C历史/指纹经原grammar重建，所有视频/原件路径都在本probe的algorithm目录。

## 必须执行的完整链

宿主原服务在唯一队列等待。前两个请求通过真实CPU容器完成各两对/93帧的原Alex/PIQ指标；客户端拿到的是完整`accept_internal_scores`原字节。重复提交首个请求应直接复用同回执，容器数和CID不变。

第三请求使用另一个完整CPU夹具：首个FIT正常，第二个FIT的视频为哈希/proof相符的刻意无效编码。worker应在一对完成后退出非零，保留完整两FIT分母；服务给出原失败，客户端不能消费一对的均值、另派CPU或自动换方法。原服务预期失败终止，所有原CLI/容器退出，无活动遗留。

宿主只读恢复必须验证原CID/名称/标签/镜像/命令/环境/挂载/CPU内存/原CLI和worker身份；全新liveness观察时间戳不能改写首次封存execution/response。服务终态后用terminal reader恢复已完成两个查询，接受字节保持且新派发为零。运维reader仅读status计数，不打开指标response。

## 唯一终态与原件

整体probe仅在上述成功、复用、失败、终态读回和清理全部成立后退出0。保存所有原命令/进程/容器资源、完整结果哈希与原字节；接受时核对registered source和runtime。不把父进程host运行说成4GiB Docker，分别列RLIMIT父进程与真实8GiB指标容器。真实单卡GPU时钟/独占、正式GPU准入和完整P1释放后科学接受仍是后续边界。

若实际环境故障，保留这一新probe原失败，先恢复原句柄，不覆盖或重跑。不要让它重跑算法R3、读旧P0/M1/搜索视频、读四卡或改中央。研究记录另写新编号；更新canonical和精确提交推送，保留S/Q未提交文件。

该CPU probe成功后，继续完整P1 outer入口：guardian启动/停止宿主服务、GPU runner→内部队列、成功失败的原费用和释放、封存内部指标复用、32个释放后新增指标上限、完整146分母/别名/预算停止位置的结果与图表/一次冻结。完整源/CPU/资产/内存/存储和10.9158＋20%余量13.0989草案须组合为正式报价，才提交>4GPUh与新卡账本事务批准；当前尚无P1 GPU授权。
