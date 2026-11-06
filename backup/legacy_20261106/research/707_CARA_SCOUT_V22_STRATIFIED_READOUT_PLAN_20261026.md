# 707：E1 V2.2分层读出探索计划登记

2026-10-26。按用户来稿增量登记，保留V2原文件及既有实验合同；没有新GPU/服务器操作或生成。

- [修订说明](../plans/cara_predictor_refresh_scout_v2_20261026/E1_V22_AMENDMENT_AND_FREEZE_CHECKLIST.md)与[增量YAML](../plans/cara_predictor_refresh_scout_v2_20261026/SCOUT_REGISTRY_PATCH_V22.yaml)：global/long双路线、全队列最强固定基线分母、固定j0与j1规则、局部梯度只诊断、E2-R先于条件E2-I。
- [状态元数据](../plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json)：Shared25-C的22/23/25/33/34/35及两个旧CAL，短长各6点；主sigma网格与两真锚点复算。尚未通过新预测器支持/实际状态恢复CPU，不冒充完整冻结。
- [检查原件](../reports/cara_scout_V22_plan_and_state_metadata_20261026.json)：V2/DEV128执行块未变。原MUSIQ/锐度已做，新增梯度和轻模糊对照待做。
- E2-R和I各16逻辑输出；若完全同身份可共享8条则合计24，否则32；Native/强参考/warm/重复/评分另报，旧2–3GPUh不可直接沿用。

DCTA commit、数值容差、费用/显存门、双端真实CPU和完整报价仍待完成；不增加授权/预算，不读取DEV128部分结果、不修改自动检查。
