# Q1 单次批准与 S 完整矩阵编排 CPU 承接

用户已直接回答“批准这一次 Q1 单卡”。[批准原件](../plans/cara_next_stage_20261028/sq/Q1_GPU_APPROVAL_R1_20261029.json)绑定修复后的 R3 执行源 `cd368922cbc70d610aaece6d1a71069fa45a3ecd`、双端原 CPU proof 与报价；科学范围仍为 12 个旧状态、111 pair/222 heads、零新 deep/父路径/视频，Ada 硬限 2、A6000 1.25 GPUh，原数值控制失败即停，不重试，不含 S。两份主机执行绑定仅是同一次批准的替代绑定，中央同 RUN 一次性 envelope 保持。

首次批准后检查发现 Ada 没有合格空卡；A6000 虽物理候选空闲，但主线 B36 持有中央主机预约，原 guardian 和原容器已只读确认运行。最新[联合准入](../reports/cara_sq_q1_approved_combined_admission_r2_20261029.json)两端仍不合格，未创建 Q1 预约或启动。同对话 15 分钟 heartbeat `q1` 已建立并去重，状态不变静默；完整准入后直接执行这一次已批准的卡，再按实际 guardian 起点设置半程和全程验收。没有更改 B36 的源、进程、锁或费用。

S 新 `sq_s_runner_r1` 在已有 inference 上构造原 resource-checked sampler 和 physical adapter，执行完整矩阵，逐请求复位并检查原模型参数/精度和模式；成功和失败均恢复原状态，store 消费后禁止重试。完整数据分类独立重查角色、每步 guided/latent/保存 RGB 与新对 pre-encoding OFF/ON、108 因果来源、56 Dense/52 C shadow、首 snapshot 前资源 schema 和八 raw/24 anchors。数据完成仍不能接受模型清理、GPU 释放、费用结算或科学收益。

执行源 `6dccf20c5d78de43e7f1ae40b640950f9a1f068c` 的 Ada 原 CPU 容器完成两个 flow、20 个完整 tiny 请求、216 次 guard、280 文件 SHA/重读，26 项入口/失败控制及 11 类错误回执拒绝已[独立接受](../reports/cara_sq_s_runner_four_card_cpu_accepted_r1_20261029.json)，容器和原 CLI 均退出 0。A6000 CPU 入口在原 stage 创建之前拒绝运行中的 Docker 容器；保留拒绝，双端接受仍待完成，不绕过准入。

Ada 实际墙钟 644.136 秒、worker CPU 203.306 秒、已回收子进程 5.543 秒、parent RSS 0.870 GiB；分配 vCPU 上界 1288.272 秒，非全 cgroup 消耗。半程确认原句柄运行；08:36:24 已退出，终态取回晚于 08:39 计划目标，实际观察与延后量保留。[完整组件回执](../reports/cara_sq_s_runner_component_readiness_r1_20261029.json)。真实模型加载和完整 allocation 生命周期未接受，真实 S 标签仍为零，S 整卡 14/17 GPUh 仍是未冻结提案，Q1 批准不扩展到 S。

后续继续 S 生产模型加载、host guardian、源 stage、独立终态与中央结算的完整承接；Q1 资源监控独立维持。没有新的 GPU 提交、GPUh 或中央账本写入，主线共享导航与预算未编辑。
