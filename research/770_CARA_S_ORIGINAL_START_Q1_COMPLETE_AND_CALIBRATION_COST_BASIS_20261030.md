# S原卡启动、Q1完整承接与预算搜索费用依据

2026-10-30。主线接入S/Q已经发布的原运行证据，并补做完整分辨率RGB的真实CPU/磁盘成本测量。预算搜索的费用方向仍待用户选择；没有启动新GPU搜索，也没有把分项测量当成整卡报价。

## S原卡与Q1完成

[主线承接回执](../reports/cara_mainline_S_launch_Q1_complete_intake_r1_20261030.json)逐字节核对S/Q已发布分支`codex/sq-production-entry-20261029`的`b4c4f6b9ad4c088bd44d6ad08b085ea6eacfd528`及五份原文件SHA。

S的唯一launch为`bfa488af-8d97-43ca-b634-b4e3a3be9040`，源`3a85be21eed90150e5a487796547741cd2e1f3ef`，另一张A6000 `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`。原guardian分配时钟为10月30日17:44:29，已确认唯一CUDA上下文；保留10路径、108标签、936分支readout及硬14GPUh。硬截止为10月31日07:44:29。半程00:05:52与终验07:27:15由S/Q原对话的`s`、`s-2`负责，没有重复检查或重新派发。这里引用原启动观察，不冒充本轮fresh运行检查，不读取部分科学分数。

Q1的原12状态、111完整pair/222 head、数值控制、释放、唯一中央结算及CPU分析已经由原负责人完整接受；实际0.2987564935850807GPUh。R16两目标分别选择同一I或M codec；R12的I-BR选择(4,8)、I-CFG选择(8,4)，M-BR/M-CFG均选择(8,4)，执行别名保留。它仍是旧保存状态的输出/codec证据，未建立完整视频收益或部署显存/速度收益。主线不重复结算、计算原指标或改写科学主表。

## 完整分辨率RGB实际成本

[登记](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_FULL_RGB_COST_CPU_FRAGMENT_R1.json)限定四卡CPU、1CPU/4GiB/零swap、无GPU/网络，180秒工作与30秒退出。使用两个显式合成3×93×432×768 float32数组，调用原RGB保存、fsync、SHA、校验、读取与完整MSE函数，原模型权重和生成均不加载。

[原捕获](../reports/cara_budget_full_RGB_cost_four_card_CPU_capture_r1_20261030.json)确认17:56:44至17:57:06正常退出/0。两份NPY共740524288字节，峰值RSS约829MiB。教师保存5.84秒，候选保存6.49秒；两数组读取/摘要/校验7.26秒，完整MSE再校验及计算0.84秒。按当前实现每个双FIT查询的两次保存、两组读取和两次MSE，观测分项合计约29.17秒。

缓存状态没有被控制，没有清理共享系统缓存；该测量不是冷盘上界，也没有测GPU到CPU复制，更不能直接当作A6000上的相同成本。文件、原证明SHA和实际Docker资源均在回执中保留。

## 费用依据与完整校准范围

[成本计算器](../scripts/prepare_cara_budget_calibration_cost_basis_r1.py)只读原B36两个FIT的Native/F19/Uniform19完整请求时间，不使用CHECK时间或T_DD替代完整请求。[4项控制](../reports/cara_budget_calibration_cost_controls_r1_20261030.json)验证完整604路径计数、CHECK不影响费用依据、部分原结果/错误资源拒绝及损坏成本摘要拒绝。

[分项依据](../reports/cara_budget_calibration_cost_basis_r1_20261030.json)中，若未来19D请求与原F19/Uniform19相近，默认301次双FIT查询加两教师的请求时间代理为36.34GPUh；若所有604路径都用原最慢Native请求作工程余量，分项为53.92GPUh。这两者都未包含完整warm、控制、冷加载、GPU复制、存储/评价、失败和释放成本，不是新实测GPU价格、保证上界或整卡报价。四卡CPU测量与旧A6000请求时间没有合并冒充同硬件报价。

[完整校准范围草案](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_WHOLE_SCOPE_DRAFT_R1.json)明确2warm、2新Native教师、2Native计时控制、2allD输出控制、2初始Uniform计时控制及2Q候选路径，总计`10+2Q`。默认301仅作612路径示例，实际Q、SA/HC轮数、整卡硬限与报价未冻结。控制不能从费用里省略，重复候选仍计查询和实际生成成本。

校准产生一个冻结mask；最终与S/DIAG/F19/Uniform等的共同端点比较仍是必需后续，待S和搜索mask冻结后绑定完整角色、去重、Native、warm和重复范围。没有以拆分校准/确认来规避GPUh审批阈值。

当前待选的是与S相同14GPUh的完整SA+HC预算适配，或保留默认301次搜索并承担更高费用。这是科学比较与成本方向选择，尚未请求或取得新GPU启动批准。后续超过4GPUh仍提交可审阅的完整方案。两卡CPU继续保留S优先；原A32/B36接受、评分、冻结和账本保持。
