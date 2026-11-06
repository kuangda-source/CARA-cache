# 真实PA12生产入口CPU与完整原件审计接口

2026-10-15，接续431。**实际生产入口已在原服务器CPU接受，真实输入/参数/资源身份与完整8父路径配置通过，原任务结束；仍没有实际模型或新P端点/价格。** 本轮完成runner和post接口，下一为GPU监督/启动接线与完整准入准备，当前新GPU仍停止。

## 已实现的完整入口

`run_wc_p_acr_local12_profile528_r1.py`使用实际 `SetupArguments`/`InferenceArguments`、原H1 batch、原受保护Inference/UniPC/RF。一次加载后四CAL各执行普通H1与诊断H1：8完整父、固定12点、五动作各1预热3正式、全528pairs/1056CFG。诊断使用已接受Profile20的quiet模式，原父输出36次、动作、A历史和终态仍比较同驻留普通父与冻结H1参考。原gamma0.7235237/表/开发coeff和source时钟保持。

8个计划位置从开始就完整列出；文本/视频拒绝与未运行保持，完整36采样后的视频拒绝仍保存向量和已有点原件，不换输入或缩分母。实际技术异常保留全8状态和错误，不冒称完成528。

GPU模式在导入Torch/native模块前要求具体新卡许可与本卡生产CPU；旧预算权限不能解除新GPU停止。当前没有新许可，也未派发任何GPU。

## 原件与评分接口

完整输出是12点21项/40tensor、8父37tensor，共20原件/776tensor。post先核对文件SHA、大小、所有分支、补偿公式、CFG Gram、重复/计时顺序、20恢复和源不更新，再比较全部36父向量/动作/终态与原H1。

8个位置的接受视频逐个完整解码93帧，检查RGB原H1等价，并按既有匹配Native执行全93帧CPU LPIPS；拒绝/缺标签保留。**这些视频是原H1父路径，评分不是新ACR策略的终点结果。** 真单支误差与每次构造已加计的动作价格仅来自同状态点，不把取证父总时间当净加速。

本地五个post控制通过：真实创新量公式/Gram、未算支结果损坏、候选/准备计费缺失、恢复/刷新异常、全8拒绝分母。未运行全部真实20原件/LPIPS，因为没有新GPU输出；本地单测不替代该层验收。

## 原服务器CPU查收

R1独立stage `.sync/wc-p-acr-local12-production-cpu-r1-20261015`，source **0dce0a0beac3cff182706798e24ffc818770a54c**，**1568文件**逐份SHA一致；原CPU **842901**，03:40:24唯一派发，预计5分钟后一次查收。实际于03:47接受原终态，全程**299.469344秒**，预算SHA前后一致、权重0/GPU0。

真实请求/Setup、原输入/形状、H1表与开发系数、资源/参考文件、原数值Core SHA均核验；实际生产CPU完整8位置/528计划计数、无guard拒绝、缩状态/父路径/刷新/当前teacher拟合拒绝及post五控制通过。原数值Profile20完整48CPU仍单独保留，不将production CPU当528次真实模型执行。缺许可的本地实际CLI也确认在native导入前拒绝。

原CPU结束，不重复查旧句柄或恢复查收自动化。没有在途本轮任务。

## 还剩的封口与投入决定

1. 准备当前整卡GPU supervisor/单次启动接线：fresh UUID、项目锁、实际余额、原生产CPU与源身份、新许可；尚未完成此层。
2. 验证完整post路径与所有拒绝/缺失的选卡口径，GPU结束后的原件/93帧验收必须再执行；目前仅接口与CPU控制通过。
3. 原保守forecast **7.529994GPUh**与整轮建议8的分配问题保持。完成具体可审查接线后再讨论新卡投入，不因低于8自动GPU，也不缩原528范围。
4. W3真sigma/history/64标签与原论文五项补验仍待；P/W3不自动并入冻结主线。F/B结束，不新增人评/训练/OMR。

证据：[R1启动](../reports/wc_p_acr_local12_production_cpu_r1_launch_20261015.json)、[原终态](../reports/wc_p_acr_local12_production_cpu_r1_collection_20261015_0346.json.gz)、[独立CPU验收](../reports/wc_p_acr_local12_production_cpu_r1_independent_acceptance_20261015.json)、[本地post/入口控制](../reports/wc_p_acr_local12_post_controls_and_entry_refusal_cpu_20261015.json)。
