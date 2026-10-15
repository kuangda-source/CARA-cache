# N10自动质量：视频身份、指标采样与分组汇总CPU准备完成

**最终视频质量评价的数据链已接好：原视频与原提示词绑定，指标采样按固定源码核对，统计以提示词组为单位。** 八项本地CPU对照通过；固定作者源码的纯采样函数和输入解析器也已实际对照。下一步可复用这条链对最终N07视频评分，实际模型资源/权重、完整评分入口和费用仍待验收。

## 1. 新增实现

`src/wcomr/automatic_quality_r1.py`提供三段接口：

1. `build_inputs`保留8prompt×2seed×10方法的全部160生成位置，按冻结维度展开全部指标位置。只有原93帧RGB、SHA、768×432/16fps审计通过的视频可评分；拒绝、坏容器、技术失败与未到达仍留在原分母。
2. `vbench_metadata`生成明确的`prompt_en`与原视频路径，不把实验文件名当提示词。视频/输入/seed不能静默串用；输入bundle变化即拒绝。上游模型/源码/权重的身份以评分配置fingerprint绑定，但fingerprint本身不替代后续实际文件SHA与真实模型CPU验收。
3. `summarize`接收逐视频分数及实际采样回执，先视频标量，再两seed提示词均值，最后提示词等权。配对差值与4096次提示词bootstrap并列；一个seed缺失时整个提示词对主均值缺失，不补0或拿另一个seed顶替。上游grand mean不用于主表。

每维独立报告，不加权成完整VBench总分。`dynamic_degree`是活动程度描述，不是越高越好的总质量；闪烁仅对预登记静态适用prompt进入质量比较，不从生成结果后选静态样本。其余prompt保留不适用位置，无需新增人工标注/评审。

## 2. 固定源码下实际核对的采样范围

使用原468固定的VBench提交`fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`，九文件SHA均一致。只提取执行纯索引与元数据解析函数，没有import整个VBench或加载模型。

|维度|93帧/16fps原视频下的采样规则|报告含义|
|---|---|---|
|主体一致性|全93帧|对应DINO源码的逐帧一致性，不是物理正确性|
|运动平滑|47个偶数帧输入、插值比较46个奇数中间帧|源视频93帧审计与AMT比较次数分列|
|动态程度|间隔2，47帧、46相邻光流对|二元活动结果，和一致性/平滑度并列|
|文本一致性|8帧，原索引5/16/28/39/51/63/74/86|不能称93帧语义评分|
|MUSIQ_LONGER512|全部93帧，沿用原项目longer512预处理与raw mean|原始逐帧分数重建均值，独立成像维度|
|静态闪烁|全93帧的92相邻帧对，仅静态适用质量分组|动态视频不进入该质量均值|

源码核对实际执行作者`get_frame_indices`、RAFT/AMT的`extract_frame`以及`load_dimension_info/load_json`。五个VBench维度的合成输入都经原解析器读回：普通维度8prompt/160位置，静态闪烁示例4prompt/80位置；提示词和路径逐一一致。MUSIQ保持项目独立评分器，不冒用VBench维度别名。

这些是源规则/输入兼容证据，未执行DINO、AMT、RAFT、ViCLIP或MUSIQ模型。原model resource SHA、ViCLIP资源及完整源版本/依赖验证仍待；九个文本文件不是完整VBench运行验收。

## 3. CPU证据

- 8项CPU对照：`tests/test_automatic_quality_r1.py`，最后一次8 passed/1.18秒。
- 接受回执：`reports/wc_paper_N10_input_statistics_CPU_acceptance_20261016.json`。
- 固定源码实际纯函数/元数据对照：`reports/wc_paper_N10_source_sampling_and_prompt_metadata_CPU_r3_20261016.json`。
- 对照脚本：`scripts/check_wc_N10_source_sampling_and_metadata_cpu_r1.py`。

合成160生成位置、960指标位置仅用于CPU协议测试，未选任何最终真实输入或维度，也没有新视频/真实质量分数。初次辅助回执序列化因作者索引为NumPy int64失败，原R1目录/源/五份metadata保留；仅转成等值Python int后R2通过。增加冻结bundle保护后，以当前源码做R3元数据核对，旧R2仍保留。未改指标数学或删对照。

## 4. 实际评分还需补什么

最终N05/N06后先冻结N07方法与输入，再绑定实际输出。N10需要完整指标源码版本、现有权重文件SHA、禁止隐式下载的隔离依赖与真实CPU入口；评分器必须提供实际采样记录和逐视频结果。ViCLIP不能用CLIP静默替代；资源缺失保留RESOURCE_UNAVAILABLE和全分母。

当前尚未选择最终维度、真实评分GPU卡或整卡费用，费用未知为null。全部实际评分GPUh计入原v2池，与生成延迟分开；没有新增付费VLM、人评或模型训练。N05原source15d77ac/1078249/1078290/post1078250、stage和今天12:05一次查收均不变，未SSH提前看partial；原cap/严格<12GPUh自主规则不变。F/B关闭，P/T1后排。
