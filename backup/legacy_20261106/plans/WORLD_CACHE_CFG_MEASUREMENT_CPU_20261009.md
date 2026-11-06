# H-T47：统一测量位置与有效条件区域的CPU验证

2026-10-09。接续[170实际抵消结果](../research/170_WC_CFG_GUIDED_TEACHER_COMPLETE_RESULTS_20261009.md)与[171联结边界](../research/171_WC_CFG_TEACHER_ENDPOINT_LINK_CPU_RESULTS_20261009.md)。已曝光Human seed2的局部误差和旧终点；本轮只验证新记录契约，不重写旧原件或判据，不证明跨卡gt_frames一致。

新增记录区分四个位置：sampler起点latent、经过原denoise条件替换的实际net输入、scheduler.step原返回、原循环解出的下一latent。各张量记录dtype/shape/device/原tree_digest。原记录保留，不能将某两个位置的摘要不等解释成数值漂移。

实际net条件额外记录gt_frames全张量和condition_video_input_mask，mask必须有限且二值、可广播到gt_frames；有效区域采用展开mask后按固定扁平顺序选出的gt值，记录元素数与独立摘要。全量不同而有效值相同只说明本记录区域同值，不追认原完整条件相同。全零mask显式记录零个有效元素，不用epsilon或虚构质量分数。

CPU先验证：同值不同dtype/空间区别、有效区域不变与改变、零mask、非法/nonfinite/不可广播mask拒绝、输入不变和RNG不变；再用原实际Cosmos CFG/denoise/冻结条件/UniPC和Toy权重执行完整2父/5起点/4动作/2重复、flow OFF/ON两组及原六类失败回滚。旧80对/240张量与全部控制保留，新增记录缺失或重复不一致拒绝控制。Toy CPU不提供真实模型质量、显存或GPU收益。

脚本和完整载荷先提交/推送，部署独立CPU目录，禁止CUDA与下载；原r1终态源目录封存不修改。完整CPU与原始张量独立重建通过后，才准备有限未曝光身份卡、实际生产CPU和完整费用预测；下一GPU仍未选择/派发。当前26.279085386/50GPUh、无在途，单次≤2GPUh自主、>2GPUh具体确认，不拆控制、重复或状态。
