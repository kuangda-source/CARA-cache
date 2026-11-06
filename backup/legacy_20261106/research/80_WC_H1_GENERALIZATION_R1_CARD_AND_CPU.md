## 2026-10-03 H1早晚双CAL终态：完整72格原件审计通过，CPU来源扰动分解完成

[80完整卡](80_WC_H1_GENERALIZATION_R1_CARD_AND_CPU.md)：source77111262a02931e01f2ca2253c2ec585e6b0852b实际CPU35后唯一run退出0；两场景各两前缀33更新/66CFG、全部九门、step13/21/33各36组件与进程内restore通过。24来源/72格/120原件240张量和96组独立float64误差、参考语义/费用/释放全部审计通过。早step12/晚step25为预登记选择，两个曝光CAL不是CONF。

S来源velocity误差0.8935%–1.7341%，D/S整组+head热耗时比1.05601–1.14293×；human早期S residual7.2962%/7.5772%超过局部5%，来源不是处处安全。未来双字段5%描述性筛查0/72（D/MF/S各0/24），dense-held velocity漂移7.2466%–40.2694%；不是视频接受门或安全寿命结论。CPU来源扰动与交叉项分解177.791秒通过，下一仅CPU完整采样与简单S/D闭环接口准备，不自动H2/RV/训练或新增人评。

实费2717.978329秒（0.754993980h），累计6.055044055960606/12GPUh、36jobs，余5.944955944039394h，无inflight。原PIDs2674427/2674442/2674444/f1锁/GPU已释放（24MiB/noapps），1273次monitor峰值27332MiB；CPU不新增GPU费用。以下在跑/预付/旧授权文字均为历史。

## 本卡真实终态与描述性结果

完整24来源/72格/120原件240张量及九门、source/费用/释放独立审计通过。两个曝光CAL，CFG、窗口和K相关；不把72格当独立样本。全部来源点都按预登记规则为早step12、晚step25，不按误差择优。

[完整汇总](../reports/wc_h1_generalization_r1_summary_20261003.json)、[独立原件审计](../reports/wc_h1_generalization_r1_audit_20261003.json)、[CPU来源扰动分解](../reports/wc_h1_generalization_delta_cpu_20261003.json)。百分比为相对真实当前D的RMSE；时间比是单个deep组+head的热重放，无候选视频或端到端结果。

| 场景/窗口/CFG | S来源 residual% | S来源 velocity% | MF velocity% | D/S组时间比 |
|---|---:|---:|---:|---:|
| common/early/0 | 3.9577 | 0.9107 | 0.3859 | 1.05601 |
| common/early/1 | 4.2469 | 0.9807 | 0.4191 | 1.05854 |
| common/late/0 | 3.0333 | 0.8935 | 0.4810 | 1.08639 |
| common/late/1 | 3.0538 | 0.9089 | 0.4750 | 1.08937 |
| human/early/0 | 7.5772 | 1.5525 | 0.5131 | 1.11608 |
| human/early/1 | 7.2962 | 1.7341 | 0.4403 | 1.11030 |
| human/late/0 | 4.7904 | 1.5723 | 0.5302 | 1.14164 |
| human/late/1 | 4.6476 | 1.5071 | 0.5261 | 1.14293 |

| 场景/窗口/CFG/K | D velocity% | MF velocity% | S velocity% | D residual% | MF residual% | S residual% | S−D velocity pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| common/early/0/1 | 13.8595 | 13.8689 | 13.7775 | 28.1652 | 28.1700 | 28.0326 | -0.0819 |
| common/early/0/2 | 16.1120 | 16.1094 | 16.0025 | 33.0253 | 32.9992 | 32.7978 | -0.1095 |
| common/early/0/4 | 25.1779 | 25.1768 | 25.0850 | 49.3909 | 49.3603 | 49.1888 | -0.0929 |
| common/early/1/1 | 18.2124 | 18.2411 | 18.0979 | 35.1159 | 35.1706 | 34.9549 | -0.1145 |
| common/early/1/2 | 21.9796 | 22.0105 | 21.8491 | 41.9144 | 41.9696 | 41.7014 | -0.1305 |
| common/early/1/4 | 32.8699 | 32.8985 | 32.7454 | 59.4935 | 59.5319 | 59.2902 | -0.1245 |
| common/late/0/1 | 8.5909 | 8.5691 | 8.6471 | 16.8137 | 16.8627 | 17.2120 | +0.0562 |
| common/late/0/2 | 12.9089 | 12.8653 | 12.9065 | 27.3032 | 27.3561 | 27.6489 | -0.0024 |
| common/late/0/4 | 14.8778 | 14.8590 | 14.8544 | 55.9570 | 55.9890 | 56.1209 | -0.0235 |
| common/late/1/1 | 8.6298 | 8.6575 | 8.7780 | 18.4575 | 18.4740 | 18.7955 | +0.1482 |
| common/late/1/2 | 12.7799 | 12.8258 | 12.9306 | 29.7531 | 29.7545 | 30.0200 | +0.1507 |
| common/late/1/4 | 15.0491 | 15.0698 | 15.0878 | 57.5617 | 57.5655 | 57.6916 | +0.0387 |
| human/early/0/1 | 17.5864 | 17.6123 | 17.5589 | 34.9233 | 35.0030 | 34.9344 | -0.0275 |
| human/early/0/2 | 19.7340 | 19.7657 | 19.7206 | 39.7002 | 39.7797 | 39.7726 | -0.0134 |
| human/early/0/4 | 29.6718 | 29.7021 | 29.7167 | 54.0970 | 54.1769 | 54.2687 | +0.0448 |
| human/early/1/1 | 25.0162 | 25.0500 | 25.0847 | 46.2189 | 46.2948 | 46.4704 | +0.0685 |
| human/early/1/2 | 28.7486 | 28.7883 | 28.8338 | 51.9102 | 51.9988 | 52.1972 | +0.0852 |
| human/early/1/4 | 40.2694 | 40.3064 | 40.3415 | 66.0048 | 66.0765 | 66.2707 | +0.0721 |
| human/late/0/1 | 7.2466 | 7.2331 | 7.2522 | 15.9931 | 16.0345 | 16.2993 | +0.0056 |
| human/late/0/2 | 9.2868 | 9.2901 | 9.2830 | 25.9332 | 25.9549 | 26.0451 | -0.0038 |
| human/late/0/4 | 30.2801 | 30.2879 | 30.2802 | 63.1272 | 63.1329 | 63.1270 | +0.0001 |
| human/late/1/1 | 7.3364 | 7.3538 | 7.3899 | 16.6711 | 16.6766 | 16.8843 | +0.0535 |
| human/late/1/2 | 9.5382 | 9.5382 | 9.5221 | 26.6297 | 26.6344 | 26.7066 | -0.0161 |
| human/late/1/4 | 30.4386 | 30.4318 | 30.4110 | 64.9713 | 64.9720 | 64.9658 | -0.0276 |

| 场景/窗口 | D双字段5% | MF双字段5% | S双字段5% | S−D velocity扰动%范围 | S velocity绝对扰动/来源范围 | S residual绝对扰动/来源范围 |
|---|---:|---:|---:|---:|---:|---:|
| common/early | 0/6 | 0/6 | 0/6 | 0.8924–1.1782 | 0.9732–1.2474 | 0.9345–1.3016 |
| common/late | 0/6 | 0/6 | 0/6 | 1.3809–1.6775 | 1.5346–1.8274 | 1.5099–1.7594 |
| human/early | 0/6 | 0/6 | 0/6 | 1.5170–2.1606 | 0.9714–1.2621 | 0.9398–1.2903 |
| human/late | 0/6 | 0/6 | 0/6 | 0.5436–1.3256 | 0.3388–0.8290 | 0.2967–0.7812 |

实费 2717.978329 秒（0.754993980 GPUh），累计 6.055044055961/12 GPUh、剩余 5.944955944039h；120原件保留服务器不入Git。峰值 monitor 27332MiB/1273次采样，原三PID/f1锁/GPU已释放。

该5%线保持冻结的局部双字段描述性筛查，不是视频接受门。逐K稀疏来源扰动不能由总误差差值替代；CPU验证了 ||S−T||² = ||D−T||² + ||S−D||² + 2〈D−T,S−D〉，也覆盖MF，保留每格reference energy、signed excess和对齐方向。

## 来源扰动与下一科学决策

CPU分解177.791秒，16个MF/S来源记录与48个MF/S未来记录、两个字段全部通过独立float64恒等式与GPU记录核对；CUDA未初始化。S−D velocity扰动0.5436%–2.1606%，绝对扰动/来源0.3388–1.8274×；residual扰动1.8708%–9.3211%，绝对扰动/来源0.2967–1.7594×。MF−D velocity扰动0.2283%–0.8848%，不能把S−D全部归于真正稀疏。

common晚期S velocity绝对扰动/来源1.5346–1.8274×，human晚期0.3388–0.8290×，第4步约0.3388/0.3672×；早期两场景总体约0.97–1.26×。不是统一随K增长，不能拟合普适安全age。S的velocity误差对齐cosine −0.1454至0.0295，signed excess relative MSE −0.0008171至0.0005811；总误差可因交叉项抵消而略降，这不是视频质量提高。该分解描述相同官方轨迹的当前输出差值，不是反事实采样轨迹的误差传播。

下一步按[81 CPU完整采样与闭环准备](81_WC_H1_DECISION_AND_CLOSED_LOOP_CPU_PLAN.md)，先证明完整36更新/72CFG的D/D尾部与恢复等价，再明确简单S/D刷新中的approximate reference语义。暂缓复杂H2/来源路由/Trust Head，不继续机械追加局部窗口。两个曝光CAL与离散K不足以接受或彻底否定来源机制；视频、端到端、独立确认与公平曲线仍缺。未选定新GPU卡。

[原件CPU核对](../scripts/check_wc_h1_raw_cpu.py)、[生命周期审计计算核心](../scripts/audit_wc_h1_generalization_receipts.py)、[来源扰动分析](../scripts/analyze_wc_h1_generalization_delta.py)已随结果保存。生命周期核心与实际主机侧执行文本逐字节相同，其SHA见audit中 `.sync/h1_generalization_terminal_audit_remote.py` 键；执行包装器注入 `raw_code` 与 `audit_code_sha256`，连接方式保留ignored，未入Git。两个输入runner/audit的SHA与CPU侧分析回执核对一致。

## 以下为本卡冻结/预部署时的原始设计快照

# H1 泛化首卡：两个 CAL 场景的早晚阶段完整72格

2026-10-03。状态 `CPU_BATCH_PASS_NEW_CARD_PENDING_COMPLETE_ACTUAL_DEPLOYMENT_NO_GPU`。上一轮 [H1 中间点](79_WC_H1_LOCAL_LIFETIME_R1_CARD_AND_RESULTS.md) 已完整审计，不重跑、取消或倒改；其来源扰动增长较温和而共同缓存漂移较大。本卡检查这一现象是否只发生在已测的中间点，不预先把来源感知路由当作成立的方法。

## 独立卡与范围

卡 `WC-H1-GENERALIZATION-R1-20261003-A`，run `wc-h1-generalization-r1`，[配置](../configs/wc_h1_generalization_r1.json)、[执行依据](../manifests/wc_h1_generalization_r1_execution_20261003.json)。当前用户自主实验 goal 与既有累计12GPUh/WorldCache优先队列下选择独立单卡；没有新的用户许可消息，不复用 r4/H1 已消耗的单次1800秒窗口。最多一次6000秒全cost/5970秒child/kill5秒，另15秒账本余额余量；下一GPU仍须实际完整门和fresh准入，当前尚未提交。

Cosmos-Predict2.5-2B、eager/minimal_a2a、共享eval、seed0，原输入规格和官方WC设置保持。场景固定为 CAL8 第2个 `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191`、第3个 `human_199`。前者已用于H1，后者已用于W1开发；两个都是曝光CAL，**不是独立CONF**。新场景不是“泛化结论”，只是有限开发诊断扩展。

每场景 baseline/observed 各33个solver更新/66 CFG，保持请求35、实际36步全网格/70 horizon。保留全部九项 input/output/trace/block counts/state/sampling/named inputs/conditions/field signatures；step13/21/33各36组件与observed进程内restore，13继续至21、21继续至33。仍不是独立可重启全管线分叉。

来源早期区间 `[8,12]`、晚期 `[25,29]`，从该场景本卡新跑的完整官方baseline中，选择区间内**最早的两CFG都为true-full、有已付probe、各有两份严格过去同CFG true-full历史**的solver step。只读取 call/counter/deep-executed；source选择在任何candidate/shadow teacher之前持久化。相应区间不得跨到另一窗口，不能按误差、稀疏率、速度或视频挑点。没有合格点就失败并保留原分母；观察路径还要重新核验真实resume_flag/条件/历史，不靠trace推断替代运行时检查。

每场景两个来源点，各两CFG × D/MF/S × reuse 1/2/4；全卡24来源臂、72复用格、120原件/240张量。来源三臂各1warmup+3repeat；未来每臂4次便宜预测，当前D teacher两次逐位一致。固定一个deep组2..27、6/23/27 dense回退、0.1/0.98/noPV。当前S/MF始终approximate，真值只评分；只有原官方路径更新sampler和部署cache。当前teacher必须在三种预测及原件写出后才计算。

每个场景和每个时间窗口拥有独立held reference、条件指纹、request/model/CFG/group/step/call/source身份与原件命名空间。窗口之间不覆盖参考；中间实际官方刷新不会修改held reference。每个request结束核验所有参考未变并恢复全部挂钩；下一request重置WC与UniPC，来源不能跨请求或跨CFG。源码旧 `h1_lifetime` 和旧r1 prefix/scope/runner均保持。

## 生产核心与CPU证据

[多窗口来源与选择器](../src/wcomr/h1_generalization.py)复用原H1实现，单独安装一组shadow attention wrapper，仅当前窗口切换D/MF/S backend；原采样前向始终dense。[生产prefix/batch核心](../src/wcomr/h1_generalization_prefix.py)被[独立CLI](../scripts/run_wc_h1_generalization.py)调用，CLI没有Toy/kernel override。两请求共用一次模型加载与同一Inference/求解器，但各自shared preparation/full RNG和缓存生命周期独立。

[CPU r1](../reports/wc_h1_generalization_cpu_r1_20261003.json)为56.275秒前缀级控制；随后加入批次核心，[CPU r2](../reports/wc_h1_generalization_cpu_r2_20261003.json)80.447秒验证**同一个真实生产batch函数**在同net/solver/Inference上处理两个stand-in请求。Torch2.7.1+cu128、CUDA lazy init禁止、无真实权重/前向；账本未变。r1保留其原源码SHA，不追认它覆盖后来加入的batch函数。

flow OFF/ON两组batch各完整72格、120原件，四个request均两前缀33更新/66CFG、九门相等，step13/21/33各36组件，prepared/full RNG/registered buffer增量与挂钩恢复通过。CPU明确使用同一有限阈值序列迫使早晚来源9/26、未来1/2步cache、age3官方full、age4继续私有held复用；这是为了覆盖真实固定源码的cache/refresh分支，**不是生产部署阈值或真实轨迹证据**。Toy、合成kernel、mock prepare/request reset的限制保留。

第二请求晚期S nonfinite、第二请求晚期条件改变、第二请求没有晚期paired-full三种控制均保持24/72全分母、第一请求36格、必要时第二请求已完成早期18格，不补选、不删除失败；全部挂钩恢复。纯scope/selector/cost/budget拒绝12种scope变更、5种selector失败、3种成本和6种账本错误；仅一条CFG提前full不改变paired来源选择。

这只证明CPU接线与控制有效，尚未证明真实双场景/多窗口结果。完整实际部署还必须验证官方prepare、UniPC在13/21/33恢复后的下一更新、固定原类meta共享eval、全部source/assets/package/import以及两个真实样本metadata/context绑定；禁止CUDA初始化。

## 完整成本，不按窗口缩矩阵

[成本草案](../reports/wc_h1_generalization_cost_draft_20261003.json)基于已审计H1：219.462秒baseline、518.815秒observed，按热中位扣除shadow重放后约182.045秒剩余开销，约6.07秒/raw；这混合首次使用、metadata、IO和其他开销，不能称为单独测得IO。

规划每个前缀更新18秒（考虑full-call比例上升与第三检查点，不是实测上界）、每个group/teacher5秒、便宜预测150ms、120份原件各8秒未分类开销，另计load113.853秒、startup/import/shutdown50秒、eval5秒，再加20%余量与30秒结算。完整包络 **5151.663秒**，不满足4800，更不满足旧1800；选择独立6000秒卡，不能删除时间窗、场景、来源或K来挤进旧cap。

raw约16.244GB；两窗口12份参考的四张量快照约6.115GB，不含网络cache/allocator/teacher工作区。要求实际数据盘余量60GB；此前峰值24912MiB只能作历史参考，新的多窗口峰值未测。加载、初始化/JIT、失败、诊断、IO和释放按实际GPU过程wall计入现有12h。

当前已结算5.300050075675308/12GPUh，35jobs，余6.699949924324692h。旧失败费用不清零；CPU新增GPU费用0。6000秒预付会占1.666667h，但现在未预付、未准入、未运行；实际启动重新读远端账本且禁止任何inflight。

## 停止与判断

只有source/config/card提交推送、实际全CPU/source/assets/import门和fresh UUID/VRAM/compute/f1锁/预算/协调槽位通过，才提交此独立run一次。stage/out/launch已存在先核查原句柄，不能因观察超时重投、改变scope或覆盖旧source。结束后独立审计全部planned24/72、120文件240张量、误差与paired S−D/MF−D扰动/交叉项、参考语义、九门、费用和释放。

保持r1描述性双字段5%线，报告各场景/窗口/CFG/K全矩阵，dense自身漂移和来源扰动分开；无达标格也不事后放宽阈值。不同窗口/CFG相关，不把72格当独立样本，不从三个K推出连续寿命或统计交互。来源效应若继续小于共同漂移，优先简单S/D、age和刷新分配；不因模块多而推进H2。RV仍需同状态、同后缀、同预算的收益标签，不能由局部误差高直接训练Trust Head。

当前未新增GPU、闭环、视频、训练或人评。本卡也不自动授予第二泛化卡/H2/RV/训练；大预算改变、关键方法选择或真阻碍再交用户，常规准备继续自主完成。
