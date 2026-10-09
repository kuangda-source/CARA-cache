# H-T61：原生政策尾部边界CPU区分与接续

## 问题与价值

[H-T60](194_WC_FOUR_ACTION_COMPLETE_SAMPLER_CPU_RESULTS_20261009.md)完整证明了四动作、固定mask及共同DD保护合同下的Toy CPU接口。H-T58同S22真实CC／DD也已完整通过。它们都没有证明这个控制器在任意新输入上等价于原生WC自适应政策：counter68的条件分支可能原生选择C，而当前成对保护区会强制DD。

下一完整真实部署必须先说清这一点。H-T61按[执行前计划](../plans/WORLD_CACHE_NATIVE_POLICY_TAIL_BOUNDARY_CPU_20261009.md)，用低成本完整CPU区分原生政策与当前合同；不改旧controller、不是新的共同刷新／风险策略，也不推翻已完成同动作等价结果。

## 预登记与实际执行

原阈值0.08与合法高阈值1e6是事前固定的两个CPU输入条件，高阈值仅用来构造政策边界，不作部署候选。两flow×观察OFF／ON×二严格重复，共16比较／32完整36步路径／1152 solver更新／2304 net调用，直接比较576个guided张量、各完整状态、step22恢复、五检查点及终点latent。观察／重复须在各执行顺序内部保持一致；完整差异如实报告，不根据相等结果删分母。

共享controller、WC／RF／velocity和fixture源与H-T60完整112行通过证明逐字相同，保留并绑定该全量结果，本轮不重复未变整批，而新增原生自适应／尾部边界完整比较。原生参照保留原WC谓词；成对合法区仅逐槽返回PaidProbe.native_cache，保护区沿用现有DD。事前检验高阈值35步原生CD／当前DD；动作差异不直接推定视频质量差。

R1实际source`2ffec0c68832f8388a337abad347ec098acd005f`，100文件／8实际runtime源码，独立`.sync/wc-cfg-native-policy-tail-boundary-cpu-r1-20261009`。原supervisor／child3456780／3456781已退出1且消失，driver52.237968秒；在高阈值第一个比较的原生CD预测断言停止，未接受此前片段为通过子集。[完整失败原件](../reports/wc_cfg_native_policy_tail_boundary_cpu_r1_terminal_20261009_capture_and_independent_audit.json)及[实际启动](../reports/wc_cfg_native_policy_tail_boundary_cpu_r1_launch_20261009.json)保留，源／预算SHA前后相同、CUDA0、GPU0。

原实际WC在68／69仍执行自己的阈值判断，重置发生在forward之后。R1高阈值原日志两个槽漂移均远低于阈值，原56／70跳过、成对54／70；之前将无条件槽预设为D是错误的。新[H-T61-R2计划](../plans/WORLD_CACHE_NATIVE_POLICY_TAIL_BOUNDARY_CPU_R2_20261009.md)事前预测CC／DD，并把科学预测从提前抛异常改为完整数据的支持布尔值，无论支持与否都完成原16比较／32路径；原假设失败不删除，数据／controller／旧证明不改。

## R2完整结果及意义

source`f979de6d58629db3370eeff7032e9e7a2aa87fa1`、102文件／8源码，独立R2全部16比较／32路径实际完成并独立验收。原3457246／3457247退出0且消失；fixture87.130879秒，driver全wall**114.222398秒**，前后预算SHA同为1d2cf34794e0…，CUDA0／新GPU0／不写账本。[所有原字节和独立验收](../reports/wc_cfg_native_policy_tail_boundary_cpu_r2_terminal_20261009_capture_and_independent_audit.json)及[全部分组／旧真实尾部记录](../reports/wc_cfg_native_policy_tail_boundary_complete_summary_20261009.json)保留。

| flow | 阈值 | 原生／成对完整调用 | 动作不同位置 | guided不同位置 | 最终latent |
|---|---:|---:|---|---|---|
| OFF | 0.08 | 28／30 | 第35步CC／DD | 第35、36步 | 不相同 |
| ON | 0.08 | 28／30 | 第35步CC／DD | 第35、36步 | 不相同 |
| OFF | 1e6 | 16／18 | 第35步CC／DD | 第35、36步 | 不相同 |
| ON | 1e6 | 16／18 | 第35步CC／DD | 第35、36步 | 不相同 |

每行包含四个观察／严格重复控制，完整16行均保留；各执行顺序内部全部36guided、状态／条件／RNG、五检查点、完整恢复和终点在四个控制下相同。只有第35步动作不同，第35／36检查点与输出不同，当前成对合同额外执行两个深层分支；这是Toy CPU函数／政策边界证据，没有视频质量或真实部署耗时比较。新高阈值CC／DD预测在全部8个高阈值比较得到支持，旧CD预测仍定性为失败。

还独立核对H-T59原完整6父的第35行：Human seed2／seed3、Common seed3的OFF／ON共6条实际记录均为CC、deep=[0,0]。所以此边界与已曝光真实轨迹也有关，不只涉及新假想输入；没有实际运行当前全36成对政策，不能把CPU调用差追认为真实重新生成费用或终点损失。

**当前发现：四动作接口在同一个明确保护合同下等价，但当前DD尾部合同与原生阈值政策不等价。** H-T58真实S22同动作等价、两个原生父无扰动、H-T60同DD保护mask等价仍成立。应修正或明确尾部政策，而不是否定缓存、成对调度或用一个局部阈值给整个方向判失败。

下一H-T62先做独立源码变换和完整CPU原生等价控制：尾部两prefix仍先支付、各槽按原动作续算，counter验收按70周期取模；初始化／无历史／新周期保护和旧模块不改。复用未变共同源的完整证明，新增两阈值／两flow／观察／重复的完整原生对照和尾部异常／reset控制；通过后才选择完整真实模型卡与全费用。预算、方向和执行权限不变。

无真实权重／CUDA／新GPU／视频／终点或未来成本标签，不写账本。累计29.895246590／50GPUh、剩20.104753410GPUh／65提交，无GPU在途；原2B接口和四动作CPU全部完成，组会CLI revision24已全文回读、将加入本具体边界，旧科学结果／负例／RA近邻保持。goal active：继续必要接口修正CPU，随后完整真实部署及正确终点／未来成本；整卡>2GPUh具体确认，不缩拆／训练／扩稀疏／OMR／DRE／人评。
