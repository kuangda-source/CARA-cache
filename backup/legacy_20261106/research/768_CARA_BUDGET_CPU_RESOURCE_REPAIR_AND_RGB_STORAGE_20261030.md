# 预算搜索 CPU 资源修订与全分辨率 RGB 存储

2026-10-30。本轮修复767原CPU准备器对继承Docker命令的资源遗漏，不改端点评价、搜索、原查询日志或任何A32/B36科学源码。R1原容器退出/0及其资源拒绝保持，R2使用新的CPU阶段身份。

## 修订边界

[共享资源函数](../src/wcomr/cara_budget_cpu_resources_r2.py)显式绑定1CPU、4GiB内存和MemorySwap=4GiB，即零额外swap；不指定CPU亲和性。删除继承的CPU/内存/swap/绑核参数后再写入统一值，并拒绝重复歧义参数、缺失参数和GPU请求。网络none、只读根文件系统、CUDA隐藏和无权重约束沿用原实际生产CPU入口。R1接收器的绑核26并非R1计划要求，R2明确登记不绑核，不把这个修订追溯用于接受R1。

[R2登记](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_ENDPOINT_CPU_FRAGMENT_R2.json)绑定启动器、接收器和控制源码；科学CPU矩阵仍为每端31组件控制、54成功tiny路径、8预定失败及12完整双FIT目标，两种flow与完整36更新/19D/93帧均保持。600秒工作与60秒退出上限不变。旧端点源码SHA未改变。

[8项本地控制](../reports/cara_budget_endpoint_CPU_resource_repair_local_r2_20261030.json)包含3项资源命令测试及5项接收器测试。使用显式合成双端证明验证完整接受、swap/绑核/GPU错误、缺失前置资源登记、部分矩阵、活跃容器、错主机和损坏摘要拒绝；合成通过不计实际主机接受。

## 原R2运行与S优先

[四卡原启动](../reports/cara_budget_endpoint_four_card_CPU_launch_r2_20261030.json)实际17:25:02开始；[首次捕获](../reports/cara_budget_endpoint_four_card_CPU_capture_r2_20261030.json)确认原容器运行，Memory=MemorySwap=4GiB、1CPU、无GPU和网络。[原终态](../reports/cara_budget_endpoint_four_card_CPU_terminal_capture_r2_20261030.json)确认17:31:01退出/0、Pid0、无OOM，工作函数350.06秒；未修改运行源或配置。[完整评估](../reports/cara_budget_endpoint_four_card_CPU_complete_assessment_r2_20261030.json)核对注册、证明、源码/运行时SHA、全部资源字段与完整矩阵：31项控制、54成功路径、8预定失败和12完整目标通过，原62份B36源码保持。此处仅确认四卡R2证据，不虚构两卡完成或双端接受。

两卡准备使用独立的56GiB可用内存门：最多4GiB CPU占用之外，为S保留50GiB及额外2GiB余量。资源不足就在创建stage和Docker进程之前拒绝。本次两卡准备在创建stage之前触发资源门；[原阶段恢复](../reports/cara_budget_endpoint_two_card_CPU_refusal_recovery_r2_20261030.json)确认stage及启动回执不存在，当时可用内存51.2626GiB，低于56GiB门。没有启动CPU任务，不占S准入内存；不反复轮询或降低门槛。当前完整双端接受尚未形成。

## 完整RGB工件容量

[存储组件](../src/wcomr/cara_budget_rgb_storage_r1.py)从原RUN_SPEC读取完整3×93×432×768 float32几何，按NPY真实头部和数据字节计算所有保存的教师、候选与额外RGB路径；不抽帧、降分辨率或丢弃重复查询工件。三项控制验证实际np.save字节、完整604路径量级和非法/缺失范围拒绝。

[容量回执](../reports/cara_budget_RGB_storage_component_r1_20261030.json)显示，官方默认301候选查询的双FIT适配，加两个原Native教师，共604份完整RGB NPY需要223638334976字节，约208.28GiB。此值尚未包括编码视频、warm、控制、评价、身份/日志、失败附加工件和文件系统余量；旧32GiB输出配额不足以承载这一示例范围。

301仅是已审核默认控制器的容量示例，不是本项目已冻结的GPU查询上限、预算或执行授权。实际完整搜索卡仍须同时冻结公平查询预算、物理范围、原未知终态读者、专用存储与双主机整卡报价，再按用户GPUh阈值推进。本轮GPU提交、预约与账本写入均为0。
