# S/Q 双卡 CPU 准备交付

**当前入口：** [Q1 控制 R3 与 S 采集准备](Q1_CONTROL_STATUS_R3.md) · [双端后续准备](DUAL_HOST_PROGRESS_20261029.md) · [完整 Q1 新卡审阅](Q1_NEXT_CARD_REVIEW_R1.md)。Q1 R3 两端各 45 项 CPU、独立源包/私有盘/宿主探针均已完成；S 两端各八路径/十六边界状态组件与十六路径 raw/流式存储组合均已接受。B1 的 32 文件直传已完成、已知句柄释放；两端各 33 项真实资产 SHA/身份已独立接受。Q1 固定 111 pair/222 heads，GPU 新授权及 fresh 准入仍待完成，真实 CUDA 数值门和新 GPU 执行均未发生。下方保留前阶段回执与边界。

**最新进展：** [Q1执行与释放后验收的双端CPU控制](Q1_EXECUTION_PREPARATION_R1.md)已接受，两端各34项、零跳过，包含五种真实Linux子进程路径；GPU隐藏、仅临时账本。固定范围仍为111 pair/222 heads，[完整流程/整卡报价](Q1_WHOLE_PREPARATION_R1.md)保持。唯一GPU staging/capture/CPU后处理入口仍需接齐，真实CUDA原C数值门未过，GPU_ready=false。S pre-D来源接口另有5项本地检查，尚非完整采集器。[R3数值失败](Q1_PREPARATION_STATUS_R3.md)、[R2条件恢复/源码证据](Q1_PREPARATION_STATUS_R2.md)与生产profile的170结构候选保持。下文保留首轮R1的158候选和max-age6诊断记录，不能将两版本混读为同一冻结方法。

2026-10-28。**本轮接受的是旧资产审计、S 局部数学与 Q0 实际字节原型；真实模型 C 重放、调度收益、部署峰值与速度均未接受，GPU_READY=false。**

实现与服务器 source revision：`90768615417cb9858b83fb1d5916b82c7b7f2aef`。源模型、原 α、Shared25-C、226 GPUh cap、16.5 GPUh 保留责任与已停止分支保持。没有改 canonical、模板、科学结果表或主线入口。

## 可复用资产与缺口

| 资产 | 本轮复核能力 | 证据边界 / 缺口 |
|---|---|---|
| B1 原件 | 32 文件（12 state、20 anchor），20,795,567,276 B；manifest 与逐文件 SHA 全匹配 | 同两已曝光 FIT、单一 Shared25-C 父轨迹；不是新输入证据 |
| B1 状态 | 两支 current original/probe/embedding/adaln、真实两旧锚点、pair 输入/condition 字段、teacher 与 post-RF C 输出 | 全 pipeline checkpoint 只留 identity，不能恢复 solver/RNG 全状态或重新生成视频 |
| S 分支矩 | 12 个 C/U/K、BR/DIAG/CFG、共同 teacher 能量归一化；直接 FP64 恒等式最大差 7.66e-15 | 所需 108 标签仅有 12，缺 96；没有 F19 父轨迹。1624 guided 统计不可反推出 C/U/K |
| Q raw | 10 对独立真锚点，两支 r/p 均有真实 BF16 张量和来源；可重建 12 个 C 读出的后两锚点视图 | 两 prompt 各覆盖 6/11 个 Shared25 C 位置；不能把局部窗口冒充整个父轨迹或完整线上缓存 |
| 历史视频 / 时间 | 原件保留，可由主线按完整身份判定评分复用 | 不池化跨硬件时间，不把旧 generate 时间改名 T_DD；S-END 保留 F19-A1 强对照 |

原件位于 `/data20t/gaokuangda/worldcache_workspace/outputs/cara-ig-b1-r2-20261027/assets`，没有复制 bulk 到本机。原 manifest SHA：`5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`。

## S：局部可辨识与计划接口

同一归一化下，AV28 的局部 CFG/DIAG 排序仅在 step22/25 对调；Human199 的六位置排序相同。这只说明已曝光六位置上的目标差异，不能据此选择全时间掩码或宣称稳定增量。实际 FP32 guided 与 FP64 几何的最大 MSE 差为 9.69e-11，单独记录舍入，未混为位级相等。

共有语法产生 158 个 19D 单交换结构候选，保留 1..7/24/36 与 max-age=6。若要求每个 C 历史均由旧 B1 见证，支持完整候选数为 0。接口对任一缺失 parent/step 拒绝聚合，不补零或外插；**本轮没有 S-CFG/S-DIAG 掩码**。完整风险到齐后，三目标共用 prompt 权重 1/2、parent 权重 1/2、teacher 分支能量归一化与 g=1，按正增益和固定 remove/add 编号生成一次交换。Uniform19、时间先验及完整执行身份由主线绑定后做共同等价类去重。

[S 风险/候选接口](S_RISK_MASK_INTERFACE.json) · [实现](../../../src/wcomr/sq_risk_r1.py)

## Q0：实际打包与读出状态

实际 r shape=`[1,24,27,48,2048]`，dtype=BF16；单支 127,401,984 B、每对 254,803,968 B。十对锚点 × 六 codec = **60 个真实 packet 编码、解码与 raw 校核**。尾组、符号/舍入/零组、FP32 scale、tensor/pair header、padding/alignment 均实际存储计数。I/M 在 FP32 变换，回转再 cast 原 BF16；独立记录的 transform-roundtrip 最大 MSE 为 1.03e-19。

| 码率 / 角色 | 每对实际 packet 字节 | 原 r / packet 比例 |
|---|---:|---:|
| R16：I/M (8,8) | 131,383,488 | 1.93939× |
| R12：I/M (4,8)/(8,4) | 99,532,992 | 2.56000× |

这是目标 r 张量的格式/字节比，不是总缓存或显存压缩比。两个已消费锚点的 packet 加窗口 alias descriptor 为 R16 262,767,040 B、R12 199,066,048 B；未压 p、solver 和其他缓存另计。真实源码及已有 `RefreshLedger` 均明确窗口保留 3 项、滚动后两项；B1 未存滞留首项及完整运行时 alias/solver。因此总持久缓存与部署 peak allocated/reserved 均留空。

GPU 隐藏容器内的 8 项检查通过，包含固定 SHA 的真实 C/warp/RF 源路径、flow OFF/ON、全部 codec 与明确 toy head；这不是 Cosmos 权重重放。实际模型 C 读出、q_total/q_codec/交叉项、BR/CFG 留一 prompt 选方向仍待 Q1。原 raw 仅作离线 teacher，未选 codec、未把 codec 安装进生产入口。六十次编码/解码累计墙钟约 139.92/119.33 秒，仅是服务器 CPU 原型计时。

[codec 与 C 适配接口](../../../src/wcomr/sq_codec_r1.py) · [检查](../../../tests/test_sq_preparation_r1.py)

## 资源与下一步

唯一 CPU stage `cara-sq-cpu-r1-20261028`，容器 17:23:10 至 17:32:58（北京时间）正常退出，退出码 0、无 OOM、源/运行时 SHA 一致。无网、无 GPU、原件只读、2 核/8 GiB，实际容器墙钟 587.94 s；进程 CPU 459.80 s = **0.12772 CPUh**，分配 vCPUh 上界 0.32664，峰值 RSS **2.24783 GiB**；SHA 读取墙钟 191.39 s。1800 s 是软墙钟，连同终止余量的硬边界为 1810 s。本地编辑、SSH/Git CPU 未完整计量，不称准备免费。

新增 GPU 提交/GPUh/预算预约/ledger 写入均为 **0**。本轮只读中央余额为 cap226 / used175.80585977 / reserved16.5 / available33.69414023 GPUh，空闲快照不构成准入。

[双端 profile](HOST_PROFILES.json) 共用同一科学源码。双卡本轮 CPU 已接受；四卡未运行新的 S/Q CPU，且只读核对发现原 B1 raw 不在四卡。若选择四卡做 Q1-saved，须先纳入一次去重传输和受影响路径验证的费用，不能重采或冒称双端接受。

下一最小 **Q1-saved** 范围是复用这 12 状态、每状态 `{原C、M变换回转C、六codec C}` 共 96 正式读出 pair（192 heads），新 deep/父路径/视频均为 0；它仍消费 GPU。真实 condition 恢复、原精度读出控制、warm/重复/加载/传输/释放/评分与双端完整报价尚未绑定，**目前不提出不完整的 GPU 授权请求**。

S 的必要新卡仍是 **A-SQ-FAST**：108 标签、最多 56 额外 Dense teacher pair、52 次实际 D 位置上的 shadow C、最多 10 父路径。shadow C 必须读取 D 前缓存。只保存 F19 的 8 个 raw；不追加 Q25 raw。若后续需要 Q25 新字段，冻结前公开修订；本轮只前瞻提议采集轻量 WC/solver alias/存储元数据。共享费用只计一次，兼容旧件先去重；S-END/Q-END 分别待自身证据后冻结。

[下一最小卡及报价缺项](NEXT_MINIMUM_CARDS.json) · [CPU 边界与规格](CPU_PREPARATION_R1.md) · [独立接受回执](../../../reports/cara_sq_cpu_accepted_20261028.json) · [完整服务器原件](../../../reports/cara_sq_two_card_cpu_terminal_20261028.json)

接收脚本首次在本机 Python 3.9 解析 Docker 纳秒时间戳时退出；已兼容为本地微秒核算视图并重新读取同一终态成功，原纳秒回执不变，未重派服务器任务。初次四卡根目录猜测无效，后用仓库登记根目录恢复检查成功；两份原观察均保留。
