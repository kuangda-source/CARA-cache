# P1宿主内部评分接口：已实现，真实Linux CPU接受待补

2026-11-02终态更新：[848](../../../research/848_CARA_P1_ALGORITHM_AND_ACTUAL_HOST_FIT_CPU_ACCEPTANCE_20261102.md)与[实际宿主CPU接受](../../../reports/cara_v1_P1_host_FIT_CPU_accepted_r1_20261102.json)已补齐本接口的真实Linux服务/容器接受。原probe结束，完整两FIT成功/预设失败/重复/终态字节恢复通过；下列设计继续约束完整GPU外层集成，尚无真实GPU入口接受或P1授权。

宿主队列/原CLI/原容器读者已实现并有九项本地边界控制，见[846](../../../research/846_CARA_P1_FIRST_FLOW_ORIGINAL_CALLER_RESTORATION_AND_HOST_BROKER_20261102.md)。它仍待真实Linux独立容器与完整服务接受，不授予GPU启动。算法CPU使用受限CPU容器内的独立指标子进程；真实GPU卡采用下述宿主队列，让模型持卡与独立评分容器同时处于各自资源边界。

## 固定队列和身份

队列仅位于该新卡独立输出的`internal-FIT-queue/`。启动前登记一次context、scope/source/launch/registration、原guardian PID/start ticks/boot/namespace、固定离线Alex/PIQ资产、CPU容器镜像和两FIT身份。GPU侧客户端只提交`score-<完整policy指纹>`及完整两FIT工件/配置，不提交任意命令或目标主机。候选只能是本卡同一合法空间的19D/22D纯C策略。

最多42个不同完整查询：三估值×两预算×top3=18，以及两预算各至多12个搜索查询=24。相同完整策略/输入/seed质量工件只评分一次；每个科学语义位置仍记录自己的别名。原成功、失败、未决、未准入记录不覆盖；有意图而缺回执时只检查原CLI/容器，不再派发。

## 宿主一次执行

原GPU guardian在启动原GPU runner前，建立该卡唯一的宿主CPU服务原句柄。服务读固定队列，在完整双FIT请求封存后验证实际proof/视频字节、原context、实际D/C历史和策略指纹、源码/运行时及离线资产。再进行CPU26/27、12GiB可用内存和磁盘实时准入。

每个新查询先封存唯一launch intent和完整命令，然后由有PID/start ticks记录的原CLI创建一次容器。沿用固定镜像，2核/8GiB/无swap、cpuset26/27、无网络/只读root、GPU不可见；项目和source只读、唯一评分输出可写。worker为`scripts/score_cara_source_lifecycle_fit_r1.py`，单查询上限600秒，并受原GPU工作停止时间更早限制。模型容器的权限只需读写本卡队列和工件。

服务只有在同ID/标签/镜像/挂载/环境/命令的原容器与原CLI均终止后，才调用`accept_internal_scores`，独占写入一次完整内部接受。客户端等待该原结果并验证配置/内容哈希；部分曲线不返回算法。原worker失败、OOM、deadline或未知保留原分母和句柄，失败按全卡既定方式退出与结算，不能自动换一个CPU评分器。

## 费用和终态

GPU一直由原guardian单调时钟计费，包含创建/等待/故障清理；broker不创建第二份GPU账单。每预算查询准入使用冻结的完整两视频和CPU600秒上界，保留释放余量；实际搜索费用超过其口径时不得冻结成功。

运维查询只返回请求/完成/失败/未知计数和原句柄，外部不暴露部分LPIPS或计划排名。整卡终态后先关闭原GPU与服务、释放并唯一实际结算，再做完整科学接受。已封存内部指标直接复用；只为尚未评分的CHECK/强基线工件创建独立完整后置评分，不重算内部FIT。

## CPU验收要求

在同一生产命令构造和接受入口下覆盖：完整两个FIT/93帧、无GPU/离线资产、服务与GPU侧队列绑定、原CLI/容器恢复、UNKNOWN拒绝新派、worker故障/内存/超时、字节变更/部分FIT、重复请求/别名、停止余量和原费用口径。实际Linux使用新CPU专属stage与合成媒体，不读旧实验视频、不访问四卡或中央账本、不加载Cosmos权重。通过后再绑定完整GPU入口、冻结全146位置及实际费用报价，提交单次审批。
