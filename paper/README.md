## 2026-10-18 当前：N10固定资源SCP在途；N09 CPU已接受、GPU资源等待

[568资源实际启动](../research/568_WC_N10_ORIGINAL_SCP_RESOURCE_RUNNING_AND_CPU_NEXT_20261018.md)：原ViCLIP 1,710,545,812字节/固定7a4d6ad6 SHA已本机重新接受；sourcef06ca5a、独立stage wc-N10-viclip-relay-r1-20261018、原Mac worker81517/lstart01:01:29，初始身份仍活跃且server-prepared存在。预计10–30分钟，已安排01:17技术半程/01:32完整独立服务端SHA各一次；worldcache-n10-scp与worldcache-n10-scp-2，完成后删除，不持续监听或重复SCP。资源/五模型CPU/质量评分分开，当前新分数0。

原N09修复R2十命令真实CPU通过（198.8012秒），原完整40 GPU派发因其他账号两GPU满显存未准入，0生成/0预留/0GPU费；原两个查收自动化已删除，不停止其他账号进程或重派旧fence。v2快照110.869061155/cap226，预留0余115.130938845，原origin保持。资源接受后接完整五模型CPU，实际N09 GPU测量时不并发重模型；连续A完整24仅静态设计，88数值CPU/生产/报价待。F/B关闭，无训练/人评/OMR。以下为历史。

## 2026-10-18 当前：N09真实CPU完整接受，外部GPU占用导致未准入

[567实际状态](../research/567_WC_N09_REAL_CPU_ACCEPTED_EXTERNAL_GPU_OCCUPANCY_AND_NO_CHARGE_20261018.md)：修复R2 source8c353ba、1787源/194overlay/十命令实际CPU全部通过（198.8012秒），原R1失败保留，原N08严格验收器/桥接不改。完整40/五冻结角色/4.245833预测及5GPUh上限保持。派发1636878/1636879在生成前因其他账号两GPU满显存退出；原句柄消失、无GPU子进程、无N09预算job、预留0/本轮GPU费0，自身锁释放。原两查收自动化已删除，不循环重派或停止其他账号任务。

fresh v2仍110.869061155/cap226，预留0余115.130938845，原origin和历史不变。当前无本项目在途GPU/CPU；资源释放时间已向用户询问，继续CPU准备和N10固定资源接入，N09实际GPU测量时不并发重模型评分。连续A完整24仅设计和静态计划；新生产/88数值CPU/报价待做，N12结果保持。F/B关闭。以下为历史。

## 2026-10-18 当前：E0与少一次D完整三臂已接受

[563完整结果](../research/563_WC_DROP1_FULL18_RESULTS_FIXED25D_CORRECTION_VALUE_AND_REMAINING_20261018.md)：18/18完成，12正式视频全部93帧/1116帧接受，三方法完整36guided重复和四旧前密终态/actions/A历史/93RGB通过，零拒绝/失败/缺失。固定25D时A相对C平均LPIPS低8.5560%，四场景均93/93帧改善；相对26D仍高31.7739%，仅恢复删D新增失真的27.9558%。核心均时221.060/215.939/215.895秒（26C/25C/25A），每格一次开发计时，不当稳定净加速或未见泛化。

原N12 GPU/post已结束、自身锁释放；半程和终态各查收一次，两个一次性自动化完成后删除，没有在途GPU卡。实费1.474263031，累计110.869061155/cap226，预留0余115.130938845GPUh；origin及历史账保持，严格<12规则不变。已完成登记的6条预热/一个AV28输入第21步零GPU解释性CPU：共同20步前缀及216原张量身份通过，guided MSE降低52.9048%，两重复一致，仅一个旧输入。本轮不自动新GPU；N09实际服务器CPU/完整40及N10服务器资源/五模型CPU/评分待补，F/B关闭。补充原件与解释见[564](../research/564_WC_DROP1_SAVED_WARM21_REAL_CPU_MECHANISM_AND_NEXT_20261018.md)。以下为历史。

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
