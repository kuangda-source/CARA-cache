# 138｜W1 批准五参考卡：完整结果与后续条件

2026-10-06。**获批五参考卡全部完成；W1 终点证据扩展到原七个接受场景，4 改善、3 退化，收益存在明显场景差异。**继续 WorldCache，优先 W3 位置干预；W1 保留为条件诊断候选，尚不直接扩大训练或独立确认。[当前计划 v4.1](../plans/WORLD_CACHE_POST_REFERENCE_WINDOW_20261006.md)。

## 1. 本批的发现和价值

原五个缺参考场景全部完成 Native35 生成并被接受，两个既有参考复用。21 个 Native/WC/W1 视频均完成 93 帧完整解码，14 对全帧 CPU FP32/Alex LPIPS 完成，独立原件与逐帧均值核对通过。原 CAL8 的 **8 场景/7 W1 接受/1 W1 视频拒绝** 不变；robot_054 不替换，不补参考，不填零。

| 原场景 | 官方 WC LPIPS | W1 LPIPS | 相对失真降低 | 改善/退化帧 |
|---|---:|---:|---:|---:|
| AV28 | 0.389524 | 0.294265 | +24.46% | 93/0 |
| Common | 0.333153 | 0.306939 | +7.87% | 93/0 |
| Human | 0.424745 | 0.390806 | +7.99% | 93/0 |
| industry_084 | 0.532712 | 0.544605 | −2.23% | 13/80 |
| misc_13398218 | 0.493993 | 0.588302 | −19.09% | 0/93 |
| physics_045 | 0.305083 | 0.278172 | +8.82% | 93/0 |
| AV51 | 0.394325 | 0.457839 | −16.11% | 0/93 |
| robot_054 | 缺失 | 原 W1 视频拒绝 | 不评分 | 不填零 |

正号表示 W1 更接近同请求、同初始噪声的原生参考；负号表示更远。各接受视频均 93 帧，无平局帧。四个改善场景全 93 帧改善，两例大退化全 93 帧退化；不是少数极端帧抬高均值，也不是独立帧样本检验。

七场景等权平均 LPIPS **0.4105051592→0.4087040246**，绝对改善 **0.0018011346**，均值降低 **0.4387605%**。场景差值中位数 +0.0262139456；逐场景相对降低率的等权均值 1.6721%、中位数 7.8684%，与“等场景平均 loss 的相对降低”是不同聚合，不互换，也不挑一种覆盖负例。旧 Common/Human 四个原 loss 完全复现，差值均为 0。

这批消除了原五个参考缺口，让两个已知正例不再独自承担结论。全局标量近似在部分场景确实有终点保真价值，但目前不能称稳定的整体优势。该结论限于冻结配置和曝光 CAL，不否定 W1、W3 或整条 WorldCache。

## 2. 与旧指标的对齐

[联合指标分析](../reports/wc_w1_native_reference_metric_alignment_20261006.json)确认新 LPIPS 的 WC/W1 视频 SHA 与旧 MUSIQ 相同；旧 MUSIQ 3 升/4 降、开发 VQA 6 平/1 降（等场景 −3.17 个百分点）保持。

- `misc` 的内部 velocity MSE 比为 1.2045、postwarp 比 1.3152，终点保真、MUSIQ、开发 VQA 也退化。该配置在此样本上的负信号一致，应保留。
- AV51 内部 velocity MSE 比 0.7633、postwarp 比 0.8363，终点 LPIPS 却退化 16.11%，MUSIQ 也降低。原 OFF 状态上的内部改善不能直接保证候选自身轨迹与终点改善。
- industry 内部改善，LPIPS 退化 2.23%，MUSIQ 却提高约 0.1127（原归一化分数单位），开发 VQA 持平。它是保真与成像代理的取舍，不能仅凭 LPIPS 判绝对视频质量退化。
- AV28、physics 的保真改善但 MUSIQ 略降，Common/Human 两类指标均改善。所有分歧保留，不删除旧负结果。

LPIPS 只衡量原生相似性；MUSIQ 是成像代理，当前小模型抽帧 VQA 也不是物理质量最终判决。本轮没有新增物理、语义、运动评价或人工评审。

## 3. 负结果的低成本实现与条件核查

五个新 Native 均 **36 solver 更新/72 CFG/一次 prepare、深层 full72/skip0**，旧实例 cache forward 未用于原生参考；完整请求、权重/运行源、decoder 与后端 flags 保持。原 W1 过去 anchor、同参数、72 条执行记录、固定 mask 与 OFF/ON parity 控制未发现新增破坏；复用已通过控制，不重跑同源 GPU 或 CPU。

[现有日志探索性分析](../reports/wc_w1_existing_replay_conditions_exploratory_20261006.json)保留全部 8 行：自然缓存判断与 fixed mask 分歧分别为 AV28/Common/Human/industry/misc/physics/robot/AV51 的 **3/3/8/0/14/5/8/16** 次。两例大退化的分歧最多，是可跟踪线索，不是“分歧导致退化”的因果结论，不据此拟合阈值。Human 有 4 次 beta 触及旧 clip=4 却改善，misc 有 3 次且退化，AV51 无截断却退化，截断不能单独解释结果。没有新测量的状态 drift 幅度或自身轨迹 teacher MSE。

新[下一轮登记](../manifests/wc_post_reference_hypotheses_r1_20261006.json)限定 misc/AV51 两负例和 AV28 正对照、seed0、原 scalar/mask、calls45/46 与67/68，在 W1 自身实际状态比较 WC/W1/full teacher，teacher 不写回部署；先验证 shadow 不干扰，再解释自身状态误差或传播差异。它是未来测量的设计，仍缺实现/实际 CPU/费用绑定和具体 GPU 批准，不是本轮已经完成的科学数据。

## 4. 完整执行、原件核查与费用

唯一 `wc-w1-native-reference-cal8-r1`，GPU source **2ae0e901c6a981d19199c912d4be675ab27cfaf0**，stage `.sync/wc-w1-native-reference-gpu-r1-20261006`，160 冻结文件与原 R2 CPU 原件绑定。获批 3600 总/3570 child/kill5，未重启、未缩减五参考、未改在跑源码。实际 exit0/`EXITED_REQUIRES_RESULT_AUDIT`，生成 5 接受/0 拒绝；加载 84.8005 秒。五次 pipeline wall 为 364.9155/325.2596/329.9709/318.3680/316.8070 秒，跨批次旧 W1 含诊断时间不可与它们拼成部署加速比。

全 GPU supervisor wall **1816.403254895 秒 = 0.504556459693 GPUh**，含加载、保护、输出、清理、释放，未超 3600。原预付 1h 已按实际结算；累计 **13.5043027920263/24 GPUh**、第48 job、无 inflight，余额 **10.495697207974 GPUh**。旧预算授权历史及失败费用保留。[实际账本](../reports/budget.json)。

GPU 原 supervisor/timeout/runner **2956439/2956518/2956519** 全部退出；f1 锁释放，终态目标 GPU 24 MiB、无本卡进程。850 条 monitor 均在原 UUID，峰值 24842 MiB。CPU supervisor/审计/评分 **2965204/2965205/2965341** 也全部退出。CPU 解码审计 22.1021 秒、评分 250.7814 秒，全 wall 272.8868 秒；CUDA 未初始化，新 GPU 提交 0。

[独立原件审计](../reports/wc_w1_native_reference_final_original_native_audit_20261006.json)通过 356 项原生 SHA、6 原句柄退出、锁/账本/实际费用、旧 CPU stage/selected 源、全部配对文件及 signed 全93帧均值重建；W3-B 新授权与新输出仍不存在。CPU原件 SHA `89ffe2bfe38c229c1f3d956ae3b2db1061e29c4dcb3f24241eac63243b51c763`；实际预算 SHA `8d868f727159804f2a6131ffb337c77e992de966a065367c68feed1e331fcdc9`。

原件：[runner](../reports/wc_w1_native_reference_runner_20261006.json)、[supervisor](../reports/wc_w1_native_reference_supervisor_20261006.json)、[CPU终态](../reports/wc_w1_native_reference_terminal_cpu_r1_20261006.json)、[全部14对逐帧loss](../reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json)、[CPU执行回执](../reports/wc_w1_native_reference_terminal_and_score_cpu_r1_20261006.json)。CPU执行/独立审计/探索性分析源均保存于 `research/sources/w1_native_cpu_execution_20261006/`；没有修改生成 stage。

## 5. 当前结论和下一执行边界

继续 WorldCache，优先 W3-B 的同配额位置干预；W3-A Human 的保真和未来计算需求正信号保留。W1 全局 scalar 保留明确正例与条件负例，先做小规模区分，暂不扩 W2/训练/稀疏或直接将此版本送大规模 CONF。旧 v4.0/原判据/原两例结果及拒绝均保持，新假设明确是下一轮登记。

本轮直接批准的完整 W1 卡已执行并评分完成。另张 W3-B 的 2父/16后缀/10输出/四交换、9600 秒具体范围尚待单独答复；旧问题已提报，不重复要求 W1 批准，不扩大“允许”的范围。总体研究目标未完成，此次不是论文、独立确认、物理质量或干净部署速度接受。

## 此前批准与启动记录（保留，以下非当前状态）


当前：**已唯一启动获批五参考卡，正在初始化/加载，真实输出与评分尚待。**

GPU源 `2ae0e901c6a981d19199c912d4be675ab27cfaf0`，selected实际CPU前置门exit0/12.158秒；原R2生产CPU原件与160文件绑定通过。[dispatch](../reports/wc_w1_native_reference_dispatch_20261006.json)与[首个现场观测](../reports/wc_w1_native_reference_first_live_observation_20261006.json)确认supervisor2956439/timeout2956518/runner2956519存活，实际GPU进程2956519，初始化加载中。child截止北京时间 `2026-10-06T18:51:19.386435+08:00`；只跟踪原stage/句柄，不修改GPU payload或重复提交。

预付3600秒使账本显示13.99974633233337/24h、第48job及本卡inflight；原12.99974633233337/47jobs保留，结束按实际全wall结算。已启动/加载并不等于五个参考接受或W1收益。下一原任务监测→终态结算/释放→独立CPU视频审计/14个可用loss评分→保留原8/7/1与缺失的综合汇报。

以下保留源冻结时的批准和准备记录。

直接用户“允许”对应最近提报的 `WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A`。完整五索引0/3/4/5/7 Native35，原8/7/1分母、两既有Native、旧WC/W1视频保持；3600总/3570child/kill5，上限1GPUh计入原累计24。此次不将答复扩大到另张W3-B9600卡，不重问已批准W1。

[直接范围原件](../manifests/wc_w1_native_reference_gpu_authorization_20261006.json)、[人类来源](../manifests/wc_w1_native_reference_human_scope_source_20261006.json)、[selected配置](../configs/wc_w1_native_reference_production_r2_selected_20261006.json)及[执行清单](../manifests/wc_w1_native_reference_execution_20261006.json)绑定R2实际CPU原件。新selected stage160文件，仅CPU配置换为selected和新增批准文件，生产/核心/评分源码保持。

[初次fresh资源观测](../reports/wc_w1_native_reference_resource_before_20261006.json)确认既有WorldCache A6000 UUID末尾b704，显存24MiB/48527MiB空闲，无计算进程，数据盘余557950390272字节；这不是最终资源准入或GPU运行。预算仍12.99974633233337/24、47jobs无inflight。下一selected实际源/资产/范围CPU门，supervisor两次freshGPU/进程/磁盘与f1锁/账本门，唯一运行和durablePID/log/receipt；预付3600后按包括加载、异常、输出、释放的实际wall结算。所有全93帧视频审计和FP32 CPU LPIPS在释放后。

该卡补证据缺口，不改变W1算法；旧两个约8%保真正结果及MUSIQ/VQA混合结果保留。新Native拒绝/技术中断明确单列，不补样/填零；全接受最多7场景14个loss，报告场景均值、中位数、正负/逐帧分布而非7/7门槛。CAL开发证据不是新seed独立CONF、物理/语义或部署速度接受。目标已由直接答复恢复active，原blocked条目为历史。
