# P1独立64GiB存储接受与新增导出CPU准备

P1新私有64GiB输出和48MiB独立日志已在两卡实际完成并接受。最终新增Linux入口CPU已完成精确源码包准备，本地14项控制通过；CPU尚未启动。P1 GPU与本卡中央权限仍为空。

## 原存储验收

[完整接受](../reports/cara_v1_P1_storage_accepted_r1_20261102.json) · [原启动](../reports/cara_v1_P1_storage_launch_r1_20261102.json) · [原完整捕获](../reports/cara_v1_P1_storage_capture_r1_20261102.json)

源`2e034b21ba9ad21c34947f2eb890330975ccc24c`，操作器`2842714d0eab4c971637955895fc1cd829248fa2b42c39b5c3e81e9d77ec596c`。新loop48、output_device1840，原准备进程已正常结束。独立观察确认：

- 64GiB backing完整物理分配，ext4带nosuid/nodev/noexec；输出空，约62.43GiB可用，4194294空闲inode。
- 48MiB日志位于另一文件系统，完整分配且原字节全零。
- 1MiB落盘后SHA一致，探针已删除；宿主剩余约688.73GiB，原低水位与共享保留规则未改。
- 旧M1/P0等卷保持；没有重测原93帧IO组件，没有GPU或账本操作。

此原准备不再启动或轮询来刷新文档。实际GPU派发仍须重新验证原挂载身份、空输出/日志、低水位与全部资源。

## 最终新增CPU

[精确1462文件隔离包](../reports/cara_v1_P1_final_packaged_local_CPU_r1_20261102.json)通过14项本地控制，其中包含一次实际本机便携出图。新Linux父进程拟执行13项：导出4、拟议19GPUh profile/报价3、原源码父类型5、空硬限拒绝1；不运行本机绘图库，不重放旧组件实验或指标。

它还会保存一份新合成完整52位置的原始导出包及独立SHA，在原CPU结束后回读该原字节，并用本机已有绘图环境实际出图。这样闭合Linux完整导出→原字节捕获→本机绘图，保持服务器模型/评分环境不变。

最初隔离包发现源码父类型控制意外依赖旧传输客户端的导入链，[本地拒绝](../reports/cara_v1_P1_final_local_source_closure_refusal_r1_20261102.json)保留；来源边界已移到独立轻量模块，默认原容器模式和显式已结束宿主模式保持。修正后的14项精确包通过，尚未创建远端最终CPU任务。

完成这项新增原件后，复用[854](854_CARA_P1_ENTRY_LINUX_CPU_COMPLETE_AND_LOCAL_FIGURES_20261102.md)及35处不变核心源，组成整卡CPU证据并准备GPU源包，再提交完整19GPUh与本卡原账本事务审阅。18.0273预测、250秒/标签未测假设、完整146/最多142与全部原科学边界保持。
