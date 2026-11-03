# Native 轨迹、单步敏感度与 F17 独立确认

2026-11-04，Phase 1。唯一计划 run 为 `cara-native-sensitivity8-confirm4-r1-20261104`。
用户原话：「批准新旧输入都做，约 8.9 GPUh，硬限 9.5 GPUh」。本阶段只准备；不预留 ledger，不启动 GPU。
范围、来源身份、队列、费用和 CPU 证据统一放在 `manifest.json`。本文件与实现必须在首次 GPU 执行前提交。

## 输入与固定协议

四旧 CAL 保持 CAL35 原身份与 seed0；两个 FIT 保持 FIT，两个旧 CHECK 仍属已曝光开发输入。
四新输入为 av_cc90f226-5312-4e0f-959a-39cd4eb4d90d、human_034、misc_9699390-uhd_3840_2160_30fps、physics_017。
选择规则是在原来源分组目录中，排除既有曝光分组、工程排除分组与整个旧 48 池，再从 av/human/misc/physics 各取
`SHA256("CARA_SENSITIVITY_20261104_SEED0|" + name)` 最小者；不依据输出或质量选样。
原四卡已保存身份清单、当前本地登记 JSON/gzip、双卡当前和历史 outputs 已纳入本次身份检查；不对未知外部运行作无曝光保证。
Phase 2 首次执行前须对固定四个身份再做增量核查，不重新抽取。final16/backup16 保持保护，DEV16 也不复用。

Cosmos checkpoint、BF16/FP32 策略、432×768、93 帧、16fps、guidance7、原负提示词、35 requested/36 actual updates、seed0、
UniPC 网格与 CAL35 一致；保留普通文本/视频 guardrails。F17-A2+light C、F19-A1、WC_T006 直接复制 CAL35 固定角色字节，不调布局、alpha 或阈值。
单步 C 使用原完整 C（alpha0，CAL35 的原 OSI/flow 设置），其余 35 步为 D。它不是轻量 C；不会用终点结果挑 C 版本。

## 采集与等价控制

(a) 八输入各一条 Native 记录轨迹。记录第 1–36 步输入 latent、第 36 步后 latent；每支记录
`RMS(v(t)-v(t-1))`，guided 严格采用原算术 `v_c + 7*(v_c-v_u)`。
first-block 每支记录 `mean(abs(h(t)-h(t-1))) / mean(abs(h(t-1)))`。第 1 步差分记 null。
实际采集采用已证明与 Native 等价的全 D 配对适配器，以同时保留真实 D 缓存。
在 8,10,…,34 步之前保存完整 latent、UniPC 全实例状态、WC 缓存及窗口/来源、两个条件、owner/readout/calibrator/executor 状态、生成器和各 RNG。
保存这些步的 Native guided 张量，便于量化 C 的实际局部扰动。单个状态先拷到 CPU，按独立字节 storage 与 typed-view 描述保存；逐个恢复，保持 alias。

(b) 八输入×14 步位＝112 条敏感度后缀。从 Native 第 t 步之前恢复，仅执行 t…36，不重复前缀。
报告终态 latent MSE、完整 93 帧 LPIPS-Alex、局部 guided 扰动 RMS。对照为同输入同 seed Native 记录轨迹。
两个原生 warm；另在首个旧输入上安排一个纯 Native bridge、t8/t34 两个不干预续跑和两个独立完整 single-C 路径。
完整 single-C 与恢复后的路径必须逐元素终态 latent 相等，释放后再核对解码 RGB/PTS；不通过则技术失败，不作敏感度结论。

(c) 四新输入各跑 Native、F17、F19、WC，按输入轮转角色顺序。额外 clean Native 是速度基准，避免将 (a) 的观测/状态写入开销带入分母。
总计 143 请求，包括 8 记录、112 后缀、16 clean、2 warm、5 控制。全部路径与拒绝/失败保留，不补样、不重派。
clean 路径复用 CAL35 `Requests` 与 T_DD 计时：去噪循环开始至解码完成；T_request 同时保留。
Native 记录与敏感度时钟只作诊断，不能用于部署提速。所有新科学评分在完整释放、唯一结算后于 CPU 执行。

## F17 确认判据

独立单位为输入，帧不是独立样本；四新输入等权，不因结果更改样本或阈值。
以下条件须同时满足：

- 同批 `mean(T_DD Native) / mean(T_DD F17) ≥ 1.9`，F17 平均 T_DD≤133秒，平均 LPIPS-Alex≤0.27，沿用 CAL35 的固定目标。
- F17 相对同批 Native、F19，各自 MUSIQ_LONGER512 均值差≥−1，subject_consistency 与 motion_smoothness 均值差≥−0.01，六个点均值门全部通过。
- 新旧 F17 平均 LPIPS 的非劣检验通过。固定容忍 δ=0.027（原 0.27 目标的 10%），H0: μnew−μold≥δ，H1:<δ。
  旧组为 CAL35 原四条 F17 的已接受 Alex，固定复用，不重评分；新组四条来自本卡。将新组数值减 δ 后，对八个输入枚举全部 C(8,4)=70 个标签排列；
  统计量为新减旧均值，取含观测排列的单侧下尾 p，p≤0.05 拒绝 H0。零假设边界要求两组输入误差在平移后可交换；逐输入值、差值及此假设一并报告。

这里把“不显著差”预先落实为有固定容忍的非劣检验；普通差异检验未显著不构成非劣证据。
四样本可能无法判定非劣；这种结果记为不确定，不能宣布独立确认成功。速度、保真、质量和统计结论分别报告。
多条件采用交集判定，不挑显著指标。无额外 seed 或骨干泛化主张。

## s·Δv 原理重建：现在固定的函数

`analyze.py` 的实现是唯一预注册函数，采集后不改系数、指数、插值、平滑或目标形式。
首先对输入 i 的实测步位定义

`s_i(t) = sqrt(MSE_latent_terminal_i(t)) / max(RMS(guided_C_i(t) - guided_Native_i(t)), 1e-12)`。

主分析仅用两个旧 FIT 的 `s_i(t)` 做等权平均得到 `s_FIT(t)`；在 8…34 的整数步上做步号线性插值，35 延续34。
1…7和36为保护 D，权重置零。对六个非 FIT 输入分别令

`w_i(t) = s_FIT(t) * RMS(guided_Native_i(t)-guided_Native_i(t-1))`，

再除以该输入8…35步的均值。新输入的终点敏感度只用于验证/逐输入报告，不反向拟合主重建曲线；条件支、无条件支和 first-block 指标作固定诊断，不轮流挑最好的代理。

相邻 D 在 a,b 时，固定区间代价 `E(a,b)=sum_{t=a+1}^{b-1} (t-a)*w_i(t)`。
保护 D=1…7,36；分别在 D 数16/17/19/22/25下精确最小化
`(max_intervals E, sum_intervals E^2, lexicographic_dense_tuple)`。
实现先枚举可能峰值并二分求可行最小峰值，再在该峰值下 DP 最小化平方和并按 D 字典序破平局，避免局部词典序递推丢失全局次目标。
17D 的 A 固定取非 D 中 `age(t)*w_i(t)` 最大的10步，平局取早步；报告与原 F17 D/A 的重合、Hamming、C Jaccard。
其它预算只报告 D，不能据此启动新布局。按六个非 FIT 及其中四新输入分别报告全部重建结果，不选择输入或预算来证明原理。
原理支持的预登记描述门：六输入的 D 自由位置重合中位数≥7/9、A 重合中位数≥7/10；无论过门与否保留全部数值，独立于 F17 速度/质量判定。

`SCOUT_READONLY_CPU_PLAN.json` 的 gains 仅有3个实测点，是转移的粗先验；已有36项 gains 曲线包含插值/延续，不能当作36个实测 s(t)。
研究 agent 的六个 `zero_gpu/` 原件按原字节纳入提交，仅作探索历史；其 `/workspace` 路径和多代理比较不是本预注册实现，不改写其结果，也不从敏感度结果再选函数。

## 费用与 Phase 2 边界

正式工程报价9.287657161 GPUh，硬限9.5，包括 a0.698969381、b旧2.769049671、b新2.769049671、c1.016971396、
warm/控制0.583223967、10%波动0.783726409、模型加载/清理0.166666667、状态 I/O0.333333333、释放0.166666667。
后缀按 CAL35 实测每 D pair6.859528063秒×剩余更新数，加每请求68.257886994秒完整 Native 非循环开销估算，C 也按 D 收费；节约来自不跑前缀。
不是新 GPU 实测，也不承诺一定跑完；硬限前保留600秒退出，≥90°C沿用原 launcher 自动停止。
既有 guardian/supervisor 的硬限、温度、独占上下文和存储检查保留；不新增 heartbeat、cron、automation 或持续监控任务。
Phase 2 必须先完成实际 Linux 入口/运行时/新输入资产/私有256GiB输出盘的 CPU 准入和 fresh 空闲、owner lock、内存/磁盘/ledger 检查，且不允许上调报价或9.5硬限。
准备完这些才在中央 ledger 为该 run/launch/source 一次预留9.5GPUh，复用原 guardian 完整 monotonic wall bill，释放后包含失败费用在内唯一结算；响应丢失只恢复原交易，不另建 run。
实际预算仍 cap250、旧责任16.5不变。本卡将使用用户本次明确批准额度，Shared25规划10不是已预约余额；未来并不能同时保证这10GPUh，需另外核价/安排。
本阶段没有 Phase 2 的远端 stage、预留或启动记录；Phase 2 再写唯一 run handoff。
