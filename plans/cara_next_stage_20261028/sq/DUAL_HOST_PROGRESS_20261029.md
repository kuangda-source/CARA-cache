# S/Q 双端准备接续

2026-10-29。Q1 R3 双端各 45 项 CPU 控制、S 双端状态组件与完整流式存储 CPU 组合均已接受。新 S/Q GPU 提交、预算预约、真实账本写入仍为零。此文件记录本对话准备；主线 A32 的接受、结算和分析由主线负责。

## Q1

[双端 R3 回执](../../../reports/cara_sq_q1_control_dual_cpu_accepted_r3_20261029.json)绑定同一固定源码 `f3be7662175889c77e3719521fecb9c4d3be83af`，两端关键源码完全一致。各自 34 核心 + 11 包装、零跳过，包括五种真实 Linux 子进程控制；GPU、温度和账本使用声明夹具，CUDA 未初始化。

两卡原 stage 于 00:51:58 启动、00:52:47 退出 0，worker 墙钟 47.53 秒、CPU 含子进程 30.00 秒、峰值 RSS 0.568 GiB。四卡原 R3 不重派，早期 R1 超时与 R2 绑定拒绝保持。源包不随当前 HEAD 更新。

两卡的[独立源包](../../../reports/cara_sq_q1_two_card_source_prepared_r1_20261029.json)、[1 GiB 私有 SSD 输出/48 MiB 异盘日志](../../../reports/cara_sq_q1_two_card_storage_prepared_r1_20261029.json)和[宿主命令探针](../../../reports/cara_sq_q1_two_card_native_probe_r1_20261029.json)已完成，与四卡既有准备形成双端绑定。探针未执行 Docker/GPU 命令、未导入 Torch 或改变设备模式。下一项是双端 B1/权重实际身份和全部 SHA；四卡仍缺 B1 bulk。

GPU 前 CPU [原件直传](B1_PORT_CPU_PROFILE_R1.json)限定原 32 文件、20,795,567,276 B，不重采、不过本机。直传用已有 Mac 验证过的 SSH 主机密钥，账户密码仅走 stdin/内存；源端实际运行有 CPU/内存上限的 `sftp-server -R`。[本地五项检查](../../../reports/cara_sq_b1_port_local_cpu_r2_20261029.json)及[服务器只读服务探针](../../../reports/cara_sq_b1_readonly_native_probe_r2_20261029.json)通过，源 manifest 写句柄确实被拒绝。源/目标均用 CPU 4/5、2 GiB AS、nice10/ionice3、7200 秒墙钟上限，与 GPU 入口的 CPU 24/25 分开；先前 CPU24/25 探针原件保留。源/目标 SHA 检查、整组空间、单次句柄、损坏/符号链接/既存目标拒绝覆盖均由新 CPU 程序负责；真实 20.8 GB 传输和 Q1 原生资产核验仍待完成。

卡仍为两旧 FIT × 六位置、111 pair/222 heads、零新增 deep/父轨迹/视频。原 C 与 Dense-hidden 逐值门、GPU 释放/中央结算后 CPU LOPO、双端原报价均保持。双端 CPU 接受不代表 CUDA 数值、真实资产、GPU 峰值或科学结果已通过。

## S

两端已接受 owner R2（同一源码 `8779bb25`）和完整采集/流式存储 R2（同一源码 `591ac3bd`），见[双端组合回执](../../../reports/cara_sq_s_dual_cpu_accepted_r2_20261029.json)。[两卡入口](../../../scripts/cara_sq_s_owner_cpu_r1.py)及[存储入口](../../../scripts/cara_sq_s_storage_cpu_r2.py)只增加注册主机选择；CPU 边界仍为 2 核、8 GiB、1800 秒、cpuset 4/5、无网、GPU 隐藏。

两卡 owner 原阶段八路径/十六边界通过，worker CPU 46.92 秒、峰值 0.887 GiB；完整存储原阶段十六路径通过，worker CPU 139.18 秒、峰值 0.898 GiB。每个 flow 均为 108 CPU 夹具行、56 Dense teacher/52 C shadow、八 raw 与 24 个去重锚点，完整 OFF/ON guided、latent、占位视频一致，另有五项实际文件失败检查、每端 280 文件重载。两卡 R1 资源拒绝发生在 stage 创建前，恢复确认无原句柄后才首次启动，未重派任何已运行阶段。

两卡原 CPU 边界比四卡多一个登记的 B1 原件只读挂载，初次收件的精确挂载清单漏列了它；[原拒绝诊断](../../../reports/cara_sq_s_two_card_CPU_mount_diagnostic_r1_20261029.json)保持。验收器现逐主机绑定所有只读目标与来源，仅本 stage 可写，额外挂载或把 B1 改为可写均拒绝。原容器、源码、数值、四卡三份接受结果均未重跑/改变。

继续真实 RAM/存储和整卡报价、真实生产 GPU 入口及生命周期准备。真实 S 卡仍最多 4 ON + 4 OFF + 2 warm，108 个实际标签与八个 F19 raw；CPU 夹具不生成 S mask、视频收益或 Q codec 选择。
