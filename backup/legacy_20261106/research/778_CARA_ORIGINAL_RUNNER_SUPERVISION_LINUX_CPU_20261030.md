# 原runner监督与Linux进程CPU验收

2026-10-30。新监督器把原子进程身份、硬限停止、独占/温度/存储检查及退出释放组合到同一控制路径。四卡CPU已完整接受；14GPUh实际GPU校准仍未批准或派发。

## 原身份先于执行

[子进程bootstrap](../scripts/cara_budget_process_bootstrap_r1.py)先核对原launch、registration和自身源码，在宿主PID视图记录boot、命名空间、PID/start ticks，再等待绑定同一原身份和launch SHA的执行许可。随后使用exec运行冻结argv，PID/start ticks保持，未得到许可则超时退出。CPU夹具强制隐藏CUDA/NVIDIA设备。当前实际CPU验证覆盖runner角色，container_cli角色还须随外层host guardian组合验证。

[监督器](../src/wcomr/cara_budget_supervisor_r1.py)独占原UUID租约，把租约FD传入原子进程；使用同一guardian的原开始时钟，扣除释放余量，不在supervisor启动时重置预算。生产默认每2秒核验独占、最长180秒等待原sole-runner上下文、每30秒采温，90C停止，保留600秒释放余量。CPU测试使用明确缩短的时间参数，不改未来生产默认。

进程组停止前核对原boot/命名空间/PID/start ticks，只给原组发送TERM，必要时升级KILL；不能把未知身份当成可停止的其他进程。记录触发温度后停止；忙设备或过热在派发前拒绝。原意图与start文件拒绝第二次运行，异常和正常退出均尝试保留原释放观察并关闭租约。

监督器不写GPU账单，也不接受部分科学输出。唯一费用仍归777的host guardian原单调时钟；这里没有单独的GPU派发CLI或预算预约。完整审批、源/资产/CPU/资源准入及Docker命令仍由待组合的once-dispatch入口负责，不能据此称整卡已可派发。

## 实际Linux验证

[原登记](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUPERVISOR_CPU_FRAGMENT_R1.json)限定1CPU/4GiB/零swap、无GPU/网络、只读根文件系统，120秒工作及30秒退出。macOS只能完成隔离载荷导入与语法检查，12项Linux进程测试明确跳过；该本地结果未计作通过。

[四卡实际接受](../reports/cara_budget_supervisor_four_card_CPU_accepted_r1_20261030.json)：原stage `cara-budget-supervisor-CPU-ada-r1-20261030`，CLI PID4188062，registration SHA `56228195c880124f4d8c38629c2e0bcacf70c1d7eb5e7d4b3e22aeb41a4eff4a`，19:52:58启动、19:53:07退出/0，无OOM。12项完整通过、0跳过，11个运行场景中实际启动8个CPU runner；正常上下文/退出、子进程失败、上下文超时/身份错误、外来上下文、运行中硬限/高温/低存储、guardian原时钟已到期、派发前过热/忙设备及CPU不能冒充生产均覆盖。

测试使用真实Linux子进程、进程组信号、锁、FD继承和48MiB控制日志；GPU观察/温度/上下文是显式合成元数据，没有真实CUDA或GPU容器。各场景精确检查预期停止原因，所有原runner已退出，旁边的真实CPU哨兵存活，租约释放，没有supervisor第二笔账单或重复运行。外层CPU容器的实际资源和源码绑定均通过验收。

[6项本地验收器控制](../reports/cara_budget_supervisor_acceptor_local_CPU_r1_20261030.json)拒绝缺失/活跃/失败终态、错误资源/源码/启动、部分场景、错误停止原因和范围升级。原62份B36关键源码、A32冻结及A/B费用保持。

下一步把host guardian、container_cli原身份、模式恢复、唯一原费用和本监督器串接，绑定实际64GiB专用文件系统，完成科学验收及双端受影响CPU/整卡报价后提交14GPUh单次启动审批。本轮新增GPU、预约及中央账本写入均为0，S/Q原运行和检查未改。
