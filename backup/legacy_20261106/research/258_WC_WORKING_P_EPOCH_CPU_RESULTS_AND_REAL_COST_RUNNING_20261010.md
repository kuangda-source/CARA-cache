# 工作P年龄与非零区间重新基准化：纯政策CPU结果

2026-10-10。完整32视频卡已有组合终点正结果，见257；下一完整真实动作成本卡已顺序唯一启动。工作P小修订在纯政策CPU通过，支持把明确的来源／周期状态接入后续完整采样验证，尚不构成实际P质量或寿命结果。

R1保留：导入动态_choice时第二行缩进12而非8，IndentationError，未进入路径。R2登记提交ac523ec后仅修该缩进、测试仅换模块导入，未改controller判据或原在跑源，原失败没有删除或改为成功。

R2完整执行0.187385333秒exit0：18完整36步／648更新、12无P关闭态原controller精确比较、六含P控制、69工作P查询与49P快照扰动／恢复，三种改策略／改区间／未完成pair拒绝通过。前后源码及本地预算SHA保持，GPU0。

## 方法与全部含P控制

原D-only年龄查询和旧区间累计作为对照。两个修订分别是：按工作P年龄借用D-only rho表但保留区间；按同样年龄，在实际P完成后把经验区间重定为本次P的非零贡献。真实D历史不变，P的创建floor仍正，旧决策／solver／latent不改；查询明确标记D_ONLY_PRIOR_TRANSFERRED_TO_WORKING_P_AGE，不是已测P未来漂移。

| 合成输入 | 策略 | C／P／D次数 | 工作P来源查询 | P快照恢复 |
|---|---|---|---:|---:|
| 0 | LEGACY_D_AGE_KEEP_INTERVAL | 7／14／15 | 0 | 14 |
| 0 | WORKING_P_AGE_KEEP_INTERVAL | 7／14／15 | 14 | 14 |
| 0 | WORKING_P_AGE_NONZERO_REBASE | 14／14／8 | 26 | 14 |
| 1 | LEGACY_D_AGE_KEEP_INTERVAL | 23／1／12 | 0 | 1 |
| 1 | WORKING_P_AGE_KEEP_INTERVAL | 23／4／9 | 20 | 4 |
| 1 | WORKING_P_AGE_NONZERO_REBASE | 24／2／10 | 9 | 2 |

动作差异说明控制实现能够区分工作缓存周期与真实D校准历史，且可保存／恢复；输入、成本、floor和rho均为synthetic，不能用表中D减少声称真实模型节省计算或未来误差安全。重新基准化改变经验区间，不能解释成历史终点偏差消失。无P关闭态完整逐项一致是必要接线对照，不替代真实视频。

## 接续

当前真实成本卡sourcee80f73a／271载荷，监督3969409／runner3969425／CPU3969410，现场1791617995实际已处理AV28 COLLECT_OFF，36步尚0完成，模型GPU24450MiB；后续继续原句柄，完整八父／八起点／六模式／192组保持。实测成本与同状态矩全量独立验收后，才写真实排名／共享κ拟合输出。

下一独立普通采样版本接R2，并保留既有完整范围、两flow、无P／旧来源controller、两修订、P/D来源分离、恢复和失败控制。先以现有四层固定50%部分MLP形成完整候选，不先扩稀疏率或后端矩阵。实际minimal_a2a query只读准备仍无算子／矩形Q验证，不能算便宜刷新结果。

- [CPU实际回执](../reports/wc_working_P_epoch_transfer_cpu_r2_20261010_results.json)
- [R1原失败](../reports/wc_working_P_epoch_transfer_cpu_r1_20261010_results.json)
- [R2执行前登记](../manifests/wc_working_P_epoch_transfer_cpu_r2_preregistration_20261010.json)
- [原完整32方法结果](257_WC_RA_PLUS_A_COMPLETE32_FIDELITY_AND_COST_RESULTS_20261010.md)

飞书57→58同步完整结果与本轮CPU／成本进度，197块仅指定段改变，全文核对通过；[同步回执](../reports/wc_ra_plus_a_complete32_feishu_20261010_verification.json)。

最新资源现场1791618170–1791618235：完整成本卡首AV28 OFF日志已36/36采样，父回执尚未终态；原三个PID仍存活，唯一compute为runner3969425、同UUID、23246MiB，74历史提交。服务器账本为ACTION_COST_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT，当前全余额预留不是本卡实费／预算耗尽；最后实结36.671789542保持，终态按监督wall结算。不依据父回执尚未刷新而重投或改源。

