# 可复现的区间方法规格 v6-r1

状态：**开发算法已明确定义并实现本地结构编译/选择控制；未接入或接受实际新生产采样。最终B1/B2配置未选定。** 文中索引k是从1开始的实际guided更新序号，不是模型噪声时间t；`num_steps=35`在当前固定后端产生36个guided更新，所有验收以真实solver网格及哈希为准。

## 1. 方法身份与接口

开发接口分两层：

1. `Compile(context, base_D, move_D, drop_D, coverage, alpha, support)`生成固定D/A/C序列和逐步真实D来源。context包含模型/权重、solver网格、精度/backend、CFG与输入协议；本地编译器只处理序列结构，生产配置必须另绑定这些身份。
2. `Select(CAL_endpoint_matrix, measured_time_budget, quality_guards)`在冻结有限候选中选择一个所有提示词共享的策略。仅使用CAL真实终点及相同定义的实测时间；不读取TEST、不按单prompt分别选赢家。预算B是秒数，K_D只是执行数量描述。

现有实现：`src/wcomr/interval_policy_v6_r1.py`。它支持区间生成和完整CAL矩阵的预算/质量约束选择；不负责模型加载、推理或GPU准入。原H1在线控制器、原A_NO_P和新编译策略有不同身份，见[映射](paper_variant_map.yaml)。新方法暂称“CARA-Cache Interval”，名称不代表已验证优于旧H1或近邻。

## 2. 合法布局与连续区间

当前基准D集合为`{1,…,21,24,27,30,33,36}`。新协议继承本后端保护更新1—7与36、开发最大来源年龄6；这些不是所有模型的普遍定律，真实owner的保护/支持条件必须再次核对。

**先得到最终保留D集合，再生成修正区间。** 移动D与删D以不同类型登记：

- `move_D=(33→22)`重新分配一个D，只改变布局，默认不会请求A33—35。
- `drop_D=21`移除D21，并在`[21,next_retained_D)`内按预登记coverage修正。
- `coverage=dropped_intervals`：修正所删D引起的连续缺口；FULL从k起，LATE从k+1起。FULL/LATE是不同候选，不能事后更改。
- `coverage=all_reuse`：每对保留D之间所有缓存更新都执行A；不创建新的真值锚。
- `explicit_ablation`：仅用于已登记单次位置/无A对照，不能把它冒称完整区间方法。

例：仅删D21，区间是A21/22/23，D24终止。若同时D33→D22并删D21，区间是**A21，D22终止**，A22/A23旧位图不可套用。移位纯C、移位全A、移位＋删21局部A是三个独立配置。

诊断/受控实验中非法位图、缺来源或不符注册scope必须明确拒绝，不默默改mask。未来部署若模型/条件/精度或支持域改变，须在执行前选择真实D回退并记录实际额外成本；此部署回退尚未实现/验证，不能用旧固定mask的“失败即退出”证明已具备部署回退。

## 3. A的实际执行和CFG一致性

对分支b，在严格过去的真实D来源s保存浅层增量p_s与pre-warp深层残差r_s；令`d_s=r_s-p_s`。当前已有浅层增量p_k给出：

\[
\hat r_k^b=r_s^b+(p_k^b-p_s^b)=p_k^b+d_s^b,\qquad\beta=1.
\]

当前实现的顺序是：在原current输入上构造`original+hat_r`，沿**同一个既有warp函数**（仍以原cached residual为参照）处理，再调用既有final layer/unpatchify；随后在当前latent/timestep/conditions上按原Rectified Flow变换得到候选velocity，最后两个CFG分支使用同一个α进行**post-RF输出融合**：

\[
v_A^b=(1-\alpha)v_C^b+\alpha\hat v^b,
\quad v_g=v^c+7(v^c-v^u)=8v^c-7v^u.
\]

共享α使线性CFG合成一致；不声称warp、非线性head或RF变换可以任意交换。原ordinary head与候选head在当前版本即使α=1也都付费，不先做head elision。A/C只能读严格过去D历史，不写true-D锚、不使用教师/未来状态；每次请求及模型/条件变化重置owner。

源码依据：`cfg_guided_w1_outputs.py:unit_increment_residual/shared_output_fusion`、`cfg_guided_w1_deployment.py:hidden/end`、`math_n2_source_readout_r1.py`与`source_phase_fixed_mask_r1.py`。实际生产适配须证明这些执行依赖与已验版本一致，只替换注册mask/coverage，不改warp或solver。旧固定执行器遇不支持状态会报错，不将该行为写成未实现的部署D回退。

## 4. 有限候选与选择规则

首轮不训练新预测器、不调β、不启P/F/B；新候选统一共享α=1。K25/K26各固定3项（[实际mask](DEVELOPMENT_UNION_V6.json)）：

| 数量档 | 候选 | 已验可复用/新增 |
|---|---|---|
| K25 | 原前密删21＋FULL21—23 | 复用Window24 A3 |
| K25 | 原前密删21＋LATE22—23 | 复用CAL12 G01 |
| K25 | D33→22、删21＋FULL | 新增，实际仅A21 |
| K26 | 原前密全部reuse用A，统一α1 | 新增；旧前密A晚段α不同，不能冒用其结果 |
| K26 | D33→22、全部reuse用A，统一α1 | 新增 |
| K26 | D33→22、纯C | 复用CAL12 |

原前密C、旧前密A及其他旧方法是对照，不按每prompt选择。R2-A补Single22/Single23，各4CAL；原Single21、无A、LATE与A3复用。

真实时间B1/B2、每prompt质量上限和tail阈值在真实生产卡执行前登记，当前为null；不从工程估价推算“同成本”。开发终点按提示词等权均值LPIPS排序，满足同口径均值时间预算和预先指定的最差提示词退化上限；同损失时按时间、固定ID确定顺序。拒绝/失败/缺失保留，候选若无完整CAL矩阵则不得被选中，不以缩小成功队列获胜。

候选初轮之后至多一次有明确失败分析的科学修订；技术打包修复保留原失败、用新版本，不能借修复无限增加候选。没有候选满足预登记预算/质量约束就报告无可冻结增强，不强选新方法。不宣称全局最优或硬实时保证。

## 5. 来源先验、价格和最终冻结

已有移位方案来自两个旧Native轨迹的分轨迹标准化统计与旧RA传播g²先验；这是共享计划开发线索。其全终点改善已验，但没有g²消融，不能独占归因给曲率或在线内容感知。R1首轮先固定这一候选来源；R3只有在原有限候选/相邻配置内做预算校准，不临时生成无限mask。

完整32路径工程价格含加载、全部warm/桥接、guard相关未归因余量、A执行规划余量、观察/哈希和margin，仍须真实入口/工具/注册闭包CPU验证后重价。价格是费用规划，不是证明各动作独立单价、clean延迟或质量收益。

最终冻结包必须同时记录：B1/B2秒数、所选D/A/α、fallback语义、模型/solver/source/资产SHA、直接近邻版本及适配边界、WC/RA有限调参、数据和质量/时间队列、完整物理scope与费用。冻结后R4/R6才为新最终方法生成独立主结果和测速；旧H1的N07/N08/N10不得迁移到该身份下。
