# 成对probe接口完整CPU通过，真实模型一致性与成本仍待

2026-10-09，承接177与预登记H-T50。**当前两侧浅层probe可以先完成，再共同决定CC或DD，并继续各自原深层计算；声明的Toy fixture上与原调用顺序的同动作对照逐项一致。** 这解决联合刷新基线的一个接口准备问题，没有执行风险拟合、真实模型生成或新GPU任务。

## 目标、方法与完整设计

原RF闭包先完成cond，再调用uncond。若在cond深层决策时使用两侧当前probe，需要把网络调用拆为成对前缀和后续续算。新模块不重写注意力或深层近似：从固定WorldCache原决策表达式暂停，保存局部变量；第二分支用自己的计数完成probe，选择器只收到两份标量统计，然后按cond→uncond续算。真实RF denoise条件帧投影、条件时间、输出替换及`.float()`保持原函数体；原FP32 CFG运算顺序保持。

通过AST逆变换比较，WorldCache除单个决策表达式、RF除单个net调用以外的语法树相同。上游文件不修改。该prototype直接调用编译的函数体，所以拒绝外部net/global hooks；block仍走普通Module调用。失败后接口poison、不得继续，整个测试副本弃用，**不声称任意真实模型故障可在此接口内完整回滚**。

| 预登记范围 | 实际完成 |
| --- | --- |
| flow OFF／ON，两配置各22次更新建立双CFG历史 | 两配置均完成，网络计数44 |
| CC／DD × 两严格重复 × 两配置 | **8／8**原顺序与成对顺序比较 |
| 两配置各一次初始化保护DD | **2／2**，选择器未调用 |
| 每配置四类失败控制 | **8／8**预期拒绝，poison后续调用均拒绝 |
| WC字段、全部模块buffer、输出、输入／条件、CPU RNG、计数和浅／深层次数 | 全部对应比较一致 |

四类失败为选择器抛错、非法混合动作、选择器改计数和外部net hook。8主比较均在同一个人工构造的latent、固定条件与相同双CFG缓存历史上进行；不能当成8个真实场景。权重、attention与条件构造声明为Toy，真实WorldCache／RF函数体及冻结Video2World条件类保留。

## 实际执行、原失败与独立检查

R1固定源`3e9cebf`的实际CPU在严格counter=44检查停止，driver **9.281182秒**。原因是测试fixture把`apply_worldcache(num_steps)`设为35；该参数是网络调用周期，应为当前两CFG的70，22次更新后计数提前重置。原源、日志、失败回执与分母已[完整封存](../reports/wc_cfg_paired_probe_core_cpu_r1_failure_capture_20261009.json)，源与账本未变，没有把R1追认为接口成功。

R2固定源`92075c5417d0e997caf2696174636bdb6de9d0ef`只修正fixture周期为70，完整范围不变。在服务器独立目录`.sync/wc-cfg-paired-probe-core-cpu-r2-20261009`，用现有生产venv且禁止CUDA／下载执行。实际fixture **5.779145秒**、完整driver **8.293475秒**，原driver3421064／child3421065均exit0并已退出。

[独立本地重建](../reports/wc_cfg_paired_probe_core_cpu_r2_capture_and_independent_audit_20261009.json)从服务器原字节捕获回执、结果与日志，验证49载荷／8上游源、每个flow的完整动作×重复集合、输出／guided／WC+buffer双臂摘要、分支44／45与终计数46、调用数、标量有限、全部失败及poison。原服务器Torch执行使用`torch.equal`核对实际张量；本地重建为原件／分组／签名检查，**不是第二次加载张量**。CPU账本前后字节相同，新GPU提交0。

## 发现与下一步

成对前缀不必重复算浅层。在四block、probe_depth=2的CPU网络中，选择前浅层block各增加2次访问、深层0次；CC保持该次数，DD深层各增加2次。原顺序同动作与成对顺序的FP32输出及最终缓存状态相同，为后续比较独立路由、简单共同刷新和校准联合风险提供接口基础。

这些访问数和CPU耗时不能换算为2B GPU速度。真实模型中准备层／深层的状态依赖、额外显存、实际同步成本、完整非干扰与真实输出仍需单独完整控制。Cosmos的rho与传播先验尚未校准，已有五个曝光状态不得冒充独立校准或确认集；当前不能称为RA-CFGCache复现。

下一优先级保持：先完成原Human seed3 H-T48的完整五起点、120张量、20重复、两视频全93帧及224条件／76solver CPU核验；再结合全部正负结果准备真实成对probe一致性和成本卡。若完整预测超过2GPUh，按既有约定询问，不缩小或拆分对照。近邻RA-CFGCache与真实缓存／solver历史信息的增量价值仍需直接区分；本轮没有选择新GPU、训练Head／LoRA、扩大稀疏、切换OMR／DRE或引入人评。

## 原GPU进展与费用边界

[同期只读快照](../reports/wc_cfg_mechanism_confirmation_r1_paired_probe_preparation_live_20261009.json)确认原3409913／3409924／3409914均活、固定source`00b06e6`／77文件保持。OFF父完整；ON已有S23_after_CC／DC／CD三个完整8对块，S22完成6对、另1对进行中，S23_after_DD待。未接受子集评分，无新seed3机制或质量结论。只跟踪原句柄，不改正在运行的源、不重投。

累计实费底数仍为**26.279085386／50GPUh**；第63次GPU任务在途，服务器used50是预留，终态按原supervisor实wall结算。原卡自动释放后已有绑定CPU程序会做完整重建。组会[飞书文档](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)revision12已包括此前完整成果与近邻；本轮CPU准备不替换其中的科学结论。整体goal active，当前实际CPU进展及原GPU验证等待，不是研究完成或方向受阻。
