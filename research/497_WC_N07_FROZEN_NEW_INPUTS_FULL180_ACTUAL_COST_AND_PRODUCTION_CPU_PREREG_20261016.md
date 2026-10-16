# 最终共同测试：实际输入、完整180范围与费用冻结

2026-10-16。**N05/N06后已锁定十方法、八个新prompt与双seed的最终共同测试；下一步仅做服务器生产CPU验证。** 本卡用于确认GCR低费用修正和CPA高保真工作点在独立新输入上的收益，同时直接面对两个强前密简单策略。当前无新GPU派发或最终视频结果。

## 固定输入与方法

方法冻结在Git提交a2948c2，早于fresh远端身份审计和本次选择。原身份审计一次读928份声明结果JSON，命中24个已执行身份、0读取错误；全部登记GPU任务已终态，无新增生成、评分、账本或原stage写入。选择仅使用名字、原prompt SHA与组身份，不提取端点、费用或安全拒绝结果。回执文件名的1225为本地标签，实际观测时刻以其observed_unix=1792124287.9359028为准。

本地保护与全部历史身份整组排除，共44成员；按先前登记salt和每类SHA排序选择前两组，seed固定17/43。只承诺已登记的prompt/reference/lexical组隔离，未宣称原录制会话或所有语义完全独立。

|类别|原始输入名|
|---|---|
|av|av_5f567f79-4dd0-413d-a81a-2607684decf2|
|av|av_3f748a97-5a86-4311-a099-c2d1bd1e5fb1|
|human|human_186|
|human|human_212|
|misc|misc_4707906-uhd_3840_2160_30fps|
|misc|misc_4761738-uhd_4096_2160_25fps|
|robot|robot_110|
|robot|robot_060|

十方法：NATIVE35、NATIVE26、WC_HALF、RA_HALF、RA_DEFAULT、RA_DOUBLE、A_NO_P、TABLE_PHASE_H1、FRONT_DENSE_C、FRONT_DENSE_A。原请求文本、negative prompt、guidance7、768×432、93帧保持原字节；适配仅改name、seed与num_steps。完整160参数/180排程、6318pairs/12636CFG、一次加载；20次warm均保留完整轨迹，160正式采用lean主计时，所有输出计时外审计与93帧CPU评分。

拒绝、失败和未到达保留原分母，缺参考不填0、不补样本。按照原提示词分组与双seed统计协议，先在prompt内聚合seed再计算组统计，不随机把step或帧当独立样本。六维自动质量测量493协议同时进入原配置引用，后续N10评分复用这些端点。

## 完整费用与待批准预算

费用依据为已接受N05/N06各方法成功请求最大完整wall、一次加载、原账单余项、完整warm额外60秒与设置300秒，再加20%规划余量；没有只用去噪core秒或把快速拒绝当廉价成功。实际运行可能偏离估计，计费上限按整卡明确绑定。

- **N07完整180：15.055555556 GPUh**，计费上限同值；超过自主严格<12门槛。
- N08原完整40：3.627500000 GPUh；两卡合计18.683055556 GPUh。
- 12:05原池可用11.389538676 GPUh，完整两卡预计缺7.293516880 GPUh；只做N07也超过当前可用量。

为了让具体批准对象可审查，N07配置将未来累计cap登记为**拟议113 GPUh、等待直接人类批准**；保留原origin79.99637737158223与当前cap104.97136333301378字段。服务器实际cap/账本未改，也未预留任何费用。若批准113，按当前实结93.581824657，余19.418175343，按两卡完整估计后约余0.735119787 GPUh；N09/N10真实费用仍需核定，不能视为已被这个估计包办。

## 真实生产CPU与执行边界

已在本地对实际配置/全部输入运行合同、引用SHA和157份overlay源码计划检查，原99数值依赖与952接受证明保持逐SHA一致。接下来以原N05注册stage为只读base，在独立fresh stage安装Git绑定源和输入，运行五组控制＋真实Cosmos无权重CPU入口，共六命令；禁CUDA/模型下载，实际InferenceArguments验证160变体、保留Native17/43与guardrail检查。

CPU通过后才提出具体整卡批准及拟议cap113；未经该批准不派发GPU、不更新cap。若生产CPU失败，保留失败原件并修复独立版本，方法和统计分母不因此改变。未来原完整GPU若批准，预计11—15小时，首次查收设置启动后16小时含CPU后处理；未完按剩余量再估一次，不持续监听。

主线之后仍为N08重复clean测速，再完成N09部署开销与N10自动质量；前密C/A保持强对照，直接近邻资源/适配缺口保持。P/T1不自动变成新主方法，F/B关闭，无训练、OMR或人工评审。

## 绑定原件

- [wc_paper_N07_actual_selected_unexposed_inputs_r1_20261016.json](../manifests/wc_paper_N07_actual_selected_unexposed_inputs_r1_20261016.json) · SHA256 `7eb74a957b571c07e1634b9315daa56a920766f2e9fd94c9f266fa3cca656e66`
- [wc_paper_N07_actual_bound_inputs_r1_20261016.json](../manifests/wc_paper_N07_actual_bound_inputs_r1_20261016.json) · SHA256 `6271100396e10afb521f07bae19de9fc837b2fa0649bfd7d4e5f4c1276489f33`
- [wc_paper_N07_actual_fresh_identity_20261016_1225.json](../reports/wc_paper_N07_actual_fresh_identity_20261016_1225.json) · SHA256 `e3d5bc36b37df3d205e8f086dcfe89d86036fba067cc7d0840bc275b58f4a9c5`
- [wc_paper_N07_N08_actual_complete_cost_r1_20261016.json](../reports/wc_paper_N07_N08_actual_complete_cost_r1_20261016.json) · SHA256 `7bb6d09b30047702a5107314e3db74a89c776a52c53e5b5b15850cdb1a1d953e`
- [wc_paper_N07_actual_freeze_local_contract_and_packaging_20261016.json](../reports/wc_paper_N07_actual_freeze_local_contract_and_packaging_20261016.json) · SHA256 `526bf69fc1b8dcce3579e330a83c01377de8d9b4f91271a2624c057aa66e88dd`
- [wc_paper_N07_frozen_shared_production_r1_20261016.json](../configs/wc_paper_N07_frozen_shared_production_r1_20261016.json) · SHA256 `9de3e5b9c2ce0377888e1244aa77043b42d4f92f0d9cea498c13c59e3aeafd0c`
