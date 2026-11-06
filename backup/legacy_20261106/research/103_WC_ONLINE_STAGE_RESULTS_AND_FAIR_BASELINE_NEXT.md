# 在线阶段八输出终态：保真改善有信号，质量保持加速尚未成立

2026-10-04。原 `wc-online-stage-r1` / `WC-ONLINE-STAGE-R1-20261004-A` 退出0，冻结执行 source `3ad34e10475ab525190bf12a21f46ec8e525385c`，八输出全部完成。仅沿原 supervisor2758008/timeout2758025/runner2758027 跟踪至终态，无重提或替换输入。

## 完整技术证据

[独立八视频/来源审计](../reports/wc_online_stage_r1_audit_20261004.json)、[费用/源码/释放审计](../reports/wc_online_stage_r1_terminal_20261004.json)、[全部四候选指标](../reports/wc_online_stage_r1_metrics_20261004.json)、[可重算汇总](../reports/wc_online_stage_r1_summary_20261004.json)。前两D/D严格九门、五处各1216状态组件与完整pipeline通过，93帧完整RGB/temporal相等；六测量每臂36更新/72CFG/真实prepare一次，93帧768×432/16fps完整解码。51文件payload、CPU/source/assets、真实稀疏metadata、来源/CFG/epoch/真D隔离、窗口/逐CFG频率和native70尾dense独立通过。

整卡[原始回执gzip](../reports/wc_online_stage_r1_runner_20261004.json.gz)/[归档清单](../reports/wc_online_stage_r1_eight_snapshot_20261004.json)：解压原件4412506 bytes，SHA `3a644b3669afe3b08c2e7dea0a320277345456cbd4ea7e8c5c4a8aaa5bef24f5`，gzip 149617 bytes，SHA `f81b49d1ed404d0dc52ceaf7baf43c0fec05d63c920d4154187afb27a1382f45`。早期[独立D/D快照](../reports/wc_online_stage_r1_dd_snapshot_20261004.json)保持其4224…f969身份，不用终态覆盖。视频与大张量保留服务器；Git仅小回执、代码、配置和文档。

## 全部四候选结果

参考均为各自**官方自适应WC**，不是Native。common参考wall198.348480秒/35deep，human参考208.100152秒/38deep。完整wall包含必要选择、来源、真实核、首次S、prepare、采样、解码、guardrail与写入；D/D额外观察费用不进入六测量比较。

| 曝光CAL | 在线策略 | 实际S/算子 | 实际deep CFG | 93帧luma SSIM | RGB MSE [0,1] | 完整wall秒 | 相对WC耗时减少 |
|---|---|---:|---:|---:|---:|---:|---:|
| common | stage_every1 | 6/138 | 35（WC 35） | 0.963415 | 0.000518952 | 197.231 | +0.564% |
| common | stage_every2 | 4/92 | 36（WC 35） | 0.962969 | 0.000529415 | 200.564 | -1.117% |
| human_199 | stage_every1 | 9/207 | 38（WC 38） | 0.927613 | 0.001809357 | 205.949 | +1.034% |
| human_199 | stage_every2 | 5/115 | 37（WC 38） | 0.916786 | 0.002333532 | 204.754 | +1.608% |

common两候选motion幅度比约1.00282/0.97078，human约1.00189/0.99894；human每次刷新与低频版本的temporal MSE分别0.00304952/0.00398824。运动幅度接近不证明动作、物理或语义正确。全部四候选均保留，不按指标删场景或只报最优输出。

human every1输出SHA `92344543aae6818ec52a313c7d2488ee68dfd00efb5270f5f9fb6b50a71c9149` 与[旧固定掩码E0L0](98_WC_TIMING_FACTORIAL_RESULTS_AND_EARLY_PROTECTION_NEXT.md)相同；参考SHA、9个S call和全部整视频指标逐项复核相等。说明这个曝光输入的简单在线窗口复现了该**编码输出**，没有证明所有内部状态或全部输入上的离线/在线等价。相较此前全组full-S人物SSIM约0.726741，本次约0.927613是保真改善信号；它仍偏离官方WC，不是质量保持接受。

每次刷新候选的单次耗时减少仅0.564%/1.034%。common低频版本反而增加1.117%，human低频减少1.608%但SSIM更低0.916786。固定顺序各一次不足以排除时间噪声，不能将这些比值作为稳定加速或质量—时间前沿优势。

## 原生反馈与窗口后的近似来源

common every1实际S45/46、49/50、53/54；every2只有45/46、53/54，却在call70(step35 CFG1)将官方cache变为full，deep35→36。human every1实际9S/deep38，完整full/cache判定与官方一致；every2实际5S，在call56(step28 CFG1) cache→full、57/58(step29双CFG) full→cache，deep38→37。频率干预会改变后续轨迹，因此少S不是少总计算或更高保真的保证。

窗口23–27只限制新增S；common两个候选仍在call57/58(step29)读近似来源，human every1在call56(step28)、every2在call57(step29)读近似来源。没有立即清空原生forecast历史，也没有安全寿命保证。

这些是同曝光CAL/seed的完整策略轨迹差异，**不是同一个实际状态上的单步F/C反事实**，不能拆出即时/传播贡献，不能将额外full或少一次deep解释为RV收益标签。RV/Head/LoRA保持后置，无训练、付费评分或新增人工评审。

## 实际费用与后续预算

全wall **1995.244912413秒 = 0.554234697892 GPUh**，3600秒预付已替换为实费，未重置历史。权威现场账本 **9.691073425147/12 GPUh、43jobs**，余额 **2.308926574853h = 8312.135669秒**，无inflight。原三PID不存在，全局f1锁可获得，指定A6000回到24MiB/no compute；935 monitor行峰值26766MiB，无其他进程。终态后CPU结构审计4.607秒、四候选指标26.912秒，期间GPU账本逐字节不变。

保留[99完整强基线草案](99_WC_ONLINE_STAGE_CPU_AND_FAIR_FRONTIER_BUDGET.md)的六工作点，不削减Native、少步或调阈值对照。按原保守完整成本，14输出fair CAL拟cap6300秒和6输出新CONF拟cap3000秒分别可单独容纳；二者9300秒+15秒门比当前余额多 **1002.864331秒（约0.278573 GPUh）**。这不是实际运行必然超额：先序真实结算退款可改变后序准入，但当前不能同时承诺两张卡。自动语义/物理、更大CONF和重复计时成本仍UNKNOWN，不能默认免费。

## 下一步与当前决策

继续WorldCache，暂取every1为**CAL选择的公平比较候选**，不是方法接受或独立确认；低频版本保留负面/混合结果。下一优先CPU完成Native35请求/36实际与Native23请求/已实测24网格的完整生成入口，以及WC0.04/0.06/0.08与候选的共享设置、prepare、完整pipeline和parity。当前只确认少步scheduler CPU，不追认为完整Native入口或GPU视频。

完成入口和实际源/CPU/成本门后，才另选并冻结公平14输出卡、fresh资源/账本准入；尚未选下一GPU卡或预付。届时按实费重算CONF，不删强基线、改CONF定义或扩额掩盖资源缺口。当前自主科学goal保持active，完整质量—时间前沿、独立CONF和语义/物理结论均未成立。

原[75单次104点补验](75_WC_FULL104_R4_CARD_AND_RESULTS.md)授权已执行；[本次只读原件复核](../reports/wc_mid_full_r4_completion_recheck_r2_20261004.json)确认四份回执SHA不变、104QKV/312case、1153.547616秒≤1800与旧PID退出，无重提交或重扣费用。
