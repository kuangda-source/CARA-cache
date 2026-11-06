# P1：监督与宿主评分共同收尾通过，快照费用待定

原 guardian/FIT R3 CPU 于 05:54:23 单次开始，05:55:28 退出0，34项控制全部通过且无skip。固定source `dd38b5fabd776faa57b4df975cafae40f2e9f802`，两卡单核26/4GiB/无swap、网络或GPU，600秒工作与60秒退出边界保持。此前R1/R2的两份导入失败原件保留；R3源包先完成独立目录、隔离解释器的完整本地检查，未修改任何原stage。

五个真实Linux原进程场景分别覆盖：正常服务关闭在原guardian账单结束之前；服务启动拒绝时没有GPU容器替身；服务中途失败停止原GPU替身；GPU替身失败也关闭原服务；CPU清理见证未知时保留失败，同时原GPU释放和账单仍可恢复。原PID/start ticks/boot/namespace、原外来CPU sentinel、Default恢复和禁止重放均通过。此CPU的GPU/Docker事件为显式夹具，不能据此声称真实CUDA执行或完整P1生产入口已接受。

- [34项原Linux接受](../reports/cara_v1_P1_guardian_FIT_Linux_CPU_accepted_r3_20261102.json) · [原proof](../reports/cara_v1_P1_guardian_FIT_Linux_CPU_original_proof_r3_20261102.json)
- [R1/R2源包复盘与R3句柄](../plans/cara_next_stage_20261101/source_lifecycle/P1_GUARDIAN_CPU_PACKAGE_REVIEW_AND_R3_HANDOFF_20261102.md)
- [848完整算法与真实宿主评分接受](848_CARA_P1_ALGORITHM_AND_ACTUAL_HOST_FIT_CPU_ACCEPTANCE_20261102.md)

可复用的P1算法原件已经覆盖完整双flow的292语义位置、128同状态标签、268实际tiny请求和158对合成93帧真实Alex指标；另一个宿主探针覆盖两个完整评分cohort、一次预设编码失败和原回执零重复。它们均已结束，原算法检查已删除，不再生成或评分。新外层只启用窄的P1服务接口，旧调用者默认行为保持。

本轮还补了费用审计。完整旧P0第20步的八干预，比同输入Uniform19完整请求平均多236.39秒，原CPU快照累计约9.97GB。P0为三图像/三恢复，V1单个shadow状态为一图像/两恢复，两者不同；该差值不能当作实测V1单标签成本。原草案给64标签的快照/IO余量为1260秒，等价每标签19.69秒，需要重新论证。若仅改变该项为20/60/120/180/240秒假设，含20%整卡余量分别约13.11/13.96/15.24/16.52/17.80GPUh；这些是敏感性场景，均非已测预测、硬限或授权。见[完整成本回执](../reports/cara_v1_P1_snapshot_cost_sensitivity_r1_20261102.json)。

下一项交付仍是完整P1生产总入口与绑定、释放后146语义位置接受、复用内部指标并只补最多32新指标、完整图表和一次冻结，以及资源/存储/正式费用报价。最多142物理生成和原科学范围保持。完整报价与受影响入口验证就绪后，一次提交>4GPUh及该新卡的原中央账本事务许可。当前没有P1 GPU启动或中央访问/交易，旧结果、预算责任和16保护/备用16保持。
