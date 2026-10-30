# S 完整 Linux CPU 入口 R6

[本地准备回执](../../../reports/cara_sq_s_native_entry_preparation_local_r6_20261030.json)已记录8项审计控制及20条默认小张量路径通过。真实 Linux 容器尚未运行，不能据此填写生产 CPU 接受或申请 GPU 准入。原38个生产关键文件、真实资源合同、科学范围和S整卡报价均未改动。

本卡沿用已接受的 CPU 启动边界：2 CPU（4,5）、8GiB、无swap、无网络、GPU隐藏、1800秒、单文件64MiB、原stage禁止覆盖。继承原base登记的全部文件，再覆盖139个明确文件；19个额外runtime源码逐字核对。启动前继续拒绝任何正在运行的Docker分配，不放宽同机准入规则。

真实 Linux 执行包括123项控制、完整上游 inference/WC/RF 导入、原 Cosmos 参数解析和现有 checkpoint 缓存定位，以及两个flow的完整十角色矩阵。原HF查找强制local_files_only，禁止下载、socket出站、权重反序列化和CUDA初始化；只允许重读本次生成的微型张量。checkpoint缓存须为原4,118,575,006字节文件的元数据，59字节合成哨兵不能通过。该卡不重做模型文件的完整内容哈希，GPU前仍须接受原资产合同。

另有五个S监督进程场景：两个flow成功、缺少一行、子进程失败、90°C停止。它们消费前述真实CPU矩阵的字节，实际执行Linux子进程、PID/start_ticks、继承锁、context握手、清理和禁止重派。GPU观察、温度、存储和子进程的模型执行是显式CPU替身；子进程只发布CPU产物。监督时间仍为不可计费诊断，不能替代真实host guardian账单。

原容器和CLI确实退出后，独立审计器核对来源、完整分母、资源隔离和全部Linux场景，才会生成 `full_S_entry_CPU_accepted`。接受的仍是CPU入口；真实模型、GPU释放、中央费用、科学效果及整卡批准各自保留原边界。

新CPU控制器的两卡路线使用现有 `gkd_minchen` FRP别名，关闭本次SSH的附带转发，要求已有主机密钥；不改SSH配置、不启动FRP。四卡仍用原 `four_card` 路线。两卡Docker组执行仅从既有0600凭据文件读取到stdin，隔离worktree不复制凭据。

先 `recover` 原R6 stage，再以已发布的精确提交 `launch` 一次；`capture` 只恢复同一启动句柄，未知状态不重派。尚无实际CPU启动时间，因此本轮不创建半程/终态检查；启动后按原句柄和实际时间安排。资源轮询和Q1旧heartbeat保持停止，S优先安排不变。

源码 `f72f5a82` 已发布。一次句柄恢复中，两卡33620拒绝连接，四卡22617在SSH握手时重置。随后仅选择原配置中的两卡visitor，经stdin交给独立FRP进程；原配置与凭据文件未复制或修改。该进程连接中继KCP超时、退出1，未重试，也未触碰其他进程。实际stage状态仍未知，尚未派发CPU/GPU卡；需可用SSH入口后继续。见[连接回执](../../../reports/cara_sq_s_native_entry_connection_block_r6_20261030.json)。
