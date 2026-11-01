# P1释放读者R3原CPU交接

仅恢复stage `cara-source-lifecycle-P1-release-CPU-a6000-r3-20261102`，source `733e908466aa0c82109a3ea7eeed7e3fb2861923`，registration `ed27e3e05421f05c075d00249de4d904c4dd53cec754fdfc404ed0293d2292b8`；[原启动](../../../reports/cara_v1_P1_release_Linux_CPU_launch_r3_20261102.json)，实际2026-11-02 07:08:20.311805+08，[首次观察](../../../reports/cara_v1_P1_release_Linux_CPU_capture_r5_20261102.json)。两卡GPU隐藏CPU2配额/8GiB/no swap/CPU26/无网络，工作1200秒/退出60秒。

只用 `scripts/cara_source_lifecycle_p1_release_cpu_r3.py capture --source-revision 733e908466aa0c82109a3ea7eeed7e3fb2861923 --output 新唯一回执`。UNKNOWN只恢复原stage/容器与原开始时间，不prepare、重派、改源、重跑旧算法/控制/指标。R1/R2原失败已收尾，旧检查已删；其同名ID不得与R3当前检查混同。R3仅修复合成账本schema；21控制继续按原R1不变source/原日志复用。新精确1414包本地隔离7项通过，不是Linux终态接受。

完整终态门：原CPU退出0/真实资源及源码runtime完整；146真实CPU工件/64标签/12恒等/52质量位置、最多32对新真实93帧Alex/PIQ、5拒绝控制、4新分析及一次原FIT冻结控制；原服务/评分子进程均结束，一次意图不可重跑，预设失败完整分母。内部host/内部评分在本夹具明确模拟，真实host证据复用848；不得把合成视频解释为V1效果。

成功仅以 `scripts/accept_cara_source_lifecycle_p1_release_cpu_r3.py` 指定本原launch、终态capture、新accepted及原proof输出接受；它不做生成/评分。失败保存原件而不重跑本stage。完整结果更新canonical并精确提交推送。

[安排](../../../reports/cara_v1_P1_release_CPU_acceptance_schedule_r3_20261102.json)：p1-cpu 07:19半程；p1-cpu-2 07:29终验。活跃仅运维计数，可调整同一个终验而不新建；终态收尾删除二者。无变化安静。

P1 GPU外层dispatch/完整资源准入和控制、后置评分实际一次派发/容器恢复、生产分析/图表/冻结组合及正式报价仍待。P1 GPU和本卡中央事务未获批准，四卡禁访；原cap226、旧16.5和所有冻结/保护集保持。
