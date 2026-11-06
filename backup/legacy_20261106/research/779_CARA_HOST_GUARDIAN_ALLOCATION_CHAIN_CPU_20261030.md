# 原 guardian 控制链的 Linux CPU 验收

2026-10-30。外层 guardian 已连接原容器入口、监督器、runner、模式恢复及唯一原费用。修订 R3 的四卡 CPU 验证完整通过；这是控制链组件证据，14 GPUh 公平预算校准尚未获批或派发。

## 控制与费用

[外层 guardian](../src/wcomr/cara_budget_host_guardian_r1.py)绑定原 launch、授权、中央预约信封和源文件，先持久化尝试，再取得模式所有权和设备租约。原 CLI bootstrap 记录身份并等待同一 launch SHA 的许可；监督器继续使用同一个 guardian 开始时钟。生产默认监控间隔2秒、释放余量600秒保持，没有独立的 GPU 派发或预约入口。

容器以原 Docker cidfile 的完整 ID、镜像、manifest 和唯一 UUID 联合识别，停止操作使用已核对的完整容器 ID。观测未知或身份变化时，不停止未经确认的容器；只通过 pidfd 尝试结束已绑定的原 runner，保留不完整关闭见证，禁止据此结算或读科学输出。模式恢复只在所选卡空闲时进行，遇到外来进程则保留原状。原单调时钟覆盖准入、执行、停止和恢复；监督器没有第二份账单。

启动失败可能早于 bootstrap 自己写出的 start 文件。R3 保留监督器在 Popen 后已记录的原 PID/start ticks/boot/命名空间，确认原进程已退出后生成明确标为 `ORIGINAL_SUPERVISOR_POPEN_AFTER_CONFIRMED_EXIT` 的身份见证，并绑定原监督器终态 SHA。该记录同时标记 `bootstrap_self_witness=false`，不将父进程记录冒充子进程自证或已执行模型。

## 原失败与修订

[R1原失败](../reports/cara_budget_allocation_four_card_CPU_failed_r1_20261030.json)完整保留：12项中，2秒硬限夹具触发结算端的“缺少原身份不能证明退出”拒绝。R2 增加上述父进程原身份承接及固定的启动回执前失败测试。

[R2原失败](../reports/cara_budget_allocation_four_card_CPU_failed_r2_20261030.json)也保留：新增身份测试通过，但硬截止和 UNKNOWN 场景只得到 CLI 失败，未命中预定停止原因。该版未保存内层临时日志，不能进一步断言根因。R3 保留每场景内层元数据和日志，即使测试失败也先导出失败 CPU proof；CPU夹具的上下文等待从1秒改为5秒、硬截止从6秒改为10秒，并允许原 guardian 或原监督器报告同一原时钟触发的截止原因。生产参数没有修改。R1/R2受影响的源码原字节及 SHA 已保存在各自失败回执，且与实际登记一致。

R3首次提交的 SSH 握手超时后，先恢复原入口，确认原 stage 和同名容器均不存在，再以完全相同绑定完成其唯一启动。后续只读终验再次超时，继续恢复原 launch，未重复执行。服务器实际返回的 `Error response from daemon: No such container: ...` 与当前生命周期读者支持的两种空容器消息不同；只读恢复已核实这一格式，正式 GPU 入口前仍须补精确兼容测试，不能把任意 Docker 错误都当成不存在。

## 实际 CPU 证据

[R3登记](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_ALLOCATION_CPU_FRAGMENT_R3.json)限定1CPU、4GiB、零swap、无GPU/网络、只读根文件系统，工作120秒、退出30秒。macOS隔离导入通过，但13项Linux进程控制跳过，未将跳过计为通过。

[原四卡接受](../reports/cara_budget_allocation_four_card_CPU_accepted_r3_20261030.json)：stage `cara-budget-allocation-CPU-ada-r3-20261030`，CLI PID4191605，registration SHA `448b9f5a0fe15884b2bb51d4c8488db2e5c63748c4d27b3370ce3d2eb9dec2d2`，20:30:02启动、20:30:45退出/0，无OOM。13项控制通过、0跳过，覆盖12场景、12个实际CPU guardian和7个实际CPU runner。

| 场景 | 接受的边界 |
|---|---|
| 正常完整链 | 四个不同原身份、上下文握手、原退出、释放及模式恢复 |
| runner失败、启动回执前失败 | 保存原身份/失败和原费用，不重派，不报告成功 |
| 凭据缺失、忙设备、模式命令失败 | 保留实际尝试范围；忙设备不改模式 |
| CLI未创建容器、容器初始化失败 | 原 CLI/容器终态明确，失败费用不丢失 |
| 原硬截止 | 使用原开始时钟，停止原运行并保留停止原因 |
| Docker未知、容器ID变化 | 保持UNKNOWN，临时账本不结算；不停止别的容器 |
| 恢复时出现外来进程 | 不强制恢复模式，不报告执行成功 |
| CPU夹具进入生产入口 | 在分配前拒绝 |

真实 Linux 进程、pidfd/进程组停止、锁、48MiB独立控制日志及临时账本均实际执行；Docker/GPU/温度观察是明确的合成元数据。十个具有完整原终态的场景在临时账本各结算一次，重复接受不再写账；两个UNKNOWN场景不结算，旧16.5责任不变。所有已绑定原进程结束，真实旁侧CPU哨兵保留，原stage重入被拒绝。没有实际GPU账本写入或科学接受。

[本地验收器](../reports/cara_budget_allocation_acceptor_local_CPU_r3_20261030.json)另通过7项控制，拒绝失败/活跃终态、资源/源码/启动绑定错误、部分矩阵、错误停止原因、UNKNOWN升级结算及范围升级。62份原B36已接受关键源码和A32冻结SHA保持；S原卡及其检查未改。

下一步合并实际Docker观察兼容、64GiB专用硬配额、完整once入口和科学验收，完成双端受影响CPU及整卡报价后，提交一次14GPUh启动方案。全部批准和fresh准入前，GPU派发、预约及中央账本写入仍为0。
