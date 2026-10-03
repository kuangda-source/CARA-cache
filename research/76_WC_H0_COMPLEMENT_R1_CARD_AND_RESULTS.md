# H0 首卡：同状态 C/S/D 互补性与真实整组成本

2026-10-03；卡 `WC-H0-COMPLEMENT-R1-20261003-A`，唯一候选 run `wc-h0-complement-r1`。状态：实际CPU26、source/assets/import/package与fresh准入通过，唯一run已启动，结果未定。用户 06:00:14UTC 授予继续自主推进常规同方向步骤，06:07:41 再确认继续实验；[本卡授权与边界](../manifests/wc_h0_complement_r1_authorization_20261003.json)。保留各项目累计12GPUh、已用历史，WC 优先，唯一协调与一个昂贵任务。r4 的单次授权已消耗，本卡来自后续继续指令，不重启 r4。

## 唯一问题与冻结范围

先回答：官方 WC 判为需要 full 的当前状态上，历史 C 是否明显偏离，固定 sparse S 能否以低于真实 dense D 的整组成本修复大部分偏差？这是一张 H0 局部诊断卡，不是来源×寿命 H1、分组 H2、RV、训练或最终方法验收。沿 [65 原计划](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)分步推进；历史 sparse 残差尚无合法存档，首次卡只比较过去真实 dense 来源 C 与当前 D/同后端 full/S，不能称完整三来源寿命实验。

样本固定为已有 CAL8 中第二例 `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191`，与 r4 第一例不同；仍为已经曝光的开发 CAL，不称独立 DEV/CONF。原模型、seed0、93帧、432×768、guidance7、UniPC-Karras 请求35/实际36网格、WC70-call horizon、probe2 与原所有 WC 判据不变。只执行 baseline/observed 各20完整solver更新/40CFG前向；不解码完整视频或部署任何候选。

在 call25..40 中，每个 CFG 分支只选第一个官方 full、resume 从当前 probe、且有两份严格过去同 CFG dense 历史的状态；选择只读已付费 probe 判据/历史，不读当前 dense 真值，不看稀疏误差挑点。冻结分母2 CFG×4臂=8臂，不因缺少 eligible full、失败或结果差增加 call/窗口；保留所有失败与已完成臂。若两 CFG 未齐，报告范围未完成，不挑另一个更有利输入。

三臂 deep layers2..27 内，layers6/23/27 固定 true dense 回退；其余23层 sim0.1/cdf0.98、no-PV、mask 每次从当前 Q/K 构造，保持 QKV/RoPE/MLP/cross-attention/输出头原样。回退来自 r4 所有12个局部误差失败位置的保守排除，并不保证另一场景安全，不逐层追着新结果调阈值。matched-full 与 S 共用路由/量化，回退层同样 dense；matched-full 不是 true dense anchor。

## 同状态与真值边界

C 在当前深层 dense 真值前，用官方原 Gamma+flow 分支及过去部署真实 full residual/window 生成。临时代理隔离 pinned branch 对 previous_input/internal 两列表的写入，预测不会把当前真值、未来指标或 shadow S 写入历史。D 仍是唯一部署输出与 cache 更新来源。

当前完整 deep group 从同一 probe/condition/embedding 重算 D、matched-full 和 S；每臂1 warmup+3 hot repeat，C代理构造及S/D模式dispatch在计时内，收费包含深层 QKV、MLP、路由/量化、attention、cross 与输出头；C 包含 Gamma/warp/输出头。每个 dense 重复须与实际当前 full hidden/velocity 逐位一致。记录 postwarp residual `Y-P` 和 velocity 的相对 RMSE，以及每臂三次 wall 中位数；每状态四臂在服务器保存 postwarp residual/velocity 原件、文件SHA/长度、张量shape/dtype/raw SHA，并以CPU独立复算误差；约1.2GB原件不入Git，只同步小回执/哈希。原件是本H0诊断的评分证据，不构成专家 TECH/FIT/CAL/CONF标签或训练输入。

独立 RNG 和 buffers 前/后恢复，shadow 执行不进入部署 block counts；原当前 WC cache-state 哈希必须不变。baseline/observed 共用官方 prepared input 与完整 RNG 转移，输入、输出、trace、块数、原状态指纹、采样、named input、condition、field signature 九门均逐项严格相等。state13/20 全组件进程内 roundtrip 继续保留；不宣称独立进程反事实 fork。

## 成功、停止与费用

先报告全部2个状态各臂误差与成本，不把两 CFG 当独立场景。局部互补筛查事前冻结：S 的 postwarp residual 与 velocity RMSE 都≤5%，S velocity RMSE≤C的75%，D/S完整 deep group+head wall≥1.05；零能量参考、非finite、任一控制/源码/条件/预算门失败停止并保留分母。筛查不通过只说明本卡局部未观察到互补区间，不升格为整个方法不可恢复失败，也不自动调阈值、启 H1/H2或第二卡。

[成本规划](../reports/wc_h0_complement_r1_cost_20261003.json)：r4模型加载107.930秒，baseline36-call前缀206.945秒按40-call折算229.938秒/臂；24次完整组 shadow 执行按5秒/次，C10秒、额外metadata/约1.2GB原件IO/完整状态签名70秒，加20%规划余量得到921.369秒，退出结算余量30秒，合951.369≤1200。5秒组 allowance 高于旧S0非重叠 deep components 下界2.722秒，但新场景/完整S成本未测，估计不是保证。

唯一候选 run 全cost硬上限1200秒（child1170/kill5，原监督释放与失败计账），预留1/3 GPUh，实际结算替换预留；从现4.710893751709566/12h、32jobs继续，余额7.289106248290434h不重置。source commit/config/payload hash、模型/guardrail/官方runtime/现有kernel package、实际CPU/import门必须通过；fresh GPU UUID/sm86/VRAM/compute、f1全局锁、无其它inflight及余额门通过后仅一次启动。没有新增预算、模型下载、重建内核、停止他人任务或改Clash。

## CPU 证据与执行状态

[官方 C 分支 CPU 门](../reports/wc_h0_cpu_interface_gate_20261003.json)：固定官方源hash，flow开/关与full/skip共48次配对调用，24次 C shadow 预测，skip与官方逐位相同、缓存/RNG未改；实际Torch2.7.1+cu128，CUDA未初始化。

[整组 shadow CPU 门](../reports/wc_h0_probe_cpu_controls_20261003.json)：flow开/关各20配对full，两CFG×C/D/同后端full/S实走，输出/cache/buffer/计数严格不变，true-D重复逐位一致、fallback与两个候选后端路径均实际覆盖，八份原件SHA/finite及CPU误差复算一致；非finite S失败保留固定状态分母和已完成四臂，并恢复模式/缓冲。使用synthetic attention做接口断言，不代表真实Sparse kernel/新场景GPU通过。Mac缺Torch，执行在已有Cosmos环境且CUDA禁用。开发时依赖路径与toy绑定失败保留task日志，修复后门通过；未GPU消耗。

实际部署、唯一启动、结果审计与结算回执待写本节；未以本规划宣称实验已执行。重大稳健质量-速度结果、明显方法负结果、跨方向调整或预算扩展回父任务讨论。

## 实际部署与唯一启动（非终态）

[部署](../reports/wc_h0_complement_r1_deployment_20261003.json)：source18e692ebb0f23a6ed832e0d7ff74ec3a6acc0ca9、26项CPU及全部source/资产/package/import通过，CUDA未初始化、账本不变；step13/20下一UniPC更新CPU逐位恢复。数据盘585783341056 bytes可用。GPU提交前源码已同步私有GitHub。

[唯一启动](../reports/wc_h0_complement_r1_launch_20261003.json)/[现场](../reports/wc_h0_complement_r1_start_observation_20261003.json)：supervisor2657420/timeout2657436/runner2657438已现场存活，初始化中。1200秒全cost/1170child、child起算最大截止北京时间15:08:40；预付1/3h，账本在途5.044227085042899h/33jobs，不是最终费用或方法结果。后续只跟踪本identity到终态、独立CPU原件复算及source/cost/release审计，不重复提交/改源码。
