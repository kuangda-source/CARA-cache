# 直接修正近邻审计：候选RFC，尚未冻结适配

身份已从一手来源确认：**Relational Feature Caching for Accelerating Diffusion Transformers**，ICLR2026；[arXiv固定v1](https://arxiv.org/abs/2602.19506v1)、[作者项目页](https://cvlab.yonsei.ac.kr/projects/RFC/)。查阅日期2026-10-20。项目页列paper/BibTeX，当前已读页面未给代码链接；这不等于断言作者没有发布代码。尚未clone或pin代码revision，也没有本地模型结果。

RFC的RFE用当前模块输入变化估计输出变化幅度，方向来自历史Taylor预测；RCS另据输入预测误差触发完整计算。[原文§3.2、式16—21](https://arxiv.org/html/2602.19506v1)。它与“仅用历史外推”不同，也不能用我们的β1向量增量替代后仍叫RFC。

拟审计的受控适配应在同Dmask/同覆盖的真实残差读出层保留：历史真D输入/输出差、Taylor方向、输入变化的幅度归一化、退化方向与历史不足处理。输入p、原模块输入I、深层残差r和原模块输出O并非自动同一坐标；需逐项证明映射、维度和尺度适配。若改为残差级全网络port，显示名必须含“RFC-RFE readout port”，明确不保留原逐attention/MLP粒度及RCS。不得宣称它是官方Cosmos RFC完整实现。

性能实验前必须填写并冻结：

| 字段 | 当前 |
|---|---|
| 原文/版本 | 2602.19506v1，已定位 |
| 官方代码/许可证/revision | 待核实，不填虚构commit |
| 方程、归一化、Taylor阶数/历史跨度 | 待原文与代码逐式对照 |
| 本地执行层/输入输出坐标映射 | 待定义并验证 |
| 同mask端点port vs完整RCS算法 | 分开身份，不能互换 |
| 历史不足/零范数/保护步骤/重置 | 待忠实实现与实际CPU |
| 默认参数与有限调参范围 | 在本地结果前冻结 |
| 计算/显存/价格/完整scope | 待真实适配后报价 |
| 同预算8formal初始端点 | 未运行，结果空 |

如果公式/坐标映射无法忠实实现或完整工程成本不合理，先形成可复查的适配不可行说明，再在未看本地性能前选择FoCa/TaylorSeer/AdaCorrection中的一项。此处不以外部论文的加速数字预测本地排名。
