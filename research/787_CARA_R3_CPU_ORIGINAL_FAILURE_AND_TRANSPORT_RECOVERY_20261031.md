# 787 — R3原CPU失败保留与连接恢复边界

原两卡R3源包经完整SHA校验后，2026-10-31 00:43:36启动，00:48:09退出/1、无OOM；容器ID和原启动回执已取回。原1174文件与12个runtime文件完整，1核/4GiB/无额外swap、无GPU、network none保持。3项规格控制通过；134项执行控制中133通过、1失败。完整112路径数值矩阵尚未开始，无CPU-proof，独立接受器实际拒绝该原终态。原stage、容器、源和失败日志保留，不重启、不覆盖。

失败为test_replaced_container_not_stopped：预期发现原容器creation ID替换，但监督器先因EXACT_OWN_RUNNER_NOT_SOLE_CONTEXT拒绝，外层记录Original container CLI failed。源码检查发现一个可导致该错误的窗口：GPU采样在前，ready文件检查在后；就绪在采样过程中发布时，空旧快照会被按就绪后状态验证。候选修复改为先读取就绪状态、再采样；独占、身份、温度和预算门不变。另增真实Linux子进程确定性回归，令就绪恰在采样期间出现。Mac只跳过该1项，尚无修复后的Linux接受；不可把修复发布等同验证通过。新版本后续须用独立CPU stage验证，不改原a498运行。

Windows诊断由用户转回：未见认证失败、并发拒绝；TUN关闭，Clash SSH流量未命中；Windows Tailscale和防火墙日志未获读取权限。不能据此证明死ControlMaster或完全排除外层网络。当前任务有效配置已确认ControlMaster=false、ControlPersist=no及客户端探活。任务专用直接TCP入口沿用原Tailscale地址、用户、密钥和严格hostkey；绕过tailscale nc后成功完成两卡1,098,971字节源包、启动和终态回收，但四卡传输校验至98,304字节后仍被100.103.229.16:22重置，后续大小待原文件prefix恢复。四卡没有启动R3。

Mac netcheck记录UDP可用、映射随目的地址变化，最近DERP为Nuremberg，并出现routerIP/FetchRIB sysctl cannot allocate memory警告；这些是排查线索，不是根因证明。本轮未改全局SSH、Clash、Tailscale或服务，也未清理其他会话。

原CPU在20分钟中点前结束，本轮直接恢复终态，未建立多余半程/终验任务。14GPUh仅设计方向，未提交新GPU、未写中央账本；cap226、旧16.5责任、62个B36源和A32冻结保持。后续先验证时序回归，再准备修订源的双端完整CPU、真实存储与完整报价。

[总回执](../reports/cara_budget_R3_original_failure_and_network_recovery_r1_20261031.json) · [原终态](../reports/cara_budget_current_CPU_two_capture_r2_20261031.json) · [失败诊断](../reports/cara_budget_current_CPU_two_failed_diagnostic_r1_20261031.json) · [有效连接配置](../reports/cara_budget_transport_effective_config_r4_20261031.json)
