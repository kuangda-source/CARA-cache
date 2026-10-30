# 788 — 两卡限定、时序回归接受与完整R4 CPU运行

用户明确“四卡服务器在更新硬件，应该有一段时间用不了”，当前只在两卡推进。不再探测、传输或提交四卡，当前准备不等待四卡CPU验收；既有双端记录仍保留，未赋予14GPUh新GPU卡执行权限。

两卡独立readiness CPU使用发布源c2b079781ceb8a2d458f5eb3680fb267326a3927，于2026-10-31 00:59:01启动、2026-10-31 00:59:46退出0，无OOM。确定性就绪时序回归1项、supervisor原12项、host guardian原13项全部通过，无跳过；原先失败的容器替换控制通过。完整1176源文件、原runtime、1CPU/4GiB/无额外swap/无GPU/无网络限制均独立复核。该26项只是受影响的Linux执行控制接受，不代替完整112设计矩阵或GPU派发链。

随后只在两卡启动独立完整R4：2026-10-31 01:02:21，stage cara-budget-calibration-CPU-a6000-r4-20261031，source同上，完整1176文件；原R3失败不改。首次成功运维观察确认原Docker容器运行、CLI2240515/667464465、worker2240559/667464482；此前及后续一次回读SSH失败均保留为UNKNOWN传输历史；最近成功观测为原容器运行，未据超时推断退出。完整范围仍为两种采样flow，各112设计路径/51双FIT查询、133成功与3预定失败，另134执行+3规格控制；当前未接受数值结果。工作2400秒、退出60秒，1CPU/4GiB，无GPU。

原实际开始绑定的一次半程检查为01:23（r4-cpu），一次终验为01:44（r4-cpu-2），无变化静默，只恢复原运行；提前完整接受或失败收尾后删除多余检查。原容器ID、PID/start ticks及恢复/接受命令在交接。R4独立接受入口增加精确两卡R4 stage，原完整分母和全部门不变；5项本地控制通过，没有把夹具当实际R4接受。

中央唯一账本仍在四卡端，用户维护限制下未进一步探测。两卡CPU可继续，但实际GPU派发仍须解决唯一中央账本fresh准入；不得将历史快照复制为第二份权威账本。本轮没有GPU提交、预留、结算或cap变化。14GPUh实际卡仍需完整两卡CPU/执行链、真实存储及完整报价后单独审批。

[本轮总回执](../reports/cara_budget_two_card_only_readiness_and_R4_running_r1_20261031.json) · [26项Linux接受](../reports/cara_budget_readiness_two_CPU_accepted_r1_20261031.json) · [原R4运行交接](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_R4_CPU_HANDOFF_20261031.md) · [两卡限定](../plans/cara_next_stage_20261028/mainline/r2/TWO_CARD_ONLY_HARDWARE_MAINTENANCE_20261031.json)
