# P1完整结果便携交付与正式工程报价

完整结果的导出和绘图交付已接通，拟议19GPUh资源配置与18.0273GPUh完整工程报价已保存。新增本地控制共13项通过；两卡Linux新增导出/配置入口、整卡证据组合、新64GiB存储及源包仍待完成。本轮没有GPU或中央账本操作。

## 便携交付

[入口](../scripts/cara_source_lifecycle_p1_result_bundle_r1.py)在两卡执行`export`，先调用原完整52分析/一次冻结入口，确认原评分supervisor、CLI、容器和worker全部结束。只导出原report、analysis和freeze字节、独立SHA及原源码绑定；不会重新计算指标、选计划或写原GPU stage。

本机`render`必须提供原导出回执的bundle SHA；检查原三个文件的SHA、run/launch/scope、完整52/146、CPU标记、分析源及原FIT冻结一致性后，用本机现有Matplotlib输出原13角色、双时钟、93帧曲线及四CSV。它不恢复远端句柄、不调用Docker、不增加服务器绘图库。已有导出只校验原字节，部分目录和变化文件拒绝覆盖。

五项CPU控制覆盖无Matplotlib的宿主导出、本机真实PNG/PDF/CSV、重复原件、错误SHA/源码/CPU模式、冻结变更及活跃/未知/失败拒绝。全部为新合成元数据，零指标计算。

## 拟议19GPUh与完整报价

[profile](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json)与[正式工程报价](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json)保留完整146语义/最多142物理、5176模型pair、42内部查询/84持卡指标、最多32后置新对。预测18.02733759237635GPUh，拟议硬限19；GPU执行授权和本卡账本许可均为空。

价格包含64点shadow与状态采集/哈希/恢复、全部候选/对照/控制、持卡评分/容器启动、加载/关闭和20%余量。250秒/标签是明确未实测的预算假设，不能称V1快照测量；22D及持卡全分辨率CPU评分仍含外推/代理。三项CPU验证新19配置与完整费用绑定，并拒绝缺少本卡授权、旧18限制和遗漏费用。原GPU未启动，实际GPU限额未获批准。

## 来源与存储准备

CPU源码传输默认仍要求原容器结束；新增显式宿主CPU分支只接受已结束、同原PID身份、无错误、带原CPU证明的来源。五项控制通过，修复[854](854_CARA_P1_ENTRY_LINUX_CPU_COMPLETE_AND_LOCAL_FIGURES_20261102.md)之前的回执类型缺口，不重放任何旧CPU。

新[64GiB私有卷操作器](../scripts/provision_cara_source_lifecycle_p1_storage_r1.py)、[单次启动/原件捕获](../scripts/cara_source_lifecycle_p1_storage_r1.py)及[接受器](../scripts/accept_cara_source_lifecycle_p1_storage_r1.py)只面向新P1：新路径不存在、80GiB预留前空间、独立48MiB日志、原进程/原源码绑定、8GiB输出/16GiB宿主低水位和8192 inode；实际完整空间分配、ext4、1MiB落盘SHA和原件接受后才算存储就绪。它们目前仅完成语法/范围准备，尚未声称已创建卷或通过实际存储验收。

[本地13控制与准备回执](../reports/cara_v1_P1_result_bundle_quote_local_CPU_r1_20261102.json) · [完整单卡审阅草案](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_REVIEW_DRAFT_R1.md)

接下来完成两卡新增入口CPU和独立存储，按原文件/源复用组合整卡证据、准备新GPU源包；全部具体可审阅后，再请求完整>4GPUh及本卡原中央读取/预约/实耗结算。四卡维护限制、旧16.5责任、cap226、原科学冻结和保护输入保持。
