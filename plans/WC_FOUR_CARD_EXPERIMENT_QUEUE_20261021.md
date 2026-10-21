# 四卡后续实验清单与两卡恢复边界

2026-10-21直接人类要求：两卡每4小时检查状态，准备在四卡继续实验。本文件取代旧“两卡一旦空闲即自动派发”的主机选择；保留原科学范围、上游、预算和失败原件。目标是得到可复现的策略生成程序，不能将换一组手工步号当作方法完成。

## 当前执行状态

- **四卡为后续实验目标主机，科学GPU尚未启动。** 29项依赖/请求/实际CPU编解码组件通过；完整固定模型、推理导入、CUDA兼容和各scope新机生产CPU尚未完整接受。
- 公开辅助模型独立R2已完整接受：Qwen3Guard/SigLIP原14文件5,034,332,532字节全部独立全哈希、两命令0、13件复用/唯一SigLIP请求完成，原R1失败和收件UNKNOWN保留。96件生产模型R1失败保留，17:42独立R2 source7f79ceef/PID94749于18:23技术失败，原1,132,462,080字节partial留存；626已核对魔搭四个Reason1分片元数据全SHA/大小精确相同并在服务器短测更快。旧R2半程已删，sha改约本日19:35一次资源恢复，尚未启动新下载worker，完整生产资源未接受。模型只在外盘`/Volumes/data`中转，每件服务器完整SHA后删除新外盘副本，令牌只Mac受限文件。详见[623](../research/623_WC_PUBLIC_ASSET_R1_TIMEOUT_AND_MISSING_ONLY_R2_RESUME_20261021.md)与[625](../research/625_WC_AUTHORIZED_MODEL_RELAY_IMMEDIATE_REPAIR_AND_MISSING_ONLY_R2_20261021.md)。
- 两卡只做只读恢复/原句柄/完整权威账本交接，不自动启动新GPU。17:48槽延后至18:11:20.181997仅一次认证前255，GPU/v2/原句柄未知；按真实尝试＋14400秒，下一最早22:11:20.181997、实际约22:12，之后仍向上取整分钟。无可行动变化静默。
- 单个昂贵任务保持串行，四张卡不代表自动启四份卡。每张卡依fresh UUID、显存、compute、锁、主存、磁盘和共同预算准入；不停止其他用户任务。

## 顺序、范围和当前缺口

| 顺序 | 实验或前置 | 固定范围与要回答的问题 | 当前状态/费用边界 |
|---|---|---|---|
| 0 | 四卡资源和主机接续 | 固定Guardrail、Reason文本编码器、Predict主权重/VAE、Qwen3Guard/SigLIP及LPIPS；完整推理导入；实际CUDA兼容；各卡新机CPU/注册/报价；单一权威v2交接 | 正在模型下载/传输。组件通过不充完整环境或实验接受；不需要Cosmos3-Nano、Wan、T5/Llama替代模型 |
| 1 | **BANK24** | 六个固定新DEV×D21/A21/NATIVE35，18正式+6完整warm=24路径，864pairs/1728CFG/1load/六Native；四CAL固定gate能否在新DEV分配D/A | 原两卡R2 CPU已接受，新机CPU待验。旧机forecast3.407222222/cap4.5 GPUh仅旧规划，Ada须完整重价 |
| 1后 | BANK24同D配额与X-R方向诊断 | 在同一已验银行比较固定配额选择、随机/可枚举组合及注册方向；保留失败分母和原生参考 | 已登记离线CPU分析，不新增独立GPU，不充在线闭环/clean端到端速度 |
| 2 | **完整1624真实区间标签＋独立动作价格** | 四CAL×406合法(s,t)=1624正式格；14完整Native/OFF/ON路径；含ON warm合计2030采集格、13020实际读出试验；保存原始量并独立重算统计和价格 | 实现与原完整报价已具备；真实生产CPU尚未接受。旧forecast9.918333333、**整卡上限12 GPUh已明确批准**，保留原config与批准，新机须重价/CPU且BANK24完整接受 |
| 3 | **PG-P1：单预算自动策略生成闭环** | B=同profile干净Native CAL均值的0.80；四FIT＋两个事前冻结的新SELECT；Q≤8，首4＋一次至多4联合邻域；候选由代码生成；完整自然轨迹端点评价 | 最大64条基础完整路径草案，额外采集另加整卡；两个SELECT未冻结、任意mask入口/真实资产绑定/完整报价/实际CPU待完成，forecast与cap均为空 |
| 4 | **PG-P2：等优化机会的独立贡献消融** | 同时间强前密C/A、固定修正覆盖仅优化D、纯局部代理、联合边界/读出＋端点修订、同语法简单/随机邻域；总Q/校准GPUh/初始信息/选择可见性一致 | P1后冻结候选并集、去重、完整报价和自身CPU。若用先D后A，两阶段共享同一总Q，不能各给8次 |
| 5 | **PG-P3：跨预算及模型/设置再校准** | 先第二预算0.70 Native，再成熟第二CFG骨干或明确第二设置；算法规则固定，重采合法结构/误差/价格并自动生成 | 条件后续；完整报价/CPU未定。第二设置不称第二模型，重新校准不称零样本迁移 |
| 6 | **PG-P4：冻结后独立确认** | 冻结方法、对手、预算、选择规则后选新TEST；保真/最差prompt/失败、重复干净时间、自动质量及校准摊销 | 最终168正式路径是未准入草案，warm/桥接/额外资产须加完整价；旧N07/N08/N10归旧H1/Efficient，不移作新生成器结果 |

WC固定官方推荐配置，无须为本队列增加WC调参。RA继续保留同期强对照；新方法的独立贡献主要由同预算强简单方案、等优化机会消融及独立输入验证，不能只用“比官方WC好”替代。旧人工32路径结构筛选后置，N07/N08/N10、Window24、CAL12已接受部分不重跑。F/B关闭，无训练、人评、付费VLM或OMR。

## 主机迁移的可执行门

1. 复用服务器已经SHA接受的源码/runtime/env-r3；GitHub发布必要新适配增量，在四卡**独立新stage**登记真实source、runtime、模型、配置和CPU命令。保留原两卡stage，不能以新HEAD覆盖其源码。
2. BANK24科学闭包仍绑定`2bd41dc8fa19f42353e03a7c78b7264b4b2695c6`生命周期1789源和`c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9`入口1772依赖；原机CPU三件套作为有SHA的依赖保留。只为新的主机/适配/环境边界做完整实际CPU验证，不重复旧248+10数值、原入口或身份扫描来冒充新进度。
3. 原CAL12真实capture/accepted/gate直接复用：`reports/wc_scout_CAL12_full12_terminal_recovered_collection_20261019_1830.json.gz`、`reports/wc_scout_CAL12_full12_terminal_independent_acceptance_20261019.json`、`reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json`。mu/中位秩固定，较大z保留D、平局>=，DEV不得重拟合。
4. 完整1624配置仍为`configs/wc_policy_interval_assets_full1624_r1_20261020.json`，SHA`75338efd0d7c2d145c73bb3d5514c37fcec46851995785724eeca8f650419f9a`；批准`reports/wc_policy_interval_assets_full1624_specific_whole12_approval_20261020.json`仍有效。原两卡首CPU提交只有认证前255/launch=null；旧stage存在性未知，不能重放或称CPU通过。四卡创建独立新stage，用自己的三命令实际CPU全原件接受。
5. 若原CLI硬编码两卡SSH/根路径/账本，先实现精确独立适配，核对`--help`和实际依赖再启动。`launch_wc_scout_gpu_r1.py`、`wc_policy_interval_assets_lifecycle_r1.py`的旧证明/调用不自动变成四卡可执行证明。
6. 新机完整报价包括全部Native/warm/载入/实际动作/观察器/复制哈希/评分post/失败退出余量；保留旧估计而不是覆盖历史。真实GPU兼容/计时核验本身若需要占卡也须先注册完整工作与费用，不能当免费探针。完整单卡严格<12且余额够直接推进；已有1624具体上限12批准不再询问，若新整卡超过已批上限或余额不足才问具体完整卡，不缩拆。

## 单一账本与未知任务

四卡目前未接受共同权威v2交接。最近两卡成功余额仅10-20 16:05历史，不能据此在新机开账本。新机科学GPU前必须取得完整权威v2、核对settlement和全部活动预留，并形成**旧主机禁新派发、唯一预算写入权、全历史SHA**的交接证明；原cap226、origin79.99637737158223和所有费用历史保持。来源缺失或活动未排除时，保留该GPU前置，继续可独立资产/CPU准备。

两卡恢复时一次读取原stage/launch/fence/句柄和完整v2。已有任务仅恢复、接受和结算，未知连接不当未启动或终态；不删除fence，不在两主机同时执行同一注册卡。CPU证明、主机准备通过和GPU实际准入分别记录。

每个新长CPU/GPU按**实际launch**安排一次技术半程和预计结束后一次原件查收；只读半程不读质量partial。终态保存原件后离线独立分析，未完依据已存进度重估一次后结束；失败、拒绝、未到达不填0/补点/缩范围。全wall实费、owner和UUID锁释放分别接受。当前模型检查保留，科研卡未启动前不虚排科研半程/ETA。

## 依据

- [622本次主机与调度决策](../research/622_WC_FOUR_HOUR_TWO_CARD_MONITOR_AND_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)
- [621四卡资源在途](../research/621_WC_FOUR_CARD_RESOURCE_COMPLETION_FIXED_PUBLIC_ASSETS_AND_AUTHORIZED_MODEL_GATE_20261021.md)
- [原BANK24接续与逐件协议](WC_SCOUT_GPU_READY_CONTINUATION_20261019.md)
- [完整1624执行卡](cara_policy_generator_20261020/REAL_INTERVAL_ASSETS_EXECUTION_CARD_20261020.md)
- [PG-P1完整范围草案](cara_policy_generator_20261020/single_budget_validation.md)与[方法验证顺序](cara_policy_generator_20261020/execution_plan.md)
