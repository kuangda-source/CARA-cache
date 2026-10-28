# S 固定父轨迹采集准备

2026-10-29。四卡已接受 [S owner R2 CPU 组件](../../../reports/cara_sq_s_owner_four_card_cpu_accepted_r2_20261029.json)：两父策略、flow 开/关、OFF/ON 共八路径、十六边界，原失败保持。以下是新采集接口的 CPU 准备，尚无实际 S 标签、掩码或 GPU 授权。

## 本轮接通的接口

[采集事务](../../../src/wcomr/sq_s_collection_r1.py)逐步绑定生产 PolicyOwner。它只增加声明的 hidden 观察点，并检查其余编译 proof 保持；父动作和读出不变。

- 目标为每父轨迹 8..35 去掉 24 的 27 位置。每位置先保留两个严格过去的真实 D 锚点；当前 D 不可成为自己的 C shadow 来源。
- 实际 C 位置支付一个独立 Dense pair，恢复 pre-pair 物理状态、使用同一输入/条件，并核对两支 original/probe 相等。实际 D 位置复用其原输出，只支付一个来自 pre-D 窗口的 C readout pair。
- 两输入、两父轨迹合计 108 行，56 额外 Dense pair、52 C shadow pair。BR/DIAG/CFG 共用 FP64 分支矩、teacher 能量归一化及从实际固定 CFG 算术核出的 8/-7；接口不选择计划。
- 每个 shadow 后恢复物理模型/cache/solver/RNG，检查 owner 历史、校准器、输入/条件、旧源和权重版本。owner 被写脏时只恢复清理并拒绝，不接受该行。
- raw 仅通过数据回调交付 F19 的 9/22/33/35，两输入共八状态。包含旧 p/r 锚点、当前 prefix/embedding/adaln、实际 teacher/hidden、pair 输入/条件的 CPU 数据；未实现本卡流式持久化或 anchor 去重，不把回调当成保存完成。没有增加 Dense-hidden head 重放；其 P1 标志明确为 false。

## 新 CPU 验证范围

[冻结范围](S_COLLECTION_CPU_R1.json)与[完整检查](../../../tests/check_sq_s_collection_cpu_r1.py)使用固定的小权重、conditioner、decoder、writer stand-ins，运行 pinned WC/RF/UniPC 和生产 owner。两个 flow 设置分别做两个 CPU 输入 × 两父 × OFF/ON，共 16 完整路径。每个设置核对 108 行、56/52 分母、八 raw 回调，以及全部 36 guided、final latent、占位视频字节的 OFF/ON 相等。

CPU 容器保持 2 核、8 GiB、1800 秒、64 MiB 单文件上限、无网、原件只读、GPU 隐藏。先恢复原阶段，再验证主机 CPU 资源；当前仅准备四卡阶段，两卡保留主线 A32。该范围不读取 Cosmos 权重，不从 CPU stand-in 矩产生实际 S 候选。

当前仅源码/边界编译通过，完整新拓扑尚未运行或接受。其[单次阶段控制](../../../scripts/cara_sq_s_collection_cpu_r1.py)要求先接受同主机 owner 组件并核对组件源码不变。原 owner R1/R2、Q1 R3 均不重派。

## 之后的顺序

完整 CPU 拓扑 → raw 流式去重写入与失败控制 → 两主机受影响路径验证/资源与完整报价 → 单独申请 A-SQ-FAST GPU 卡。该卡仍最多 4 ON + 4 OFF + 2 warm，范围在去重后冻结；相容原件优先复用。S-END 以不同合法 mask 和自身端点比较为晋级条件，Q-END 按独立 Q1 证据推进。

Q1 仍固定旧 Shared25-C 的 111 pair/222 heads；不因本 S 接口增加其父轨迹、raw、heads 或预算。两条线尚无新 GPU 执行、预算预约或 ledger 写入。
