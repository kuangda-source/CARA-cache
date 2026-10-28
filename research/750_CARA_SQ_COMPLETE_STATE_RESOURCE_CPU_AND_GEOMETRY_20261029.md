# S 完整状态清单、原2B元数据与双端CPU接受

2026-10-29。A6000 与 Ada 的原 R5 CPU 容器及 CLI 均完整退出0，独立验收后，两端33种状态 schema、108个 before-pair 边界及原2B meta架构逐项相同。[双端原件与费用](../reports/cara_sq_s_resources_dual_cpu_accepted_r5_20261029.json)。每端九项单元控制、四条完整36步 tiny 路径与十项错误回执拒绝均通过；tiny模型/decoder stand-in和meta网络分别声明，不产生真实S标签或视频结果。

原2B meta-only构造保留28 Block、569个BF16参数对象、113个原TE RMSNorm及完整H0拓扑。TE constructor/reset使用同一原函数体的显式meta设备，结束后恢复。虚拟参数字节4,118,349,824；七个buffer的meta字节368。没有权重加载、checkpoint路径解析、完整真实网络前向或CUDA初始化。R4的PyTorch2.7设备上下文拒绝改为零元素factory设备探测后通过；旧R1–R4原失败不覆盖、不重派。

A6000 R5容器68.450110秒、worker CPU74.036253秒；Ada459.525201秒、worker CPU118.041443秒。已回收子进程CPU分别2.943211/5.717769秒，parent RSS分别1.007416/0.974247GiB。七次原技术失败加两次成功共九个CPU容器，墙钟合计1805.790696秒、分配vCPU时间上界3611.581392秒；失败、wrapper及结果写出后的退出CPU未完整计量，以上不作为cgroup总CPU或聚合峰值。两端半程与终态检查按实际起点绑定；Ada曾写出结果但容器仍运行，继续等待原终态才接受。

[完整八组逻辑几何核算](../reports/cara_sq_s_complete_resource_geometry_r1_20261029.json)逐一投影所有33种原schema，并补入旧真实B1完整条件中的padding_mask和完整2B七个buffer。保留原BF16特征时，逻辑复制守卫最大28.679178GiB；特征按FP32保守情景为55.257303GiB。64GiB仅为下一版入口的逻辑守卫提案，尚未冻结进GPU profile。引用、完整backing storage、CPU/VRAM物理分配和临时峰值分开：这些数值不建立物理峰值或整卡时间。

下一步是把实际schema/backing-storage检查接入S生产入口，未知字段或超限在首次snapshot前拒绝，再完成双端生命周期与覆盖模型加载、完整hash/copy、流式存储、I/O和释放的整卡报价及受影响CPU组合。之后再提交单独S授权卡；真实108标签仍为0。已有Q1 R2审阅卡继续独立待授权，主线B36/F19及共享导航/中央账本保持原归属。新增GPU提交、GPUh和中央写入均为0。
