# V1标量CPU：保留原R1源身份失败，准备独立R2

新R1 CPU原容器于02:29:45启动、02:30:42退出1，1353份注册源及原运行时字节保持。11项固定估值/选择控制已在该Linux容器通过；完整标量采集尚未执行。原终态、完整回读及摘要见[原失败记录](../reports/cara_v1_scalar_Linux_CPU_original_failure_r1_20261102.json)，不得重启或prepare原R1。

失败位于原UniPC尺度导出：完整请求夹具把调度器类放在动态执行的`cpu_full_unipc`命名空间，`inspect.getfile(type(scheduler))`无法找到原源文件，固定源身份检查因此拒绝它。修复只让新CPU夹具通过已注册的importlib模块从固定原UniPC文件导入类；源哈希检查保持。尚未得到标量、完整父请求或方法效果结论。

独立R2 stage为 `cara-source-lifecycle-V1-scalar-CPU-a6000-r2-20261102`，沿用32条完整tiny请求/128标签、原11组件控制及固定原UniPC尺度。仅复用已终止R1中逐字验证过的源码缓存，不继承其CPU通过结论，不改原失败目录。R2仍是CPU、单核26、无CUDA、原内存/零swap及600+60秒边界，实时资源准入后单次启动，UNKNOWN只capture。

并行完成了[完整P1剩余接口审计](../reports/cara_v1_P1_remaining_interfaces_audit_r1_20261102.json)：旧搜索硬编码19D、额外保护第24步和RGB MSE，不能直接作为新LPIPS/22D公平对照。新对照须使用与V1相同合法空间、完整93帧LPIPS及按每预算实测V1校准费用设限；查询数上限不等于GPUh，持卡CPU等待、失败和共用参考均计入。旧赢家与费用保持。

P0原GPU source3263bdfe、14/512/8范围、1.95硬限、原句柄和03:03终验不变。此次只有新CPU准备；完整P1 GPU和本卡之外的新中央事务仍待完整方案审批。
