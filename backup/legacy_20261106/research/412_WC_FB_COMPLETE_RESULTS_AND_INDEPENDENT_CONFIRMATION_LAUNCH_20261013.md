# F/B 首批完整结果与冻结候选独立确认

2026-10-13。**B 已得到真实局部计算节省，且误差有明显状态差异；F 的当前特征配置未改善动作选择。两者继续作为独立探索。** 已完成全部432成对调用与自动CPU分析；随后按既定主线启动冻结H1的新输入、双seed独立确认，不用F/B修改候选。

## 1. 完整执行和费用

原卡 `WC-FB-PROBE-F16-B4-BASE4-DIAG4-FULL432-R1-20261013-A`，源码 `a95b8166efd0371363bd28a1852bbddb448ec935`，686文件逐份一致。服务器目录 `.sync/wc-fb-probe-cpu-r1-20261013`，原输出 `outputs/wc-fb-probe-full432-r1`。

|项目|完整实际分母与验收|
|---|---|
|父轨迹|4普通＋4诊断，共8条完整36更新轨迹；guided、终态、动作、93帧RGB与原392父轨迹逐位一致|
|F|16同状态点，4提示词组；其中14点父策略原动作C，2点原动作P|
|B|4同状态点×9模式×4次：1预热＋3正式，共144离线pairs|
|总调用|288父轨迹pairs＋144离线pairs＝432pairs／864CFG，一次加载|
|原件|F/B共16 raw文件、352张量；父向量另8文件、296张量，不混作同一分母|
|控制|四Dense模式逐位一致，四状态DENSE_PLAIN与原392同状态teacher一致；各模式四次输出逐位一致；父缓存与RNG恢复接受|
|终态|原supervisor571934／runner572024退出0，自动CPU post退出0；旧句柄消失、kernel释放、GPU24MiB／无计算进程后才准入下一卡|
|费用|全GPU wall9590.663548秒，**2.664073208 GPUh**，含加载、预热、诊断和清理；CPU post74.612966秒，不新增GPU计费|

原始验收：[完整终态捕获](../reports/wc_fb_probe_scheduled_collection_20261013.json)、[独立接受](../reports/wc_fb_probe_full432_and_curve_cpu160_acceptance_20261013.json)。GPU与post账本SHA绑定，接受发生在新CONF启动前。

## 2. F：预测误差有信号，决策收益未出现

使用因果浅层差分的固定16通道。SOURCE_PHASE_LOPO、RAW_CLOCK、RAW_SUB、Haar、FFT按提示词留一组验证；PCA和回归仅用训练组，固定ridge与既定三档lambda，不重选特征或参数。预测对象是C/A的绝对guided MSE，teacher只作离线标签。

主lambda为525.146350981。五方法在全部16点均选择10A／6C，且误选同三个状态：AV51 step30选C而局部oracle为A；Human step29选A而oracle为C；misc step30选C而oracle为A。这三个都是父策略原C点，不能删去。

|主lambda方法|16点提示词等权regret|含已测特征费用的regret|特征新增费用 / 毫秒|
|---|---:|---:|---:|
|来源×阶段LOPO|0.007022508|0.007022508|0（基线记法）|
|RAW_CLOCK|0.007022508|0.007022508|0（基线记法）|
|RAW_SUB|0.007022508|0.008192422|1.1699|
|Haar|0.007022508|0.010267964|3.2455|
|FFT|0.007022508|0.009627928|2.6054|

regret对应局部 `cost + lambda × gain² × absolute guided MSE` 的差，不是视频LPIPS或实测端到端毫秒。14个自然C点单独保留：五方法regret均为0.009050566；包含特征费用后RAW_SUB／Haar／FFT分别为0.010221133／0.012299665／0.011658922。

独立重构还确认：低、中、高三档lambda中，五方法选择分别同为8A/8C、10A/6C、14A/2C。没有只挑主档或最好档。与此同时，RAW_SUB的预测误差均值确实较低：预测C的平方误差由来源×阶段的0.787030降到0.628270，预测A由0.297989降到0.233724；Haar／FFT未表现出类似明确增量。**更准地预测标量误差，尚未改变本批计算选择。**

因此，本轮结论是当前16通道、两特征、固定回归配置未给出调度收益，不否定频域信息本身。若继续F，优先利用保存标签检查动作边界与误选状态，预登记一次有针对性的区分实验；不直接扩大频谱网格或并入主线。

边界集中说明：这只是C/A模块LOPO，既定gamma/lambda先前用过四CAL，不是全方法独立泛化。没有重建合法四动作在线策略；两个父P点的离线A不表示P_OFF允许在线执行。特征计时包含调用器实际提取、差分和变换；完整回归、控制和来源维护税尚未测全，RAW_CLOCK/无F新增费用记零有利于基线。没有F方法终点视频。

见[F独立重构](../reports/wc_fb_probe_F16_independent_decision_analysis_20261013.json)。

## 3. B：重算可以更便宜，但需要按状态检验代价

P0只在4层对部分token更新MLP；M8扩到8层，两者attention完整计算并保留当前门控。L2跳过第13、19层的完整Block计算，使用过去真实父轨迹的整层残差；当前identity保留，历史残差内含旧调制/位置项。它仍是离线探针，未部署连续L2策略。Q2本卡未实现。

以下均为3次正式计时中位数，预热另存。相对误差为 `sqrt(mean((v_candidate−v_D)²) / mean(v_D²))`，`v=8v_c−7v_u`，由CPU重新读取全部raw并校验SHA和绝对MSE。P0/M8主表使用预登记rotation掩码；随机对照完整保留。

|状态（来源／年龄）|Dense / 秒|P0 / 秒；相对RMSE|M8 / 秒；相对RMSE|L2 / 秒；相对RMSE|L2局部省时|
|---|---:|---:|---:|---:|---:|
|AV28 step21（P／2）|6.643539|6.577112；12.83%|6.514806；14.79%|6.169354；16.96%|7.14%|
|AV28 step27（D／2）|6.643056|6.573701；12.13%|6.504603；13.81%|6.167518；13.54%|7.16%|
|Human step15（P／2）|6.645823|6.581361；24.70%|6.513105；30.67%|6.173837；37.73%|7.10%|
|Human step29（D／2）|6.635643|6.567524；11.35%|6.499786；12.60%|6.159914；11.27%|7.17%|

P0四点省约0.97–1.04%，M8约1.94–2.08%，L2约7.10–7.17%（约1.077×Dense）。真实收益没有把两个CFG分支或深层其余费用遗漏。四点rotation的绝对误差都小于同覆盖random；随机正式秒数和全部退化保留在原件。

有价值的局部条件：AV28晚期L2比M8更快、误差略低；Human晚期L2比P0/M8更快且误差略低。Human早期L2误差明显较大，需保留为可能有害状态。早P／晚D与阶段同时变化，不能唯一归因于来源或阶段。

计时包含双probe、整个深层组、head、RF与臂内实际缓存维护。诊断安装和快照恢复不在微计时内，但全卡GPU费用包含；共享历史bank在所有模式均存在。记录的峰值显存不是独立在线部署显存，逻辑cache字节可能别名，不相加宣称内存收益。四Dense控制的数值相等，不能据这几次计时解释0.1%以内抖动。

**下一步B应优先做保存真实状态的单次动作后缀与视频终点评价，再验证合法连续历史更新。** 使用预登记的全状态分母与Dense控制，先分清局部时间节省和终点保真；不把7.1%当完整视频加速。探索仍独立，合入需收益、控制、实际费用和共同讨论。

见[B逐状态CPU独立重构](../reports/wc_fb_probe_B_relative_error_independent_analysis_20261013.json)。

## 4. 同批成本曲线CPU已完整接受

[411完整60规划](411_WC_H1_FULL60_COST_CURVE_AND_STATIC_CONTROL_CPU_PREPARATION_20261013.md)的原CPU592697已结束：两flow×四Toy×十方法×audit/lean，共160完整路径，295.821367秒，source `055b55755dbc0c745fd2fa2da2a69c82476f71e4`／695文件一致。Native动作仍为null；三档H1、中档冻结参数、固定序列与audit/lean等价均接受，GPU0、账本0。

完整60真实曲线**未启动GPU**，仍需实际生产计时/评分封口和新准入。预计7.815847555 GPUh是保守规划，不能当已经消耗或科学结果；优先保护下面的冻结确认。

## 5. 冻结H1独立确认已单次启动，按时间查收

原[405完整50卡](405_WC_FROZEN_H1_INDEPENDENT_CONFIRMATION_FULL50_FINAL_PRODUCTION_PREREG_20261013.md)保持：四个新提示词AV46、Human125、misc2711212、robot043，seed17/43，Native／RA／A_NO_P／P_OFF／TABLE_PHASE_H1；40正式＋10完整CAL预热，1800pairs／3600CFG，一次模型驻留。H1参数fingerprint `34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8`不变。

- 2026-10-13 **16:51:26北京时间**启动唯一supervisor594353、runner594521、自动CPU post watcher594354。
- source `e48ba58047b09507ea6f438f5077ebffb4fb2114`／684文件全一致；原stage `.sync/wc-source-confirmation-production-r1-20261013`，output `outputs/wc-source-conditional-confirmation-full40-r1`。
- 首次准入实际A6000 UUID正确、原三句柄存在，GPU14066MiB／100%，只表明任务真实运行，尚无确认终点结果。
- 完整保守预测 **6.561346751 GPUh**，≤8自主范围。按已测主时间预计约3–4小时，再计自动CPU评分；到 **21:01:59北京时间**一次查收原任务和全部40正式视频93帧。期间不持续查询；若届时未完成，据剩余工作量重新估时查收。
- CONF前累计实结 **72.013792437／104.971363333 GPUh**，余额 **32.957570896**。在途预留不能算已实耗；CONF结束完整费用再结算。F/B花费已包含其中。
- 当前对话自动化 `worldcache` 负责到时接续；已完成的 `worldcache-f-b` 已停止安排。服务器预算watchdog和自动CPU post保留。

本次查收SSH曾因本地FRPC的KCP通道不稳定失败，观察失败封存。只切换本任务拥有的本地客户端transport为TCP，认证与visitor不变，原KCP文件保留；连接恢复后接收同一服务器任务，未因此重投F/B或改服务器配置。连接设置仍仅在忽略目录，不进入Git。

下一次先接受全部50原件、40正式93帧、失败分母、prompt内双seed聚合、冻结参数、实际费用和释放状态，再讨论是否继续成本曲线与孤立B后缀。旧E2完整76的自身批准与暂缓P13h保持，不转用；不新增训练、OMR或人工评审。

回执：[GPU启动](../reports/wc_source_confirmation_final_r1_GPU_launch_20261013.json)、[首次准入](../reports/wc_source_confirmation_final_r1_initial_admission_20261013.json)、[预计查收](../reports/wc_source_confirmation_final_r1_delayed_check_receipt_20261013.json)。
