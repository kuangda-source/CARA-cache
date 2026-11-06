# WC-MID-COVERAGE-PREP-20261003-A：中间刷新与全深层覆盖

2026-10-03；累计12GPUh已授权；本卡单次GPU监督墙钟上限1200秒，子进程1170秒截止、5秒强杀余量，余额及资源现场重核。CPU准备限2小时。新run候选`wc-mid-coverage-r1`，不重跑任何旧launch/build/W1/replay，不训练或抢跑RV。

本卡终态：[r1初始化门位置错误/0覆盖与失败结算](70_WC_MIDDLE_R1_FAILURE_AND_REQUEST_GATE.md)。原source375261a与配置保持历史身份；当前仓库已准备首次请求前向的生命周期门修正，但没有第二GPU提交。以下是本卡原预登记范围，不能写成已实现的GPU覆盖。

## 冻结范围与控制

沿用S0第一个CAL8开发场景`av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632`、seed0/93frames/432×768/guidance7；官方WC近似器与probe保持。UniPC/Karras请求35步、实际36步/72CFG调用、WC70-call horizon保持，仅在第18个完整solver更新（call36）后主动结束。因此没有完整视频、decode或视频质量评价，不绕过安全管线生成输出；文本与输入检查正常执行。

S0原trace中首个首调用≥17与≥35的完整CFG对分别为25/26、35/36。预选这4次实际deep刷新×layers2..27，104个post-norm/RoPE BF16 QKV，形状`[1,31104,16,128]`。如果新运行的原官方路径没有这些完整计算，保留失败，不换好位置/强制改变跳步。

同一次加载内两段新prefix：baseline不做QKV/sparse诊断，observed采集并做shadow。两段都记录36次输入/输出hash、实际深层执行trace、完整时间网格、call26/36之后solver-state/cache/output/RNG指纹。两段相同配置/噪声与原近似器；比较全prefix输入/输出与state指纹，不仅比末尾误差。已有历史结果用来锁定入口，不重跑旧任务。

observed的104输入各比较dense、同后端匹配routed-full、sparse（固定sim0.1/CDF0.98、no-PV）；1warmup/3热repeat，312个算子case。full与sparse共同支付路由/量化，仅mask执行不同。当前真实dense输出始终原样返回，shadow结果仅评分；完整QKV文件+raw hash、逐arm结果/输出hash/热repeat持久化。技术筛查沿用RMSE≤5%、dense/sparse≥1.1×，不事后放宽，不把算子加速当视频收益。单个场景、4相关调用不是104独立场景。

## 状态恢复与实现边界

在第13/18个完整solver更新之后抓取全部scheduler非callable字段、明确列举的两路WC缓存/计数/窗口、最新latent与Python/NumPy/CPU/CUDA RNG，以及传给solver.step的独立seed_g状态。observed执行深拷贝restore，并比较原指纹、继续生成后的prefix；CPU负控制主动破坏两路cache、solver历史/额外字段、全局及独立generator RNG，确认恢复。方法包装callable单独保留，不作为数值状态。

这只验收当前进程内、原conditioning/closure保持时的cache/solver恢复。尚不提供可跨进程独立续推的完整pipeline分叉，也未构造H1的三来源×K轨迹；H0/H1仍需各自具体卡与条件/缓存兼容检查。局部dense不是Native全轨迹，量化full不是真dense anchor。

## 来源、成本与停止

复用S0资产校验函数，但只作checkpoint/guardrail/runtime/sampler及场景身份门，不执行旧750秒卡。新runner/supervisor按12h权威账本与新source/input配置核验；旧硬编码4h脚本不launch。Sparge现有sm86构建和实际import回执按hash复用，不重建。新stage独立，只写新输出，不改upstream/runtime。

预计QKV约39.8GB，预留至少80GB可用磁盘；当前只读现场约666GB可用，但提交前重核。历史S0两完整阶段总611秒；本卡减少decode/末尾，增加92个QKV及新shadow，估计800–1000秒而非保证。1170秒子进程硬截止、累计12h和1200秒本卡上限先于科学完成；超时/拒绝/部分/非finite/恢复或prefix不一致全部保留，不自动重试。计load/hash/IO/JIT/失败/flush总墙钟，热算子测速不作端到端速度。

首个card结束后核对source/payload、全部输入raw/hash、全部repeat/结果、计费、原PID退出/锁释放及资源归属。只报告覆盖与数值/接口技术结果；再提出H0/H1最有信息的下一卡，不自动跑完整路线。
