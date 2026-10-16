# N09部署开销补验：五个冻结工作点的完整40路径范围

2026-10-16。**已将运行部署开销固定为五个原冻结工作点、两场景、完整40路径的独立对照，便于在N08后接真实生产验证。** 这项范围登记回答组件开销和请求显存；同状态动作报价、可复现标定采集费用继续分别保留，不能用组件计时替代。

本轮只读取本地原件并检查完整矩阵，没有查询在途任务、派发生产CPU或GPU。原N07及其明早05:30验收保持；原本机资源今天14:00查收保持。

## 1. 三个需要测清的量

|问题|已有证据|仍需完成|
|---|---|---|
|最终实现的线上费用|完整102 Toy CPU验证观察器不改变执行、输出和owner释放；此前完整请求有主计时与外层字段|在真实Cosmos上测组件、请求初始化/清理/GC和逐请求显存，并作profile/原执行的等价对照|
|同一已支付双probe状态的动作价格|旧C/A/P0/D费用及head转移记录可追溯|按当前冻结读出、来源及实际执行边界重测；C/A/P0/D完整合法集保持|
|可复现部署标定的采集费|16标签能精确重建冻结四格表；CPU拟合约0.2ms，相关历史整卡4.383638799GPUh|明确需要采哪些标签/传播先验/动作费用，完整执行一次部署采集流程并分项计费|

第三项可给出可复现配方的实测成本，不预先声称达到数学意义的全局最低值。旧研究账单继续保留；标量拟合耗时不含教师标签产生费用。

## 2. 五个工作点与两场景

沿用N07/N08在新共同输入选择前冻结的五角色，不依据正在生成的新测试结果改选：

|角色|原内部方法|
|---|---|
|Full Inference|NATIVE35|
|WorldCache|WC_HALF|
|RA-CFGCache|RA_DEFAULT|
|GCR Efficient|A_NO_P|
|CPA High Fidelity|TABLE_PHASE_H1|

输入沿用N08的旧AV28与Human场景、seed0、35请求步/实际36次更新、768×432、93帧及原提示词/negative/guidance。两个旧场景用于部署测量，不增加未见测试样本。

## 3. 完整40路径

每个场景、方法均有三条完整路径：

1. **ORIGINAL_AUDIT**：原执行，完整guided轨迹与原件。
2. **PROFILE_AUDIT**：启用组件观察器，保留相同完整guided轨迹。
3. **PROFILE_LEAN**：组件观察器保留，仅关闭研究取证副本/文件，不关闭算法实际维护。

十个scene×method组，共30正式诊断路径；另每组一条完整原执行预热，共10预热。总40路径、1440 guided pairs/2880 CFG调用、一次模型加载、零在线teacher。其中20条启用profile。

顺序继承原N08的事前平衡框架并将三轮标为不同诊断模式。原N08自己的40路径及独占clean协议不变；额外profile路径不附加到其未重报价的scope，也不进入clean均值。

完整检查10组原audit/profile-audit的所有36步guided张量，以及10组profile-audit/lean的终态、动作、A/source history、全部兼容93帧RGB和owner释放。拒绝、技术失败与未到达位置保留在完整分母；不能只以前几个路径不OOM或终态相似接受整个scope。

## 4. 记录与解释

组件包括shallow/deep block、普通head、solver、VAE、安装、选择/提交、修正warp/velocity转换、请求边界GC与写盘。计时使用已验记录器：显式当前stream的CUDA事件在请求结束后读取，内部不逐项同步；CPU与CUDA区间均为inclusive，嵌套部分不相加冒充总延迟或纯kernel成本。

真实测量保持正常安全管线。逐请求显存在模型驻留后、安装/请求开始前reset peak，完整请求和清理后读取allocated/reserved及各自峰值；保存起始值和执行顺序。该整体峰值包含正常guardrail与算法开销，不自动称为纯缓存模块显存。allocator缓存会跨请求保留，报告起始基线与绝对峰值，避免把warm-cache差异归成方法独立内存需求。

主部署表使用PROFILE_LEAN的组件与显存，PROFILE_AUDIT用于等价检查和诊断取证税。两模式的时间差只描述当前观察设置；正式重复速度来自N08，不能把不同模式当同一方法的三次clean重复。

如果某个合法动作在两场景没有被选中，对应运行计数为0不代表其价格为0。尤其H1原P0仍合法；真正的C/A/P0/D同状态报价要另以共享双probe输入、真实来源和完整动作分支测量。旧one-phase A、旧head转移费用不能未经当前实现核对就当最终报价。

## 5. 已登记与尚未选定的部分

[完整scope manifest](../manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json)绑定原五角色冻结、N08原输入/顺序、102 CPU接受及当前观察器/执行器源码。独立重新读取矩阵确认40唯一位置、30正式/10warm、每组完整三模式、1440 pairs及20 profile路径；这只是声明范围检查，没有实际采样或生产CPU结果。

同时重新读取原102接受回执绑定的完整capture，核对其原SHA后，确认当前观察器、共享执行、有限基线与GC包装四份源码均与原payload完全一致。已有102观察等价证据可以保留复用，本轮没有重新跑102或952，也没有把声明范围检查升级成实际Cosmos生产验证。

执行前仍要完成真实Cosmos/guardrail/设备的受影响生产CPU、完整打包与实际整卡报价。已有102/952 Toy数值与观察器接受在源码一致时复用，不重复整个开发CPU矩阵。原N07、N08完整验收后，再按fresh v2余额/逐UUID锁及严格<12 GPUh规则推进；本轮没有新GPU卡、计费上限或授权。

N09的动作报价与标定配方采集仍须单独具体化完整范围及合并费用，不能以本40路径范围声称N09全部完成。无需新增人工标注/评审，也不恢复F/B、P-ACR、训练或OMR。

## 原件

- [40路径声明范围与源SHA](../manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json)。
- [独立矩阵检查回执](../reports/wc_paper_N09_runtime40_scope_inventory_20261016.json)。
- [原102观察器/执行器四源码一致复核](../reports/wc_paper_N09_profile40_unchanged_observer_reuse_20261016.json)。
- [已接受102 CPU观察等价证据](478_WC_N09_FULL102_CPU_PARITY_ACCEPTED_COMPONENT_PEAK_PROFILE_READY_20261016.md)。
- [已有标定与费用盘点](465_WC_DEPLOYMENT_COST_SOURCE_INVENTORY_AND_PROFILE_NEXT_20261016.md)。
