# 修复后的 P1 新单次完整审批卡

请求批准一张**独立的新单次P1 R2**：仅两卡服务器原单张A6000，完整146语义／最多142物理请求、5176模型pair、64同状态shadow标签，预计 **18.05067GPUh，硬限19GPUh**；同时请求仅本卡在四卡原中央账本读取、唯一预约和原guardian实际结算。新卡未获GPU/中央许可，未预约、未派发。原R1失败的4.933201964GPUh已结算；该单次批准不复用。

## 要回答的问题和保持的科学范围

用来源条件化估值和双来源DP自动生成19D/22D布局，比较阶段／阶段+当前年龄／阶段+年龄+前来源间距三层估值；每层每预算最多3个最低代理代价候选，按完整双FIT LPIPS原规则选一次，再观察原曝光CHECK。保持36真实更新、Cosmos/UniPC/CFG/C读出、合法性和来源年龄约束、原权重与Fidelity-v2。

原完整146范围不缩减：8来源父轨迹、24新基线路径、最多36候选FIT、12已选候选CHECK、48搜索FIT、4已选搜索CHECK、14warm/控制；允许原预登记同路径别名，物理上界142。内部最多42次双FIT查询／84评分对；完整释放后最多32新CPU对并复用本卡已封存内部FIT，完整52逻辑位置接受。基线含Native35、Uniform19/22、F19-C、F19-A1和原冻结RGB-MSE搜索赢家，新LPIPS搜索保持同实际校准费用限制。

**全部重新执行完整卡，不复用原失败38条视频、64标签或两个部分FIT结果。** 所有旧冻结/原CHECK曝光/四旧CAL范围、WC/RA FIT UNMATCHED和最终/备用16保护输入保持。新DEV、P2与V2不在本卡范围；DP优化的是代理目标，效果由完整视频验收决定。

## 两处修复与完整CPU准备

1. 生产者先在隐藏的`.pending-score-*`目录完整写入/fsync请求，再原子rename发布；真正残缺的既有请求仍严格拒绝，隐藏未发布意图保留且不能重试。确定性暂停测试在旧实现上复现失败，修复后消费者扫描期间看不到半成品，完整发布仅调用一次评分入口。
2. RPC输出包装使用隔离执行命名空间，内层saved/raw等变量不能覆盖外层stdout；原异常仍返回失败，不伪造成功封包。原故障保留。

[修复CPU33](../../../reports/cara_v1_P1_publication_RPC_Linux_CPU_accepted_r2_20261102.json)：本地隔离28通过，Linux33全通过，含实际Linux进程/服务清理；原CPU已退出。[新身份CPU56](../../../reports/cara_v1_P1_successor_identity_Linux_CPU_accepted_r2_20261102.json)：本地57通过（另含1个本机绘图控制），Linux56全通过，覆盖新卡权限、完整入场、失败拒绝、后评分完整52、一次FIT冻结和便携导出。无真实模型或原科学指标重放。原非Client broker函数/Host的AST与原源完全一致，科学数值/DP/模型/评分核心与原runtime保持，见[整卡组合CPU证明](../../../reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json)。

## 已准备的源、存储和唯一身份

- run：cara-source-lifecycle-V1-P1-full146-r2-20261102
- planned launch：498503f9cfd249f1aab929da18f04e10
- source：8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99
- registration：8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884
- GPU：GPU-cebf7119-cf03-23b9-e192-cd196332b704
- stage：/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102

[1473文件源包](../../../reports/cara_v1_P1_successor_source_accepted_r2_20261102.json)已独立回读，原CPU证明/报价/评分环境/存储4 sidecar SHA一致，无GPU授权sidecar、意图或容器。初次输入超时后回读确认stage、意图、原bootstrap全部不存在；只减少重复传输的来源映射，在CPU父注册SHA核验后恢复相同映射，才完成该唯一stage，保留全部原拒绝回执。

[独立64GiB输出与48MiB日志](../../../reports/cara_v1_P1_successor_storage_accepted_r2_20261102.json)已接受，/dev/loop49、output device1841，原准备进程已结束，输出空且journal pristine、完整物理占用及1MiB持久化探针通过。原R1失败卷/日志和所有旧CPU不改动、不重建。

## 费用、资源与调度

完整报价为原整卡保守18.02734GPUh＋最多42查询每次2秒额外发布落盘余量，总 **18.05067GPUh**；原64标签每个250秒snapshot余量仍是工程预算假设，不作为实测点成本。硬19GPUh包含CPU评分期间GPU持有、控制、加载、监督、停止及释放的完整原guardian单调时间。原R1实际4.93320GPUh单列，不抵扣新卡完整报价。

CPU/GPU资源：GPU容器2CPU/40GiB、内部CPU2CPU/8GiB均不swap；宿主初始50GiB、CPU24–27、每个内部查询新鲜12GiB；90°C、600秒停止释放余量；输出低水8GiB/宿主16GiB保持。最新[两卡只读快照](../../../reports/cara_v1_P1_successor_resource_snapshot_r2_20261102.json)：MemAvailable 50.106483GiB、原GPU空闲45°C、无compute PID/MPS/新卡容器，亲和性与独立输出通过。**这是准备快照，审批后仍须完整生产资产与现场资源fresh准入。**

最后一次原R1结算后中央cap250、used201.95503799855743、旧责任16.5、available31.54496200144257。本新卡尚未访问四卡或读写账本；批准后才实时核验，余额不足则不预约/派发。本请求不含新cap增额或迁移账本。四卡只做本卡原账本事务，中央operator复制到同机持久化`.sync`缓存以避免/tmp丢失，不做实验。

按实际guardian开始安排1/4、半程和终验三个单次安静检查；原硬截止为实际开始+19小时，提前10分钟停止释放。UNKNOWN只恢复该原句柄；成功失败都唯一实耗结算。完整GPU成功退出/释放/结算后才允许完整146/64/RGB接受、一次新CPU评分和一次FIT冻结。失败不自动新卡。

## 执行授权边界

[新授权草案](V1_P1_SUCCESSOR_SINGLE19_AUTHORIZATION_R2.json)保持execution_authorized=false、central_transaction_authorized=false；只有用户对本张新单次19GPUh及本卡原账本事务明确批准后才能绑定。审批依据用户既有“超过4GPUh每张单独批准”规则；原19单次已失败结算，不授予新卡预算。执行交接见 [R2准备交接](P1_REPAIRED_SUCCESSOR_PRELAUNCH_HANDOFF_R2_20261102.md)。
