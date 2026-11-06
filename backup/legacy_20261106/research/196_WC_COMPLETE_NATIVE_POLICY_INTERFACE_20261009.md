# H-T62：修正尾部联合决策后的完整原生接口验证

**完整服务器CPU与本地独立原件验收已通过。** source `37e954b6b3dbfa99b261ed88710c7bab85d72bed`，112冻结载荷／8实际源；3458243／3458244均退出0且消失，fixture98.469217秒、完整driver125.369907秒。全16比较／32完整路径的576实际guided张量直接torch.equal、最终latent、实际动作／访问、50状态分量／五检查点、条件／RNG、step22扰动恢复，以及观察／重复均一致。尾部两prefix28次决策／counter68、69与周期重置实际覆盖。全部4尾部异常／非法动作控制在34步后拒绝，poison拒绝继续、整fixture弃置；不宣称任意异常回滚。

| Toy CPU设置 | 原生第35步 | 修正接口第35步 | 全36步完整调用（原／新） | 全部guided／最终latent |
|---|---|---|---|---|
| 阈值0.08，flow OFF | CC | CC | 28／28 | 相同 |
| 阈值0.08，flow ON | CC | CC | 28／28 | 相同 |
| 阈值1e6，flow OFF | CC | CC | 16／16 | 相同 |
| 阈值1e6，flow ON | CC | CC | 16／16 | 相同 |

每行含观察OFF／ON×两个严格重复；完整分母20行全量通过。[独立验收](../reports/wc_cfg_complete_native_policy_cpu_r1_terminal_20261009_capture_and_independent_audit.json)保存原件SHA和完整范围，全部原始回执／日志／结果gz保留。旧H-T61 CC／DD差异和原R1失败不删；本轮说明修正可恢复Toy全周期原生政策等价，不是新策略质量／速度优势，也不是2B全36部署。新增GPU0，预算原字节SHA不变，29.895246590／50GPUh保持。

下一准备真实2B完整36步原生接口等价卡，保留曝光Common／Human、观察切换、严格重复、全部输出与费用，不把S22局部通过当作全轨迹通过。完整GPU费用估计／源和资产CPU验收后，按现有≤2自主、>2具体确认规则执行；本轮尚未选新GPU。以下保留执行前登记。

本轮继承[H-T62计划](../plans/WORLD_CACHE_COMPLETE_NATIVE_POLICY_INTERFACE_CPU_20261009.md)，修复[H-T61](195_WC_NATIVE_POLICY_TAIL_BOUNDARY_CPU_20261009.md)已经定位的接口合同差异：原生第35步可CC，而旧接口共同DD。旧实现、完整失败、同动作等价和真实S22结果均保持。该修正是后续新政策实验的必要对照，不是独立新方法成果。

新增独立 `NativePolicyPairedExecutor`，仅在固定base方法上变换五个唯一AST站点：四动作集合／逐槽续算／错误信息、counter68／69的合法联合决策、续算counter按70周期取模。精确逆AST相等、原base源SHA固定；初始化／无历史／warmup／新周期、两prefix先支付、源绑定和异常poison保持。静态证明中的实际模型／完整采样验证字段仍为false，不能用编译证明代替CPU或GPU结果。

已冻结[完整CPU登记](../manifests/wc_cfg_complete_native_policy_cpu_r1_preregistration_20261009.json)：112载荷／8实际runtime源，默认0.08与高阈值1e6、flow两配置×观察两配置×两严格重复，16原生／新接口比较、32完整36路径、1152solver／2304net、576实际guided直接比较；再加两flow的尾部selector异常／非法动作4控制，共20行。成功路径实际尾部必须支付counter68／69两个prefix并重置0，随后第36步以counter0执行；失败34步后整fixture弃置、poison拒绝继续，不声称任意异常完整回滚。未改变的H-T60全112及H-T61完整16按原SHA复用，不挑通过子集。

当前本地语法、固定源和五站点逆AST检查通过；登记不是CPU执行，真实服务器CPU与独立原件验收待。新GPU0、CPU不写账本，最新结算29.895246590／50GPUh保持。完整CPU通过后准备真实2B全36政策等价卡与完整费用估计，再测新策略终点及未来成本。整卡>2GPUh具体确认，不缩拆、训练、扩稀疏、OMR／DRE或人评。
