# 成对增量成本读取与联合选择接线

2026-10-10。已补齐从完整成本表到现有联合选择器的输入接口，真实测量产生后可直接绑定。原32路径卡及顺序成本卡的算法、范围、在途源码和预算均不改变。

## 本轮进展与作用

`IncrementalRankingCosts` 继承现有成本接口，但明确记录两probe已支付后的边界，以及仅用于动作排序的角色。它保留六模式全部144个计时值，按每起点三重复平均、场景与step等权汇总；D用带投影缓存维护的版本，plain dense作为独立开销控制保留。原C与两个共享A读出分别有成本输入。两注册step的统计保留作描述，本版没有安装动态阶段成本或推断A质量。

已完成登记976922a后的纯Python CPU执行：36条完整36步策略路径、1296更新，C/P/D均触发；原增量成本与显式添加相同probe前缀的成本得到相同动作、风险状态和健康恢复。完整48成本行／144时间值保持，19个缺起点／缺动作／删重复／非法时间／边界／头及A语义变异被拒绝。实计0.155433秒，源文件前后SHA一致，GPU提交0。所有输入是synthetic，仅证明接线与所测序列，不是实际时间或新视频效果。

这个接口解决了一个实际语义问题：共同前缀不改变同一步的相对排序，但增量值仍不能充当完整pair延迟、未来计算预算或clean端到端速度。现有风险规则和P非零创建误差保持，A的计时不被解释成A的质量收益。

## 真实数据接续

`build_wc_action_cost_ranking_real_r1.py` 只读取新完整成本卡的独立捕获与原始压缩元数据，核对完整八父／八起点／六模式、112分支／288guided／八latent、实际post-RF边界、真实D历史、额外头及来源指纹后，输出三种配置读出的成本排名输入。旧P0表缺C/A，不能补充或替代。该脚本已在真实回执缺失时返回WAIT且无文件／GPU／预算写入；真实数据处理尚未执行。

运行顺序仍为：原32卡GPU／原件／全93帧评分结束 → 两独立capturer保存并提交原卡证据 → 原卡接续回执 → 已部署CPU等待器fresh准入后唯一启动完整成本卡 → 成本原件CPU与独立capturer → 本成本读取器。随后在新完整方法卡中绑定质量、近似器与成本来源，做完整视频比较。CPU接口通过不代替真实方法视频；不扩局部层／模式／历史矩阵。

本轮开始时原GPU3929440/3929519仍实查存活，14视频／14张量；原件CPU3929441、评分CPU3930095和成本CPU等待器3950825均存活，后者新GPU提交0，原卡是唯一compute进程。整卡科学结果待产生，目标active/progress；等待活进程不视作blocked。

接续现场1791614552.878605：已保存25方法视频／25张量，AV28、Human和misc各七方法完成，AV51四方法完成，原生参考尚未开始。五个原句柄均存活，唯一compute仍为3929519，原账本SHA c3e4417f保持，成本等待器仍为GPU0。[只读现场回执](../reports/wc_ra_plus_a_r1_ranking_preparation_live_20261010.json)保留全部方法状态；该进度不代替终态和全93帧评分。

飞书组会文档 revision55→56 已仅更新进度段，197块全文核对保持其他内容；[写入与读回验证](../reports/wc_action_cost_ranking_feishu_20261010_verification.json)保存三个完整无损原件。无消息或分享权限变更。

证据：[执行前协议](../plans/WORLD_CACHE_PAIRED_INCREMENTAL_COST_RANKING_R1_20261010.md)、[CPU登记](../manifests/wc_action_cost_ranking_cpu_r1_preregistration_20261010.json)、[全部CPU结果](../reports/wc_action_cost_ranking_cpu_r1_results_20261010.json)、[成本接口](../src/wcomr/action_cost_ranking.py)、[真实数据读取器](../scripts/build_wc_action_cost_ranking_real_r1.py)。旧源与原判据保留。
