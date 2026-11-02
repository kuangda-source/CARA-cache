# P1 请求发布竞态：原失败、释放与唯一结算

原单次P1已于 **2026-11-02T20:40:28.311146+08:00** 失败退出并释放，完整146语义范围未完成。此轮交付是工程失败定位和收尾，未形成V1视频效果结论、未冻结FIT、未派发任何后评分或新GPU。[完整收尾回执](../reports/cara_v1_P1_original_failure_complete_acceptance_r1_20261102.json)绑定原终态和唯一费用结算。

## 原终态与范围

用户要求新增的1/4检查原计划20:15；本次原句柄实际回读于2026-11-02T20:51:42.263445+08:00，该时间晚于原20:40终态，不将目标检查时间冒充实际观测时间。[原capture](../reports/cara_v1_P1_quarter_original_status_r1_20261102.json)仍绑定launch a2b1dcf993774897902a5f0cc0858220、source6bf82dd262c082a6786588d39d9ea23da74cc907、registration9bf9a98db7308f3fa0b867e9ec0a928c8ea0d7389c31f394fd7bda5f3715dc35和原A6000。

- 已完成38个物理请求文件，物理上界142；语义分母始终为146，未在失败后推算完整语义或科学接受比例。
- 内部FIT运维计数为请求3、完整接受2；未读取/解码部分科学分数或据此选计划。
- 原服务报告 `OriginalQueryUnknown: Torn original query intent; no new scorer`，guardian发现服务退出后停止原GPU；容器退出130，OOMKilled=false。supervisor共7928次观测、原runner上下文已核验。
- guardian/CLI/supervisor/runner及原FIT服务均已结束，UUID/模式锁释放，Default恢复，GPU空闲。后续只读快照46°C，MemAvailable约51.515GiB，独立输出余量62.115GiB。[释放接受](../reports/cara_v1_P1_original_failure_release_accepted_r1_20261102.json)由原financial_terminal入口通过。终态证据的失败入口是查询发布；本次没有报告容器OOM或热保护错误。

## 请求发布竞态的直接证据

[只读文件元数据](../reports/cara_v1_P1_quarter_failure_operational_metadata_r1_20261102.json)仅保存文件大小/时间/摘要和运维状态，未返回科学指标。第三个请求的request.json写入时间为2026-11-02T20:40:24.629285+08:00；服务已于2026-11-02T20:40:24.492562+08:00记录退出，前者晚 **136.722毫秒**。该请求随后存在，原服务在目录已可见、请求尚未发布的窗口中退出。

固定源码中，`Client.request`先创建可被`score-*`扫描到的目录，fsync父目录，再创建request.json；`Host.serve`扫描到目录但request不存在时立即判为torn并失败。这是生产者发布完成前就暴露给消费者的竞态。[绑定诊断](../reports/cara_v1_P1_original_publication_race_diagnosis_r1_20261102.json)保留原路径、顺序和精确时间。原模型、DP、搜索和评分代码未修改或回放。

下一步应单独做CPU修复与确定性回归：先在不可见临时目录完整写入/fsync请求，再原子发布可见查询目录；暂停生产者覆盖发布前窗口、完整发布只派一次、既有响应复用和真正残缺原请求继续拒绝均须验证。不得以等待或重派掩盖真实未知原查询。该CPU修复尚未执行；新的GPU整卡需要重新完整准备和单独批准，本次19GPUh单次批准已消耗。

## 原中央事务恢复和结算

最初central-status在原缓存校验处失败。[只读诊断](../reports/cara_v1_P1_quarter_central_cache_readonly_r1_20261102.json)确认原 `/tmp/source-lifecycle-P1-central-operator-a2b1dcf993774897902a5f0cc0858220` 整体缺失，未将原因归于任何未经证实的维护操作。

[精确恢复回执](../reports/cara_v1_P1_original_central_cache_restored_r1_20261102.json)先确认原账本和原预约身份，再将原CPU证明绑定的同115个源码字节恢复到原位置，未调用central-prepare、未建立新operator身份、未改GPU源或账本。中央原预约和账本随后回读与原预约快照完全相同。

一次central-recover还暴露了本机RPC包装问题：外层暂存stdout的全局变量saved被内层CENTRAL的原预约字典覆盖，导致`dict has no attribute flush`。失败回执保留；随后用原central-status成功回读证明原预约无变化，没有重复增额/预约。此包装缺陷仍待CPU修复，不能把输出来回失败当成重复事务的理由。

[唯一实际结算](../reports/cara_v1_P1_original_failure_central_settlement_r1_20261102.json)由原settle接受完整terminal capture，原audit_settlement通过。guardian完整单调区间17759.527069943026秒，实际 **4.933201963873063 GPUh**；原19预约解除，cap250保持，used201.95503799855743、旧reserved16.5、available31.54496200144257。只增加原job的一次结算事件86，原旧责任和所有其他记录保持。

## 监控与科学边界

原p1-quarter、p1-2、p1-3均已删除，[关闭清单](../reports/cara_v1_P1_acceptance_schedule_closed_r4_20261102.json)及[删除核验](../reports/cara_v1_P1_quarter_check_complete_cleanup_r1_20261102.json)保留。没有重新prepare/dispatch/重启GPU，没有派发后评分、读取部分LPIPS、重选任何计划或冻结本轮。A32/B36/S/Q/旧搜索、四旧CAL及曝光CHECK范围、WC/RA FIT UNMATCHED、最终/备用16保护输入保持。
