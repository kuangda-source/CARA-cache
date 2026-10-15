# 实验总表：状态、论文贡献、缺口与优先级

更新：2026-10-16。与[内部实现→论文表述映射](INTERNAL_TO_PAPER_MAPPING.md)一起使用；[机器索引](experiment_master_table.json)保存相同条目、依赖和证据SHA。本表按科学问题／完整卡汇总，不逐个罗列CPU修复重试；旧原件复用与多个报告引用同一实验，不增加独立样本数。

**当前最强主干：GCR廉价修正已有终点归因，CPA已有校准导出的高保真阶段部署；新W3监督子集与CPU阶段对照完成，简单阶段规则解释T1几乎全部局部收益。** 同26D对照新增了三场景的刷新位置与修正作用信号，完整四场景卡因OOM中断，原分母保留。写作可使用已有两个工作点和固定消融；强基线与N06完整收尾仍是关键补证。

**最新执行状态：** 144完整CPU与实际入口已独立接受；修复R2于23:54:49在GPU0准入，1040857/1040918/post1040858。完整36重跑，旧28仅作等价控制，原失败卡保留；新卡科学结果待10-16 04:55一次验收。预测5.766055/上限8 GPUh；v2实结86.864054，预留8，可准入10.107310。原W3已完成455监督验收与456阶段CPU对照。见[453](../research/453_WC_SIMPLE26D_MEMORY_FULL144_ACCEPTED_AND_COMPLETE36_GPU_R2_LAUNCH_20261015.md).

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
|N01 · 已完成｜开发性CPU决策评价|`T0/T1/T2/T_TIME/T_STEP_TABLE/STEP23` → Grouped Action-Value and Phase-Only Controls|主组T1/时间-only/仅23步regret为0.339971/0.340532/0.337549；敏感性0.329269/0.332689/0.330417。|E-W3→C2阶段校准；未并入主线|简单阶段解释几乎全部局部收益；第23步为事后候选，无新策略视频或速度。先收同26D，再讨论原H1/简单规则/T1完整视频卡。|P1-C·CPU区分完成，闭环待决定|[456](../research/456_WC_T1_VS_SIMPLE_PHASE_CPU_RESULTS_AND_VIDEO_DECISION_20261016.md)|
|N02 · 待补｜条件闭环|`W3_FROZEN_PREDICTOR_CLOSED_LOOP` → Phase-Revision versus Learned Allocation|保留原H1、简单第23步规则、冻结T1及匹配Native；具体完整范围/费用待决定。|C2阶段修订或状态增量；C3端点|456局部收益已由简单规则解释；先收同26D再决定是否做视频，不提前把局部收益当终点。|P1-C·同26D收尾后讨论|[456](../research/456_WC_T1_VS_SIMPLE_PHASE_CPU_RESULTS_AND_VIDEO_DECISION_20261016.md)|
|N03 · 待补｜可选整卡|`PA528` → Single-Branch Readout: Real Error and Price|原完整8父/12状态/C,A,D,Pc,Pu各1warm+3正式，共528pairs/1056CFG；预计7.529994GPUh。|E-P费用/精度候选；不作为主稿前置|需要实际单支报价、误差下包络与恢复/视频控制；不默认为必须执行，先保护主稿补验余额。|P2-C·条件可选|[433](../research/433_WC_P_ACR_WHOLE528_LAUNCH_CPU_AND_NEXT_DECISION_20261015.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md) · [448](../research/448_WC_W3_FULL864_APPROVED_GPU_LAUNCH_AND_UNDER12_AUTONOMY_20261015.md)|
|N04 · 待补｜条件组合|`S1_SIX_CONFIGURATION_TEMPLATE` → P-ACR / Trend Readout Bridge and Combination|既有模板：4开发prompt×6配置=24正式＋12预热；含H1原集/CAD桥接、Trend、ACR及组合。|拟增强E-P/C2；不提前计主贡献|先有值得追踪的误差—费用或交互信号，再冻结完整范围；只做读出闭环，合法来源refresh须另设计。|P2-C·有信号/余额才做|[roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N05 · 待补｜正式开发|`PAPER_E1_TUNED_BASELINES` → Fair Tuned-Baseline Frontier|拟议12配置×4CAL=48正式＋24预热：Native完整/少步、WC/RA有限调优、两工作点、一个忠实修正近邻。|C1/C2实用增量；C3公平性|需先固定可比规格/计时/资源与点选择；约149/223秒两区域公平比较；完整卡费用/CPU尚未登记。|P1·论文关键补验|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N06 · 在运行｜原中断证据保留|`PAPER_E2_STATIC_26D / SIMPLE26D_FULL36` → Simple Schedules at Matched Dense Budget|原24正式＋12warm不缩；12warm/16正式完成且1488正式帧评分，misc前密A OOM、另7位置未到达。三个完成输入中原阶段胜均匀；均匀内部A三例改善。|C2刷新位置线索；C1跨位置作用|整卡未接受，四场景均值空缺；粗阶段两例混合。144完整CPU接受，修复R2完整36已准入；旧28作等价控制，04:55验收。所有26D，A5/10/0；并发秒数不作clean。|P0·04:55一次验收|[451](../research/451_WC_SIMPLE26D_PARTIAL_RESULTS_OOM_TERMINAL_AND_PAPER_IMPLICATIONS_20261015.md) · [预登记](../research/449_WC_DUAL_GPU_ACCOUNTING_AND_SIMPLE26D_COMPLETE36_PREREG_20261015.md)|
|N07 · 待补｜最终共同测试|`PAPER_E3_FROZEN_SHARED_TEST` → Common Frozen Evaluation Matrix|原模板8新prompt×2seed×10最终配置=160正式＋20预热；规模以完整费用事前登记。|C1/C2最终版本确认；C3覆盖|先冻结最终候选与强基线；417和R01输入已曝光，不重称下一版未见；拒绝/缺失保留。|P2·N05/N06后冻结|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N08 · 待补｜最终重复测速|`PAPER_E4_REPEAT_SPEED` → Balanced Repeated Clean Latency|两场景×五最终配置×三平衡轮=30正式＋10预热；同轮倍数/波动/质量并列。|C3稳定费用；C1/C2工作点复验|D07已完成但不是最终高保真重复；模型驻留、初始化和算法维护口径固定。|P2·最终版本冻结后|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N09 · 待补｜部署证据|`PAPER_E5_COST_PROFILE` → Calibration and Minimal Deployment Profile|拆必要离线标定、probe/warp/head/RF、选择/缓存维护、显存；已有报价有转移成分。|C3部署开销；C2费用一致|不能用历史全部GPUh当最小标定费，不能以D05 head次数当延迟；回本量须同保真真实净省时。|P2·最终实现后|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N10 · 待补｜最终质量维度|`PAPER_E5_AUTOMATIC_QUALITY` → Automatic Video Quality on Final Outputs|旧MUSIQ/抽帧VQA已做；最终共同视频的语义/一致性/闪烁/动态维度尚未统一。|C3生成质量范围；补充保真主指标|优先复用输出、冻结少量相关自动指标；不能把更静当更好，或子集评分称完整官方总分；不增人评。|P2·复用最终视频|[28](../research/28_W1_DEVELOPMENT_VQA_RESULTS.md) · [closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|N11 · 待补｜主张条件|`SECOND_MODEL_TRANSFER` → Second-Backbone Transfer|模型内接线pilot→必要q/g/费用标定→冻结共同测试；尚无本项目迁移结果。|C3跨骨干；若不做则限定Cosmos|原8/−7权重、36更新、step25不原样当新模型真值；模型/范围/费用待定。|P3-C·主张跨骨干时必补|[closure_plan](../plans/WORLD_CACHE_PAPER_CONVERGENCE_AND_FINAL_EXPERIMENTS_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|
|Z01 · 暂缓/未执行｜旧卡|`OLD_E2_FULL76 / OLD_P_REFERENCE_13H` → Legacy Deferred Cards|旧E2完整76、P参考双flow13.0600GPUh等历史卡保留。|不算当前待执行承诺|不由新文档重启、缩卡或借用授权；新P/W3及正式补验用各自完整登记。|X·暂缓，不恢复|[369](../research/369_WC_E3_COMPLETE64_RESULTS_SOURCE_READOUT_INTERACTION_AND_NEXT_20261012.md) · [424](../research/424_WC_FINAL_EXPERIMENT_CLOSURE_AND_PAPER_EVIDENCE_20261014.md) · [roadmap](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)|


## 接下来的顺序与论文用法

1. **R01→N01已完成：**455真实监督与456阶段区分均完成。仅时间与第23步规则解释T1几乎全部局部收益；建议简单阶段修订优先、T1作完整视频对照，先收完N06再决定整卡。目前没有新W3视频、内容自适应或加速结论。
2. **主稿N06有部分开发证据，完整收尾与N05仍待：**先诊断OOM，保持原六配置四场景及必要复验的事前登记；修复R2已完整启动，04:55验收。N06回答位置分配，N05回答强对手公平性。D14 fixed等价与本批三场景不能充当完整四场景优越性；并发时间不替代N08独占重复测速。D13/D14主结果继续保留，可同步写作。
3. **最终候选冻结后做N07–N10：**共同测试、重复测速、最小费用和相关自动质量分开承担证据职责。已有D07测速、D13确认保留，不重写成没做过；新测试不能重用已曝光输入冒称未见。
4. **P与组合保留选择权：**N03/04若有可购买的信号再投入，不强制P成功才允许论文收束；也不把“单模块必须先显著有效”设为组合的硬门槛。F/B不恢复。

资源快照以01:19原件为准：v2实结86.864053599／cap104.971363333，同26D R2完整预留8，可准入10.107309734 GPUh；本轮CPU没有新扣费、服务器查询或预算写。严格<12 GPUh的完整卡可按授权和fresh资源/余额准入推进，达到12需具体确认；本次没有选新视频卡，不能把待补模板视为已准入。

写作时，把D13/D14放主性能与修正消融，D09放来源机制，D07补计时说明；旧开发、CPU准备、F/B放复现材料或相关附录。若N02没有形成新工作点，C2仍可准确表述为“calibration-derived phase deployment”，不据此否定C1与已有两配置价值。若N05/N06尚未完成，保留现有实测比较，不提前写完整强基线前沿或同预算调度优越性。

统计身份继续沿用映射：420是四CAL/seed0开发、每格一次clean计时；417是四新prompt×seed17/43确认，RA一个拒绝保留，不能填完整八视频RA质量均值。两个工作点不拼接性能；LPIPS是Native相对保真，93帧不是93个独立样本；物理CC不等于语义C；P_OFF仍含P0。

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
