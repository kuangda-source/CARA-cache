# E1读出准备与E0 Native-relative诊断

已实现六逻辑候选同状态入口、源码精确WC/RF转换与原phase alpha；本地11项小张量检查通过，含六状态×双flow旧A一致、顺序打乱、故障回滚和拷贝预算拒绝。真实父采集、双端和整卡CPU尚未接受。DCTA同时保留官方组件未混合输出和公共phase输出，不把组件对照称为完整DiCache。

旧CAL66的12视频1116帧CPU补充诊断已完成：A对Native的空间梯度MSE比C降低24.23%–36.34%，四输入同向；固定轻模糊C也降低3.41%–27.32%。这说明平滑与参考误差改善可以并存，不足以判定最终质量或唯一因果。原MUSIQ门保持，未对新DEV做任何科学读取。

详细入口、证据和费用缺口见[接续说明](../plans/cara_predictor_refresh_scout_v2_20261026/E1_ENTRY_PREPARATION_R1.md)、[最终CPU原件](../reports/cara_scout_readout_CPU_v22_r3_20261026.json)、[旧视频诊断](../reports/cara_CAL66_native_gradient_fixed_blur_20261026.json)、[双端资源草案](../manifests/cara_scout_E1_resource_draft_v22_20261026.json)。草案不等于完整报价：示例隐藏特征就约26.58GiB，真实峰值/范围/teacher和I/O计时待绑定；不沿用约1GPUh作为执行上限。

本轮无GPU提交、无新预约、无运行stage或已接受模块变更。只读取回已结束CAL66的四个Native视频，3.25MB；DEV128保持原半程、释放后评分、终态安排。下一步先接真实Shared25-C父状态及完整控制，再补双端CPU/生命周期和完整报价。
