# V1进入主线：把刷新来源的区间作用变成自动预算规划

2026-11-01。按用户最新分层路线，近期主交付改为**来源生命周期感知V1：同状态来源校准→双来源DP→19D/22D自动计划→完整视频验证**。完整离散伴随转为V2，先完成一次有界终点响应增强再决定是否投入；既有反向组件保留，V1不等真实模型反向。

[当前方案](../plans/cara_next_stage_20261101/source_lifecycle/README.md)和[机器协议](../plans/cara_next_stage_20261101/source_lifecycle/V1_PROTOCOL_R1.json)明确三种嵌套估值、相同规划器/候选额度、完整FIT一次选择、旧CHECK观察、强对照和止损。6GPUh是建议研发设计上限，未作为GPU或原账本授权。

## 当前四项交付

|交付|本次证据|下一项|
|---|---|---|
|真实缓存四格入口|原M1第8步完整14/8评分直接复用；第20步参数化入口新增flow OFF/ON各6条完整小权重CPU路径，00对Uniform、11对D20的latent/mock RGB逐值一致；原Linux合并24路径也接受|补完整14卡的源/收件/资源绑定，再真实GPU接受|
|来源覆盖审计|原108份JSON逐字节SHA回读，来源/网格/父计划核验；真正C状态的56行只有17种来源组合，固定阶段/年龄下的前来源间距对照为0|按四通用父计划补最多64个真实C状态shadow-D标签|
|可运行双来源DP|五项本地控制通过：小网格全枚举top3一致、来源改变后的区间重算、真实36网格精确19D/22D、原UniPC系数及拒绝边界|固定低阶模型与真实数据接入；合成计划不当作方法结果|
|P0/P1范围与报价|完整top3范围列入采集、所有消融/预算、参考与强对照、新LPIPS搜索、FIT评分持卡等待和释放|费用草案超过6，先确定预算设计方向；不靠缺项缩账|

原件与SHA入口：[组合准备回执](../reports/cara_v1_mainline_intake_preparation_r1_20261101.json)、[DP五项](../reports/cara_source_lifecycle_DP_CPU_component_r2_20261101.json)、[设计五项](../reports/cara_v1_source_design_CPU_component_r1_20261101.json)、[Point20十二路径](../reports/cara_v1_point20_CPU_component_r1_20261101.json)。真实V1模型尚未拟合，新视频效果为空。

## 机制复用与补点

按用户口径复算原完整损失的代数差，未重新计算任何指标：[第8步接受及消费者](../reports/cara_v1_P0_point8_reuse_and_consumers_r1_20261101.json)。两FIT平均`W_C=0.09436819`，`W_D=0.08329722`，两种读出条件下写入收益均为正。来源8由C9–15、C17–18读取，D19后退出最近两来源；这是原完整执行history的直接残差来源记录，不冒充全部工作状态的因果路径测量。

第20步由动作结构预定，预期直接消费C21、D23后被替换，形成不同消费结构；这些新终点结果保持null。P0合计16科学位置，8旧接受＋8新增，不重跑第8步。无未来C消费者的第35步写缓存交换，已经在原WC/UniPC小权重CPU剩余硬后缀中得到完全相同latent控制。

新增固定槽/来源图保留两CFG分支、三个物理窗口槽、真实sigma/step和工作状态。首轮CPU发现`previous_output`源图遗漏函数尾部写入，原失败保留；完整源码顺序要求第35步reset后仅无条件分支写回本步输出，修正后五项通过。没有改原WC源码或旧实验数据。

## 覆盖缺口已具体化

[108行审计](../reports/cara_v1_S108_source_coverage_audit_r1_20261101.json)：全部数据只有39种(t,a,b)，56个实际C状态shadow-D只有17种。全部标签中的六组固定阶段/年龄、不同前间距对照来自D父状态反事实；不能拿它们替代新父轨迹上的C状态覆盖。按父计划跨两FIT留出，不随机拆相邻行。

[64标签设计](../plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json)以sigma最远点/更新索引最远点分别生成19D/22D四父计划。每父最多8个C状态，包含固定(t,b)下改变a的(11,10)、(20,19)、(32,31)三组对照；选择只看网格和动作，不看误差，不从F19初始化。8父路径/64额外Dense paired标签的原调用分母为352，输出、复制、控制及释放另计。

## 费用决策

[范围与可行性草案](../plans/cara_next_stage_20261101/source_lifecycle/P0_P1_SCOPE_AND_COST_DRAFT_R1.json)以E1实测请求时间、原M1完整报价及显式外推为依据：新增P0约1.60GPUh、完整top3 P1约8.57GPUh，合计约10.18；包含已发生M1则约11.68。P1含至多132完整路径的责任上限，搜索按实测校准费用先验止步，实际查询数不预称相等；全新22D时钟、scalar-only采集IO和持卡评分时间仍需验证。

该草案不是已验整卡或新批准；用户已选择[先补P0，完整P1另审预算](../plans/cara_next_stage_20261101/source_lifecycle/P0_FIRST_P1_SEPARATE_BUDGET_DIRECTION_R1.json)。继续第20步独立14/512卡的完整入口、释放、评分与资源准备，P1另行提交预算。

实际Linux的原R2现已[完整接受](../reports/cara_v1_Linux_CPU_accepted_r2_20261101.json)：15项控制、24条tiny完整路径，72.014秒，容器退出0；四项独立接受器控制通过。R1原容器因漏入旧S元数据模块而退出1，[原失败](../reports/cara_v1_Linux_CPU_R1_failed_closeout_20261101.json)保留；静态依赖闭包107模块检查后，仅为新R2补一模块，没有改动或重派原R1。[最新组合准备](../reports/cara_v1_mainline_preparation_r2_20261101.json)明确新GPU仍为0。

原M1 1.500620266GPUh已唯一结算、检查已删；A32/B36/S/Q/搜索/E1冻结和WC/RA FIT UNMATCHED保持。新P0/P1四卡账本例外尚未获得，两卡限制、cap226、旧16.5及最终16/备用16保护不变。
