# S 完整 Linux CPU 入口 R6

[本地准备回执](../../../reports/cara_sq_s_native_entry_preparation_local_r6_20261030.json)已记录8项审计控制及20条默认小张量路径通过。真实 Linux 容器尚未运行，不能据此填写生产 CPU 接受或申请 GPU 准入。原38个生产关键文件、真实资源合同、科学范围和S整卡报价均未改动。

本卡沿用已接受的 CPU 启动边界：2 CPU（4,5）、8GiB、无swap、无网络、GPU隐藏、1800秒、单文件64MiB、原stage禁止覆盖。继承原base登记的全部文件，再覆盖139个明确文件；19个额外runtime源码逐字核对。启动前继续拒绝任何正在运行的Docker分配，不放宽同机准入规则。

真实 Linux 执行包括123项控制、完整上游 inference/WC/RF 导入、原 Cosmos 参数解析和现有 checkpoint 缓存定位，以及两个flow的完整十角色矩阵。原HF查找强制local_files_only，禁止下载、socket出站、权重反序列化和CUDA初始化；只允许重读本次生成的微型张量。checkpoint缓存须为原4,118,575,006字节文件的元数据，59字节合成哨兵不能通过。该卡不重做模型文件的完整内容哈希，GPU前仍须接受原资产合同。

另有五个S监督进程场景：两个flow成功、缺少一行、子进程失败、90°C停止。它们消费前述真实CPU矩阵的字节，实际执行Linux子进程、PID/start_ticks、继承锁、context握手、清理和禁止重派。GPU观察、温度、存储和子进程的模型执行是显式CPU替身；子进程只发布CPU产物。监督时间仍为不可计费诊断，不能替代真实host guardian账单。

原容器和CLI确实退出后，独立审计器核对来源、完整分母、资源隔离和全部Linux场景，才会生成 `full_S_entry_CPU_accepted`。接受的仍是CPU入口；真实模型、GPU释放、中央费用、科学效果及整卡批准各自保留原边界。

新CPU控制器的两卡路线使用现有 `gkd_minchen` FRP别名，关闭本次SSH的附带转发，要求已有主机密钥；不改SSH配置、不启动FRP。四卡仍用原 `four_card` 路线。两卡Docker组执行仅从既有0600凭据文件读取到stdin，隔离worktree不复制凭据。

先 `recover` 原R6 stage，再以已发布的精确提交 `launch` 一次；`capture` 只恢复同一启动句柄，未知状态不重派。尚无实际CPU启动时间，因此本轮不创建半程/终态检查；启动后按原句柄和实际时间安排。资源轮询和Q1旧heartbeat保持停止，S优先安排不变。

源码 `f72f5a82` 已发布。一次句柄恢复中，两卡33620拒绝连接，四卡22617在SSH握手时重置。随后仅选择原配置中的两卡visitor，经stdin交给独立FRP进程；原配置与凭据文件未复制或修改。该进程连接中继KCP超时、退出1，未重试，也未触碰其他进程。实际stage状态仍未知，尚未派发CPU/GPU卡；需可用SSH入口后继续。见[连接回执](../../../reports/cara_sq_s_native_entry_connection_block_r6_20261030.json)。

主线随后转来用户授权共享的Tailscale私有入口；两端已实际恢复登录，确认原R6 stage不存在。启动请求均超过原180秒观察窗口；再次恢复仍无stage，并确认原控制进程已退出、CPU控制锁空闲。该状态不计为CPU执行失败。传输层现将约1.7MB JSON压缩编码为约0.65MB，并把SSH操作观察窗口改为420秒；两种主机的本地原字节往返通过。原逐文件SHA、同stage/锁拒绝重派、CPU30分钟硬限和GPU权限保持。私有配置只被本次进程的SSH wrapper引用，未复制凭据或改全局配置。

两卡原R6容器已正常退出0并独立接受：123项控制、两个flow完整20条小张量路径和五个Linux监督场景通过，容器192.869秒、进程峰值1.372GiB。它在原预计450秒半程前完成；连接波动导致首次成功终态快照比实际结束晚约332秒，未按及时收件描述。原收件器缺少登记对象，已补取与原启动SHA一致的登记字节；此接收端修复未重跑CPU。收件时沿用原两卡Docker组执行边界。见[完整接受](../../../reports/cara_sq_s_native_entry_two_card_cpu_accepted_r6_20261030.json)与[检查时间记录](../../../reports/cara_sq_s_native_entry_two_card_acceptance_schedule_r6_20261030.json)。

四卡压缩请求遇到连接中断；随后确认原控制进程已退出、锁空闲、同R6 stage不存在，才能继续该CPU卡。两卡成功不替代四卡证据，也不授予S的GPU权限。GPU提交和真实S标签仍为0。

四卡随后沿同一R6句柄完成，06:45:32 UTC退出0，容器431.963秒；123项控制、两个flow共20条tiny路径及五个Linux监督场景均独立接受。首次成功收件在06:51:35 UTC，半程收件未获接受，保留迟收事实，不补写及时检查。见[四卡完整接受](../../../reports/cara_sq_s_native_entry_four_card_cpu_accepted_r6_20261030.json)与[原时间记录](../../../reports/cara_sq_s_native_entry_four_card_acceptance_schedule_r6_20261030.json)。两端原生CPU接受只证明接线与控制流程，真实S标签和GPU提交仍为0。

用户要求停止反复查看资源后，14:52北京时间只核查两卡一次：0号A6000的利用率0%、显存450MiB、43°C，两张卡均无计算进程、项目GPU租约未持有、无本项目运行容器。[该次观察](../../../reports/cara_sq_two_card_other_gpu_one_time_observation_r6_20261030.json)支持把另一张卡作为S候选，不建立硬独占，不替代实际派发时的fresh准入，也不恢复资源轮询。

后续CPU准备复用既有 `cara_fast_b36_dispatch_r2.assets_check/assets_unchanged` 对原20个模型和辅助文件逐字节校验。新worker只绑定原S源码stage并产生单次、不可覆盖的PID/摘要回执；2CPU（4、5）、2GiB地址空间、低优先级及1800秒硬限，无模型加载或GPU权限。原38个生产关键文件与两个原生CPU接受的源码不变。
