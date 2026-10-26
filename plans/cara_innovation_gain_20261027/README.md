# 创新量增益探索 R1

依据用户“抓紧验证，结果后再决定是否并入主线”以及“双服务器兼容”的要求建立独立支线。附件六文件逐字保留在[source/](source/)，不是既有GPU结果或独立授权来源。

**当前：同一科学代码在两卡A6000、四卡RTX 6000 Ada上完成GPU隐藏CPU兼容验证；尚无真实模型结果、GPU提交或预算预约。** 本轮优先核查两卡。完整记录见[712](../../research/712_CARA_IG_DUAL_HOST_CPU_AND_PENDING_MODEL_VALIDATION_20261027.md)，双端回执见[CPU接受](../../reports/cara_IG_dual_host_CPU_acceptance_r2_20261027.json)。

每端通过8项单元检查、8条采集CPU路径、20条自由运行CPU路径、6个故障边界。支持Scalar/Band、actual-guided四角/中点、prompt留一拟合、唯一真D锚点流式保存、保存后FULL/DEEP重放。IG端点在整个36步CPU轨迹复现FULL/DEEP；部署复用已付C输出，额外一对head。原V2.2/DEV128不变；小权重CPU控制不代表模型质量或CUDA兼容结果。

[范围登记](../../manifests/cara_IG_scope_intake_r1_20261027.json)与[双端配置](../../manifests/cara_IG_dual_host_profiles_r1_20261027.json)：保留原六读出，Scalar/Band并行；轻收缩λ=.05，中心来自训练prompt。保存输入的24次端点控制使附录重放上界由84变为108，不在计费中隐藏额外C参考head。整轮与旧E1/E2合并规划上限7 GPUh、累计226不变。B2拟46条完整路径，B3最多一次10路径修订，均在同一轮上限内。

两卡GPU现无计算进程，原DEV128 CPU评分仍在CPU0–1运行；其中央预算责任尚保留。新配置建议CPU2–3，启动时重新核查。原通用准入对“已释放GPU、CPU仍评分”尚需精确区分；不提前结算或覆盖原任务。

下一步：完成真实形状/显存/存储和整卡费用、GPU生命周期绑定及准入，然后取得B1真实输出；有可利用信号再做固定布局完整视频与原独立质量门。当前不能判断并入主线，不把开发留出叫独立TEST。

## B1执行回执

两台服务器最新[B1整卡CPU接受](../../reports/cara_IG_dual_host_B1_CPU_acceptance_r3_20261027.json)绑定`667afb05`。2026-10-27已在两卡GPU0独占启动，见[713](../../research/713_CARA_IG_B1_EXCLUSIVE_A6000_LAUNCH_20261027.md)。该进展取代前文“未提交”的当时状态；没有结果前不决定并主线。
