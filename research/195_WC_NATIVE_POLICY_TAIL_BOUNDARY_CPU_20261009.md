# H-T61：原生政策尾部边界CPU区分与接续

## 问题与价值

[H-T60](194_WC_FOUR_ACTION_COMPLETE_SAMPLER_CPU_RESULTS_20261009.md)完整证明了四动作、固定mask及共同DD保护合同下的Toy CPU接口。H-T58同S22真实CC／DD也已完整通过。它们都没有证明这个控制器在任意新输入上等价于原生WC自适应政策：counter68的条件分支可能原生选择C，而当前成对保护区会强制DD。

下一完整真实部署必须先说清这一点。H-T61按[执行前计划](../plans/WORLD_CACHE_NATIVE_POLICY_TAIL_BOUNDARY_CPU_20261009.md)，用低成本完整CPU区分原生政策与当前合同；不改旧controller、不是新的共同刷新／风险策略，也不推翻已完成同动作等价结果。

## 预登记与实际执行

原阈值0.08与合法高阈值1e6是事前固定的两个CPU输入条件，高阈值仅用来构造政策边界，不作部署候选。两flow×观察OFF／ON×二严格重复，共16比较／32完整36步路径／1152 solver更新／2304 net调用，直接比较576个guided张量、各完整状态、step22恢复、五检查点及终点latent。观察／重复须在各执行顺序内部保持一致；完整差异如实报告，不根据相等结果删分母。

共享controller、WC／RF／velocity和fixture源与H-T60完整112行通过证明逐字相同，保留并绑定该全量结果，本轮不重复未变整批，而新增原生自适应／尾部边界完整比较。原生参照保留原WC谓词；成对合法区仅逐槽返回PaidProbe.native_cache，保护区沿用现有DD。事前检验高阈值35步原生CD／当前DD；动作差异不直接推定视频质量差。

R1实际source`2ffec0c68832f8388a337abad347ec098acd005f`，100文件／8实际runtime源码，独立`.sync/wc-cfg-native-policy-tail-boundary-cpu-r1-20261009`。原supervisor／child3456780／3456781已退出1且消失，driver52.237968秒；在高阈值第一个比较的原生CD预测断言停止，未接受此前片段为通过子集。[完整失败原件](../reports/wc_cfg_native_policy_tail_boundary_cpu_r1_terminal_20261009_capture_and_independent_audit.json)及[实际启动](../reports/wc_cfg_native_policy_tail_boundary_cpu_r1_launch_20261009.json)保留，源／预算SHA前后相同、CUDA0、GPU0。

原实际WC在68／69仍执行自己的阈值判断，重置发生在forward之后。R1高阈值原日志两个槽漂移均远低于阈值，原56／70跳过、成对54／70；之前将无条件槽预设为D是错误的。新[H-T61-R2计划](../plans/WORLD_CACHE_NATIVE_POLICY_TAIL_BOUNDARY_CPU_R2_20261009.md)事前预测CC／DD，并把科学预测从提前抛异常改为完整数据的支持布尔值，无论支持与否都完成原16比较／32路径；原假设失败不删除，数据／controller／旧证明不改。独立R2实际CPU尚待。

无真实权重／CUDA／新GPU／视频／终点或未来成本标签，不写账本。累计29.895246590／50GPUh、剩20.104753410GPUh／65提交，无GPU在途；原2B接口和四动作CPU全部完成、飞书CLI revision24全文回读通过，旧科学结果／负例／RA近邻保持。goal active：继续CPU区分，随后完整真实部署及正确终点／未来成本；整卡>2GPUh具体确认，不缩拆／训练／扩稀疏／OMR／DRE／人评。
