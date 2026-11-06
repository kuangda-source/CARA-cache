# 在线阶段D/D独立通过，少步网格CPU确认

2026-10-04。承接[100原八输出卡](100_WC_ONLINE_STAGE_EIGHT_OUTPUT_EXECUTION_CARD.md)。原source `3ad34e10475ab525190bf12a21f46ec8e525385c` / `wc-online-stage-r1` 继续运行，未改冻结stage或再次提交。当前完成D/D两输出，六测量及四候选指标待完成；科学goal保持active。

## 原D/D完整视频与来源审计

[第一官方视频](../reports/wc_online_stage_r1_first_D_audit_20261004.json)已独立完整解码93帧，36更新/72CFG/prepare1及完整pipeline、历史common D SHA相同。单臂检查不接受成对九门，历史partial回执SHA fd95…8874保留其身份。

[独立D/D审计](../reports/wc_online_stage_r1_dd_audit_20261004.json)重新计算九项：input/output hashes、trace、block counts、state fingerprints、sampling、named inputs、conditions、field signatures，全部相等；13/21/33/35/36五检查点各1216项组件指纹和共享eval模式通过。prepare、sample/decode、视频guardrail、save、flags/RNG及完整pipeline也一致。

关闭S的在线适配器来源/CFG/epoch/真D窗口/native70清空和尾dense独立通过；不读未来掩码，不覆盖原生skip判定。两视频均531916 bytes、93帧432×768/16fps完整解码，SHA `fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379`，与历史common官方WC完全相同。[逐帧CPU指标](../reports/wc_online_stage_r1_dd_metrics_20261004.json)RGB MSE=0、SSIM=1、92个转移的temporal difference MSE=0。

这证明当前关闭S的适配器控制，不是候选质量、跨输入泛化或Native接受。两D/D wall339.843842/324.357021秒包含严格观察开销，不能拿两者差值当稀疏加速。D/D只占八分母中的2，不改为全卡完成。

[回执快照](../reports/wc_online_stage_r1_dd_snapshot_20261004.json)/[原件gzip](../reports/wc_online_stage_r1_dd_runner_20261004.json.gz)：raw2635196 bytes，SHA `42242a72782564e43de77c50563e9b926e4328cbae25574a23a801f42d15f969`；gzip108934 bytes，SHA `9cb4aea88088301aeab8aa6f3e21418270a52f39afeadb69bd9cc46048515ba0`。独立分析目录与原stage分离；后续终态回执另存，不覆盖D/D原件。CPU审计1.178秒/逐帧8.825秒、预算未变，没有新增GPU。

## 必需少步基线的一项CPU前提

[检查入口](../scripts/check_wc_fewer_step_schedule_cpu.py)/[实际CPU与原件复核](../reports/wc_fewer_step_schedule_cpu_20261004.json)：官方固定model/scheduler两源SHA及真实constructor（num_train_timesteps1000、shift1、dynamic=false）绑定，禁止CUDA、不加载权重，在同一官方UniPC上验证35→23→35请求的Karras网格。

35请求对应36实际grid/update；**23请求对应24实际grid/update**。timesteps int64、sigmas float32/CPU/末端0、每次step index/begin index/model_outputs/last sample/lower-order reset通过；常量velocity toy全部更新finite，前后35网格与toy结果完全相同。实际CPU15.452405秒，服务器原件SHA `517752d70044f7d602d7836920d066fe9fa5e11ec2b94e88e462e93bca694046`、脚本和两官方源及全部行独立复核通过，原账本保持。

这是scheduler CPU前提，不是Native23完整管线/真实CFG48/权重前向、视频、质量或速度证据。Native完整/少步入口与同mode/pipeline parity仍未实现；不能用grid计数按比例折扣完整成本，也不能把不同网格当同状态误差。旧99成本草案保留原身份，后续完整基线应以24实际更新记录23请求，并另测权重管线。

## 当前运行与下一步

原三句柄supervisor2758008/timeout2758025/runner2758027现场live且命令行匹配；D/D通过后第一common官方测量已开始。原3600全cost/3570child/kill5、八分母和每请求历史D桥止步不变。已结算9.136838727254782h/42历史jobs，含预付10.136838727254782/12h、43jobs，未预留余1.8631612727452183h；实费与释放须原卡终态后核对。

继续跟踪原八输出至终态，再独立每臂真实在线窗口/频率/来源/核/八视频、原件源码/费用释放和全部四候选指标。暂不选下一GPU卡、训练或人评。只有可用在线保真与成本信号才继续完整Native/少步/三WC阈值/stage前沿；CONF和语义/物理仍待，后续费用在本卡实际结算后重算，不缩矩阵或重置预算。

[现场1791072053.8974915](../reports/wc_online_stage_r1_live_observation_20261004.json)：原三句柄live，common官方测量正常返回36更新/72CFG/prepare1，wall198.348480秒，原卡3/8；第一在线window候选正在生成，完整四候选指标待结果。预付未变，不用单官方wall作加速结论。
