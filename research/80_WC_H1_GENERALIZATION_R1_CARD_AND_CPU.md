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
