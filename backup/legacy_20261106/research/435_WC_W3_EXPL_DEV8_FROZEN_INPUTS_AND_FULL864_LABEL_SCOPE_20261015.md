# W3八开发输入冻结与完整标签范围

2026-10-15，接续[434真实时钟](434_WC_W3_REAL_CONTINUOUS_CLOCK_AND_FULL432_CAUSAL_HISTORY_CPU_20261015.md)。**已锁定8个仅供W3开发使用的提示词，完成本地／服务器身份排除审计，明确64正式标签的完整采集分母。** 当前没有真实标签、新视频或训练；本次CPU只核对身份和范围，完整采样器CPU及真实生产入口／费用尚待。

## 已冻结的开发输入

|类别|两个输入|
|---|---|
|AV|av_9a39abb2-7289-4b00-8707-887be4f46c04；av_a6beffc6-0c10-45d4-9ac1-06e482f25ebf|
|Human|human_272；human_173|
|Misc|misc_3196505-sd_960_540_30fps；misc_5629687-hd_1920_1080_25fps|
|Robot|robot_001；robot_145|

先登记固定salt和各类取两个的SHA排序规则，再检查全部1044 benchmark参考／词汇分组、本地configs／manifests和服务器88份原回执及输出路径。排除36个已用或保留组成员后按规则选取；没有读取视频效果、耗时或拒绝结果来挑输入。原CAL24、已曝光CONF和原E2保留组不挪用。

八条均是现有主平台的text2world入口，原提示词／negative prompt保持，seed0、guidance7、35请求／36实际更新、768×432／93帧。无需下载首帧或权重。参考／词汇组分开已经核对，不能据此声称原拍摄会话或语义完全独立。它们现在是EXPL_DEV，后续正式保留测试必须排除整个选中组。

证据：[预登记](../manifests/wc_w3_expl_dev8_input_protocol_r1_20261015.json)、[输入冻结](../manifests/wc_w3_expl_dev8_inputs_r1_20261015.json)、[请求](../configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl)、[身份审计](../reports/wc_w3_expl_dev8_identity_exposure_cpu_r1_20261015.json)、[独立身份／范围接受](../reports/wc_w3_expl_dev8_scope_independent_identity_CPU_acceptance_20261015.json)。

## 完整采集分母

拟议卡 `WC-W3-LABEL-EXPLDEV8-PARENT18-LOCAL64-FULL864-R1-20261015-A`。每个开发输入保留一条普通H1和一条非提交式诊断H1；首输入另保留普通／诊断各一次完整预热。总 **18父路径＝16正式＋2预热**。

每条诊断路径固定 **10、16、23、25、29、30、32、35** 八个位置，保留原H1普通合法集合，包括原P0；诊断只是C/A/D对照，不删普通父P0。每个有合法支持的状态独立执行C/A/D三对并恢复，D作为同状态教师。不先假定普通D可免费复用。

- 64正式标签位置＋8预热位置＝72完整诊断位置。
- 18×36＝648普通pairs，72×3＝216诊断pairs，计划最多 **864pairs／1728CFG，一次加载**。
- 每状态C/A/D六个post-RF velocity及latent／timestep，共8tensor；72点576tensor。18父各37vector，共666tensor；全部90raw／1242tensor。
- 全部18位置保留，接受视频完整93帧解码和普通／诊断父RGB比较；其36输出、动作、A历史、终态均需等价。拒绝、失败和不支持标签保留全分母，不换提示词或另挑状态。

上述调用／原件数是全部状态有支持、全部路径采样完成的计划最大范围。实际未知支持／文本拒绝会减少已执行调用或有效原件，审计仍保留72状态／18路径分母；不为凑864执行无意义调用，也不把未计算格写成零误差。

本卡研究标签与无扰动采集，不是新策略端点比较，因此不新增Native路径、也不宣称Native LPIPS收益；真正闭环卡必须补匹配Native。完整费用必须含加载、18父、全部diagnostic／teacher、恢复、保存及余量，**当前forecast为UNKNOWN**，没有将它按64个局部点低估。[固定范围](../manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json)。

## 下一实际工作与权限

实现独立W3 sampler collector：只把普通父的前动作观测推进因果历史，标签与额外候选信息隔离；同状态C/A/D物理快照完整恢复并核对父路径。先验证完整CPU流程，再接实际资源／入口／原件post及费用。不以本轮身份CPU代替该层。

随后按prompt分组检验T0/T1/T2的合法动作regret，只有真实控制信息和闭环质量—时间出现增量才考虑合入。新P与Trend不自动并入，F/B不恢复，不新增人评或生成器训练。

原PA528的source715cae7／独立stage／7.529994 forecast和待回复许可保持；本轮不改它。GPU／模型／教师调用／拟合／预算写均0，账本SHA仍a3e8d93f。8GPUh自主规则不解除当前停止新GPU要求；新W3卡也尚未批准，不重复询问原PA。
