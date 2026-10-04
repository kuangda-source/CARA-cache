# 公平卡D/D与首个Native35实际输出：独立技术审计通过

2026-10-04。承接[105十四输出执行卡](105_WC_FAIR_NATIVE_TUNED_WC_FOURTEEN_EXECUTION_CARD.md)。冻结GPU源1a22ac6，仅原 `wc-fair-cal-r1` 在运行，未新增GPU提交或改源。本轮完成D/D及首个Native35独立审计，**不是完整公平矩阵、质量保持加速或CONF结果**。

## D/D两份控制输出

[独立审计](../reports/wc_fair_cal_r1_dd_audit_20261004.json)核验九门和完整pipeline，五检查点13/21/33/35/36各1216状态组件、逐输入/输出/条件/轨迹/采样/RNG与全部模块eval标志一致。两臂各36更新、72CFG、prepare1，deep35；关闭S的阶段adapter来源/窗口/native70/true-D历史隔离独立通过，没有实际S算子。

两93帧432×768/16fps mp4完整解码通过，SHA同为 `fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379`，各531916 bytes，复现历史common官方WC输出。[逐帧CPU指标](../reports/wc_fair_cal_r1_dd_metrics_20261004.json)10.217秒，RGB exact equality、MSE0、lumaSSIM1、92转移时序MSE0、运动量比1。指标计算期间原GPU预付账本不变。

两控制wall351.034476/343.231146秒包含诊断观察器，不进入六工作点的速度比较。D/D这里验证的是WC官方路径与S关闭的候选adapter等价，不把deep35称作Native完整计算。

[独立原件快照](../reports/wc_fair_cal_r1_dd_snapshot_20261004.json)/[压缩原件](../reports/wc_fair_cal_r1_dd_runner_20261004.json.gz)：原JSON2636749 bytes，SHA `e027b826c38c8b97e92f894518d1c2d670a255094064d38b9a617854ec9437ed`。D/D快照单独保留，不用后续Native或终态回执覆盖。

## 首个Native35实际输出

[独立部分审计](../reports/wc_fair_cal_r1_native35_partial_audit_20261004.json)/[独立原件](../reports/wc_fair_cal_r1_native35_partial_runner_20261004.json.gz)核验common场景第0工作点：

- 固定原 `MinimalV1LVGDiT.forward` 与 `MiniTrainDIT.forward` 实际文件/源SHA绑定，worldcache_enabled=false。
- 35请求→36实际更新、72CFG、prepare1；denoiser72/full72/skipped0，所有cache counter保持0，worldcache_horizon=None，Karras网格与35步控制一致。
- 普通完整generate返回，pipeline顺序/输出几何、backend flags恢复和完整93帧视频独立通过；未用WC负阈值forced-full充当Native。

Native35编码视频SHA `2d33014068b445e30327b8bb83b07f7ce151499122f51c55da25bdeb1674efdd`，403372 bytes，完整wall321.262012秒。部分原件SHA `139a19e34c0ff107ecfa7ff787b04b97164de526de671ec527cf6ab600fabcd0`，与D/D快照分开。原三PID2771711/2771727/2771729在审计现场仍live，CPU部分核验0.490秒、账本不变。

这证明当前冻结原方法、网格、真实deep调用和一个完整Native视频的技术行为。没有另跑未加观察器的GPU参考分支，因此不追认独立GPU parity；与WC的不同视频SHA不直接说明谁的语义/物理质量更好。十组Native相对指标和完整成本仍待全卡。

## 继续原卡与边界

现场1791077765.7947712：三个原句柄和命令行匹配、3/14视频，第一Native35完整返回后Native23已启动。含预付11.441073425147268/12GPUh、44jobs保持；原6300全wall/6270child/kill5，终态按含加载、失败、flush与释放的实费替换。

下一先跟踪Native23真实24更新/48CFG，再三WC点及stage、第二CAL完整六点；十四分母和历史WC0.06止步桥不变。已有全矩阵汇总[九项CPU控制](../reports/wc_fair_summary_cpu_20261004.json)通过，完整十四视频/原件/源码/来源/费用释放和全部十组Native35相对RGB/luma/motion/temporal指标待终态后执行。未追加卡、训练、付费评分或人工评审。后序CONF按实际结算和科学结果重新准入，科学goal active。

## Native23与WC0.04随后独立通过

[三输出部分审计](../reports/wc_fair_cal_r1_native23_wc004_partial_audit_20261004.json)/[独立原件](../reports/wc_fair_cal_r1_native23_wc004_partial_runner_20261004.json.gz)绑定原55份stage文件、原方法来源与十四分母，CPU1.384秒、账本未变。Native35/Native23/WC0.04分别36/24/36更新、72/48/72CFG、prepare各1；两个Native均完整deep且counter0，WC0.04实际deep43/cache29及native70/尾部reset。23→35实际采样网格与CFG重置成立；三份93帧/16fps完整解码通过。

Native23 SHA `22a673e8014745d96a0844fda1727f65616cc605ee1e0812a88e050aad76f2a7`，362073 bytes，wall239.265306秒；WC0.04 SHA `f4b60a6887e4dfa8aa02bc8e0b969dc9bddd85448842a8f60552450ecf5bba91`，427489 bytes，wall235.157578秒。新部分原件SHA `3e9107e47aa762f8e598357c86344ba5490930a1ce3c576dd1bbff62c280a383`，与D/D/首Native快照分开。

最新现场1791078782.8019598原三句柄仍live匹配，7/14视频；common WC0.06/0.08均36更新72CFG/prepare1完整返回，wall208.204236/198.832189秒，stage every1在生成。WC0.06返回后才进入后续阶段，符合历史桥止步规则，桥原件与后两WC/真实stage还须完整独立审计。含预付11.441073425147268/12h、44jobs与原6300/6270/kill5不变。尚未计算完整十组指标，不据这些单次wall报质量或速度优势。继续原卡，无新增GPU/训练/付费/人评，科学goal active。
