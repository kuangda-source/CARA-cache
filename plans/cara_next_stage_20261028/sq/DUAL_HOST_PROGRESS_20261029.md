# S/Q 双端准备接续

2026-10-29。Q1 R3 双端各 45 项 CPU 控制已接受；S 接续两卡同版本检查。新 S/Q GPU 提交、预算预约、真实账本写入仍为零。此文件记录本对话准备；主线 A32 的接受、结算和分析由主线负责。

## Q1

[双端 R3 回执](../../../reports/cara_sq_q1_control_dual_cpu_accepted_r3_20261029.json)绑定同一固定源码 `f3be7662175889c77e3719521fecb9c4d3be83af`，两端关键源码完全一致。各自 34 核心 + 11 包装、零跳过，包括五种真实 Linux 子进程控制；GPU、温度和账本使用声明夹具，CUDA 未初始化。

两卡原 stage 于 00:51:58 启动、00:52:47 退出 0，worker 墙钟 47.53 秒、CPU 含子进程 30.00 秒、峰值 RSS 0.568 GiB。四卡原 R3 不重派，早期 R1 超时与 R2 绑定拒绝保持。源包不随当前 HEAD 更新。

下一步在两卡安装本卡独立源包，准备 1 GiB 私有 SSD 输出、48 MiB 异盘日志和宿主原生命令探针，再完成双端 B1/权重实际身份与全部 SHA 核验。四卡仍缺 B1 bulk，GPU 前 CPU 传输必须按原 32 文件、20,795,567,276 B 去重核验；不重采。

卡仍为两旧 FIT × 六位置、111 pair/222 heads、零新增 deep/父轨迹/视频。原 C 与 Dense-hidden 逐值门、GPU 释放/中央结算后 CPU LOPO、双端原报价均保持。双端 CPU 接受不代表 CUDA 数值、真实资产、GPU 峰值或科学结果已通过。

## S

四卡已接受 owner R2（源码 `8779bb25`）和完整采集/流式存储 R2（源码 `591ac3bd`）。新[两卡入口](../../../scripts/cara_sq_s_owner_cpu_r1.py)及[存储入口](../../../scripts/cara_sq_s_storage_cpu_r2.py)只增加注册主机选择；CPU 边界仍为 2 核、8 GiB、1800 秒、cpuset 4/5、无网、GPU 隐藏。[本地入口检查](../../../reports/cara_sq_s_dual_host_entry_local_r1_20261029.json)确认三份原四卡接受结果不变并拒绝跨主机错绑；这不是两卡远程接受。

先在两卡运行同一 owner R2 八路径/十六边界，再运行完整存储 R2 十六路径；后者已包含完整采集拓扑，不另重派旧四卡或额外两卡采集 R1。每次以其原 stage/PID/container 收件。两个 flow 各为 108 CPU 夹具行、56 Dense teacher/52 C shadow、八 raw 与 24 个去重锚点，全部 OFF/ON guided、latent、占位视频一致，另有五项实际文件失败检查。

完成后形成双端绑定，继续真实 RAM/存储和整卡报价、真实生产 GPU 入口及生命周期准备。真实 S 卡仍最多 4 ON + 4 OFF + 2 warm，108 个实际标签与八个 F19 raw；CPU 夹具不生成 S mask、视频收益或 Q codec 选择。
