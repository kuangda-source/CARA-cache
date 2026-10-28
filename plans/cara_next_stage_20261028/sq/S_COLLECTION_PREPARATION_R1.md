# S 固定父轨迹采集准备

2026-10-29。四卡已接受 [S owner R2 CPU 组件](../../../reports/cara_sq_s_owner_four_card_cpu_accepted_r2_20261029.json)、[R1 完整采集 CPU 拓扑](../../../reports/cara_sq_s_collection_four_card_cpu_accepted_r1_20261029.json)及 [R2 raw/流式存储 CPU 组合](../../../reports/cara_sq_s_storage_four_card_cpu_accepted_r2_20261029.json)。R1 源码 `6ec052dbcf8343800ba1206d704484f98593e045`，R2 源码 `591ac3bd2b8231de8a44c933bf26560acc7921e0`，各自 16 完整路径；原失败保持。两卡同版本检查、真实数据/资源与整卡报价未齐，尚无实际 S 标签、掩码或新 GPU 授权。

## 本轮接通的接口

[采集事务](../../../src/wcomr/sq_s_collection_r1.py)逐步绑定生产 PolicyOwner。它只增加声明的 hidden 观察点，并检查其余编译 proof 保持；父动作和读出不变。

- 目标为每父轨迹 8..35 去掉 24 的 27 位置。每位置先保留两个严格过去的真实 D 锚点；当前 D 不可成为自己的 C shadow 来源。
- 实际 C 位置支付一个独立 Dense pair，恢复 pre-pair 物理状态、使用同一输入/条件，并核对两支 original/probe 相等。实际 D 位置复用其原输出，只支付一个来自 pre-D 窗口的 C readout pair。
- 两输入、两父轨迹合计 108 行，56 额外 Dense pair、52 C shadow pair。BR/DIAG/CFG 共用 FP64 分支矩、teacher 能量归一化及从实际固定 CFG 算术核出的 8/-7；接口不选择计划。
- 每个 shadow 后恢复物理模型/cache/solver/RNG，检查 owner 历史、校准器、输入/条件、旧源和权重版本。owner 被写脏时只恢复清理并拒绝，不接受该行。
- raw 只交付 F19 的 9/22/33/35，两输入共八状态。新增 R2 格式保留旧 p/r 锚点及 request/branch/xi，当前 prefix/embedding/adaln、实际 teacher/hidden、原 C 输出、pair 输入/条件和完整噪声坐标身份。原 C 输出直接复用父 C；没有增加 Dense-hidden head 重放，其 P1 标志明确为 false。teacher prefix 经相等检查后只在 current 保存一次。

## 新 CPU 验证范围

[冻结范围](S_COLLECTION_CPU_R1.json)与[完整检查](../../../tests/check_sq_s_collection_cpu_r1.py)使用固定的小权重、conditioner、decoder、writer stand-ins，运行 pinned WC/RF/UniPC 和生产 owner。两个 flow 设置分别做两个 CPU 输入 × 两父 × OFF/ON，共 16 完整路径。每个设置核对 108 行、56/52 分母、八 raw 回调，以及全部 36 guided、final latent、占位视频字节的 OFF/ON 相等。

CPU 容器保持 2 核、8 GiB、1800 秒、64 MiB 单文件上限、无网、原件只读、GPU 隐藏。先恢复原阶段，再验证主机 CPU 资源；当前仅准备四卡阶段，两卡保留主线 A32。该范围不读取 Cosmos 权重，不从 CPU stand-in 矩产生实际 S 候选。

R1 于 00:30:31 退出 0，源/运行时一致；worker 墙钟 312.07 秒、CPU 162.91 秒、峰值 RSS 0.875 GiB。两个 flow 各 108 行、56 Dense/52 C、八 raw 回调和四组完整 OFF/ON 均通过；[独立接受](../../../reports/cara_sq_s_collection_four_card_cpu_accepted_r1_20261029.json)拒绝运行中、缺父、缺 raw、当前 D 混源、少 Dense、CUDA 与存储越界宣称七类伪回执。原完整[启动](../../../reports/cara_sq_s_collection_four_card_cpu_launch_r1_20261029.json)和[终态](../../../reports/cara_sq_s_collection_four_card_cpu_terminal_r1_20261029.json)保持。它验证回调接口，不验证真实数据保存。

[流式存储组件](../../../src/wcomr/sq_s_storage_r1.py)实现独占写入、逐文件 SHA/字节、24 个旧真锚点去重、八 state 和 108 行终态分母；触发限额、混源、重复或同源不同字节即保留 partial 并终止，不支持续跑覆盖。本地五项实际文件检查和完整 R2 Linux 组合均通过，原 R1/R2 schema 的记录分别保持。[R2 冻结范围](S_COLLECTION_STORAGE_CPU_R2.json)是 16 CPU 路径，另含五项小文件失败检查；每个 flow 实际重载校验 140 文件，80 次 tiny tensor 读取加六次单元夹具读取均限制在自己的 CPU 输出或临时目录，Cosmos 权重不可读。

[R2 原启动](../../../reports/cara_sq_s_storage_four_card_cpu_launch_r2_20261029.json)于 00:41:15、[原终态](../../../reports/cara_sq_s_storage_four_card_cpu_capture_r2_20261029.json)于 00:43:49 退出 0，源/运行时一致。worker 墙钟 151.66 秒、CPU 135.21 秒、峰值 RSS 0.883 GiB；每个 flow 的 108 行、56/52 和八 raw/24 unique anchors 均完整，新增原 C 与实际噪声坐标身份在文件重载后保留。五项 Linux 存储单元检查零跳过，[独立接受](../../../reports/cara_sq_s_storage_four_card_cpu_accepted_r2_20261029.json)另拒绝十一类缺项/越界伪回执。

每个 flow 的小张量夹具实际保存约 2.29 MB，全部 280 个数据文件重载 SHA/字节一致；不把该数值外推为 F19 真实 raw 大小、部署缓存或 peak。[阶段控制](../../../scripts/cara_sq_s_storage_cpu_r2.py)核对过原 R1 终态/接受和 owner 组件源码。原 owner R1/R2、采集 R1、存储 R2、Q1 R3 均不重派。R2 tiny-file 的 16 MiB/flow、8 MiB/file 上限仅是 CPU 夹具资源，不能作为真实 raw GPU 卡的存储报价。

## 之后的顺序

两卡同版本受影响路径验证 → 两主机真实存储/RAM/资源与完整报价 → 单独申请 A-SQ-FAST GPU 卡。主线 A32 保持原状态，不在其运行中启动 20 GB B1 跨机读取或扩大本对话资源边界。该新 S 卡仍最多 4 ON + 4 OFF + 2 warm，范围在去重后冻结；相容原件优先复用。S-END 以不同合法 mask 和自身端点比较为晋级条件，Q-END 按独立 Q1 证据推进。

Q1 仍固定旧 Shared25-C 的 111 pair/222 heads；不因本 S 接口增加其父轨迹、raw、heads 或预算。两条线尚无新 GPU 执行、预算预约或 ledger 写入。
