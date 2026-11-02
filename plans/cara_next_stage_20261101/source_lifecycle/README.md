# V1：来源生命周期感知的预算规划

2026-11-01，按用户最新分层路线调整。**V1进入主线，完整离散伴随保留为V2。** 当前交付目标是从校准数据自动生成19D/22D计划，并接受完整视频验证。真实Cosmos/VAE反向不再是V1的前置条件；既有组件和原件保留。

## 方法与证据

[完整方法与证据对应](V1_METHOD_AND_EVIDENCE_MAP_R1.md)已对齐当前固定实现；[无标签设计几何审计](../../../reports/cara_v1_P1_label_free_design_geometry_r1_20261102.json)确认22种来源三元组、四折训练特征满列秩和三个来源跨度对照。实际标签预测与视频效果由完整P1检验。

固定Cosmos、实际36更新的UniPC、CFG7和纯C读出。候选自身当前状态支付shadow Dense，取实际CFG输出误差；不借Native另一轨迹作同状态真值，shadow不写回父轨迹。按噪声位置、当前真实D的sigma年龄、前两个D的sigma间距拟合固定低阶非负风险。首版三种嵌套特征为phase、phase+age、phase+age+gap，使用同一程序和候选额度。

连续真实D为a,b,c时，代理区间代价为`sum_{b<t<c} w[t]*q(t,a,b)`；`w`取固定原UniPC单步在冻结历史下对当前velocity的响应系数平方，包含本步corrector/predictor。它是数值尺度，不是终点敏感度。双来源DP在每次改变来源后重算受影响区间，精确优化这个代理；latent、UniPC历史和C工作状态被压缩后的影响，交由自由运行的完整视频检验。

[可运行DP](../../../src/wcomr/cara_source_lifecycle_planner_r1.py)已经通过小网格全枚举的top3对照、真实36网格精确19D/22D、来源条件重算和原UniPC系数检查；[本地五项](../../../reports/cara_source_lifecycle_DP_CPU_component_r2_20261101.json)。目前使用合成风险，未拟合真实V1、未产生真实方法视频。DP不是单独的创新主张。

[原R2 Linux CPU](../../../reports/cara_v1_Linux_CPU_accepted_r2_20261101.json)现已退出0并接受，72.014秒：15项状态/DP/覆盖控制与第8/20步共24条完整tiny路径通过。原R1缺少打包模块的失败保留，未改原stage。复用原件，不重复验证这些已完成控制。

## P0：复用第8步，补第20步

[原M1完整14](../../../research/834_CARA_M1_COMPLETE_READ_WRITE_MECHANISM_AND_M2_CONTINUATION_20261101.md)直接作为第8步证据，不重跑或重评分。两FIT/seed0：平均`W_C=L00−L01=0.09436819`、`W_D=L10−L11=0.08329722`；两读出条件的写入收益均为正。原费用1.500620266GPUh已唯一结算，检查已删除。

新增第20更新由“序列中点之后首个C/C”确定。仍为同一Uniform19：第8步写入来源被C9–15及C17–18读取、D19后被替换；第20步的预定直接消费者为C21，D23后离开最近两来源。前者直接消费记录从原完整history复用，后者现已由第20步完整原history确认，见844完整结果；这些直接来源记录不等同于完整因果影响终点。

两个FIT×两个状态×四格=16个科学位置，其中8个第8步位置复用、8个第20步位置新增。新卡按原完整请求方案计14条：8科学四格、4独立Uniform/D20控制、2 fresh Native，共512paired调用。00对Uniform、11对额外D20的20D控制；混合四格保留完整y/cache分组。新增Point20入口已通过flow OFF/ON各6条完整小权重CPU路径，[回执](../../../reports/cara_v1_point20_CPU_component_r1_20261101.json)；真实权重14路径及8新评分现已完整接受，并与旧8合并；原CPU准备及完整GPU结果分开保存。

[独立Point20完整14范围](P0_POINT20_FULL14_MANIFEST_R1.json)、整卡执行/释放/评分绑定现已完成：原Linux77项控制、28条loaded tiny完整请求、8对93帧合成真实指标和2Native桥接接受；原CPU退出0，新16GiB独立卷/48MiB journal及固定GPU源接受。见[837记录](../../../research/837_CARA_P0_POINT20_COMPLETE_PREPARATION_AND_CENTRAL_AUTHORIZATION_20261102.md)与[完整执行审阅](P0_POINT20_EXECUTION_REVIEW_R1.md)。预计1.60476/硬1.95GPUh；用户2026-11-02已许可仅本卡原账本读取、预约与结算，原卡已于2026-11-02 01:24:19.536402+08实际开始并于02:53:12结束，14/14、工件与8评分完整接受，实际1.481354486595115GPUh唯一结算，两检查已删除；见[844完整结果](../../../research/844_CARA_P0_TWO_POSITION_COMPLETE_RESULTS_AND_V1_CONTINUATION_20261102.md)。原M1八行原样复用；当前卡及原M1均不可重派或重评。

报告W_C、W_D、读出、总收益和交互，不从部分结果挑条件。按有消费者位置的重复可辨写入作用及可信状态拆分决定是否继续，不设机械5%线。原35步附近“无未来C消费者”的写缓存交换已在原算子小权重CPU上得到剩余latent逐值相同控制。完整缓存仍保存三个物理槽和全部工作状态，不能把“两来源代理”误用成只保存两个张量。

## P1：完整V1与公平搜索

**当前P1完整CPU、唯一GPU源包和独立64GiB存储已接受，正在等待单次GPU/账本审批。** [857完整准备](../../../research/857_CARA_P1_WHOLE_CPU_COMPLETE_PORTABLE_DELIVERY_AND_GPU_SOURCE_20261102.md)与[审批卡](V1_P1_SINGLE_CARD_REVIEW_R1.md)为当前入口：146语义／最多142物理，保守预计18.02734GPUh、硬19GPUh。最近49.82GiB内存快照低于52GiB，批准后仍须实时准入。下列845–849为保留的阶段性准备记录；已结束原件不重跑，旧13.0989GPUh草案不用于启动。

[849监督服务共同收尾](../../../research/849_CARA_P1_GUARDIAN_FIT_LINUX_CPU_AND_SNAPSHOT_COST_AUDIT_20261102.md)新增原Linux34控制无skip接受，五原进程场景验证同一guardian时钟、服务/GPU替身失败关闭与未知保留，原CPU结束。完整生产总入口和释放后146接受仍待；快照费用经旧P0完整元数据复核须重新论证，13.0989GPUh草案尚不可冻结，P1 GPU与中央许可仍无。

[848完整算法与宿主评分CPU接受](../../../research/848_CARA_P1_ALGORITHM_AND_ACTUAL_HOST_FIT_CPU_ACCEPTANCE_20261102.md)：原R3已退出0，两flow完整292语义/128标签/268实际tiny请求/158对合成93帧指标接受，caller状态与绑定恢复通过。独立宿主FIT探针也已结束：两完整成功请求、一次预设编码失败保留2分母、重复和终态恢复零新派。原内部评分核不改；无真实V1结果。两项R3检查均已删除。下一步补整卡guardian与宿主服务的原时钟/失败关闭、释放后完整接受及正式报价，P1 GPU与中央事务仍另审。

[846单flow与绑定修复](../../../research/846_CARA_P1_FIRST_FLOW_ORIGINAL_CALLER_RESTORATION_AND_HOST_BROKER_20261102.md)：原R2 CPU首flow完成146语义/140实际请求、64标签和82对合成真实指标，但外层`net.forward`绑定未还原，第二flow未到达，整体验收未通过。生产入口已修复成功/恢复/失败时的调用者绑定，准备独立R3完整双flow、3600秒CPU；原件保持。宿主broker另有九项本地控制，真实Linux独立容器接受待补。

[845完整算法与公平比较准备](../../../research/845_CARA_V1_P1_WHOLE_ALGORITHM_INTERNAL_FIT_AND_FAIR_SEARCH_PREPARATION_20261102.md)已将64标签、三组固定估值、两预算各top3、完整FIT选择、CHECK和新LPIPS搜索接通，本地33项控制通过。原132草案漏14个必要预热/控制，完整上限修正为146；真实加载与独立指标CPU尚待当前新run接受，宿主CPU broker/完整终态接受/正式报价仍待。当前无真实V1结果或新GPU授权。

[108行原件覆盖审计](../../../reports/cara_v1_S108_source_coverage_audit_r1_20261101.json)确认39种(t,a,b)；真正C状态的56行shadow Dense仅17种组合，没有固定阶段/当前年龄、改变前来源间距的对照。全部108行中的六组这种对照来自D父状态反事实。旧S标签保持原用途，不直接拟合任意新来源组合。

[新64标签设计](V1_CALIBRATION64_DESIGN_R1.json)采用sigma最远点与更新索引最远点两种通用规则，各生成19D/22D，共四父计划×两FIT。每父最多8个C状态，只使用sigma和动作结构选择。设计包含三组固定阶段/当前年龄而改变前来源间距的C状态对照，不用F19位置或实测误差初始化。按整条父计划跨两个FIT留出，禁止随机拆相邻行。

固定二次多项式嵌套特征与ridge1e-4，训练样本按输入等权；预测截为非负，完整公开截零比例与来源外推范围。不搜索网络、阈值或特征阶数。原始目标为同状态两次实际FP32 CFG运算输出差的FP64均方，不沿用S的teacher-energy归一化风险冒充新目标。

[固定估值/完整FIT选择组件](../../../research/839_CARA_V1_FIXED_ESTIMATION_AND_COMPLETE_FIT_SELECTION_CPU_20261102.md)现已本地11项CPU接受：64标签结构、整父计划4折、三组特征/同DP/19D与22D各top3、全93帧输入等权选择及拒绝控制跑通。参见[实现细节合同](V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json)、[离线CLI](../../../scripts/fit_cara_source_lifecycle_v1_r1.py)与[回执](../../../reports/cara_v1_fixed_estimation_CPU_component_r1_20261102.json)。使用合成标签和尺度；真实采集、生产来源接受和完整Linux入口仍待，无真实拟合或视频收益。

[标量原缓存入口的R3 Linux组件](../../../research/843_CARA_V1_SOURCE_SCALAR_COMPLETE_LINUX_CPU_ACCEPTANCE_20261102.md)现已退出0并完整接受：13控制、32完整tiny请求、128同状态标签；所有带shadow父请求与独立普通请求的latent/mock RGB逐值一致，实际CLI接通64标签到18个候选位置。[原接受](../../../reports/cara_v1_scalar_Linux_CPU_accepted_r3_20261102.json)和[一次固定的原UniPC数值尺度](../../../reports/cara_v1_frozen_UniPC_current_input_scale_r1_20261102.json)复用，不重跑。R1/R2失败保持；仍无真实模型校准/视频结果，完整P1生产组合和GPU审批另待。

三个估值器均用相同双来源DP，分别在19D/22D各取至多3个不同的最低代理计划，完整两FIT全93帧LPIPS按预定规则选择一次，再看旧CHECK。选择以输入等权Alex最小，完全相同时按代理成本、D序列字典序；旧CHECK只作已曝光开发检查。共享指纹可复用同一生成/评分，独立计时控制保留物理槽，所有别名/未用上限位置有完整账目。

强对照包含Uniform19/22、F19-C、F19-A1、原一次冻结BudgetSearch19和新LPIPS目标搜索。原RGB-MSE搜索赢家不改。新搜索仅用两FIT，沿用相同初始Uniform、合法空间、完整成对查询和SA+HC接口；为19D/22D分别记录实际校准费用限制。共享采集成本只计一次、按两个预算各半归属V1；新搜索的每预算允许费用等于对应V1实际采集份额、完整候选评分和同口径共用参考费用，包含持卡等待CPU与重算，不以相同允许上限声称已实耗匹配。

P1继续条件是full相对Uniform和单来源有真实终点增量、19D进入F19附近且同程序22D有效、来源消融可解释、校准费用可接受。`LPIPS≤1.10×F19-A1，T_DD≤1.05×F19-A1`仅为同批口径工程筛选目标，不替代科学判断，不修改旧门槛。机制成立但规划不足时，仅允许一次针对明确覆盖/遗漏条件的修订。

## P2/P3与论文

P1通过后开始论文主体，优先另行登记约8个未参与选择的新DEV和同实际延迟强对照，再在预定子集验证50请求/51实际更新。特征、DP与选择规则保持，数值重校准费用单列。原最终16与备用16继续保护，新DEV须另做元数据/曝光审计。

P3先在V1同一批少量合法交换上做一次有界终点响应排序增强；新增响应费用后仍有净收益才继续。完整状态伴随再单独验证真实前向、导数和硬交换，不阻塞V1稿件。V2无净收益则保留冻结V1并停止增强。

全93帧LPIPS为主指标、输入等权；PSNR/SSIM、相对Native的时序变化与盲评为补充。T_DD、完整请求和校准GPUh并列，保留失败/拒绝/缺失分母。论文聚焦来源条件化估值的可验证增量：[CEM](https://arxiv.org/html/2512.23258v2)已有离线误差与DP，[LeMiCa](https://arxiv.org/html/2511.00090v1)已有全局误差加权缓存图，[BudCache](https://proceedings.mlr.press/v306/lei26j.html)已有预算终点搜索，[GPH](https://arxiv.org/abs/2609.39343)已有共享计划迁移论证。

## 费用与执行

[原完整范围与费用草案](P0_P1_SCOPE_AND_COST_DRAFT_R1.json)保留为历史初算；现已发现漏计14条必要预热/控制，见[146位置与费用修正审计](V1_P1_SCOPE_AND_COST_AUDIT_R1.json)。正式报价还须计入新的搜索费用上限、broker/CPU持卡等待与snapshot开销。6GPUh是用户建议的研发设计上限，尚未批准或冻结；当前完整top3矩阵超过6，不能靠漏掉必要对照、回放旧分数或拆卡规避阈值。

用户已明确[先补P0，完整P1另审预算](P0_FIRST_P1_SEPARATE_BUDGET_DIRECTION_R1.json)。这是设计方向，未批准完整P1或新四卡账本例外。第20步已完整接受且不重做；继续完整P1生产组合和报价，后续单独提交。

当前P0两状态已完整接受：[844结果](../../../research/844_CARA_P0_TWO_POSITION_COMPLETE_RESULTS_AND_V1_CONTINUATION_20261102.md)，新14/8评分与旧8复用、图表、释放/唯一1.4813544866GPUh结算完成，GPU/CPU退出，两检查已删除。新标量R3 CPU13控制/32tiny/128标签也已接受。复用原件；完整P1生产组合与预算另审，尚未授权。单张整卡按<2自主、2–4说明后推进、>4单独批准，始终保留fresh准入。中央cap226与旧16.5保持；原M1例外已结束，新P0只依据本卡新许可。

本卡的半程/终验已按实际开始处理，完整接受后均已删除，见[关闭回执](../../../reports/cara_v1_P0_point20_acceptance_schedule_r5_20261102.json)。未来长程新卡仍须实际开始后安排半程与终验，准备阶段不预建重复监控。

## P0完整两状态结论

第8/20步只写入的输入等权LPIPS分别下降19.51%/0.64%；W_C为4/4输入状态正，W_D为3/4，Human199第20步轻微负。新来源的直接消费者/替换分别为C9–15、17–18/D19和C21/D23；两位置同时改变阶段/年龄/间距，不能独立归因于消费者数量。P0支持写入价值的条件性与继续准备V1，不确立自动规划器。后续完整P1按原top3/强对照/同费用LPIPS搜索报价与审批推进，不改旧门槛或自动新GPU。
