# P1 guardian/FIT CPU 源包复盘与新 R3

两次新CPU均在测试导入阶段结束，未进入原进程场景、未加载模型或派GPU。R1遗漏原guardian测试夹具；R2补上测试依赖后暴露出测试模块为检查REMOTE语法而导入本地SSH transport，间接要求远端携带只应在本机使用的源码。原失败分别保存，原stage不改、不重启。这是同一源包边界的连续失败，按执行流程完成本次复盘。

修复收敛为：远端测试直接读取已注册transport文件的REMOTE字面量并做AST语法检查，不执行本地传输层导入。新的R3先将完整1390文件源包复制到独立临时目录，用隔离解释器、仅包内src/scripts/tests路径执行完整测试集。本地29项通过、5项Linux原PID场景明确skip；新CPU再执行34项且必须无skip。这样验证打包后的真实导入/资源断言，而非继续补传无关本地SSH模块。

- 新stage `cara-source-lifecycle-P1-FIT-guardian-CPU-a6000-r3-20261102`，两卡。
- [打包隔离本地回执](../../../reports/cara_v1_P1_guardian_FIT_packaged_local_CPU_r1_20261102.json)；原R1/R2失败见同目录报告。
- 固定CPU26/单核4GiB/no-swap/no-network/no-GPU，600秒工作、60秒退出；只使用显式合成GPU/Docker事件和真实Linux原进程。
- 新发布source与原launch/capture以`reports/cara_v1_P1_guardian_FIT_Linux_CPU_launch_r3_20261102.json`为准。已有stage/意图或连接UNKNOWN只用`scripts/cara_source_lifecycle_p1_guardian_cpu_r3.py capture --source-revision 原source --output 新唯一回执`，禁止再次prepare。
- exited0且原proof完整后，用`scripts/accept_cara_source_lifecycle_p1_guardian_cpu_r3.py`只读原launch/terminal capture，接受和原proof都写新文件。要求34控制、五原进程场景、外来CPU sentinel保持、原服务/GPU替身全部结束、费用区间覆盖正常服务关闭；cleanup未知场景保留原失败而不抹去GPU原账单。

原完整算法R3与实际宿主FIT探针均已接受，不重生成或评分。当前CPU只验证新外层窄接口，仍不是完整GPU入口接受；完整生产CLI、释放后146语义/内部指标复用/至多32新指标、图表/冻结、资源/存储及正式报价继续准备。没有P1 GPU或新中央事务许可，不访问四卡。

另外，[完整旧P0费用审计](../../../reports/cara_v1_P1_snapshot_cost_sensitivity_r1_20261102.json)给出八条单点干预相对同输入Uniform的平均236.39秒差值。P0使用三CPU图像/三恢复，V1标量为一图像/两恢复，不能把该差值当作实测V1单标签价格。当前1260秒快照余量相当于64标签各19.69秒，必须重新论证；20/60/120/180/240秒假设仅作敏感性场景，对应含20%余量约13.11/13.96/15.24/16.52/17.80GPUh。不是实际预测或获批额度，不由CPU tiny耗时推GPU费用。
