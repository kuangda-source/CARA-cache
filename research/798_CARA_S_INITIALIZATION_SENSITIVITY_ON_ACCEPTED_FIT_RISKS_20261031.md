# 798 — S初始化敏感性CPU核验

按既定A2.1复用已完整接受的S风险，F19起点三目标均精确复现D21→D35；固定Uniform19起点BR/DIAG为D22→D35，CFG为D25→D35。7项本地CPU控制通过；新增138种历史槽组合待生产选择器CPU验证，不改原S冻结、不读取运行中预算搜索分数、不形成端点收益或新GPU权限。

依据已采用的02_SQ_Method_and_Experiments.md A2.1，比较两个事前指定起点F19和噪声坐标Uniform19。预算都为19D，36更新，原保护点含D24，max-age28，同一组27位置风险，同一合法一次remove/add与正增益/固定编号平局规则；未扫描18D/Q5或反复迭代。Uniform19由原真实噪声网格的确定性程序重新生成，并与原接受策略逐字段核对。

| 起点 | BR | DIAG | CFG | 本起点执行等价类 |
|---|---|---|---|---|
| F19 | D21→D35 | D21→D35 | D21→D35 | 1 |
| Uniform19 | D22→D35 | D22→D35 | D25→D35 | 2 |

F19的170个合法候选及原三项分数/指纹精确复现。Uniform19同样完整枚举170个候选，三目标共享候选域；新结果只是原Shared25-C/F19-C父轨迹、两旧FIT等权风险在另一初始化上的一次提案。没有收集Uniform19父轨迹风险，没有读取CHECK/最终输入，也没有使用运行中新预算搜索的中间候选或分数；不能据此声称CFG端点优势或冻结通用方法配方。

相对原S选择器历史槽覆盖，Uniform19完整候选域增加138种(step,older-D,newer-D)组合。当前仅经原生产语法编译与严格过去锚点检查，未做这些新增组合的实际生产选择器CPU验证；本机Python无Torch，未安装依赖或把纯Python检查冒称生产验证。下一步是有界、隐藏GPU的生产选择器CPU覆盖，以及之后按完整独立卡绑定端点比较。

7项控制覆盖原决定复现、起点专属零/负收益回退、正平局顺序、缺失/非有限风险拒绝、原接受篡改拒绝、禁止第二预算/破坏保护点、三个目标共域。原S文件未改，原A32/B36科学行未动。当前14GPUh新卡继续依照797的原句柄和23:16/06:01检查，未额外派GPU或修改其源码。

[CPU诊断](../reports/cara_s_initialization_sensitivity_r1_20261031.json) · [7项控制](../reports/cara_s_initialization_sensitivity_checks_r1_20261031.json) · [设计要求](../plans/cara_next_stage_20261028/02_SQ_Method_and_Experiments.md) · [原S接受](../reports/cara_sq_s_A6000_post_analysis_accepted_r1_20261030.json)
