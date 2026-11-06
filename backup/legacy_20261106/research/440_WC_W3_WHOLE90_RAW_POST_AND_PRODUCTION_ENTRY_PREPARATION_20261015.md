# W3 全量原件审计与真实入口准备

2026-10-15，接续439。**完整18父／72位置的原件审计和真实执行入口已实现；新增11项本地CPU控制通过。原R3完整采样CPU仍按06:17一次查收，当前没有真实标签／GPU。** 本轮没有修改正在运行的R3或已接受的PA715cae7目录。

## 全量原件检查

`w3_label64_fullpost_r1.py`和独立CPU post脚本保留全部18父、64正式＋8warm标签分母。完整合成例实际保存并读取90个文件、1242张量，检查每父36个guided＋终态、普通与诊断的全部动作/A历史一致，每点原始C/A/D与一遍g²标签；实际视频接口使用已固定的93帧、432×768、16fps完整解码，逐像素RGB比较原父。标签卡不增加Native，不把这些H1控制视频当新调度的端点。

七项本地控制覆盖：完整90原件与18/72全分母、全部文本拒绝、坏周期/坏视频、缺父/乱序、坏原件/父轨迹、技术失败后的部分点，以及先保存但后续标签失败的孤立原件。部分原件仍读/hash/校验，但缺失状态不补成可训练教师标签；实际已记录调用数和完整已核验调用数分别保存，未知实数不填零。

实际post入口另外绑定stage全源码、原runner/supervisor SHA、原GPU句柄退出、原件canonical路径/hash/字节、全部接受视频和前后预算SHA。当前只有合成CPU输入，**没有真实90原件或18视频的post验收**。

## 真实入口与下一CPU

`run_wc_w3_label64_full864_r1.py`保持原H1 table/gamma/合法动作及真实WC/RF/UniPC，一次加载，八EXPL_DEV各普通/诊断加首个完整预热对，共18父。每个支持点额外C/A/D3对，未知保留8点分母，不补齐864。诊断保存候选、原输入、完整普通因果历史和父向量；文本/视频拒绝和技术停止保留原矩阵与已保存文件。

入口重用PA代码的**冻结H1资源检查**，不执行PA卡、改其目录或借用许可。W3输入/范围、实际连续sigma、原数值核心和独立R3完整CPU要单独绑定。实际CPU入口创建真正Setup/八InferenceArguments并核对所有配置和资源，禁止CUDA、模型权重和下载；仅允许测试自己创建的临时目录里的合成.pt加载。

四项新合同控制通过，缺许可的实际CLI在Torch/native导入前拒绝。完整W3授权与PA授权严格分开；目前真实生产CPU、fresh监督/锁/预算接线尚待。即使以后实际入口CPU通过，未接受整卡supervisor CPU也不得开GPU。>8完整卡确认和用户停止新GPU两条规则均保留。

新生产CPU部署脚本已经准备，但**尚未派发**：必须先取得原R3完整终态接受文件，再将全部已提交源码/原材料同步到fresh `.sync/wc-w3-label64-production-cpu-r1-20261015`。估计约5分钟后一次查收；不在R3目录注入新代码，不提前检查其partial。

## 结果边界与下一步

[本地CPU回执](../reports/wc_w3_label64_fullpost_and_actual_contract_local_CPU_20261015.json)记录新11控制及源码SHA；旧支持/周期/raw-label12控制继续保留。R3接受后先核对原完整72/288/3456与预算，再验收真实入口/完整post CPU与整卡监督接线，最后才具备讨论W3完整投入的具体材料。

W3临时完整费用11.645828GPUh，PA7.529994，其具体许可仍待。原余24.974986不重置；无新GPU、训练、F/B、OMR或人工评审。费用/CPU准备不是动作收益、质量或速度结果。

## 真实入口打包的准备修复

原source3fd72a5首次生产CPU打包在SSH之前拒绝：八份已冻结prompt JSON来自被Git忽略的上游vendor目录，无法满足逐文件Git源码校验；未建服务器stage、未派发CPU/GPU。现已将八份JSON逐字节归档到 `research/sources/wc_w3_expl_dev8_prompts_20261015`，[身份绑定](../manifests/wc_w3_expl_dev8_prompt_archives_r1_20261015.json)核对全部原SHA和原输入manifest，打包仍使用原stage相对路径。上游文件、提示词、选择和scope没有变化。[原本地停止](../reports/wc_w3_label64_production_CPU_r1_local_packet_failure_20261015.json)保留。
