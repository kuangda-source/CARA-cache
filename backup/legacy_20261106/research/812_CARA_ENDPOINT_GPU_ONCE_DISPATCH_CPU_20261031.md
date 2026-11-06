# 812 — 端点GPU一次派发CPU组件接受

端点GPU一次派发与容器入口已通过两卡CPU组件验证：16项派发控制、8项容器/worker控制及1项真实Linux子进程控制，共25项通过；11项独立终态接受检查通过。启动回执曾因SSH超时未知，随后恢复原容器的退出0终态，没有重复提交。真实子进程验证了凭据管道、原guardian发布、分配前失败记账和禁止重派；未使用GPU、未访问中央账本。

## 实际边界与证据

源码`b46e03e369d67acb59675305bc90cd2d88fe0ad0`，原stage为`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-GPU-dispatch-CPU-a6000-r1-20261031`，注册SHA为`158e4e1770b196c2defca40c1da383676355a6245a3b492052315983b23c1c75`。外层真实Docker在22:48:17开始、22:48:21退出0，无OOM，工作3.080437秒；CPU26、1核、4GiB、无额外swap、network none、只读根文件系统、无GPU设备，上限180秒加30秒退出余量。

端点派发复用未修改的中央账本核验、GPU/主机资源准入和原句柄恢复函数；绑定端点自己的32/25范围、冻结SHA、runner、容器命令和guardian入口。意图在派生子进程前独占写入，任何已存在意图均走原句柄恢复；凭据只经私有stdin传递，不写入记录。容器保持2核/40GiB无额外swap、单张指定GPU、network none、只读源码、仅原runner可暴露CUDA；测试还验证错误范围、四卡、资源变化和死/未知guardian被拒绝。

真实Linux测试启动原生产入口子进程PID2601459/start ticks675300412，通过临时sitecustomize注入明确CPU夹具。真实Popen、私有管道、身份发布和guardian日志/终态账单写入均执行；在任何GPU/Docker/模式分配前模拟凭据丢失，子进程按预期退出1。原失败账单和独立journal一致，墙钟区间完整，恢复时没有第二个子进程。内部GPU、容器与资源准入检查仍为模拟元数据，临时CPU墙钟账单不是实际GPU费用。

启动SSH回执超时后，只读取同一个原stage，恢复到已完成的原容器。原prepare失败回执和成功capture均保留；容器只启动一次，没有将超时当成重派依据。

## 仍待整卡组合

这次接受的是一次派发、容器命令和真实guardian子进程边界，`whole32_CPU_accepted=false`保持。实际CUDA上下文、真实Cosmos加载和私有存储准入未运行；还需整卡入口与采集链的CPU组合、端点复用资产的完整准入包、24位置汇总/图表。实际预算mask继续等待原112/51完整验收及一次冻结；之后核对所选策略CPU、最终源、完整报价和新端点/原中央交易授权。

原14GPUh卡、23:16半程、次日06:01终验、06:45:04硬截止、cap226和旧16.5责任保持。本轮未读取该GPU部分结果或重新查询其运行。A32/B36/原S冻结和科学结果表保持。

[CPU接受](../reports/cara_s_endpoint_gpu_dispatch_CPU_accepted_r1_20261031.json) · [完整原终态](../reports/cara_s_endpoint_gpu_dispatch_CPU_capture_r1_20261031.json) · [本地及独立接受检查](../reports/cara_s_endpoint_gpu_dispatch_acceptance_checks_r1_20261031.json) · [交接](../plans/cara_next_stage_20261028/mainline/r2/S_ENDPOINT_GPU_DISPATCH_CPU_HANDOFF_20261031.md)
