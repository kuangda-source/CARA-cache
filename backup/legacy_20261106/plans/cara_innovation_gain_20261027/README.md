# 创新量增益探索 R1

依据用户“抓紧验证，结果后再决定是否并入主线”以及“双服务器兼容”的要求建立独立探索。附件六文件逐字保留在[source/](source/)，作为研究提案；执行授权来自本次用户请求。

**当前：用户于2026-10-27明确暂停IG后续分支。** 不执行B2/B3或系数搜索；B1完整结果和费用保留，已无运行任务。优先准备预测器—刷新机制线，见[718](../../research/718_CARA_IG_PAUSED_SCOUT_REUSE_AND_CPU_PREPARATION_20261027.md)。

B1真实模型验证及完整保存资产分析已结束，本轮具体Scalar/Band候选的停止结论保持。 两个留出方向均拟合到Scalar=1、Band=(1,1)，等于DEEP；相对训练prompt选出的固定A_PHASE，留出误差分别高62.2%/53.2%。完整结果与停止依据见[717](../../research/717_CARA_IG_B1_COMPLETE_BOX_ENDPOINT_RESULT_20261027.md)。含工程失败共1.452095GPUh已结算，GPU及CPU均退出；不启动重复的视频臂或范围修订。

两端采用同一科学源码和冻结参数，分别绑定A6000 SM86与RTX 6000 Ada SM89。[B1双端CPU接受](../../reports/cara_IG_grouped_dual_host_CPU_acceptance_20261027.json)及[B2条件入口双端CPU接受](../../reports/cara_IG_B2_dual_host_CPU_accepted_20261027.json)均完成；真实模型证据来自两卡，四卡目前验证到生产环境CPU路径。

[范围登记](../../manifests/cara_IG_scope_intake_r1_20261027.json)与[双端配置](../../manifests/cara_IG_dual_host_profiles_r1_20261027.json)：保留原六读出，Scalar/Band并行；轻收缩λ=.05，中心来自训练prompt。保存输入的24次端点控制使附录重放上界由84变为108，额外C参考head完整计费。B1为4完整父路径、12状态；B2拟46条完整路径，B3最多一次10路径修订。整轮与旧E1/E2合并上限7 GPUh，累计226不变。

原B1尝试因重复全状态拷贝与哈希超出成本假设而提前停止，0.582724GPUh已结算，原件保留；两状态部分输出不是科学结果。见[714工程诊断](../../research/714_CARA_IG_B1_HASH_OVERHEAD_AND_GROUPED_REPAIR_20261027.md)。R2仅重构隔离审计，逐读出完整恢复与私有输入复制保留，数值函数不变；原尝试成本计入同一轮，不重新获得7小时。

原V2.2/DEV128保持原样，本轮不使用DEV128部分指标拟合。完整B1后决定本轮停止，不进入固定布局视频验证；未获得完整视频质量或部署速度结论。两prompt留出属于开发证据，不称独立TEST。

历史准备回执：[712双端初验](../../research/712_CARA_IG_DUAL_HOST_CPU_AND_PENDING_MODEL_VALIDATION_20261027.md)、[原B1 CPU](../../reports/cara_IG_dual_host_B1_CPU_acceptance_r3_20261027.json)、[713原启动](../../research/713_CARA_IG_B1_EXCLUSIVE_A6000_LAUNCH_20261027.md)。这些记录的当时状态由当前回执更新，但原始失败和费用不覆盖。
