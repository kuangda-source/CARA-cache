# 完整采样与简单稀疏刷新：CPU 接口验证

2026-10-03。承接 [81 的下一阶段范围](81_WC_H1_DECISION_AND_CLOSED_LOOP_CPU_PLAN.md)。直接授权的 [r4 完整 104 点补验](75_WC_FULL104_R4_CARD_AND_RESULTS.md) 已执行并结算，本阶段没有重提该任务，也没有新增 GPU 卡。H1 的冻结 source `77111262a02931e01f2ca2253c2ec585e6b0852b`、原 GPU 原件与失败历史保持。

## 完整 D/D 控制

新增生产核心 [full_sampling.py](../src/wcomr/full_sampling.py)，实际执行调用方的 `Inference.generate` 到普通返回，不再由 PrefixComplete 截断。固定官方 WC、rectified-flow 采样器、UniPC、video2world 和 Inference 五份源码的函数体被 CPU 夹具按 AST 原样加载；类型注释延迟解析。真实 GPU 阶段仍须使用原运行时和真实类，CPU 提取函数不是整个官方环境的加载验收。

共享一次官方 prepared batch 及其完整 RNG 转移、初始 buffers 和明确 eval 模式。每个请求比较两个完整采样路径，核对九项无扰动门、最终 sampler latent、解码输入/输出、guardrail 输入/输出、写出输入与输出文件、后端 flags 和结束 RNG。13/21/33/35/36 五处检查点覆盖 WC、UniPC 多步历史、显式生成器、全 RNG、net buffers 和模块模式；恢复出的 latent 实际返回给官方循环继续采样。故意破坏仍存活的 latent、计数、求解器索引、buffers、模式和 RNG 后，完整后缀仍与对照相同。

发现并保留官方尾部行为：请求 35 步产生实际 36 次 solver 更新/72 次 CFG，但 pipeline 将 WC horizon 设为 70。call70 后缓存清空，call71/72 的计数为 0/1，均为重新暖启动的 full。不能为了对齐实际网格把原生 horizon 偷改为 72；新增第 35 步检查点专门覆盖缓存清空。

原 [CPU r1](../reports/wc_full_sampling_cpu_r1_20261003.json) 失败：stand-in 的 movedim 返回非 contiguous 布局，官方 OSI 的 `.view` 拒绝。只改夹具的布局，没有修改官方源码，失败及原文件 SHA 保留。[CPU r2](../reports/wc_full_sampling_cpu_r2_20261003.json) 在实际 Torch2.7.1+cu128、禁止 CUDA 的环境通过，耗时 77.964 秒：6 个完整正控制请求对，5 个第二请求失败控制。尾部失败、解码失败、写出缺失、输出损坏和解码后 RNG 偏移均被拒绝；第一请求和计划 2 请求/4 phase/各 36 更新与 72 CFG 的分母保留。

## Native forecast window 和 true-dense 历史分开

新增 [refresh_deployment.py](../src/wcomr/refresh_deployment.py)。它用文件 SHA 和唯一源码锚点约束适配；保留官方 probe、skip 判据、缓存命中分支、Gamma、flow/warp、缓存写入规则与 reset。只在官方已经选择刷新、已支付 probe、处于 retention 阶段、同 CFG 有两次过去真实 dense 时，允许深层 self-attention 调用现有 `routed_no_pv`。sim0.1/cdf0.98/no-PV 不调参，生产默认层 6/23/27 走 dense；QKV/RoPE、MLP、cross-attention、head 保持。暖启动、历史不足和最后两次原生重置后的 full 均走 D。没有读取本步 dense teacher、候选误差或最终输出来选动作。

官方 residual window 实际最多保留三个条目，达到三个后保留首项并平移末两项；metadata 跟随同一拓扑和 native tensor 对象。它是 **forecast window**，允许保存近似来源以供后续 Gamma/warp 使用。另有只接收实际 D 计算的 true-dense metadata，S 从不进入。当前原生 OSI 只从 probe 差分计算 Gamma，没有用 deep residual 作拟合 target，也没有 W1 在线 deep calibrator。`probe_exact_operator` 仅表示浅层算子完整执行，不表示它的输入仍与另一条 dense 轨迹相同。D 同样仅表示候选当前状态上的真实 dense 计算。

每个来源明确绑定 request/model/condition、deep group、CFG、绝对 call、solver step、cache epoch 和来源种类。call70 的 native reset 同时清空两个 CFG 的 forecast/true-dense metadata；绝对 call 不随计数归零。跨请求/phase 建立新 ledger。checkpoint 还保存 ledger；native 状态恢复后重新绑定新复制的缓存 tensor，不能继续使用旧对象身份。

## CPU 候选是实际闭环接线控制

[CPU r3](../reports/wc_full_sampling_cpu_r3_20261003.json) 178.700 秒通过，包含全部 11 条 D/D 控制，以及 17 条刷新接线记录：flow OFF/ON、两个请求、D/D provenance 无扰动、D/S、破坏后恢复、历史不足与五类失败。S stand-in 故意返回不同的 attention 输出；该输出进入原生 cache window、后续 cache hit、实际 UniPC 更新和最终 sampler 返回。不是 shadow 返回原 dense，也没有从 baseline trace 回放位置。CPU 夹具用两路径相同的有限阈值排布强制覆盖 hit/full，该排布不作为部署参数或自适应效果证据。

D/D 保留严格九门和最终输出等价；D/S 记录九项比较结果而不要求其相等，只要求共同初始输入、条件、完整 grid、后端 flags、RNG 和 pipeline 阶段契约成立。候选实际改变最终 latent 属于接线正确性，不能当质量正结果。CPU stand-in 的最终 RGB 转 uint8 后可以与对照文件相同；不能因此声称生成结果保真。

r3 的 limits 字段曾沿用 D/D 夹具的“no candidate”表述，与同一 receipt 内明确标记的 CPU stand-in 接线控制不一致；新版本改正文字，原 r3 回执不回写。新增模型对象和 deep group 变化拒绝门后的 CPU r4 状态及实际文件 SHA，见下面的终态记录；不得用 r3 给后来代码追认 CPU 通过。

CPU 使用 4-block toy、2048 通道与缩小几何，fallback 使用 toy layer2。真实 28 层、probe2、fallback6/23/27、N15660/BF16/QKV、真实稀疏 CUDA kernel 的闭环尚未验证。解码 stand-in 给出 1×3×93×16×16，writer 写明确标记 `CPU_MOCK_WRITER_NOT_VIDEO` 的 JSON 文件；没有运行真实 VAE、视频编码、模型权重或 CUDA。恢复仍为同进程/存活条件闭包，不是独立序列化整管线重启。

## 下一科学工作

CPU 源码门通过后，具体化两曝光 CAL 的官方 WC 与简单 WC+S **完整输出诊断卡**，覆盖生产 fallback、实际自适应 trace、call70 reset、实际 decoder/guardrail/writer 和完整视频原件。它们仍是开发数据，不称独立确认。先定义全部请求分母、失败/拒绝处理、source/assets/import/package、VRAM 和成本包络，冻结单独 source/card，重新现场准入；不复用 r4 或 H1 已消耗的单次窗口。

当前核心包含逐步 tensor hash、condition hash、checkpoint 深拷贝与每层 finite/路由 metadata 的同步。其 wall time 必须全部计入累计预算，但不适合作为干净净加速结论。完整视频诊断成功后，要另以相同输出路径、轻量必要来源维护、明确冷/热口径、成对重复与顺序，量实际生成耗时；将来源维护/路由成本纳入候选。不能用算子中位 1.219× 或 H0 整组热比推算视频净收益。

当前累计结算 6.055044055960606/12 GPUh、36 jobs，剩余 5.944955944039394h，CPU 不改变账本。本阶段未选定或启动下一 GPU 卡；不训练 H2/Trust Head/RV，也不新增人评或付费评分。方法接受仍需调优 WC/少步 Native 的公平质量–时间曲线与独立数据确认。

## 最终源码 CPU 终态与同步边界

[CPU r4](../reports/wc_full_sampling_cpu_r4_20261003.json) 122.205秒通过新增 model/group 失败控制。随后代码检查发现 net.forward 的清理 lambda 捕获了循环中会重绑定的变量；外层完整采样的最终恢复可能掩盖这一缺口。将变量固定到回调参数，并在适配器关闭后立即核对官方 forward 已恢复，未删掉外层恢复。[最终 CPU r5](../reports/wc_full_sampling_cpu_r5_20261003.json) 122.224秒通过相同19条刷新记录：12个完整请求对和7类失败控制，D/D provenance 严格九门/最终pipeline一致；D/S、故意破坏恢复和历史不足控制完成36更新/72CFG。七种失败保留第一完整请求、计划4phase与第二请求baseline36/候选11更新，不重补失败样本。

[独立 CPU receipt/source 审计](../reports/wc_full_sampling_cpu_audit_20261003.json)通过：最终payload每文件SHA匹配当前源码；无适配器D/D核心及依赖仍与r3完整11条控制的字节一致；r1失败及各轮原SHA保留。最终19条刷新控制使用明确toy group(1,4)、fallback2，新增provenance后五检查点各51个组件。snapshot仍为同进程接口，未增加独立重启声明。

r5现场观察 Unix1791031104.1672678：指定A6000为24MiB，compute apps为空；账本仍为6.055044055960606/12GPUh、36jobs，新增GPU费0。该观察不是下一任务的持续资源预留。当前没有运行中的CPU控制或新增GPU任务，下一需先具体化完整输出卡。
