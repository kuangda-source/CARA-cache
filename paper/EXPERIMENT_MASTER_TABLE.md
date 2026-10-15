# 实验总表：状态、论文贡献、缺口与优先级

更新：2026-10-16。与[内部实现→论文表述映射](INTERNAL_TO_PAPER_MAPPING.md)一起使用；[机器索引](experiment_master_table.json)保存相同条目、依赖和证据SHA。本表按科学问题／完整卡汇总，不逐个罗列CPU修复重试；旧原件复用与多个报告引用同一实验，不增加独立样本数。

**当前N05准备：**完整CORE66科学范围已事前冻结，真实Native三网格CPU接受；216条本地Toy检查已单次启动，03:12一次收。尚非生产CPU/GPU或新质量/速度。见[460](../research/460_WC_N05_CORE66_FROZEN_GRID_AND_FULL216_LOCAL_CPU_LAUNCH_20261016.md)。

**当前接续：**459本地阶段/T1完整72 CPU已接受，04:55同26D验收不变；最新用户已授权之后按主线优先级推进。下一优先N05强基线有限调优，随后N07/N08与费用/自动质量；P/T1增强后排。见[当前队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)。

**当前最强主干：GCR廉价修正已有终点归因，CPA已有校准导出的高保真阶段部署；新W3监督子集与CPU阶段对照完成，简单阶段规则解释T1几乎全部局部收益。** 同26D对照新增了三场景的刷新位置与修正作用信号，完整四场景卡因OOM中断，原分母保留。写作可使用已有两个工作点和固定消融；强基线与N06完整收尾仍是关键补证。

**此前执行快照（04:55安排仍保持）：** 144完整CPU与实际入口已独立接受；修复R2于23:54:49在GPU0准入，1040857/1040918/post1040858。完整36重跑，旧28仅作等价控制，原失败卡保留；新卡科学结果待10-16 04:55一次验收。预测5.766055/上限8 GPUh；v2实结86.864054，预留8，可准入10.107310。原W3已完成455监督验收与456阶段CPU对照。见[453](../research/453_WC_SIMPLE26D_MEMORY_FULL144_ACCEPTED_AND_COMPLETE36_GPU_R2_LAUNCH_20261015.md).

**23:00一次查收更新（历史）：**N06已因OOM终态，12预热＋16正式完成、1失败＋7未到达，16正式全93帧评分通过；整卡未接受，不自动重跑。[451](../research/451_WC_SIMPLE26D_PARTIAL_RESULTS_OOM_TERMINAL_AND_PAPER_IMPLICATIONS_20261015.md)保留全部36/24分母与逐场景结果。R01原W3财务条目已结，科学原件仍于2026-10-16 01:00另验，本轮未提前查看。

15:41资源核对、双卡启动和预留保留在[原449](../research/449_WC_TWO_GPU_OCCUPANCY_AND_SAFE_MAINLINE_PARALLELISM_20261015.md)/[450](../research/450_WC_DUAL_GPU_SIMPLE26D_RUNNING_AND_ACCOUNTING_ACCEPTANCE_20261015.md)。23:00 v2账本实际86.864053599/原cap104.971363333GPUh，预留0，可准入18.107309734；本卡2.292842043。自身GPU0进程/锁已释放。并发秒数仍不作clean加速证据；财务结算不替代W3科学验收。

## 阅读图例

- **C1｜GCR：**真实CFG输出空间的廉价修正读出。当前已完成实验可支撑修正作用与效率工作点。
- **C2｜CPA：**对实际动作的误差／费用标定与计算安排。当前已支持阶段部署；优于强简单安排或内容自适应的增量仍待相应实验。
- **C3｜系统实证：**保真—时间工作点、新输入确认、真实费用与部署分析，属于实验支撑，不额外包装成第三个新算法。
- **E-P／E-W3：**新单分支补偿读出／新因果风险估计，当前是独立增强。是否纳入正文取决于后续完整证据。
- **R：**保留已接受结果，不默认重跑。**P0：**先收原在途卡与CPU标签评价。**P1：**论文核心补验。**P2：**最终测试／重复测速／部署质量。**P3-C：**跨骨干主张的条件补验。**C**后缀表示依赖信号与资源选择。**X：**关闭或暂缓，不是待执行队列。

## 一张总表

“已完成”包括不同证据层级：终点、机制和CPU准备各自标明，不互相替代。“待补”只表示已设计的证据问题；模板规模不是已通过CPU或已经选定的GPU卡。

|编号／状态|实验：内部ID → 论文表述|已经得到什么／待补范围|支撑哪项贡献|缺口与下一步|优先级|证据入口|
|---|---|---|---|---|---|---|
|D01 · 已完成｜基线|`F1_R3 / NATIVE / WC` → Full Inference / WorldCache技术复现|初始3个接受配对场景，WorldCache加速1.476–1.602×；后续420另有同批WC/RA/Native结果。|C3基础；非本文新算法|初始样本不是官方论文全部质量复现；原视频保留，公平调优比较见N05。|R·保留，不重跑|[11](../research/11_F1_R3_TECHNICAL_RESULTS.md) · [420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)|
|D02 · 已完成｜历史开发|`W1_CAL8 / SCALAR / SHRINK` → Scalar Incremental Calibration|8开发场景中7/8内部预测与残差误差改善，预测MSE均值降低24.08%；后续视频评价混合。|C1设计线索；不替代当前GCR主结果|保留局部与终点差异；当前正文使用CFG共享阶段修正，不再扩展旧逐支W1。|R·历史机制|[21](../research/21_W1D_CAL8_RESULTS.md) · [28](../research/28_W1_DEVELOPMENT_VQA_RESULTS.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)|
|D03 · 已完成｜早期干预|`WC_W3_SMALL_HUMAN` → Refresh Intervention|Human单点强制D使LPIPS降低2.8080%，后续两CFG完整调用合计18→16。|C2机制线索；非在线调度结论|次数变化是干预后果；并非固定配额或clean端到端优势。新W3不复用该单点充泛化。|R·机制/附录|[129](../research/129_WC_W3_HUMAN_APPROVED_EXECUTION_AND_RESULTS.md)|
|D04 · 已完成｜开发终点|`RA_PLUS_A_FULL32 / W1_ONE_PHASE / BETA1_ONE_PHASE` → CFG-Aligned Corrected Reuse|四CAL×七候选＋四Native，共32路径；阶段β=1相对WC均值LPIPS低11.1600%，4/4改善。|C1直接终点证据|旧wall含取证，不作为clean延迟；速度引用D07/D13的同口径结果。|R·主干开发证据|[257](../research/257_WC_RA_PLUS_A_COMPLETE32_FIDELITY_AND_COST_RESULTS_20261010.md) · [420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)|
|D05 · 已完成｜工程等价|`E5_FULL24 / LEGACY / FAST` → Equivalent Head Execution|24路径，所测输出/动作/RNG等价；修正配对head次数868→688，少20.7373%。|C3工程支持；非新加速主结果|次数不等于时间；已验clean主配置未自动启用该FAST，不能把比例加到1.8974×。|R·工程/附录|[365](../research/365_WC_E5_COMPLETE24_REAL_HEAD_EQUIVALENCE_RESULTS_AND_E3_NEXT_20261011.md) · [374](../research/374_WC_CLEAN_SPEED20_COMPLETE_RESULTS_20261012.md) · [420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)|
|D06 · 已完成｜组合开发|`E3_COMPLETE64 / KEEP / NONZERO` → Source-Rule × Readout Interaction|两规则×四CAL×八方法，64视频/5952帧；KEEP阶段W1/β1较同规则CPD失真低13.6735%/12.7233%；NONZERO组合反转。|C1来源机制；E-P旧P0组合条件|不能算P独立收益，不能以含取证/复用的时间作净加速；不再重跑全矩阵。|R·机制与条件|[369](../research/369_WC_E3_COMPLETE64_RESULTS_SOURCE_READOUT_INTERACTION_AND_NEXT_20261012.md)|
|D07 · 已完成｜重复测速|`CLEAN_SPEED20 / KEEP_A_P / A_NO_P` → Forward–Reverse Clean Timing|两场景×五配置×正反两轮=20正式＋20预热；A无P在两个场景的两轮均快于WC且LPIPS更低。|C1效率工作点；C3计时证据|重复范围限两场景旧五配置；未覆盖最终高保真版本，最终重复计时见N08。|R·计时证据|[374](../research/374_WC_CLEAN_SPEED20_COMPLETE_RESULTS_20261012.md)|
|D08 · 已完成｜旧控制开发|`N2_SOURCE_H1 / SOURCE_H2 / H2_P_TO_D` → Normalized-Risk Controllers|36正式＋18预热；来源门控P_OFF有质量工作点，旧H1/H2没有执行A。|C2设计分析；不是新absolute H1|与D12的新TABLE_PHASE_H1分版本；不再把旧H1/H2当待完成主模块。|R·设计/附录|[380](../research/380_WC_MATH_N2_COMPLETE_SOURCE_GATE_POSITIVE_AND_ROUTER_A_UNUSED_RESULTS_20261012.md)|
|D09 · 已完成｜同状态机制|`SOURCE_PHASE16 / FULL368` → Source-Consistent Readout and Calibration|四CAL×D/P×早晚16状态；来源一致A为16/16优于C；P来源旧D参考2/8、融合8/8改善。|C1直接局部机制；C2标定依据|16状态不是16独立视频；旧gamma使用过CAL；局部regret不等于端点，桥接见D10。|R·机制主证据|[392](../research/392_WC_SOURCE_PHASE16_COMPLETE_POSITIVE_RESULTS_AND_CONSEQUENCE_NEXT_20261012.md)|
|D10 · 已完成｜后果干预|`PI0_SUFFIX8 / FULL266` → Single-Readout Suffix Consequences|4父＋8后缀/12视频；AV28一次A让LPIPS低0.9812%、后续D+P由8→7；另外三点有小幅反例。|C1/C2交互机制|确认局部更准并不保证终点更好；取证/解码顺序影响不作为clean收益。保留全四点。|R·因果机制|[396](../research/396_WC_PI0_SUFFIX8_COMPLETE_RESULTS_LOCAL_TARGET_AND_FUTURE_COMPUTE_20261013.md)|
|D11 · 已完成｜工程筛查/归档|`R4_FULL104 / SPARSE_FAIR` → Sparse Attention Feasibility|104 QKV输入/312算子案例，中位1.218931×；旧两视频全流程少0.2916%/1.4070%。|不作为当前CARA核心模块|算子与视频成本层级不同、覆盖率有限；当前不继续稀疏搜索，不拿微收益否定整个方向。|X·归档，不续开|[75](../research/75_WC_FULL104_R4_CARD_AND_RESULTS.md) · [134](../research/134_WC_SPARSE_COST_CONDITIONS_EXPLORATORY_RESULTS.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)|
|D12 · 已完成｜主方法开发|`TABLE_PHASE_H1 / TABLE_POOLED_H1 / ABS_H1_CAL24` → Absolute Source-and-Phase Allocation|六方法×四CAL=24正式＋12预热；absolute guided MSE/g²/源分价下A真正被选择，高保真轨迹26D/5A/5C。|C2已实现标定与工作点；C1读出|更多D和阶段位置共同影响终点；已有固定归因D14，仍缺简单同配额对照N06。|R·主干开发证据|[403](../research/403_WC_ABSOLUTE_H1_COMPLETE_RESULTS_HIGH_FIDELITY_AND_NEXT_20261013.md)|
|D13 · 已完成｜冻结确认|`FROZEN_CONFIRM50 / TABLE_PHASE_H1 / A_NO_P / P_OFF` → Frozen New-Prompt Confirmation|四新prompt×seed17/43，40正式＋10预热；39兼容视频，RA拒绝1；高保真LPIPS0.0530368、Native加速1.2681×。|C1/C2工作点确认；C3有限新输入|RA完整八视频质量均值缺失；当前输入已曝光；更广的全部对手共同冻结测试见N07。|R·主结果确认|[417](../research/417_WC_FROZEN_CONFIRMATION_FULL50_RESULTS_AND_COST_CURVE_NEXT_20261013.md)|
|D14 · 已完成｜主比较与归因|`COST_CURVE60 / H1_LOW/MID/HIGH / FIXED_A / FIXED_PLAIN` → Common-Batch Trade-off and Matched-Refresh Ablation|40正式＋20预热；Efficient比WC时间少13.72%、失真低11.1600%；同26D的A/plain失真低3.5196%、多0.8762秒；MID=fixed。|C1修正独立归因；C2阶段部署；C3同批比较|三λ都26D，不是宽连续前沿；每格一次计时；fixed等价不证明优于均匀/粗阶段规则。|R·主表/消融|[420](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md)|
|D15 · 已完成并关闭｜探索|`F / RAW / Haar / FFT` → Spectral Risk-Feature Probe|F真实局部实验及分组分析已完成；RAW改善预测但动作未变，Haar/FFT未产生当前决策增量。|不合入主线；独立附录|F新差值假设未做但已随方向关闭，不记为活跃待补或自动追加训练。|X·关闭|[412](../research/412_WC_FB_COMPLETE_RESULTS_AND_INDEPENDENT_CONFIRMATION_LAUNCH_20261013.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)|
|D16 · 已完成并关闭｜探索|`B_FULL312 / C_REPLAY / DENSE_VELOCITY / L2_VELOCITY` → Block-Reuse Endpoint Diagnostic|4状态/16视频/1488帧；C/Dense/L2均值LPIPS 0.3272410/0.3289287/0.3300823，端点混合。|不合入主线；独立附录|首返回保存速度、实际C缓存，不是在线B刷新或净加速；保留父C/A差异解释，不再扩展。|X·关闭|[423](../research/423_WC_B_FULL312_COMPLETE_ENDPOINT_RESULTS_AND_READOUT_BOUNDARY_20261014.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md)|
|D17 · 已完成｜离线增强机制|`P_ACR_E0 / Pc / Pu` → Single-Branch Compensation E0|旧16真实状态；按prompt留出的SourcePhase Pu系数相对A的guided MSE低37.2996%，14/16点、4/4提示词改善。|E-P局部可行性；未成为主贡献|只隔离系数留出，A已用过CAL；没有新单支实际价/新来源/闭环结果。下一可选N03。|R·增强机制|[426](../research/426_WC_P_W3_E0_COMPLETE_ASYMMETRIC_ORACLE_AND_COEFFICIENT_RESULTS_20261014.md)|
|D18 · 已完成｜CPU准备|`PA528_CPU_R2` → P-ACR Production CPU Validation|完整PA528的原语、父恢复、真实入口和启动/post CPU接受；模型/权重/GPU为0。|E-P执行准备，不是性能证据|CPU通过不等于真实528执行；P-ACR当前不更新来源，GPU卡未选定。|R·无需重做CPU|[433](../research/433_WC_P_ACR_WHOLE528_LAUNCH_CPU_AND_NEXT_DECISION_20261015.md)|
|D19 · 已完成｜CPU准备|`W3_CLOCK432 / W3_FULL72_CPU / W3_PRODUCTION_CPU_R3` → Causal Clock and W3 Collector Validation|真实scheduler CPU重放对齐旧432步；完整模拟采集/父恢复/因果隔离及生产23控制接受。|E-W3/C2监督工具；不是新风险模型收益|模拟72父/3456pairs不是真实W3标签；真实18父卡为R01。无需再派准备CPU。|R·准备封口|[434](../research/434_WC_W3_REAL_CONTINUOUS_CLOCK_AND_FULL432_CAUSAL_HISTORY_CPU_20261015.md) · [441](../research/441_WC_W3_FULL72_COLLECTOR_CPU_ACCEPTED_AND_PRODUCTION_NEXT_20261015.md) · [447](../research/447_WC_W3_COMPLETE_CPU_CLOSED_AND_WHOLE864_PERMISSION_DECISION_20261015.md)|
|R01 · 已完成｜有缺口监督接受|`W3_LABEL64 / FULL864` → Same-State C/A/D Label Collection|80原件/1104张量/64标签通过；15视频1395帧，8组完整模型非提交等价/7组RGB等价；原18/72分母保留。|C2/E-W3真实监督，非新策略端点|1坏视频及2文本拒绝保留；主6prompt/48点、raw敏感性7/56、warm8不拟合，原整卡非全成功。|R·监督子集接受|[455](../research/455_WC_W3_RAW_COHORT_ACCEPTANCE_GROUPED_T1_T2_RESULTS_AND_PHASE_ATTRIBUTION_20261016.md)|
|N01 · 已完成｜开发性CPU决策评价|`T0/T1/T2/T_TIME/T_STEP_TABLE/STEP23` → Grouped Action-Value and Phase-Only Controls|主组T1/时间-only/仅23步regret为0.339971/0.340532/0.337549；敏感性0.329269/0.332689/0.330417。|E-W3→C2阶段校准；未并入主线|简单阶段解释几乎全部局部收益；第23步为事后候选，无新策略视频或速度。闭环列N02可选；先收同26D并优先N05强基线。|R·CPU区分完成|[456](../research/456_WC_T1_VS_SIMPLE_PHASE_CPU_RESULTS_AND_VIDEO_DECISION_20261016.md)|
|N02 · 待补｜本地完整CPU已接受|`W3_FROZEN_PREDICTOR_CLOSED_LOOP` → Phase-Revision versus Learned Allocation|459全72 Toy路径、32audit/lean、8旧H1完整控制与8/8第23步D→A实际覆盖通过。|C2执行准备；非新视频端点|服务器生产CPU/真实视频未做；主线N05优先，阶段/T1仅有明确最终版本价值时再冻结闭环。|P2-C·可选增强|[459](../research/459_WC_PHASE_FULL72_LOCAL_CPU_ACCEPTED_AND_MAINLINE_PRIORITY_20261016.md)|
|N03 · 待补｜可选整卡|`PA528` → Single-Branch Readout: Real Error and Price|原完整8父/12状态/C,A,D,Pc,Pu各1warm+3正式，共528pairs/1056CFG；预计7.529994GPUh。|E-P费用/精度候选；不作为主稿前置|需要实际单支报价、误差下包络与恢复/视频控制；不默认为必须执行，先保护主稿补验余额。|P2-C·条件可选|[433](../research/433_WC_P_ACR_WHOLE528_LAUNCH_CPU_AND_NEXT_DECISION_20261015.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md) · [448](../research/448_WC_W3_FULL864_APPROVED_GPU_LAUNCH_AND_UNDER12_AUTONOMY_20261015.md)|
|N04 · 待补｜条件组合|`S1_SIX_CONFIGURATION_TEMPLATE` → P-ACR / Trend Readout Bridge and Combination|既有模板：4开发prompt×6配置=24正式＋12预热；含H1原集/CAD桥接、Trend、ACR及组合。|拟增强E-P/C2；不提前计主贡献|先有值得追踪的误差—费用或交互信号，再冻结完整范围；只做读出闭环，合法来源refresh须另设计。|P2-C·有信号/余额才做|[roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N05 · 待运行｜完整生产CPU已接受|`PAPER_E1_TUNED_BASELINES` → Fair Tuned-Baseline Frontier|完整11配置四CAL、44正式+22warm/2220pairs冻结；216 Toy与真实R2生产CPU四命令/1671源/44请求/三Native网格已接受。|C1/C2实用增量；C3公平性|原N06 04:55接受后fresh v2/UUID启动完整66；forecast8.568548038/上限9.5<12。真实视频结果及直接修正近邻Cosmos适配仍待。|P1·下一主线卡|[464](../research/464_WC_N05_CORE66_REAL_PRODUCTION_CPU_ACCEPTED_AND_N06_0455_NEXT_20261016.md) · [当前队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)|
|N06 · 在运行｜原中断证据保留|`PAPER_E2_STATIC_26D / SIMPLE26D_FULL36` → Simple Schedules at Matched Dense Budget|原24正式＋12warm不缩；12warm/16正式完成且1488正式帧评分，misc前密A OOM、另7位置未到达。三个完成输入中原阶段胜均匀；均匀内部A三例改善。|C2刷新位置线索；C1跨位置作用|整卡未接受，四场景均值空缺；粗阶段两例混合。144完整CPU接受，修复R2完整36已准入；旧28作等价控制，04:55验收。所有26D，A5/10/0；并发秒数不作clean。|P0·04:55一次验收|[451](../research/451_WC_SIMPLE26D_PARTIAL_RESULTS_OOM_TERMINAL_AND_PAPER_IMPLICATIONS_20261015.md) · [预登记](../research/449_WC_DUAL_GPU_ACCOUNTING_AND_SIMPLE26D_COMPLETE36_PREREG_20261015.md)|
|N07 · 待补｜本地隔离/统计CPU已准备|`PAPER_E3_FROZEN_SHARED_TEST` → Common Frozen Evaluation Matrix|579配置/1044记录本地隔离，44成员排除已独立接受；prompt分组/两seed/4096 bootstrap与总耗时比统计5控制通过。原8×2×10=160正式+20warm模板保持。|C1/C2最终确认；C3覆盖|最终8prompt/16请求、方法/对手与fresh远端曝光尚待N05/N06后冻结；完整生产CPU/费用与GPU均未选。旧CONF与EXPL全排除。|P2·N05/N06后冻结|[466](../research/466_WC_N07_LOCAL_INPUT_ISOLATION_AND_GROUPED_STATISTICS_CPU_READY_20261016.md) · [当前队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)|
|N08 · 待补｜排程/统计CPU已准备|`PAPER_E4_REPEAT_SPEED` → Balanced Repeated Clean Latency|两旧CAL×五配置×三轮30正式+10warm的完整40排程、逐轮汇总已实现；每配置场景内平均位置2，5项CPU控制通过。|C3稳定费用；C1/C2工作点复验|实际方法/阈值、sampler/生产CPU、费用与GPU待前序冻结；当前没有新速度/视频结果。全部三轮秒数/范围/倍数与质量并列。|P2·最终版本冻结后|[467](../research/467_WC_N08_BALANCED_REPEAT40_MATRIX_AND_STATISTICS_CPU_PREPARED_20261016.md) · [当前队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)|
|N09 · 待补｜本地成本盘点完成|`PAPER_E5_COST_PROFILE` → Calibration and Minimal Deployment Profile|全40旧正式计时/3720帧已复核；16标签四格表精确重建，五次CPU拟合平均0.200142ms；四相关历史采集4.383638799GPUh。|C3部署开销；C2费用一致|历史采集费用不等于最低标定费；最终C/A/P0/D（按合法集）、组件/GC/逐请求峰值与最小必要采集仍待测。旧累计显存峰值不能作逐方法峰值。|P2·最终实现profiling|[465](../research/465_WC_DEPLOYMENT_COST_SOURCE_INVENTORY_AND_PROFILE_NEXT_20261016.md) · [当前队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)|
|N10 · 待补｜最终质量维度|`PAPER_E5_AUTOMATIC_QUALITY` → Automatic Video Quality on Final Outputs|旧MUSIQ/抽帧VQA已做；最终共同视频的语义/一致性/闪烁/动态维度尚未统一。|C3生成质量范围；补充保真主指标|优先复用输出、冻结少量相关自动指标；不能把更静当更好，或子集评分称完整官方总分；不增人评。|P2·复用最终视频|[28](../research/28_W1_DEVELOPMENT_VQA_RESULTS.md) · [closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N11 · 待补｜主张条件|`SECOND_MODEL_TRANSFER` → Second-Backbone Transfer|模型内接线pilot→必要q/g/费用标定→冻结共同测试；尚无本项目迁移结果。|C3跨骨干；若不做则限定Cosmos|原8/−7权重、36更新、step25不原样当新模型真值；模型/范围/费用待定。|P3-C·主张跨骨干时必补|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|Z01 · 暂缓/未执行｜旧卡|`OLD_E2_FULL76 / OLD_P_REFERENCE_13H` → Legacy Deferred Cards|旧E2完整76、P参考双flow13.0600GPUh等历史卡保留。|不算当前待执行承诺|不由新文档重启、缩卡或借用授权；新P/W3及正式补验用各自完整登记。|X·暂缓，不恢复|[369](../research/369_WC_E3_COMPLETE64_RESULTS_SOURCE_READOUT_INTERACTION_AND_NEXT_20261012.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|


## 接下来的顺序与论文用法

最新用户已要求当前验收完按主线重要性推进，执行入口为[主线优先队列](../plans/WORLD_CACHE_MAINLINE_PRIORITY_QUEUE_20261016.md)。

1. **N06原完整R2仍04:55一次验收。** 不改运行源、句柄、六配置四CAL或原分母。全部适用原件/视频/显存/费用接受后继续；技术失败保留并定位。
2. **N05是下一张主线卡。** 优先完成Native少步、有限调优WC/RA与两个冻结工作点的实际CPU/整卡费用，按原严格<12GPUh及fresh v2/UUID自主推进。近邻Cosmos适配未验，明确完整范围，不按授权阈值删对照。
3. **N07共同冻结测试→N08最终重复clean测速，N09/10费用/自动质量配套。** 原CONF输入与新EXPL都已曝光，不再作未见输入；已有D07/D13/D14保留。完整卡>=12或总余额不够时先交付具体整卡决定，不拆/缩或重置窗口。
4. **N02/03/04保持可选。** 阶段/T1完整本地72已在459接受，生产/视频尚无；简单阶段解释几乎全部局部收益，不让新预测器/PA准备挤占强基线和确认。F/B关闭。

本轮未SSH查同26D或新资源，也没有新增GPU扣费。预算仍用01:19已捕获快照：实结86.864053599、N06预留8、可准入10.107309734GPUh；不是实时余额。04:55结算后按v2原账单加法重算，原cap104.971363333不变。

正文围绕GCR修正与校准阶段部署的两个工作点组织，N05验证强对手公平性，N06验证位置/读出归因，N07–N10补冻结覆盖和部署证据。420是四CAL/seed0开发、每格一次计时；417确认有一个RA拒绝，两个工作点不拼接，LPIPS为Native相对保真，93帧不是93个独立样本。新CPU通过不升级为新策略质量/速度结果。

## 交给写作对话的读取顺序

```text
请一起读取：
/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr/paper/INTERNAL_TO_PAPER_MAPPING.md
/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr/paper/EXPERIMENT_MASTER_TABLE.md

机器索引为同目录 internal_to_paper_mapping.json 与 experiment_master_table.json。
先用映射解释名称，再用总表确定证据状态、论文贡献、缺口和优先级。
当前正文采用已完成的GCR与校准阶段部署；运行、CPU准备和未执行模板不写成方法收益。
“待补”不是已完成具体范围/CPU准入；选定并通过完整准入后按现行授权推进，不恢复历史许可门槛。
后续有新的完整结果后，按原ID更新本表和映射，不改旧配置/原件身份。
```

**W3 01:18收尾：**原只读CPU与本轮分组评价均已结束，不再查旧句柄或自动续GPU；同26D R2仍04:55验收。T1冻结参数只是离线候选，CARA/GCR/CPA现有主方法范围保持。

**456 CPU收尾：**简单阶段与T1对照已完成，三个隔离控制和独立折内拟合/指标复算通过；原同26D行、任务、04:55验收不变。新视频验证目前是建议，不是已启动任务。

**457执行准备：**新接口已接四种原H1/合法集/阶段/T1配置，六标量控制通过。完整72本地Toy CPU已启动，02:28一次查收；没有新GPU视频或生产CPU接受。N06原任务/04:55验收不改。
