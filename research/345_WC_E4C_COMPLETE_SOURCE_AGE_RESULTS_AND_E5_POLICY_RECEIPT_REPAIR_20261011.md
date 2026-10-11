# E4c 来源年龄全范围结果与 E5 回执比较修复（2026-10-11）

**本轮最有价值的新发现是：P 来源的后续复用误差有明确的阶段和场景差异，现已获得全部 24 个真实同状态教师标签。** 原 GPU 全范围完成，独立只读 CPU 验收 44 文件、388 张量、162 直接比较，四条完整视频均解码 93 帧。来源为 6a5910c，原 supervisor 4075406／model 4075494 退出 0，唯一 CPU 后处理 4079033／4097774 退出 0；399 原源码字节保持。捕获器只读并独立从完整归约重建 12 对标量，不重跑 GPU／教师／张量读取器。

## 来源年龄结果

两个已曝光场景，各有早期与晚期一个实际 P 出生位置；从同一出生前状态干预 P 或 D，随后强制 C4，年龄 1／2／4 各自与该臂实际 latent 上的 dense teacher 比较。

| 场景与窗口 | P/D guided MSE，年龄 1 | 年龄 2 | 年龄 4 |
|---|---:|---:|---:|
| AV28 早期（出生 13） | 1.1435 | 1.2688 | 1.3852 |
| AV28 晚期（出生 25） | 1.4311 | 1.1666 | 1.1551 |
| Human 早期（出生 12） | 2.0294 | 2.8474 | **8.4598** |
| Human 晚期（出生 27） | 1.5922 | 1.2956 | 1.0542 |

12 对中，P 的当前 guided MSE 均高于相同出生／年龄的 D 臂；Human 早期随强制复用累积的变化最大，晚期比值则趋近 1。这里各自后继 latent 不再相同，标签是“各臂自身状态上的新增近似误差”，不是两臂轨迹间的单步差异。四个窗口不构成四个独立场景，也不能从局部误差推出视频质量或线上缓存寿命；强制 C4 未通过在线可行性选择。自然重复与未采集父路径的等价控制都保留并通过。

这支持优先执行 [335](335_WC_E4C_FIRST_FIXED_WINDOW_TENSOR_FINDING_AND_A_TARGET_ALIGNMENT_20261011.md) 已预登记的 **H-P-W1-WORKING-REFERENCE**：当前标量候选依然以真实 D 的 residual／probe 为参考，Flow warp 已使用 P 工作源；下一版只把标量读出参考换成 P 的 prewarp residual／probe，系数 β 仍仅由真实 D 估计，P 仍付正误差底线，D／fallback／RA 控制器不变。先做同状态、同动作的低成本区分，保留所有年龄与负结果，不直接放宽 C 阈值或把 P 当真值。尚未实现或提交这张新 GPU 卡。

## E5 实际 CPU 失败的性质与修复

R5 原 1185a47／4095672、4095678 已退出 1，1087.504412 秒，429 载荷保持；写出 flow OFF 的固定／current-birth 两族共 12 完整路径，flow ON 未开始，完整 24 路径未验收。原回执、log、Meta 和部分路径引用已捕获保留。

只读原写出张量诊断显示：这 12 路径六对的全部 36 guided 输出与 final latent **逐元素相等**，动作、求解器返回、条件、RNG 也一致。固定族 W1／β=1 原生 head 各 100→82；current-birth 各 128→94；OFF 均 72→72。它们仍是 Toy 权重、attention／prepare／unpatchify／decode／writer 下的 CPU 证据，不能换算真实速度。

实际失败位于逐步 `source_policy` 回执比较：两个单独构建的控制器的 `decision.owner=id(self)` 本应不同，却被直接要求相等。36 步内各自 owner 稳定；除这个 opaque identity 外，三个 A 模式的全部 policy 字段相等。**这是验收器的跨对象比较错误，没有观察到输出张量不等价。**

R6 保留原 R4 数值／head guard／sampler／controller 字节，只修新 fixture 的比较；各自完整路径先检查 owner 为正整数、全程稳定，并确认 decision 对应实际 step／action，随后只去掉该内存地址比较其余全部字段。新增四拒绝：foreign owner、gain 改变、floor 改变、缺 owner，全部 CPU 通过。旧 R1–R5 失败保持，R4 Meta 原 426 源码和 result hash 精确复用；全 24／444／888／96、两 flow、两族、三个 A 模式范围保持。新 434 来源 CPU 待执行；旧阶段不改、不补写成功。

## 下一步与费用

E5 完整 CPU 独立通过后，拟做两个曝光场景×三个 A 模式×新旧×两次顺序互换，共 24 条真实完整路径、四次独立加载，以真实原生 head、视频与同计时边界确认。已具体登记 whole-card 成本提案 `manifests/wc_e5_native_wrapped_head_complete24_cost_proposal_r1_20261011.json`，从 E1 八条实际原父路径、加载和外部费用预测，另加明确未实测的每 CFG 1 秒新 guard 余量及整卡 30% 余量，约 **5.126846 GPUh**。这不是已测速度、GPU ready 或最终 E5 科学 frontier，需完整 CPU 与实际执行接线通过后才选中；不替代 E2、E3 的完整设计。

原 E4c 全费用 **1.594927306 GPUh**（5741.738302 秒，包括加载、记录、复制与结束）。累计 **41.908688946／77.895246590 GPUh**，新增 48 窗口已用 12.013442356、剩 **35.986557644 GPUh**，78 次提交、无在途预留；CPU 不写远端账本。本轮新 GPU 0。完整预测 ≤8 可自主、严格 >8 具体整卡确认；E2 9.869732459／E3 12.377456422 原批准问题待，不拆卡、不重问，无训练／人工评审，目标 active。

证据：[完整来源年龄捕获](../reports/wc_e4c_terminal_20261011_capture.json)；[E5 原失败](../reports/wc_e5_complete_sampling_cpu_r5_terminal_20261011_capture.json)；[回执四拒绝](../reports/wc_e5_policy_receipt_comparison_faults_cpu_20261011.json)。
