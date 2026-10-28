# Q1 执行与释放后验收：双端 CPU 控制接受

2026-10-28。新增 [双端验收回执](../../../reports/cara_sq_q1_execution_dual_cpu_accepted_r1_20261028.json)。源码 `a8ce13e8` 已发布；两个独立 CPU 容器均退出为 0。**接受的是执行/终态解析的 CPU 控制；真实 CUDA 原 C 数值门与 GPU 执行仍未接受，GPU_ready=false。** 原单状态 CPU 重放的数值失败保留，没有本轮真实 B1/权重重放或 codec 评分。

## 本轮实际完成

- Q1 专属 runner、supervisor 和 mode guardian 已绑定固定范围、双端报价、原件身份和执行 profile。共享的独占、热保护、双缓冲日志与中央账本组件沿用，不修改主线入口。
- 两端各 34 项检查、零失败、零跳过。Linux 上实际创建子进程，核对 PID/start ticks、父进程和继承的锁 FD，验证成功、原数值门失败、runner 失败、90°C 热停和超时五种路径；GPU/温度查询使用声明的夹具，未创建 CUDA 上下文。
- 成功与失败均保留原测量费用，原始子进程退出、锁释放，既有句柄禁止重启。中央结算只用临时 CPU 账本，保留原 16.5 GPUh 未知责任，重复结算幂等；没有写真实中央账本。
- 独立终态解析核对原始字节、完整分母、来源、独占监测、释放与结算。完整接受后才允许 CPU LOPO；原数值失败接受为诊断终态，不选 bit 方向。另有七项伪造/缺项证据被拒绝。
- B1 reader 先核对全部 32 文件 SHA，再加载；加载前复核 inode、字节和修改时间，拒绝替换/符号链接及小张量冒充真实几何。

| CPU 主机 | 容器墙钟 | worker 墙钟 | 进程 CPU，含子进程 | 峰值 RSS |
|---|---:|---:|---:|---:|
| 两卡 A6000 | 41.10 s | 35.60 s | 22.72 s | 0.574 GiB |
| 四卡 Ada | 48.05 s | 37.79 s | 24.01 s | 0.567 GiB |

两端均为 GPU 隐藏、禁网、2 核/8 GiB。夹具测试结束时 Torch 使用 1 线程，位于 2 核资源上限内。实际进程 CPU 合计 0.012980 CPUh，分配 vCPUh 上界 0.049529；SSH、staging、Git 与本地编辑成本未完整计量。

原始回执：[A6000 启动](../../../reports/cara_sq_q1_execution_two_card_cpu_launch_r1_20261028.json)、[终态](../../../reports/cara_sq_q1_execution_two_card_cpu_capture_r1_20261028.json)；[Ada 启动](../../../reports/cara_sq_q1_execution_four_card_cpu_launch_r1_20261028.json)、[终态](../../../reports/cara_sq_q1_execution_four_card_cpu_terminal_r1_20261028.json)。Ada 首次捕获时容器尚在退出，随后只重查同一句柄；未重派。

## 固定的下一张 Q1 范围

[原完整范围](Q1_WHOLE_SCOPE_R1.json)与[整卡报价](Q1_WHOLE_PREPARATION_R1.md)保持：固定 Shared25-C，两旧 FIT × 六位置；96 正式 C pair，加上预热/原 C 预检/Dense-hidden 控制，共 **111 pair / 222 heads**。新增 deep、父轨迹和视频均为 0。原 C 和 Dense-hidden 均须与 B1 逐值相等，失败即停止，不改精度或容差。

建议硬限保持 A6000 1.25 GPUh、Ada 2 GPUh；预测约 54.33/109.28 分钟仍是含未实测 GPU 余量的工程报价。GPU profile 为 2 核/16 GiB、私有输入逻辑副本上限 8 GiB、CUDA allocator fraction 0.5、独立 1 GiB 输出及 48 MiB 跨盘控制日志；本轮 CPU 容器没有证明真实大张量的 GPU 峰值。Ada 的 B1 传输尚未完成，不能据 CPU 控制接受判为可启动。

## 距实际执行还差什么

1. 将唯一 staging/dispatch/recovery、只读运行/终态捕获和释放后 CPU CLI 接到本轮已验组件，验证受影响入口；现有历史 CPU stage 保持不可变。
2. 核对新卡授权，并在提交前重新检查双端已有 intent、实际源/权重/B1、独占、显存、热环境、内存、磁盘与中央整卡余额。新卡只有一个中央 envelope，不能双端重复提交。
3. 实际开始后，按原开始时间与完整预测创建半程和终态检查；半程只看运行身份、进度与资源。当前没有 GPU launch，因此没有创建运行检查。
4. GPU 原控制通过后完成正式收集；全部进程/模式释放、中央结算和独立终态接受后，再在 CPU 上生成 LOPO/共享方向报告。此卡本身不证明视频收益、部署缓存峰值或速度。

本轮 GPU 提交、预约、GPUh 和真实 ledger 写入均为 0；cap226 和原未知责任保持。S 的 [pre-D 来源接口](../../../src/wcomr/sq_s_sources_r1.py)仍只是已验组件，108 标签生产采集器、完整 OFF/ON 与八 F19 raw 状态存储继续待完成；没有由本轮控制测试生成 S 掩码。
