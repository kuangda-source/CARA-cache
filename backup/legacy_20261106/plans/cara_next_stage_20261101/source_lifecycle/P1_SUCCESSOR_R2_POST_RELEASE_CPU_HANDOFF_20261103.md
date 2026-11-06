# P1 R2已完整关闭：引用原接受、冻结与结果记录

**当前全链已结束：146语义/64标签/142物理/5176模型pair/12完整等价门，以及32新对＋20封存对组成的52质量位置全部接受。原评分CPU于12:44:56退出，完整分析、原FIT一次冻结、原bundle及本机图表已保存。当前V1未通过19D工程筛选，来源间距特征在19D/22D均未产生质量增量；不晋级P2。所有P1 R2检查已删除，不再调用现场读者、派发、评分、结算或冻结来刷新文档。**

当前只读 [完整结果869](../../../research/869_CARA_P1_R2_COMPLETE_RESULTS_SOURCE_INCREMENT_FAILED_20261103.md)、[完整接受](../../../reports/cara_v1_P1_successor_complete_acceptance_r1_20261103.json)、[原分析](../../../reports/cara_v1_P1_successor_original_complete_analysis_r1_20261103.json)、[原FIT冻结](../../../reports/cara_v1_P1_successor_original_complete_freeze_r1_20261103.json) 和 [已删除检查R7](../../../reports/cara_v1_P1_successor_acceptance_schedule_r7_20261103.json)。以下内容均为历史承接，不授权重跑。

**最新阶段：R3工件读者已12:28:35正常退出，146语义/64标签/142物理/5176模型pair/12完整等价门通过，未重算旧分数。32新对评分意图已唯一启动，原supervisor56710/start_ticks697511712活跃（boot13495735-f30b-47a2-af0a-2496f5206a0b）。只用R3控制器recover-score，不再launch-reader、dispatch-score或重跑任何读者。当前同一个p1-r2在13:15继续，R6检查承接为准。**

先读 reports/cara_v1_P1_successor_full146_artifacts_accepted_r3_20261103.json、reports/cara_v1_P1_successor_post_score_dispatch_r1_20261103.json、reports/cara_v1_P1_successor_post_score_original_capture_r1_20261103.json 和 reports/cara_v1_P1_successor_acceptance_schedule_r6_20261103.json。以下保留了原终态与验收环境修正历史。

先读 reports/cara_v1_P1_successor_final_release_accepted_r1_20261103.json、reports/cara_v1_P1_successor_final_settlement_r1_20261103.json、reports/cara_v1_P1_successor_released_reader_actual_start_accepted_r1_20261103.json 和 reports/cara_v1_P1_successor_acceptance_schedule_r5_20261103.json。本交接是当前阶段，旧post-launch交接保留历史。

原run cara-source-lifecycle-V1-P1-full146-r2-20261102，launch498503f9cfd249f1aab929da18f04e10，source8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99，registration8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884。原stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102`。

GPU于2026-11-03 10:55:21.249004 Asia/Shanghai正常退出，142物理请求和42双FIT内部查询全部完成，原进程/FIT服务结束、锁释放、Default恢复。**12.270682711747423 GPUh已唯一结算**，原硬19未超，禁止重派GPU、改源/配置或重复settle。cap250未增加，used214.22572071030484/reserved16.5/available19.27427928969516；旧16.5和原R1失败4.933201964费用保持。四卡不做实验、不迁账本。

以下R2工件读者已于12:18:48失败退出，保留原件且不得重启。它缺少主机Docker核验入口及原查询状态目录写入挂载，未能恢复原FIT容器的终态；不是GPU失败，也没有运行任何新评分。见 reports/cara_v1_P1_successor_released_reader_original_failure_r2_20261103.json。

原R2完整工件CPU读者历史：

- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-P1-successor-released-artifacts-CPU-r2-20261103`
- container：`90a1fba73c8583059d793e4b7a37d14233334c991081806bdd2240a77ee81509`
- worker4191648/start_ticks697430552，boot13495735-f30b-47a2-af0a-2496f5206a0b；12:16:42开始。
- 2CPU/8GiB no-swap、26,27、无网/GPU隐藏，最长3600秒；固定原stage/source的released_artifacts。
- launch：reports/cara_v1_P1_successor_released_reader_launch_r1_20261103.json；原capture_r1及后续新capture只恢复，不重派。

当前修正验收边界的R3工件恢复使用同一原科学worker字节，stage为 `/data20t/gaokuangda/worldcache_workspace/.sync/cara-P1-successor-artifact-host-inspect-CPU-r3-20261103`，container `0e5155e35f43c142448e9b4b00b61114db8cc5da9d041ca2213a037427f3a05d`，12:26:32开始，2CPU/8GiB no-swap/26,27/GPU隐藏不变。新增只读主机Docker CLI/socket挂载，供原Host.reader.inspect恢复旧容器；原输出可写仅供原recover_query写查询状态元数据。原指标和数值源不变，不重算已有分数。

当前只用 `python3 scripts/cara_p1_successor_artifact_recovery_r3.py capture-reader --output 新唯一回执`，不再使用旧R2入口。禁止launch-reader、prepare或重启原容器。网络UNKNOWN只恢复原件。固定released_artifacts完整验证146语义/64标签、142视频和12latent/RGB/RNG等价门，不重新评分。活跃时只保存运维，不读部分科学分数。

当前R3读者成功退出且状态为 `ORIGINAL_RELEASED_FULL146_READER_ACCEPTED` 后，才由同一R3控制器 `dispatch-score` 调用原stage的score_dispatch一次至多32新CPU对，复用本卡封存FIT组成完整52位置。原post-score intent存在/CPU活跃/UNKNOWN只用 `recover-score`，禁止重复评分。评分原2CPU/8GiB no-swap/26,27/GPU隐藏、7200秒保持，不读活动CPU的部分LPIPS或T_DD。

完整52原CPU退出接受后，控制器 `complete-export` 调原固定source完整报告、一次原FIT冻结和portable export。成功回执的bundle_raw_utf8是原bundle字节，保存到本机并以export.bundle_sha256独立校验。使用已有 `.sync/cara-p0-plot-python/bin/python scripts/cara_source_lifecycle_p1_result_bundle_r1.py render --bundle 原本机bundle --expected-sha256 原exportSHA --output 新目录` 生成完整图表，不在服务器装Matplotlib，不重选赢家或重评旧冻结。真实失败保留原终态和完整失败分母，不冻结或自动重跑。

同一个p1-r2于2026-11-03 **13:15** 继续，quarter/half已删。32新对原CPU评分活跃则调整同一终验；完整接受或真实失败收尾后删除。13角色双时钟/93帧/实际完整校准费用、四旧CAL/曝光CHECK、全部旧冻结、WC/RA FIT UNMATCHED和最终/备用16保护输入保持。GPU完成不等于方法成立。更新canonical、研究记录并精确提交推送，不自动下一卡。
