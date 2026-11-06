# 共用官方prepared-input与完整状态：独立CPU修复 / r3最短前缀卡

2026-10-03。协调任务在r2封存后明确授权独立 `WC-PREPARED-INPUT-CPU-20261003-A`；CPU完整证明及source/资产/成本门通过后，条件授予 `WC-INPUT-STATE-PARITY-R3-20261003-A`，唯一run `wc-mid-parity-r3`。此前“不自行第三窗口”不限制本次明确授予的独立卡；**没有r4授权**。r1/r2 source、原FAIL、费用和回执永久保留，见[71](71_WC_MIDDLE_R2_RESULTS.md)。

## CPU合同

保存/恢复Python、NumPy、Torch CPU及初始化的全部可见CUDA RNG；请求内独立solver `seed_g`由现有StateRoundtrip单独完整保存。共享函数是官方 `_get_data_batch_input`：首次完整执行并深拷贝原batch，记录其请求/每个prepared字段签名及RNG前后状态；第二臂检查请求和准备前RNG一致，复用隔离拷贝，并重放准备带来的RNG状态转移。既不新抽FPS，也不硬编码FPS，保留官方模型/场景/采样方法。

命名记录网络所有位置/关键字输入（包括非张量参数）和实际CFG condition全部dataclass字段。记录完整原StateRoundtrip指纹及每个net/cache、全部非callable solver字段、latent、Python/NumPy/CPU/CUDA/独立Generator组件哈希；原input/output/state/trace/counts/sampling门全部保持。新CPU工具不改原r2比较语义。

回归覆盖隔离拷贝、错误输入与RNG拒绝、非张量条件变更、实际官方准备函数observer OFF/ON及原UniPC恢复后下一步逐位一致。实际官方prepare函数体在CPU控制中执行，GPU转移及text encoder用CPU模拟；该限制明确记录，不能称GPU准备验收。实际Cosmos Torch环境复核时CUDA禁止初始化；全部权重/Guardrail1/upstream/import/package字节门先通过，账本不变。

## r3冻结范围

仍为首个CAL8开发场景seed0、Cosmos-Predict2.5-2B、93帧432×768、guidance7、UniPC/Karras35请求。两个匹配prefix仅到**第13个完整solver更新/第26个CFG网络前向**：包含首个中间刷新CFG pair25/26，不到第二pair35/36，不重复采104点。

仅call25/26×layer2，2个QKV/6个dense、matched-full、sparse shadowcase，sim0.1/cdf0.98/no-PV/1warmup/3repeat，触发与r2相同真实observer路径；dense输出始终返回，shadow不写部署cache。第13步记录全部字段并检查observed进程内恢复。没有完整解码视频；不做H0/H1/RV/专家数据或训练。

判定要求26个原输入/输出哈希、命名输入、26个完整condition、trace/counts/sampling、全状态指纹及所有组件全部一致，prepared隔离batch/RNG转移一致，2QKV/6case完整。任一差异保留字段级原因并失败，不删字段或事后调门槛。第13步后没有实际续推，因此不称完整因果分叉接口，也不自动解锁H0/H1。

## 监督/停止/成本

累计cap12GPUh，r3前权威已结算4.255375150608726h、30jobs，余7.744624849391274h；历史费用不重置。单卡GPU全过程wall≤1200秒含加载/失败/诊断/flush，1170秒child、kill-after5秒。唯一新stage/output/supervisor，fresh UUID/VRAM/compute、shared f1.lock、无inflight、余额与15秒结算余量；只停止自身任务。

部署先CPU/资产/hash通过，再fresh准入。启动不报结果，持续跟踪同一identity直到终态、原PIDs/锁/GPU释放及实际账本结算。raw/source/fieldwise/成本独立审计后再报技术门结论。失败不自行r4重试。原QKV大文件不入Git，只存小回执/路径/SHA。

## 实际CPU/来源门回执

部署source `4bd3b72ef68b90d0eb3eb833e8f452c2b7149aa4`，实际Cosmos Torch2.7.1+cu128下17项CPU控制（含固定官方prepare OFF/ON和UniPC恢复后下一步）通过，CUDA未初始化、权威账本不变。source/资产/import/package全部字节门通过；[部署回执](../reports/wc_mid_parity_r3_deployment_20261003.json)。剩余disk626.300GB与global锁可用只是CPU准备证据，GPU仍须fresh准入并跟踪终态。

## r3终态

独立[73结果](73_WC_MIDDLE_R3_PARITY_RESULTS.md)已完成严格最短前缀技术门、实际成本和释放审计；r2原FAIL保留。没有r4授权、H0/H1或RV自动解锁，当前不新增GPU任务。
