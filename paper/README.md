# WorldCache 论文写作入口

从[内部实现到论文表述映射](INTERNAL_TO_PAPER_MAPPING.md)开始。它定义暂定CARA-Cache／GCR／CPA名称、C/A/P/D动作、主结果与消融显示名、历史H1重名、数学符号、证据批次与写作边界。

随后读取[实验总表：状态、贡献、缺口与优先级](EXPERIMENT_MASTER_TABLE.md)。它统一登记33项已完成、在途、待补和归档实验，区分主线证据与独立增强；[实验总表机器索引](experiment_master_table.json)保存相同条目与依赖。

- [机器索引](internal_to_paper_mapping.json)：带命名空间的稳定ID、配置／源码SHA和结果职责，供表格与写作工具读取。
- [当前正文框架](WORLD_CACHE_MAIN_TEXT_OUTLINE_20261014.md)：中心问题、最小算法、贡献与章节图表。
- [研究路线](../plans/WORLD_CACHE_RESEARCH_ROADMAP_20261015.md)：后续P/W3开发及论文补验。
- [最新交接](../memory/handoffs/LATEST.md)：执行状态可能更新，使用前核对。

显示名称不会改变内部实验身份。两个工作点分别报告；旧P0和新单分支补偿读出分开，新探索取得完整证据后再决定纳入。

## 已接受结果的图表与机器数据

[2026-10-17 N07/N08图表包](results/accepted_n07_n08_20261017/README.md)保存原19配对表、全部三轮计时、逐场景倍数、SVG/PNG、英文图注与SHA来源。N07共同5提示词图为同队列可视化，原配对主统计5/6提示词和原时间队列分别保留；N08为两个旧CAL重复计时。data.json中的N12/N10未完成结果为空，不补写推测值。当前实验状态继续以LATEST和实验总表为准。

可直接用于部署补充表：[N08已验收的30条独立计时间隔](results/accepted_N08_separate_intervals_20261017/README.md)（核心/guarded分别统计，安装/清理/写盘/三个GC单列；不合成新的完整请求计时）。
