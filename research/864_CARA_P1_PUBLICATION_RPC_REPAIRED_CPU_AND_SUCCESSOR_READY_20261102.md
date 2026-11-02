# P1 两处修复已接受，独立新单次准备完成

请求发布竞态和RPC stdout包装问题已经修复并完成实际两卡Linux验收。独立新单次R2的完整CPU、1473文件源包、64GiB独立输出及48MiB日志均已准备接受；新GPU与本卡中央事务仍需明确批准。原单次R1的失败、4.933201964GPUh唯一结算和全部旧冻结保留，不重放原运行或读取其部分科学结果。

## 修复与验证

[确定性修复前回执](../reports/cara_v1_P1_publication_RPC_deterministic_RED_r1_20261102.json)复现了两个生产故障：消费者在request发布前看到score目录；内层saved字典覆盖外层stdout。修复后Client先创建隐藏.pending目录、完整写入/fsync再rename发布并fsync父目录。未发布意图保留且拒绝重试，真正可见的残缺原目录仍拒绝，不以轮询等待掩盖未知请求。RPC使用隔离exec命名空间和redirect_stdout，原异常保持失败，输出按原字节SHA封包。

[第一组Linux33](../reports/cara_v1_P1_publication_RPC_Linux_CPU_accepted_r2_20261102.json)：本地隔离28通过，Linux33全通过，包含实际Linux进程/服务清理5项；新CPU已退出0。新发布/失败/原响应复用/42上限/RPC等8控制和原受影响broker10、权限/服务/guardian15均通过。CPU明确使用合成工件和模拟Docker，未加载真实Cosmos、未重评原指标。非Linux本机对进程见证做显式fixture，Linux使用实际/proc见证；没有将本机5项平台skip冒充通过。

[第二组Linux56](../reports/cara_v1_P1_successor_identity_Linux_CPU_accepted_r2_20261102.json)：独立R2身份的权限、完整入口/资源、中央事务、后评分52/失败拒绝、一次FIT冻结和便携导出56项通过，原CPU已退出0。另本机1项真实绘图控制通过，本地共57；Linux未安装Matplotlib，图表仍按原方案本机交付。该组没有真实科学指标重算。新CPU只继承原33组已成功结束的源，未继承失败GPU的结果。[整卡组合证明](../reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json)完整绑定原科学/入口CPU证据与这两组增量：仅broker Client发布、RPC控制、身份/binding和相应fixture改变，原非Client broker/Host AST与原源一致；其余原1462文件中未改的数值/算法字节和全部runtime保持。

## 可执行的新卡

新run为cara-source-lifecycle-V1-P1-full146-r2-20261102，planned launch498503f9cfd249f1aab929da18f04e10，source8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99，registration8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884。[独立源接受](../reports/cara_v1_P1_successor_source_accepted_r2_20261102.json)回读1473文件和4 sidecar全部一致，没有授权sidecar、GPU意图或容器。初次长输入包超时后，先capture再只读确认无stage/intent/原bootstrap；随后仅移除重复传输的来源映射，在SHA绑定的CPU父注册中重建同一映射，保持CPU证明原字节SHA，完成同一stage并独立capture。原未知/拒绝均保留，没有重复准备已结束CPU/存储或原GPU。

[新独立存储](../reports/cara_v1_P1_successor_storage_accepted_r2_20261102.json)：/dev/loop49、output device1841，64GiB完整物理占用、独立48MiB journal、1MiB持久化探针通过，输出空/日志pristine，准备进程已结束。原R1卷和日志保留。[准备资源快照](../reports/cara_v1_P1_successor_resource_snapshot_r2_20261102.json)MemAvailable50.10648GiB、原A6000空闲45°C/24MiB、无compute PID/MPS，CPU24–27与独立输出通过；这是只读准备快照，审批后必须重新做完整fresh准入。

新中央operator使用原账本同机持久化.sync缓存，避免再次依赖/tmp。新卡尚未访问四卡、准备中央operator或写账本；新授权草案execution_authorized/central_transaction_authorized均false，旧单次许可不能继承。四卡仅待申请本卡原账本读取/唯一预约/实际结算，不请求实验、迁移或新cap增额。

## 完整范围、费用和下一步

科学scope97c6941ebded8e829d1ba28e5f71e868aa781e20b2075fd9062c5abe47ebaad1保持：完整146语义／最多142物理／5176pair／64同状态shadow标签、自动19D/22D、三层估值与同费用LPIPS搜索、13角色/52位置；原93帧Fidelity、旧CAL/曝光CHECK、旧冻结和最终/备用16保护输入保持。整卡冷启动重新执行，不复用失败R1的38视频或部分FIT结果。

[完整新审批卡](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_REPAIRED_SUCCESSOR_SINGLE19_REVIEW_R2.md)：预计18.05067GPUh、建议硬19；较原18.02734多列最多42查询×2秒发布落盘余量84秒。原64标签snapshot250秒仍是保守工程假设，未从部分科学输出取成本。40GiB GPU/8GiB内部CPU/no swap、宿主初始50GiB/每查询新鲜12GiB、90°C/600秒释放余量保持。

当前只等待新单次19GPUh及本卡原账本事务批准；批准后按[新交接](../plans/cara_next_stage_20261101/source_lifecycle/P1_REPAIRED_SUCCESSOR_PRELAUNCH_HANDOFF_R2_20261102.md)先恢复原R2句柄、完整fresh资源/资产/预算、唯一预约/启动，再按实际开始设1/4、半程和终验。余额不足不增额。成功失败均唯一实耗结算；完整成功后才一次CPU接受和一次FIT冻结。新的GPU启动尚未发生，CPU通过不构成V1方法效果。
