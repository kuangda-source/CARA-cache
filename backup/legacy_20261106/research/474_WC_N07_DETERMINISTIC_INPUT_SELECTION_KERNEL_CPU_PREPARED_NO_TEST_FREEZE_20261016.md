# 最终共同测试输入选择核：CPU准备完成，未冻结真实输入

更新：2026-10-16。本轮仅本地准备，没有读取在途952 CPU或N05服务器结果。

**输入选择现在有确定性的可执行核与拒绝控制。** 依原登记salt，对每类未曝光的完整prompt/reference/lexical组排序，各选四类中的两个组；保留两seed17/43。三组合成控制通过，没有对真实1044记录执行选择，最终8prompt/16请求尚未冻结。

## 1. 具体行为

`src/wcomr/frozen_input_selection_r1.py`只接受独立完整验收后的N05/N06、开发集冻结的十方法工作点、其后新做的身份审计；当GPU作业仍在途、审计读取了指标、发生read_error、曾看最终测试输出调参、缺强简单对照或混入未登记P/T1时拒绝。没有新增任意“几小时内”时间阈值，时序只要求开发→方法冻结→身份审计。

输入按原salt与组代表名的SHA256排序，类别顺序av/human/misc/robot保持；每组记录必须互相一致，任一成员已曝光就排除整组。打乱records顺序不改变选择；不足两个未曝光组时不回填旧组、拒绝点或改seed。所有实体选取只依身份，不依质量、耗时或拒绝。

输出核还不读取物理benchmark JSON或写冻结manifest，因此不能代替fresh服务器身份审计、prompt/输入文件SHA绑定、十方法参数源绑定、全部真实InferenceArguments、完整生产CPU及费用。实际输入/方法仍须N05完整接受后冻结，原180模板不改。source-group隔离也不证明录制场次或语义独立。

## 2. 已运行的CPU控制

`tests/test_frozen_input_selection_r1.py`有三组控制：排序与别名闭包/两seed；不完整开发或过期/含指标/在途GPU审计及test调参拒绝；缺组/缺对照/未登记新P及无足够未曝光组拒绝。只使用SYNTHETIC身份，不将其作为真实测试选择。

原件：`reports/wc_paper_N07_input_selection_kernel_synthetic_CPU_controls_20261016.json`。这不是新的质量、速度、实际N07 CPU或GPU结果。

## 3. 当前任务保持

原952 CPU R3 source616caef/PID9817，**06:02一次查收**（最早06:00:48.865855），不提前看partial；473中的失败与修复原件保留。N05完整66 source15d77ac、1078249/1078290/post1078250仍**12:05一次查收**。本轮0GPUh/0SSH/0预算写，原cap/v2/严格<12规则不变，F/B关闭。
