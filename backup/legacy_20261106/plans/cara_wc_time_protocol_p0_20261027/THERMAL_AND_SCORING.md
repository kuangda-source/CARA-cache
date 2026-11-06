# 热环境、完整费用与评分执行边界

优先可准入四卡空闲GPU，否则两卡；仅一host一GPU执行同一卡，禁止双发。实际独占须设备隔离或支持的EXCLUSIVE_PROCESS与sole-runner上下文核验；项目锁本身不足。不得挪走他人BeamNG、修改忙卡模式。每阶段重新核验UUID、进程/锁/账本、磁盘、内存和源哈希。

同一阶段模型resident；记录首次load独立费用，方法独立warm。请求前后记录温度、SM/显存频率、功耗、利用率、显存、throttle flags；外部低频采样不在solver逐步同步，观测成本纳入报价。既有配置/功耗限制不擅改。出现他人context、驱动故障、显著节流时登记环境无效并停止，无自动删点重跑；额外热稳定等待实际持卡成本入账。两阶段分别记录，不跨阶段拼时间基线。

GPU释放并结算后才加载评分模型。A只运行4个Alex选择配对；B逐视频独立跑Alex、PIQ/VGG，及MUSIQ_SPAQ长边512、DINO subject、AMT_S motion三门；额外RAFT_THINGS dynamic degree仅描述活动度，防止静止获高一致性。28视频×4=112评分位置，三门仍84位置，不增造质量综合分。源模型继承已接受CAL66身份，实际资源另核对hash。

固定FP32评分：Alex输入[-1,1]、PIQ/VGG[0,1]，均全部93帧432×768，不隐式resize；MUSIQ全93帧长边512双线性无antialias；subject全93；motion偶数47帧插值到奇数46；dynamic每2帧取样47。每项采用原构造器/weights SHA、decode/frame-index receipt。同一编码原件RGB输入、按视频先平均，不将单帧当独立n。

复用现有模型CPU接受件仅证明未变组件；新卡decoder/矩阵/scorer总线仍需组合验证。B评分规划4CPU/12GiB/6小时=24 allocated vCPUh；A评分单独预留4CPU/12GiB/1小时=4 allocated vCPUh，总28为预注册上限提案，非实测。超限记录不完整，不能自动扩任务。单模型串行避免同时驻留峰值。

LPIPS网络资源也必须在未来准入绑定实际weights/version；完整新卡评分CPU墙钟、RSS、磁盘吞吐及实际耗时目前未知，PRICE_QUOTE明确留空，不以4卡/2卡GPU数量倍乘单GPU卡费用。当前实际质量模型执行为0。
