# WC中间覆盖r2：算子样本齐全，跨阶段输入/完整状态门失败

2026-10-03，北京时间。run `wc-mid-coverage-r2`，卡 `WC-MID-COVERAGE-R2-20261003-A`，部署源码 `dac08aa8514b7ce671ef1b237d7e89b6a24e7a40`。原runner/supervisor均 `TECH_BLOCKED`、退出码1；不改原失败结论，不据局部输出一致解锁H0/H1。r1封存，其初始化门失败和172.900538秒成本见[70](70_WC_MIDDLE_R1_FAILURE_AND_REQUEST_GATE.md)。没有第三GPU窗口。

## 1. 已完成与未验收

固定调用25/26、35/36×层2..27，取得104/104个BF16 post-norm/RoPE QKV，312/312个dense、matched-full、sparse case。baseline与observed各完成18个UniPC更新、36次CFG网络前向；第13、18步各一次observed进程内快照恢复通过。完整视频没有生成或解码。

| 跨阶段门 | 结果 | 解释 |
|---|---|---|
| 36个网络输出哈希 | 一致 | 本次前缀输出字节一致 |
| full/skip trace与block counts | 一致 | 调用与块执行统计相同 |
| sampler时间网格与配置 | 一致 | 35请求、36有效solver步、WC70-call horizon保持 |
| 第13、18步完整状态指纹 | 两点均不一致 | 原runner在此抛错；没有字段级实际值，不能定位真实差异 |
| 36个网络输入聚合哈希 | 36个均不一致 | 原runner尚未执行到此门；CPU读取原回执后发现，不得遗漏 |

只能接受原始QKV和配对算子诊断的文件/成本审计，**不能接受跨阶段同输入、全部部署状态无扰动或正式分叉接口**。两次进程内restore通过不等于跨请求条件/闭包一致，更不等于独立可重启的整管线快照。

## 2. 局部算子诊断（部分可用）

固定sim0.1/cdf0.98、无PV、1warmup/3hot repeat。每点三臂输入文件SHA相同；真实dense输出始终返回原网络，候选只在shadow评分。CPU核验所有104个文件SHA、字节数、Q/K/V dtype/shape/finite/raw SHA及312条重复计时；没有新GPU重算误差。

| 调用 | 点数 | dense/sparse中位速度比 | RMSE≤5% | 速度比≥1.1 | 两项均过 |
|---|---:|---:|---:|---:|---:|
| 25 | 26 | 1.211 | 23 | 17 | 14 |
| 26 | 26 | 1.204 | 23 | 17 | 14 |
| 35 | 26 | 1.239 | 23 | 20 | 17 |
| 36 | 26 | 1.236 | 23 | 20 | 17 |
| 全部 | 104 | **1.215** | **92** | **74** | **62** |

matched-full相对真dense最大RMSE1.333%；sparse最大9.287%。层6、23、27各四个输入都超过5%误差；层27约8.90–9.29%，其约1.83–1.86×操作加速不能算保质收益。matched-full含量化/路由后端误差，不是真dense锚点。当前仍无统一全输入配置。

104点来自**一个已消耗的开发场景**，不是104个独立场景。它们只说明observed轨迹上的局部算子表现，不能拿未通过的跨前缀输入门作因果保证，也不能把操作加速换算成端到端视频加速。全部104行和失败筛查保存在[诊断回执](../reports/wc_mid_coverage_r2_diagnostics_20261003.json)，原失败summary保持不变。

## 3. CPU定位：确认控制缺口，实际差异仍UNKNOWN

原runner每阶段重置Python/NumPy RNG，没有重置Torch CPU/CUDA全局RNG。固定官方 `video2world.py` 的 `_get_data_batch_input` 执行 `torch.randint(16,32,(self.batch_size,)).float()` 构造FPS。噪声seed和独立solver Generator相同，不保证该随机输入或完整RNG相同。

实际Cosmos Torch2.7.1+cu128环境下，CPU执行固定官方FPS表达式：仅恢复Python/NumPy时两阶段FPS与输入哈希不同；CPU演示中net/solver/output/独立Generator等组件一致，仅`cpu_rng`组件不同，完整状态哈希不同。恢复同一Torch CPU RNG后整个CPU控制逐位一致。CUDA未初始化，5.544316秒CPU检查，GPU账本不变。本地6项新审计及原恢复/拒绝控制通过。

**这证明控制缺口存在，不能证明实际GPU运行只差FPS或cpu_rng。** 原回执只有两处总指纹和36个未命名输入总哈希；实际FPS、各net/cache/solver/RNG组件值或各命名输入哈希未保存，不能从SHA逆推差异。未删任何状态字段、未改变比较语义、未覆盖原source/stage/run/receipt/log。新增CPU工具只重审封存回执和列组件，不被原GPU任务调用。

下一CPU准备需完整恢复两阶段Python、NumPy、Torch CPU及全部CUDA RNG；保留官方随机FPS行为，不通过硬编码FPS消除差异。首次采样前冻结条件/CFG身份；命名记录所有输入和net/cache、全部非callable solver字段、latent、各RNG及独立Generator组件哈希，保留完整指纹和逐项拒绝门。补条件/闭包快照，避免把进程内恢复当正式反事实接口。

若发现纯诊断元数据，须证明其不被部署读取，版本化比较语义并独立重审；不能事后drop字段让旧r2变PASS。原证据不足时继续UNKNOWN。H0/H1仍等接口和数值/范围门及下一具体协调卡；累计余额不等于第三窗口授权。

## 4. 实际结算与释放

r2监督墙钟 **1064.1407573288307秒（0.2955946548135641GPUh）**，包括加载、两前缀、文件/诊断、失败和flush，未超过1200秒。累计 **4.255375150608726/12GPUh**、30jobs；余 **7.744624849391274GPUh**，无inflight，r1与原28jobs均保留。

supervisor2628242、timeout2628258、runner2628259均已退出；global `f1.lock`可取得；指定A6000 UUID的VRAM回到24MiB、compute apps为空。只释放自身任务，没有停止其他任务。权威账本保留supervisor原settled状态标签，审计另存，未改费用。

## 5. 证据与接续

- [原runner](../reports/wc_mid_coverage_r2_runner_20261003.json)、[supervisor结算](../reports/wc_mid_coverage_r2_supervisor_20261003.json)、[原失败summary](../reports/wc_mid_coverage_r2_summary_20261003.json)。
- [104文件/312重复/source/费用/释放审计](../reports/wc_mid_coverage_r2_audit_20261003.json)、[部分可用算子诊断](../reports/wc_mid_coverage_r2_diagnostics_20261003.json)、[实际CPU重审](../reports/wc_mid_coverage_r2_cpu_postmortem_20261003.json)。
- 原大张量留服务器 `outputs/wc-mid-coverage-r2/diagnostic/`，约39.8GB；Git只存小回执、SHA与路径，不搬大文件或连接凭据。

下一动作为CPU完善全状态/命名输入诊断与成本提案；不重跑W1/replay/build、不自动第三GPU窗口、不提前H0/H1或专家数据采集。[WC-RV](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)继续作为W3条件设计：先因果接口、同预算收益空间、短/终点标签可靠性，再考虑小Head。
