# 现有两卡CPU联结：执行轨迹部分对应，完整输入与记录空间未完全对齐

2026-10-09。先登记并推送[H-T46](../manifests/wc_cfg_teacher_endpoint_link_cpu_preregistration_20261009.json)于509ca46，标准库CPU脚本ee615b5推送后执行。**旧固定配额四组合与新教师对应计算的16组网络输出/deep/cache全部相同，8个原求解器一步输出与历史对应；严格全字段联结未通过。** 保留所有原不同项，未删字段、改登记门或重新生成。预算仍26.279085386/50GPUh，无新GPU、训练或人评。

## 怎样联结

固定映射为BASE CC→DD、CFG0 DC→CD、CFG1 CD→DC、PAIRED DD→CC。四旧细胞各两重复，比较45/46对应新S22，47/48对应自己实际S23，共16个两调用联结、8个S22组件对照、8个原一步/历史桥。两个完整卡的原回执和独立审计均绑定SHA，所有重复保留。终点loss与H-T45局部误差已经曝光，本分析是探索性联结，不是独立CONF。

## 实际结果与不匹配

| 比较 | 相同/总数 | 含义 |
| --- | --- | --- |
| 完整两调用inputs/outputs/deep/banks同时相同 | 0/16 | 严格全字段联结不通过 |
| 网络输出摘要 | 16/16 | 实际net预测摘要对应 |
| deep计数及cache banks摘要 | 各16/16 | 缓存/完整动作与缓存结果对应 |
| 完整网络输入字典 | 0/16 | 两槽的差异字段均为gt_frames；其余输入字段包括实际x、timestep、mask、crossattn等对应 |
| S22全部1216组件相同 | 0/8 | 每次差异均为output与solver._internal_dict，其余1214组件相同 |
| 原一步solver返回值摘要 | 8/8 | 旧第一update与新根首重复的实际solver返回相同 |
| 旧solver返回值直接比新子起点latent摘要 | 0/8 | 记录空间不同，不能直接当数值不一致 |
| call46结束历史对S23自己的历史 | 8/8 | 四个实际分支的刷新来源对应 |

[原结果](../reports/wc_cfg_teacher_endpoint_link_cpu_results_20261009.json)保留全部每字段旧/新值与组件差异。原S22的历史8/8相同；solver数值配置8/8相同，原字典中`_use_default_values`名称列表的顺序不同。名称集合相同不能追认原字典相同，也不能把顺序差异写成求解器数值配置已变。

源码解释了两个摘要不能直接比较的记录位置：旧`rv0_cfg_budget_causal.py`在net.forward前用实际`x_B_C_T_H_W`生成pre45组件；新`cfg_teacher_sampling.py`/`GuidedTeacherFork`在完整solver更新后捕获sampler latent。旧solver_outputs对scheduler.step原返回整体作tree_digest；新child起点对原循环解出的latent作digest。原件中的两个同空间solver返回摘要8/8对应，网络x摘要亦对应；跨空间摘要不等仍按登记结果保留，不能凭它宣布真实latent不同或完整状态已通过。

`gt_frames`全张量摘要跨卡不同，当前旧卡未保存其实际张量/有效mask区域摘要；不能从相同输出或相同mask推断该字段相同。旧pre47全部组件与旧post-denoise有符号向量均UNRECORDED，未补造。条件帧替换也可能使用gt_frames，不能仅凭raw net输出相同追认post-denoise速度逐位一致。

## 科学价值与下一步

[170机制结果](170_WC_CFG_GUIDED_TEACHER_COMPLETE_RESULTS_20261009.md)是在新卡内部同状态、完整条件、全部重复和OFF/ON严格无扰动下得到，跨卡完整联结未通过不否定它。当前可说新卡存在真实分支误差抵消，且相应raw net/cache/求解器输出与旧例有记录联系；尚不能说旧例全部条件/速度/状态相同，或局部抵消是旧终点退化的唯一原因。

下一轮先统一测量位置：分别记录sampler latent和net实际x的dtype/shape/SHA、scheduler.step原返回与解出latent的各自摘要；同时记录gt_frames全部与实际条件mask有效区域的摘要、post-denoise两个速度与实际CFG。保留原字段和失败，不改旧判据。再准备一个有限未曝光seed/场景的完整四动作机制确认，已有两父无扰动/5起点/全部重复保持，先CPU生产验证、完整成本和fresh资源，≤2GPUh自主、>2GPUh具体确认。

本轮实际CPU完成，无重要资源阻碍，整体goal active。暂不训练Head/LoRA或扩展模块，也不需要人工评审。当前下一GPU未选定或派发，原两个完整GPU身份均已消耗，不重投。
