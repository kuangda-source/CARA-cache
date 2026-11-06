# 早期×晚期稀疏刷新：缺失两臂接口与 CPU 验证

2026-10-04。承接[95 真实六输出结果](95_WC_FORECAST_PLACEMENT_RESULTS_AND_TIMING_FACTORIAL_NEXT.md)，完成两种缺失对照的生产核心接口、当前版本 CPU 回归与原件源码绑定。没有新增 GPU 提交、预付、人物视频或质量结果。现累计 **8.67188491753794/12 GPUh，41 jobs**，余 **3.3281150824620607 GPUh**，无在途任务；科学 goal 保持 active。

## 原 104 点单次授权已完成

[75 原执行结果](75_WC_FULL104_R4_CARD_AND_RESULTS.md)对应用户直接授权的七份文件、CPU 验证与最多 1800 秒的唯一 `wc-mid-full-r4`。该任务在 10 月 3 日完成全部 104 QKV / 312 算子 case、九门与状态恢复审计，实际 **1153.547615806 秒**已计入原 12 GPUh 账本。不能把当前对同一授权的恢复视为一次新的重复提交。

本轮[只读终态复核](../reports/wc_mid_full_r4_completion_recheck_20261004.json)重新读取服务器原 supervisor、runner、日志及监控四份文件，SHA 与原独立审计完全相同，104/312 完成数及原三个 PID 已退出再次确认。没有重新运行算子或重读约 39.75 GB QKV。64/104 同时通过局部误差和速度筛查、层 6/23/27 不适合统一配置的原结论保持；这不是视频质量或端到端加速接受。

## 缺失两臂的明确合同

上一轮的首次 S 匹配与自由位置两臂共享 9 次 S，只把 call23/24 换成 call55/58。本轮将早期 E 和晚期 L 是否使用 S 分开；其他刷新位置、深层组、原生缓存机制和共同 full/cache 掩码保持。

| 因子组合 | 稀疏调用 / 每 CFG | 算子数 | 状态 |
|---|---|---:|---|
| E0L0：共同 9 次 S | 9 / 5,4 | 207 | 缺失臂；当前只有 CPU 接口和来源图 |
| E1L0：加入早期 23/24 | 11 / 6,5 | 253 | 上一轮已实测，首次 S 匹配 |
| E0L1：加入晚期 55/58 | 11 / 6,5 | 253 | 上一轮已实测，自由位置 |
| E1L1：早期和晚期都加入 | 13 / 7,6 | 299 | 缺失臂；当前只有 CPU 接口和来源图 |

当前 `run_selective_output(..., comparison='timing_factorial')` 单独声明不同臂的逐 CFG 配额。先严格官方 D / fixed-D，再轻量 fixed-D / legacy SD / E0L0 / E1L1，总计六输出。D/D、历史 D 和 legacy SD 不复现时停止新臂；失败保留六分母及此前输出。默认 layer/cadence 和旧 forecast_placement 的同预算检查保持，并用当前函数体重新回归。

新增 `validate_timing_factorial` 要求：legacy 为同全层组 every2；两新臂为不可变显式 CFG 序号；共同臂不含 first；both 只添加每 CFG 的 first 和一个在共同臂最后刷新之后的位置，配额分别为旧 legacy 的减一与加一，并受当前掩码范围约束。结构合法不等于已经冻结人物执行卡；[原人物草案](../manifests/wc_timing_factorial_draft_20261004.json)和两已实测臂的原始来源复现保持不变。

## 当前源的实际 CPU 证据

[服务器 CPU 原件](../reports/wc_timing_factorial_sampling_cpu_r1_20261004.json)在 Torch 2.7.1+cu128 环境用 **186.972710 秒**完成：

- 旧 selective 六输出 14 项回归，以及旧 forecast placement 8 项回归。
- 新 timing factorial 8 项：flow OFF/ON 各完整六输出、D/D 掩码不符、E0L0 核 nonfinite、历史 legacy SHA 不符。
- 当前控制器入口拒绝 25 项：旧位置 8 项、新因子 17 项，拒绝错误配额、first/late/共同集合、越界、CFG、层组、legacy cadence、错误模式、SHA 或已有身份；状态未改且未开始任何 phase。
- 纯策略 unittest 4 组，包括 19 个拒绝子例、非对称 CFG 配额和冻结人物缺失臂的 207/299 算子数核对。

新完整路径每臂一次 prepare、36 solver 更新 / 72 CFG，固定实际 toy 掩码，三份 D 产物一致；legacy 的采样返回、解码、guardrail 返回与写入前实际张量 SHA 和先前同场景 CPU 路径一致，避免 mock 编码饱和掩盖回归。新两臂实际来源图与离线图逐项相等、逐 CFG 配额正确；真 D 历史隔离、native70 清空、尾 dense、counter snapshot/restore 和错策略拒绝、所有 hook/forward/模式/buffer 清理通过。非完整场景保留两或四个此前产物和原六输出计划。

[独立 CPU 原件审计](../reports/wc_timing_factorial_sampling_cpu_audit_20261004.json)另行读取服务器原 receipt、console、42 份 stage 文件及 5 份固定 Cosmos 源文件，确认与当前本地文件及记录的 SHA 完全一致。此次当前源覆盖新增模块和已改控制器；不拿旧 e5e5 控制器的 CPU 证明替代新函数体验证。原 CPU 报告及已部署 GPU stage 都保留，没有覆盖旧原件。

全部 CPU 运行禁止 CUDA 初始化，使用固定官方函数体配合明确的 toy 模型、CPU stand-in 核、mock 解码/写入边界，未加载实际生成器权重。**toy 配额为 legacy6 / neither4 / both8，人物为 11 / 9 / 13，两者不能混用。** 账本运行前后保持；没有真实人物缺失臂、稀疏 CUDA 核、视频质量或耗时证据。

## 下一步与研究边界

继续 WorldCache。下一常规步骤是两缺失臂的独立 runner / scope / 监督器和完整成本规划，再冻结新身份与源码；实际准备需核对本轮 CPU 原件、原视频和两已实测臂 SHA、共同条件/RNG/掩码、官方 prepare / native-meta、资产和 import，之后 fresh UUID / VRAM / compute / 全局锁 / 无在途预算 / 磁盘准入。当前没有选定下一 GPU 卡、部署或预付；不复用原 104 点或 forecast 卡。

分析目标仍为有符号的早期条件效应、晚期条件效应及交互，使用完整轨迹的最终保真损失。四组 S 次数不同，不能称等成本前沿；位置介入包括即时近似与后续传播，不能分解成独立缓存误差或 budget-matched RV 标签。上一轮 SSIM 0.927207 的保真改善保留为单曝光场景、未来掩码 oracle 的机制证据；Native/少步/调过 WorldCache、独立确认、语义物理质量及稳定加速尚未接受。不扩场景、启动训练或引入人工评审。
