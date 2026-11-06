## 最新：原完整卡已结束

全部1父/10后缀/6新视频及全93评分、独立重建已经完成，GPU/CPU均exit0，原四句柄退出并释放；实费1.388123693GPUh，累计23.702366117/50h。见[158完整结果](158_WC_CFG_FACTORIAL_COMPLETE_RESULTS.md)。下文正在运行/评分待是保留的启动历史，不能重启原身份。

# 累计预算50 GPUh生效，完整CFG四组合已启动

2026-10-08。本轮用户直接“批准扩大 gpuh，直接加到 50 吧”，已在共享锁内把服务器累计预算24→50原子更新。既有22.314242424 GPUh、59次任务和所有失败费用完整保留，启动前余额27.685757576 GPUh。原24→25请求及三轮blocked记录保持历史身份，当前预算阻碍已解除；单次预测≤2 GPUh自主、超过2 GPUh才询问，旧秒数上限取消的约定保持。

此前联合刷新相对单槽退化修复2.3974%，但仍比原WC失真高0.4527%，且当前多2次完整计算、严格未来少2次、全程均35次。这个有条件信号见[155完整结果](155_WC_CURRENT_CARD_FIXED_REFERENCE_RESULTS.md)。本轮补齐缺少的CFG0单槽，并在同一新快照内重新建立四组，检验单槽收益与自适应系统的联合交互；当前还没有新四组合质量结果。

## 已实际执行的预算和CPU绑定

[直接累计50h授权](../manifests/budget_authorization_20261008_wc_50gpuh.json)、[服务器更新回执](../reports/wc_cumulative50_authorization_receipt_20261008.json)和[24h旧账本原字节](../reports/wc_budget24_before_extension_20261008_native.json)均已存档。只改变cap、当前授权ref和追加历史；既有费用、任务计数及账本其他字段未改。

已通过CPU的生产源9c69152、全部277份载荷、完整事前登记和静态绑定保持。[selected配置](../configs/wc_w3_cfg_factorial_selected_r1_20261008.json)仅绑定允许的五项动态字段（selected、目标GPU、CPU原回执、cap、预算权威），冻结登记里的24h和注册预算保留原历史字节，外层cap为50h。

实际服务器selected CPU **13.805250秒**通过，PID3313244已退出、CUDA未初始化。独立从原始CPU回执重算静态配置绑定、277份载荷、授权SHA、账本全部旧历史、GPU/评分绑定，见[独立CPU验收](../reports/wc_w3_cfg_factorial_50h_selected_independent_cpu_audit_20261008.json)。这些是实现和资源证据，不是新方法结果。

## 原任务正在运行

`WC-W3-CFG-FACTORIAL-R1-20261008-A` / `wc-w3-cfg-factorial-r1`，冻结source **12bc430b54e9b1829e6d5c62b46cad1c5f05c6b7**，独立stage `.sync/wc-w3-cfg-factorial-selected-r1-20261008`，输出 `/home/gaokuangda/data/gkd/worldcache_omr/outputs/wc-w3-cfg-factorial-r1`。

完整范围保持：**1 WC父、10完整后缀、6新视频、1旧Native、4细胞全帧损失、4预定比较、1交互**；五组重复、当前输入/完整状态恢复、两个pre46前缀桥、70reset/71–72尾均保留。BASE、CFG0只D45、CFG1只D46、PAIRED D45+D46；后续各自按原生自适应策略继续，原D/no-op和负结果保持分母，不跨旧运行拼因果四组合。

全卡预测 **1.994372556 GPUh**，包含原加载/尾程/编码余量，不是秒数截止；完整卡≤2且在50h余额内，没有减少或拆分控制绕预算。

fresh准入目标A6000、SM8.6、24MiB/noapps，共享锁/账本/磁盘与原source通过后唯一提交。实际句柄：GPU监督器 **3313447**、运行器 **3313516**；CLI、source、stage和目标GPU已现场确认，随后目标显存24514MiB、compute PID为运行器。模型加载完成，已进入human_199_seed2生成入口，完整视频、后缀和终点质量仍待。

[启动原回执](../reports/wc_w3_cfg_factorial_gpu_r1_launch_20261008.json)、[实际三句柄与277源检查](../reports/wc_w3_cfg_factorial_live_handles_r1_20261008.json)、[生成入口观察](../reports/wc_w3_cfg_factorial_initial_generation_progress_20261008.json)保存原时点。该时点不是整卡完成或科学验收。

服务器第60job在途时used=50是**预留全部剩余余额**，不是已花完50h；已结算实费仍22.314242424h，本卡退出后按真实全wall（含加载/失败/刷新/释放）结算。根仓库budget保存最近结算及50h授权原字节，实时在途字段在上述live回执，不冒充结算。

## 后处理和接续

CPU等待driver **3313629**已部署于独立 `.sync/wc-w3-cfg-factorial-post-cpu-r1-20261008`，绑定上述两个原GPU句柄/source/config/完整scope/scorer SHA；等待时零评分/新增GPU0。GPU正常结束并释放后自动运行冻结全93审计：七个文件完整解码、四Native损失、四有符号比较和交互；CUDA禁用。GPU或审计失败保留全部原件/分母/费用，不自动重启，见[绑定回执](../reports/wc_w3_cfg_factorial_post_cpu_r1_launch_20261008.json)。

后续只观察这三个原句柄，不修改在跑源或重新提交；捕获终态/费用/释放及评分原件，独立重算状态、实际动作、93帧比较和交互后再解释收益。科学边界保持：一个已曝光seed2的卡内固定Native探索性诊断，无独立CONF、清洁端到端速度、正式单动作RV训练标签或物理/语义质量验收。新假设按下一轮事前登记；重大方向选择共同讨论，不自动扩大训练、稀疏或人评。

此前goal工具blocked属于旧累计预算阻碍，直接用户授权已解除该条件，本轮已实际恢复执行。该工具没有主动resume接口，保留其原始状态为工具历史，不将整体科研目标误报为完成。
