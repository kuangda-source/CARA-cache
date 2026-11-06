# P-ACR完整H1父轨迹接口与下一轮真实报价设计

2026-10-15，接续428；冻结A/H1和417/420/423/424科学结果保持。本轮仅新增CPU接口验证和生产范围准备。**02:22完成R3终态查收和独立验收，完整32路径/48状态/528诊断接受；原CPU817370结束，370.9358秒，预算SHA不变，GPU0。** 新生产重复/报价层仍待，不把本层当真实模型收益。

## 本轮要完成的能力

新单支执行器已经通过80个原语用例；本轮将它接到完整H1父轨迹，在当前真实使用的同一Toy状态上非提交地执行 C/A/D、Pc/Pu，然后恢复物理缓存、solver、RNG、condition及完整部署状态，让原H1继续。

CPU注册范围为两flow×四Toy提示词×两种合成来源情形×普通/诊断父路径，共32条完整路径；48固定状态，每状态3次CAD、Pc/Pu各1完整预热和3正式试次，共528额外pairs、1152普通pairs、总1680pairs/3360CFG。恢复后36 guided、动作、A历史、终态和mock视频与普通父路径逐项对照。它验证接口与恢复，不执行真实权重，也不产生视频保真或加速结论。

## 已保留的技术失败和修订

R1 source c9ae286/1531文件、CPU806131已结束，83.1286秒，支持守卫拒绝强制动作，完整32未接受。R2 source5baae20、CPU813648已结束，42.6171秒，进一步定位step29的旧P出生于22、age7，因此原rho校准不支持。两轮预算SHA前后一致，GPU0；原stage/回执不覆盖。

R3在执行前登记两种合成来源情形的C_scale1e9；正且很便宜/很贵的P出生误差区分P工作源与D源，保持同一固定12/23/29/30位置和原age1–6域。这是CPU夹具的高风险输入，不是修改真实H1的模型、lambda、表或策略。另有四项独立scalar guard通过：保护拒绝、age7拒绝、支持A决策不提交、未来步/非CAD拒绝。没有用扩大校准表或放宽守卫消除失败。

R3 source6ef228e，唯一CPU817370，独立stage wc-p-acr-full-h1-parent-cpu-r3-20261015；1532文件绑定Git版本与既有生产runtime，禁止CUDA初始化、下载和weights load。02:09:07单次提交，预计5分钟，02:14:07以后一次查收；未结束时按原句柄重新估时，不重复派发。

## 完整查收与独立验收

02:14按预计时间首次查收：原CPU817370仍运行，1532源文件一致，尚无终态结果。一次补充余量读取在02:15:46见16个普通父trace和32个mock视频文件，预算当前SHA仍一致；这只是文件/进度，不升级为32路径或恢复验收。

按剩余终态检查与封口余量，重新安排**02:20:00北京时间（unix1792002000）**一次查收，自动化`p-acr-cpu`已创建，仅接受此原CPU句柄，完成后暂停。旧F/B和旧GPU自动化保持暂停。本轮结束，不持续轮询。02:22按重估时间一次接受原终态，source6ef228e/1532源一致，两flow各16完整路径、24状态、264额外pairs，共32路径/48状态/528额外/1152普通/1680总pairs/3360CFG，全部恢复与36guided/actions/A_history/final/mock视频对照通过。数值测试341.4803秒，全bundle370.9358秒；原进程817370已结束，预算前后SHA一致。16组对照逐项独立核对，未用mock文件数替代验收。`p-acr-cpu`已暂停。

## 下一轮实际生产报价

新生产报价建议另登记：4普通H1父＋4诊断父、12原H1位置；每位置C/A/D/Pc/Pu各1预热＋3正式，完整528真实pairs/1056CFG，一次加载。数值恰与本轮CPU额外试次数相同，但分母与硬件完全不同，不能混淆。

此生产范围增加CAD的全部重复与顺序对照；当前CPU原型CAD各1次，因此还需要生产版CPU验收。详见[完整范围与报价边界](p_w3_e0_20261014/PA12_Production_Controls_And_Price_Scope_20261015.md)。D/P来源A额外head不同，单支价格包含两个probe、A与D实际heads、RF及补偿；原型取证timer与后续clean报价分列。旧PA1.5GPUh是建议额度，尚未完成本卡模型加载/全部父路径/恢复/I/O/余量forecast，不用它冒称成本。

Pc/Pu的0/1/抵消系数和oracle可从真实同状态分支张量离线计算，不声称这些离线版本已独立计时。历史差分只读过去普通DD，shadow teacher不能进入历史。来源保持ACR_READOUT；未实现ACR_REFRESH，不把velocity修正当合法hidden源。

## 研究设计的最新安排

1. **保留并行的论文主干。** A/H1已有实际终点与归因证据；正文组织、强基线素材和最终测试清单可继续，不等待增强方向全部成功。
2. **先回答新P的真正费用与位置价值。** 当前依据是旧pi0的局部系数结果和已接受的执行原语；完整父接口接好后准备真实PA12，不直接扩大闭环。
3. **W3按真实数据缺口推进。** 全36步pre-action probe/来源/实际sigma与同状态C/A/D标签分库；PA12只是四旧CAL的有限检查，不能代替8开发提示词×8位置。先按提示词分组比较T1当前特征、T2因果趋势的合法动作regret。
4. **必要时做六配置配对闭环。** Native、H1_ORIGINAL、H1_CAD桥接、Trend、ACR和组合，保留全部对照与真实费用；有终点/费用价值后才讨论合入。
5. **论文正式补验保持待办。** 强调过的WC/RA/少步Native基线、同26D简单刷新、真正独立共同测试、三轮测速与部署/质量，仍是后续模板而非已完成卡。

F/B已结束且独立归档，旧13h P卡暂缓、E2旧具体审批未取得；不恢复旧自动化，不训练生成器/LoRA或引入人评。新GPU仍停止，新增8GPUh提案不是许可。原窗口cap104.971363333、最后核验余24.974985961保持，本轮预算SHA不变不扣费。

证据：[R1终态](../reports/wc_p_acr_full_h1_parent_cpu_r1_collection_20261015_0158.json.gz)、[R2终态](../reports/wc_p_acr_full_h1_parent_cpu_r2_collection_20261015_0207.json.gz)、[R3启动](../reports/wc_p_acr_full_h1_parent_cpu_r3_launch_20261015.json)、[R3首次查收](../reports/wc_p_acr_full_h1_parent_cpu_r3_collection_20261015_0214.json.gz)、[同次余量记录](../reports/wc_p_acr_full_h1_parent_cpu_r3_remaining_work_20261015_0216.json.gz)、[4项守卫](../reports/wc_p_acr_h1_probe_support_guard_cpu_20261015.json)。

最终证据：[R3终态查收](../reports/wc_p_acr_full_h1_parent_cpu_r3_collection_20261015_0222.json.gz)、[独立scope验收](../reports/wc_p_acr_full_h1_parent_cpu_r3_independent_acceptance_20261015.json)。
