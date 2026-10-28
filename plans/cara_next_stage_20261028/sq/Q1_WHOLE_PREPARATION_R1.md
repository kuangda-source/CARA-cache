# Q1 完整流程、整卡报价与 S 来源接口

2026-10-28。**Q1 流程/后端配置的双端 CPU 夹具已接受；真实 CUDA 原 C 数值门和整卡执行尚未接受，GPU_ready=false。** [原流程回执](../../../reports/cara_sq_q1_whole_dual_cpu_accepted_r1_20261028.json)保留；后续[执行/财务生命周期的双端 CPU 控制](Q1_EXECUTION_PREPARATION_R1.md)已各34项通过，仅为夹具与临时账本接受，实际 GPU 启动/结算未发生。此前 [R3 单状态 CPU 数值诊断](Q1_PREPARATION_STATUS_R3.md) 的失败仍保持，本轮没有重复真实 B1 加权重放。

## 完整分母

固定 Shared25-C、两个已曝光 FIT、六位置，共 12 状态，正式比较仍为 96 个 C pair / 192 heads。

| 工作 | pair 数 | head 调用数 |
|---|---:|---:|
| 八正式角色 × 12 状态 | 96 | 192 |
| AV28 step22 原 C 预热 | 2 | 4 |
| 首状态额外原 C 预检 | 1 | 2 |
| 保存的 Dense-hidden head/RF 控制 | 12 | 24 |
| 整卡合计 | 111 | 222 |

没有新增 deep、父轨迹、视频或 timing-only 重复。首次预检不通过即停止后续 codec；后续任一原 C 或 Dense-hidden head 控制失败也停止，保留原分母和费用，不用部分状态选择方向。GPU 持有期间只收集记录；完整释放、结算和终态接受后才做 LOPO 与最终 bit 方向选择。[范围](Q1_WHOLE_SCOPE_R1.json)。

对照函数已适配保存于 CPU 的参考输出和设备上的输出；Dense-hidden 按实际 head 设备传送。原 C/warp、完整 FinalLayer、unpatchify 与 RF 源体保持；额外保护覆盖异常后的模型 buffer、solver 与所有 RNG 恢复。后端按固定模型加载器绑定 TF32，以及所选实验继承的 WAN FP32 head/条件帧配置，离开作用域后恢复。参数绑定没有放宽原数值相等门。

## CPU 接受的范围

两端各 20 项相关检查通过，并额外运行完整 12 状态 / 222 heads 的小张量入口，明确使用声明的 fixture 权重。七项伪造证据控制均被拒绝，包括把 CPU 结果升级为 CUDA 数值通过、GPU runner 已接受或在 GPU 收集中选择方向。

| 主机 | worker 墙钟 | 进程 CPU 秒 | 峰值 RSS |
|---|---:|---:|---:|
| A6000 主机 | 37.04 s | 18.52 s | 0.575 GiB |
| Ada 主机 | 58.07 s | 29.92 s | 0.569 GiB |

两个容器正常退出；实际进程 CPU 合计 0.013455 CPUh，分配 vCPUh 上界 0.125655。均为 2 核/8 GiB、禁网、GPU 隐藏、原件只读。没有新真实状态或模型权重执行，没有重复哈希 20.8 GB B1 来充当新的数值证据。本地 R1 曾把 macOS 的 RSS 原始 bytes 标为 KiB，原回执保留且不用于资源接受；后续本地 R2/R3 已显式归一单位。SSH、staging、Git 与本地编辑 CPU 未完整计量。

## 整卡报价草案

| 主机 | 工程预测 | 建议 GPU 硬限 | 数据条件 |
|---|---:|---:|---|
| A6000 | 54.33 分钟 / 0.90556 GPUh | 75 分钟 / 1.25 GPUh | 已有原 B1，启动前重新核验 |
| Ada | 109.28 分钟 / 1.82139 GPUh | 120 分钟 / 2 GPUh | 当前 B1 目录/manifest 缺失，先完成核验传输 |

[A6000 完整报价](Q1_WHOLE_QUOTE_TWO_CARD_R1.json) · [Ada 完整报价](Q1_WHOLE_QUOTE_FOUR_CARD_R1.json) · [只读 Ada 资源观察](../../../reports/cara_sq_q1_four_card_B1_availability_readonly_20261028.json)。

报价包含加载/上下文、原件 SHA/I/O、144 次窗口内 pair 编解码、FP32 M 回转、CPU/GPU 传输、111 个读出 pair、输入/RNG/buffer 审计、输出、释放和 25% 失败余量；CPU 编码时 GPU 仍被持有的时间没有从 GPUh 中扣掉。释放后 CPU 选择/接受另留最多 300 s、2 核。Ada 如需传输，单独保留 32 文件/20,795,567,276 B 的 GPU 前 CPU 传输范围，不经本地，不混入 GPU 执行授权。

**这些不是实测 GPU 单价或速度。** 打包/I/O 项有历史 CPU 依据；每 pair 4 s、Ada codec 倍数等是显式未实测规划余量，无法保证不超时。硬限到时停止原任务，不自动重试。最新只读中央账本为 cap226、已用175.805860、保留16.5、可用33.694140 GPUh；[快照](../../../reports/cara_sq_q1_budget_readonly_20261028.json) 不是新的准入或预约。本轮所有 GPU 提交、预约、ledger 写入均为 0。

## S 的同步进展

[pre-D 来源接口](../../../src/wcomr/sq_s_sources_r1.py) 只允许在当前 pair 执行前，按固定父掩码核对 readout/context、真实过去 D 步和 native p/r 窗口。它保留已克隆的旧真锚点对象；即使父策略随后追加当前 D，shadow C 的来源仍是此前两点。元数据保留 native 三槽信息，不把消费的两点视图当作全部持久缓存。

[五项本地 CPU 检查](../../../reports/cara_sq_S_pre_D_source_local_cpu_r1_20261028.json) 通过，覆盖当前 D 不得进入源、错误时点/父策略/条件/物理窗口拒绝和来源变异拒绝。与 Q1 合计 25 项本地相关检查通过。该接口还不是 108 标签完整采集器：生产 owner hook、shadow 事务、完整 OFF/ON、八 F19 raw 状态的流式存储及完整采集报价仍待完成；没有生成 S 掩码或新标签。

## 下一项验收

1. 完成 GPU runner、独占监管、中央单 envelope 与释放/结算的整体验证，连同本完整报价形成可审查的新卡；当前 CPU 回执明确没有接受这部分。
2. 新卡按原规则获准并通过 fresh 准入后，先执行原 C/Dense-hidden 数值门；相等才继续正式 96 pair，不相等则收取原失败与准确费用。
3. 将 S pre-D 来源接口接入生产父轨迹采集，验证完整 OFF/ON 和数据/内存边界；保持 108 标签、56 Dense shadow、52 C shadow 与最多 10 父路径的既定设计。

长程检查只在实际唯一 launch 后创建：按实际开始时间加预测一半安排半程，按预测加释放后 CPU 余量安排终态；ETA 变化更新已有检查，不重复提交，也不从半程科学分数调参。当前没有新 GPU launch，故没有创建虚假的运行检查。
