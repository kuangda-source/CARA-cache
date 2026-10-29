# S 完整矩阵编排入口 CPU 准备

新 `sq_s_runner_r1.run_matrix` 消费已有 inference，不加载模型或获取 GPU。它构造原 resource-checked sampler 和原 physical adapter，执行冻结的十个逻辑角色及各主机物理范围；请求前完整复位，成功、构造拒绝、存储拒绝、采样失败后都保留原失败并恢复状态。消费原 store 后不能重试。原数值采集、布局、codec、精度、28-block 资源 schema 和读写分母不变。

独立完整矩阵分类重新核查十个角色、36 步 guided/latent/保存视频与新对 pre-encoding OFF/ON 等价、108 因果源、56 Dense/52 C shadow、108 次首 snapshot 前 guard，以及八 raw/24 anchor、最终模型参数/精度和状态复位。数据完成仍标记等待模型清理与原 allocation 终态，不接受 GPU 释放、费用结算或科学收益。

本地 26 项控制通过。新双端 CPU 范围为每端两个完整 flow：A6000 18 个新 tiny 请求及两个独立 OFF 源；Ada 20 个新 tiny 请求；各 216 次 guard、280 个落盘文件 SHA/重读。使用固定 Linux image，2 CPU、8 GiB、1800 秒、GPU 隐藏、无网络。Ada 原容器/CLI 已退出 0，完整矩阵和 11 类错误回执拒绝已[独立接受](../../../reports/cara_sq_s_runner_four_card_cpu_accepted_r1_20261029.json)。A6000 因原 CPU 入口拒绝运行中的 Docker 容器而在 stage 创建之前退出，保留拒绝、不放宽准入、不影响 B36；双端 runner 接受仍未完成。不重跑已接受的原 full2B meta 或默认合成解码组件。

Ada CPU 实际耗时 644.136 秒、worker CPU 203.306 秒、已回收子进程 CPU 5.543 秒、parent peak RSS 0.870 GiB，分配 vCPU 时间上界 1288.272 秒；不是 cgroup 全量 CPU/峰值。半程原句柄确认仍在运行；作业 08:36:24 正常退出，终态取回晚于原 08:39 目标，实际观察时钟和延后量保留在[组件准备回执](../../../reports/cara_sq_s_runner_component_readiness_r1_20261029.json)。

这是完整 GPU entry 的一段实际编排，模型加载、host guardian、原生 GPU context/模式、源 stage、中央结算及真实标签仍未接受，S 14/17 GPUh 仍为未冻结提案。用户此次批准仅属于 Q1，不授予 S GPU 权限。下一步接通并验收原生产模型加载和完整 allocation 生命周期；真实 108 标签继续为零。
