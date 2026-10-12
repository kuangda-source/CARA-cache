# 后果分析准备、计时边界更正与新输入确认准备

2026-10-13。393完整266任务保持source c9b32ce/655、四点/八后缀/十二视频、全部原GPU/CPU入口不变。本轮新增独立结果分析与确认输入准备，0新GPU提交/teacher/训练/人工评审；不改原E2或用户暂缓P13h卡。

## 两个有价值的准备

**后果分析不再混淆D/P的默认角色。** D来源默认A、替代C；P来源默认C、替代A。预登记Yq仍是默认LPIPS减替代LPIPS；另统一报告A相对C的效果、逐帧改善/退化、未来全部动作次数。D格需要换符号，P格不需要。四个状态的来源/阶段同时与场景绑定，不能凭四个后缀事件分离来源效应与场景效应，也不能称完整新策略已经验证。

[独立分析入口](../scripts/analyze_wc_pi0_suffix8_complete_cpu_r1.py)要求完整12视频/93评分、4父与266pairs、默认与原父尾部等价、原进程退出、锁释放、source与账本证据通过，再从全部逐帧分数和真实区间独立重建原Yq/Yt。只有三个后果状态与cal16有精确同一步teacher标签；AV51 suffix27不冒用cal16 P26。CPU植入正/负/零效果和A额外耗时均保留，错误符号/少视频/少帧/非有限/未来次数不符拒绝，见[CPU回执](../reports/wc_pi0_suffix8_signed_effects_cpu_validation_20261013.json)。这些是分析正确性验证，不是新视频结果。

**独立确认已固定四个新提示词、两个seed。** 采用新salt、类别内SHA排序与最小组代表，排除CAL24、工程/参考/词汇组、当前本地登记及服务器WorldCache暴露，以及原E2四个保留组。没有按终点、耗时、拒绝或内容评分筛选。

|类别|固定基名|seed|
|---|---|---|
|AV|av_46fe9718-b496-4c30-b1b6-8b02028dd336|17、43|
|Human|human_125|17、43|
|misc|misc_2711212-uhd_3840_2160_24fps|17、43|
|robot|robot_043|17、43|

本地515登记文件与远端88 receipt的身份扫描无读错；独立重构全候选组、排除集、排序、原提示词hash和全部八请求通过。四类剩余候选池112/293/88/168。协议、输入与审计见[输入清单](../manifests/wc_source_conditional_confirmation_inputs_r1_20261013.json)、[独立回执](../reports/wc_source_conditional_confirmation_input_independent_audit_20261013.json)。仅证明本实验已记录的参考/词汇组与提示词暴露不重叠；未知原拍摄会话、预训练曝光和外部未登记运行不据此证明独立。

完整确认仍保留Native、RA、A_NO_P、P_OFF、一个待冻结新候选，40正式位置＋10完整CAL预热；没有执行模型。候选、生产采样CPU、完整费用、实际GPU卡尚待冻结。不根据未来seed17结果修改seed43或替换失败输入；不让原E2四保留组提前被此卡使用。确认准备不无限等待所有数学/P模块成熟。

## 重要计时边界更正，原数据保持

在原GPU日志和源码核对中发现：官方视频guardrail位于`write_tail`内，之后才调用`save_img_or_video`。`decode_tail`没有这两个调用。原runner实际分别量了这两个整个函数区间，字段命名和393冻结时的描述不准确。

|原字段名（保留）|实际区间|
|---|---|
|VAE_and_video_guardrail_seconds|官方decoder尾部：VAE/后处理与原有卸载加载；不含视频guardrail|
|video_write_seconds|整个guarded writer：帧转换、视频guardrail、编码保存；不能叫纯写盘|

[只读源码审计](../reports/wc_pi0_suffix8_timing_source_boundary_cpu_20261013.json)绑定原runner/hash/source和两个固定runtime源码；不初始化CUDA，不改部署，不推断guardrail时长。原流程/原件/费用不变，当前质量与实际后续动作问题仍可完整回答。

原计划“后缀采样＋VAE＋guardrail，排除编码写盘”的时间，从本卡原字段**不能精确识别**。该项不能写成已通过的主计时。报告保留原预登记与原字段，并单列两个可观测区间：

1. 带取证的后缀采样＋整个decoder尾部；原post比较数值实际对应此区间。
2. 上项＋整个guarded writer，明确包含安全检查与编码保存。

研究端点导出、CPU→GPU上传、raw写出另列；加载/捕获/恢复/所有写出/清理仍全部进入实际GPU账本。本卡两臂仍只有一次instrumented计时，不作为稳定clean加速证据。未来真正clean重复测速使用已有可分别测量的编码、去噪、VAE、guardrail、保存计时接口，输出等价和算法维护成本保持。

这个更正在新LPIPS和后果分析前登记，不能用未分开的timer补造guardrail秒数，也不按哪一时间口径有利就选择赢家。原自动post的数值和误名继续作为原始证据，独立分析映射到正确区间，未覆盖或改写在途stage。

## 执行状态与下一步

原supervisor445447/runner445752/postwatcher445448均live，kernel锁持有，GPU17550MiB。最新原件观察2/4父完成、4/8后缀记录完整，misc在跑；AV28/Human父144范围中的72步guided/动作/final均与已验收父相同，全部视频原件仍待终态CPU审计。全部12视频/93评分和真实终态费用仍待。启动前实际65.810679625/cap104.971363333、余额39.160683708，第88提交在途，used=cap为保守预留。

下一沿原进程完成全部原件和评分，再独立重建四点行动后果，决定有限偏离π0的下一个候选。新输入已固定，不用它调参；同时继续CPU准备时钟特征/旧标签复用与P费用profile，GPU仍单任务。

输入准备R1曾在macOS本地普通文件read路径停滞，已核对自身PID和栈后终止该CPU进程，保留[记录](../reports/wc_sourceconf_input_local_read_stall_r1_20261013.json)。恢复版只在tracked configs/manifests无修改时，批量读取准确Git blob；所有untracked当前输入仍扫描。该CPU工程恢复不计GPU费，不作为科研配置失败。
