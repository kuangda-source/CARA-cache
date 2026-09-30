# W1固定跳步闭环准备：scalar-recent，原预算内

2026-09-30；状态FROZEN_CPU_MODULE_READY_RUNNER_NOT_IMPLEMENTED_NOT_GPU_RUN。进入依据为完整CAL8的MECHANISM_ONLY_CAL8、7/8联合改善；旧4工程点的负结果不改写。

## 唯一问题与冻结范围

在官方记录的相同完整计算位置，只替换近似器为scalar-recent（decay0、ridge1e-6、clip4、min_energy1e-12；不重新调参），候选自身状态演化是否可稳定完成8场景？额外校准成本和相对官方的视频差异如何？这只是固定schedule诊断，不能宣称在线调度更聪明、质量或干净速度收益。

[协议manifest](../manifests/w1_fixed_replay_protocol.json)hash绑定完整CAL8 runner/screen、原CAL24/input，以及所有8场景72call的真实full/skip/counter位置；原场景顺序/seed/93帧432×768/UniPC36点/WC70周期/eager/offload/guardrails和decode策略不变。misc原失败保留，不择优取子集。

运行顺序只有一个batch、一次model load：

1. 第一CAL AV运行新official fixed replay，必须与本轮旧OFF的72output/trace/cache/sampling/latent/rawdecode/safety/decoder identity/接受视频严格一致；证明force schedule接口没有改变官方行为。
2. 第一AV scalar OFF，再scalar ON隔离shadow。两条自身候选轨迹72output/trace/cache/latent/rawdecode/safety/视频严格一致；full/skip位置与旧官方一致，当前truth只评分、registered buffers/RNG恢复、分支和真实anchors隔离。首个candidate OFF计入8闭环样本，ON只作技术门，不当重复统计样本。
3. 前两门全部通过才继续剩余7个scalar OFF；任何未知/parity/非有限/轨迹错位技术错误立即停止。安全拒绝保留原分母，不关闭过滤或替换样本。每条轨迹输出实际计数、fallback/beta/过去anchors、哈希/阶段时间/peak memory；返回值异常也保留记录。

候选所有预测基于自身当前latent、condition、timestep与full anchors；trace只提供位置，不提供旧probe/residual/latent。自然判据仍计算并记录，但其决定被冻结位置替代；日志不得把“自然与冻结不同”当作自适应加速收益。候选不应把每次skip计算的近似值当真anchor。

## CPU实现证据与待做

`src/wcomr/fixed_replay.py`沿源码唯一anchor注入固定决策及execution校验，明确request/call、counter、模型/expert、horizon reset与past anchors。真实固定上游函数在CPU toy上验证：官方重放bitwise output/trace/RNG；自然阈值强制全算仍保持frozen skip；显式decay0；official/scalar自身闭环输入演化下OFF/ON output/trace/cache/RNG与controller记录一致；counter/模型切换/不可能early skip/不完整请求拒绝。24项针对性测试通过，[CPU回执](../reports/w1_fixed_replay_cpu_20260930.json)。这些不是CUDA/视频或候选有效性证据。

待实现完整generation runner及监督模式（沿既有锁/真实GPU归属/冲突停止/wall账本），逐视频finite output观测、source/hash/config与trace gates、全结果拒绝处理及终态summary。部署后Linux CPU checks、旧任务终态/锁/实际余额/GPU admission重新核验；新唯一run ID及目录，不能改写w1d-cal8-r1或共享上游。

## 成本与科学出口

从实测8OFF1592.147秒、firstOFF208.135秒、首点诊断29.090秒及此前batch其余187.111秒，预估10次generation合计2224.619秒；30%余量2892.004秒，冻结cap **3000秒/0.833333h**。剩余1.004955157h足够容纳cap，最坏余0.171621823h。校准额外reduce/clone与新比较成本未测，估计不保证全批完成；超时/技术失败按实际覆盖和账本收尾，不自动重跑或扩预算。

完整通过只证明固定schedule候选可运行及自身诊断无扰动；图像/视频相对WC差异是保真描述，不是物理正确性或质量增益。带逐call hashing/诊断的时间不能当干净部署性能；标准质量、clean重复计时、多阈值曲线和未调参确认仍待后续阶段。没有明确局部缺口时不加W2，不引入当前无必要的人评。
