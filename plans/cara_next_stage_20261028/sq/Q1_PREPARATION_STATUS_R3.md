# S/Q 下一步与原 C 数值门

2026-10-28。当前顺序为：**原 C 数值一致性 → Q1 同字节输出比较；S 生产采集准备 → 完整 108 标签 → 同 19D 预算的调度比较；之后分别进入 S-END / Q-END，最后才组合。**

[完整 CPU 执行与数值诊断回执](../../../reports/cara_sq_readout_cut_dual_cpu_diagnostic_r2_20261028.json) · [首轮失败与配置修正](../../../reports/cara_sq_readout_cut_R1_failure_and_selected_config_fix_20261028.json) · [六项拒绝控制](../../../reports/cara_sq_readout_cut_acceptor_controls_r2_20261028.json)。

主线 P0/F19 由主线对话推进；本目录继续负责 S/Q。原始 α、强基线、226 GPUh cap 和 16.5 GPUh 既有责任保持，新增 GPU 提交、预约与 ledger 写入均为 0。

## 本轮原 C 核验

实现了固定源码的完整 FinalLayer、unpatchify、原 C/warp 和 RF 读出子图。只物化三块已核对的原 checkpoint head 权重；没有 deep forward、采样或新视频。head 的 FP32 参数为 6,815,744 B，这不是总运行内存或部署显存。

预先固定的控制只有旧 B1 的 **AV28 step22**：一个原 C pair，加一个已保存 Dense-hidden 的 head/RF pair，共 4 个 head call。原件 5 文件共 2,327,511,482 B，逐文件 SHA 与旧接受回执对应。任何输出不相等时，停止 codec 评分。

首轮使用了通用 `use_wan_fp32_strategy=False`、`conditional_frame_timestep=-1`，没有完整继承选定 2B 实验。这是配置绑定错误，原 stage、输出、失败和费用均保留。随后从固定实验继承链绑定 `True` 与 `0.1`，单独冻结 [R4 CPU 控制](Q1_READOUT_CONTROL_CPU_R4.json)，用新 R2 stage 复核，未修改上游或更改容差。

修正后的 A6000 主机 CPU 对照仍未与历史 GPU 输出逐值相等：C 两支 maxabs 为 0.578291 / 0.572473，Dense-hidden head 两支为 0.007473 / 0.007671。两轮这些误差相同；**配置修正没有消除 CPU 差异，差异原因尚未确定**。CUDA 隐藏时，原 head 内 CUDA autocast 由 PyTorch 正常禁用；这项 CPU 核验不能接受 CUDA 数值等价。

本地修正后 14 项相关检查通过；真实单状态的输入、CPU RNG 与 head 权重保持。codec pair、deep call、新状态、新视频均为 0。两轮复用同一个旧状态，不是两个独立样本，也不是 Q1 的完整 12 状态结果。Ada 没有 B1 raw，只做源码、fixture 和 head 构造/权重核对。

两端两轮 CPU 容器均已正常终止。实际进程 CPU 合计 0.058726 CPUh，分配 vCPUh 上界 0.327571；修正轮实际 CPU 为 0.029441 CPUh。R2 A6000 主机容器墙钟 97.68 s、峰值 RSS 5.816 GiB；Ada 为 181.82 s、0.588 GiB。全部使用 2 核/8 GiB、禁网、GPU 隐藏及只读原件；本地编辑、SSH/staging 和 Git CPU 未完整计量。这些墙钟/RSS 是离线准备资源，不是 GPU 速度或部署显存。

## Q：接下来回答哪个问题

1. **先准备原硬件 CUDA 数值控制。** 使用修正后的选定实验配置，完整绑定原 head dtype/autocast、WC/warp 设置、模型加载器的 TF32 设置和资源。先核对原 C 与已保存 Dense-hidden head；保持逐值相等门，不通过就不评分 codec。
2. **通过后做 Q1。** 固定 Shared25-C、两个已曝光 FIT prompt、六个位置，共 12 状态 × 8 正式角色 = 96 个 C pair / 192 heads；不新增 deep、父轨迹或视频。同一真实 packet 字节下比较 I/M，保留 codec 增量与误差交叉项，完整 cohort 后才做留一 prompt 与最终共享 bit 方向选择。
3. **有实际输出证据后冻结 Q-END。** 做独立完整视频比较，并实测目标 tensor、总持久缓存、peak allocated/reserved 和时间。所有 native 窗口、solver、readout/calibrator/owner storage 及其别名都进入分母；CPU packet 比和小 head 权重不能替代部署内存。

Q1 的 96 个 pair 仍不是整卡报价。正式范围外的原始数值控制、warm、重复、CPU 编码、传输、加载、SHA/I/O、释放、评分和失败余量须逐项冻结；当前没有可据此启动的完整 GPU 卡。

## S：可以同时推进的准备

生产采集器须支持 2 FIT × {Shared25-C, F19-C} × 27 目标位置，完整覆盖 108 个分支矩标签。现有 B1 只覆盖 12 个 Shared25 局部状态；不做插值或零填充。

- 父动作是 C 时，新增同状态 shadow D；最大 56 个额外 Dense pair。
- 父动作是 D 时，复用实际 teacher，以**本步 D 之前**的两真锚点计算 shadow C；最大 52 个 C pair，不能让当前 D 进入源。
- 验证 OFF/ON 全 36 步 guided、solver/RNG、final latent 和完整视频；shadow 不更新父状态，父动作偏离冻结掩码时失败退出。
- 最大 4 ON + 4 OFF + 2 warm = 10 条父路径，费用去重一次。只新增 F19 的 8 个指定 raw 状态；它们不冒充 Shared25 的 Q 资产。
- 补齐标签后，才在共同生产语法（max-age28、D24 额外保护、170 个结构候选）下选 CFG/DIAG/BR 掩码，按完整 actions/α/执行身份去重。不同合法掩码出现后再准备 S-END，保留强 F19-A1 对照。

## 闭环顺序

S-END 和 Q-END 各自有晋级条件，互不要求对方先成功。分别通过后，再做布局 × codec 的 2×2 组合，报告净前沿与交互；不要求超加性。新卡逐项绑定 Fidelity-v2，旧协议和历史失败保持。

后续获准长程运行按唯一 launch 的实际开始时间安排一次半程和一次终态验收。半程只看运行身份、进度和资源健康，不用部分科学结果调参；终态完整收取退出、释放、原件和准确费用后，再做分析。
