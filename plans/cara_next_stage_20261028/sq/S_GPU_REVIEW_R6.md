# 另一张 A6000 上的单次完整 S

建议在两卡服务器的另一张 A6000（UUID GPU-de9a5370-cd87-0f1c-a48e-288888777dd3）运行一次完整 S。目的：补齐两个已曝光 FIT、Shared25-C 与 F19-C 父轨迹的完整风险标签，按已经冻结的 BR/DIAG/CFG 规则分析是否得到有效且不同的调度。原 Q1 单卡批准继续有效；本 S 申请需要独立批准整卡预算。

| 项目 | 固定范围 |
|---|---|
| GPU 范围 | 一张 A6000、一次分配；10 条全新路径，含 2 warm、4 OFF、4 ON |
| 完整分母 | 468 pair / 936 heads、552 deep block calls、108 moment rows、8 raw states、24 unique anchors |
| 输入与协议 | 两个旧 FIT；seed0、guidance7、实际36步、93帧、432×768；原模型、WanFP32Strategy 和阈值保持 |
| 整卡预算 | 保守 FP32 特征情形预计 **12.7125 GPUh**，申请硬限 **14 GPUh**；包含原明确余量，尚非实测整卡价格 |
| 运行资源 | 单 GPU；2 CPU、40 GiB RAM，host MemAvailable 至少52 GiB；32 GiB私有输出与48 MiB异盘控制日志 |
| 停止规则 | 原数值、热界、独占、存储或硬限失败即停；保留实际费用，不自动重试，不缩小范围 |

CPU 准备已完成：两端各123项原生控制、两个flow共20条tiny路径及5个Linux监督场景接受。所选 A6000 端20个真实模型/辅助文件共21.35 GB已逐字节摘要核验；32 GiB输出镜像已实际预分配并挂载，48 MiB日志在独立文件系统；原存储worker已退出0。原38个生产关键文件未改，源码stage、CPU、真实资产与存储SHA均绑定于[机器审阅卡](S_GPU_REVIEW_R6.json)。实际S标签、真实模型加载和GPU提交仍为0。

14:52北京时间的一次观察中，候选GPU利用率0%、显存450MiB、43°C，两卡均无计算进程、项目租约未持有。该观察只支持候选选择，提交前重新核验实际独占、UUID/进程、内存、盘、资产及中央责任。此后不再进行资源空闲轮询。15:05的中央账本只读快照为cap226、可用29.0539 GPUh、原16.5 GPUh未知责任保持；本准备未预留预算或写账本。

批准后按这张审阅卡唯一绑定原执行源码 ab3a306144f0cf24c04c0f0001a17665748a7518、原stage和这张A6000，完成fresh准入后只提交一次。从真实host guardian启动安排约6.356小时半程、12.713小时预计GPU终态与释放后CPU验收；硬限14 GPUh。检查不采用当前推算的绝对时刻。

全体真实标签和原始产物完整验收、GPU释放及费用结算后，才运行冻结风险规则分析；结果用于决定下一张S端点比较卡。该比较、新输入、额外seed及Q采集需要自己的范围与预算。

[原整卡报价](S_WHOLE_QUOTE_TWO_CARD_OTHER_GPU_R2.json) · [原生CPU接受](../../../reports/cara_sq_s_native_entry_two_card_cpu_accepted_r6_20261030.json) · [真实资产接受](../../../reports/cara_sq_s_assets_two_card_cpu_accepted_r1_20261030.json) · [实际存储接受](../../../reports/cara_sq_s_storage_two_card_cpu_accepted_r1_20261030.json)
