# 创新量增益探索 R1

依据用户“抓紧验证，结果后再决定是否并入主线”以及“双服务器兼容”的要求建立独立探索。附件六文件逐字保留在[source/](source/)，作为研究提案；执行授权来自本次用户请求。

**当前：分组审计R2通过双端CPU复核，并在两卡GPU0独占运行；真实模型完整结果尚未接受。** 两端采用同一科学源码和冻结参数，分别绑定A6000 SM86与RTX 6000 Ada SM89。见[双端接受](../../reports/cara_IG_grouped_dual_host_CPU_acceptance_20261027.json)及[715启动记录](../../research/715_CARA_IG_GROUPED_R2_DUAL_HOST_AND_A6000_LAUNCH_20261027.md)。四卡兼容目前验证到生产环境CPU路径，尚未做四卡真实模型运行。

[范围登记](../../manifests/cara_IG_scope_intake_r1_20261027.json)与[双端配置](../../manifests/cara_IG_dual_host_profiles_r1_20261027.json)：保留原六读出，Scalar/Band并行；轻收缩λ=.05，中心来自训练prompt。保存输入的24次端点控制使附录重放上界由84变为108，额外C参考head完整计费。B1为4完整父路径、12状态；B2拟46条完整路径，B3最多一次10路径修订。整轮与旧E1/E2合并上限7 GPUh，累计226不变。

原B1尝试因重复全状态拷贝与哈希超出成本假设而提前停止，0.582724GPUh已结算，原件保留；两状态部分输出不是科学结果。见[714工程诊断](../../research/714_CARA_IG_B1_HASH_OVERHEAD_AND_GROUPED_REPAIR_20261027.md)。R2仅重构隔离审计，逐读出完整恢复与私有输入复制保留，数值函数不变；原尝试成本计入同一轮，不重新获得7小时。

原V2.2/DEV128保持原样，本轮不使用DEV128部分指标拟合。完整B1实际输出后再决定固定布局视频验证；只有后续完整视频、原独立质量门及完整请求费用才能支持主线决策。两prompt留出属于开发证据，不称独立TEST。

历史准备回执：[712双端初验](../../research/712_CARA_IG_DUAL_HOST_CPU_AND_PENDING_MODEL_VALIDATION_20261027.md)、[原B1 CPU](../../reports/cara_IG_dual_host_B1_CPU_acceptance_r3_20261027.json)、[713原启动](../../research/713_CARA_IG_B1_EXCLUSIVE_A6000_LAUNCH_20261027.md)。这些记录的当时状态由当前回执更新，但原始失败和费用不覆盖。
