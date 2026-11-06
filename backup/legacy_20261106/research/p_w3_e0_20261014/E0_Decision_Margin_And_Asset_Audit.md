# E0：H1真实决策边界与现有素材审计

2026-10-14。本次完成CPU/只读E0，GPU、模型前向、新teacher和服务器写入均为0。已有A/H1结果不变，原F/B结束。本报告接续[425设计](../425_WC_P_W3_DESIGN_UPDATE_AND_NEXT_STEPS_20261014.md)，不覆盖其当时“仅设计”的记录。

## 1. 最有用的发现

**H1的完整计算可以准确分成“优化器主动”“保护”“缺支持”三类。** 四个CAL的中档均为：

|实际执行类别|更新位置|每条数量|新实验处理|
|---|---|---:|---|
|保护D|1–7、36|8|保持保护，不拿来证明替代D有效|
|优化器主动D|8–24|17|新P主要检验区域|
|实际A读出、物理CC|25–29|5|W3 A/C边界与P读出对照|
|实际C读出、物理CC|30、32–35|5|W3 A/C边界与P读出对照|
|缺校准支持回退D|31|1|保留fallback，不能算主动D或新特征可解锁的位置|

共独立重构低/中/高三档×四提示词的**12条路径、432步**；中档144步中108步有完整合法动作评分。重构未导入旧控制器，直接核对冻结参数、实际来源、年龄、paid packets、绝对MSE、g²、费用、J、argmin及实际读出。

## 2. D31的具体原因

四条中档第31步均记录`missing_current_calibration`，`protected=false`，真实D/工作来源出生于24，查询age=7，`local_proxy/gain/candidate_risk_and_price`为空、`optimizer_selected_D=false`。底层在`(anchor,step)`相关性或该步传播增益缺支持时回退，当前原支持采用age1–6。

这里不是“风险很高所以优化器选D”。新Trend不能仅靠预测值取代缺失的合法校准域；支持扩展是另一个实验问题，本轮不做。

## 3. 边界与优先位置

H1报价仍为历史after-paid-probe完整CFG对报价，不是新clean算子费用。中档所有主动决策的最优/次优J差为**0.0106976–3.0036307秒**；主动D为**1.2286331–3.0036307秒**，次优均为旧P0。后者分差在四提示词间完全相同，因为该区间的次优P0使用同阶段固定出生误差报价；这不表示真实误差相同。

最接近边界的几个点：

|提示词|步|最优/次优|J差秒|
|---|---:|---|---:|
|AV28|29|A/C|0.0106976|
|AV51|30|C/A|0.0151184|
|Human|30|C/A|0.0205685|
|misc|30|C/A|0.0479024|

因此新P以早期主动D为主体，W3重点检验A/C边界的真实标签。J差是局部代理分差，不能当最终视频误差差或真实节省时间。

**PA已按原动作预选12个H1状态**：每提示词12、23步的主动D，共8主状态；AV28/misc第29步A、Human/AV51第30步C，共4边界控制。未根据新teacher或终点选点，未将旧pi0同一步冒充H1状态。此为状态清单，完整重复、预热、执行器与费用仍待生产封口。

## 4. 服务器只读审计结果

一次SSH-stdin CPU读取全部旧28状态文件，约2.45GB；不传新文件、不修改旧stage、final或账本。源代码归档分别652/638文件，原runner/final SHA及逐张量身份均通过。

|素材|核验|可用范围|缺口|
|---|---|---|---|
|source_phase16，16点/192张量|VERIFIED，全部文件/张量哈希、形状、原Gram/MSE一致|两个post-RF分支的C、D_REFERENCE_A、FUSION_A、NEW_P及同状态DENSE|PI0_NOT_H1；无逐步完整前置probe张量序列|
|N1，12点/144张量|VERIFIED文件/张量身份、schema/分支形状；本轮不重做N1拟合|四种旧读出及Dense|FUSION_HALF不是当前γ=0.7235237；不作为当前A的新验证|
|420 H1清洁运行元数据|完整12条H1/432步实际记录重构|因果动作、来源、两个paid漂移标量、完整timestep列表|没有逐步H1分支C/A/D真值和浅层张量；timestep不能冒充sigma|
|旧parent-vectors|已有索引/原审计，**本轮未重读**|guided36与final latent|guided不可唯一恢复c/u；不是完整求解器/cache/RNG快照|
|N1快照字段|METADATA_ONLY|输入/状态哈希身份|明确`NOT_SERIALIZED_CHECKPOINT_HASHES_ONLY`，不可直接恢复|

分支velocity形状为`[1,16,24,54,96]`、float32。N1与source_phase文件总336张量。source_phase四候选绝对Gram以float64差值重新计算，全部64候选MSE/Gram与原件一致。所有teacher严格离线。

CPU审计体内116.3323秒、含SSH/启动总496.8954秒。后续同类查收按总启动耗时估时，不只看CPU体内时间；这次未持续监听远程日志。Torch CUDA未初始化、远程写入0、预算SHA前后一致，实结79.996377372/cap104.971363333、余额24.974985961 GPUh。账本旧文字状态未改；它不表示旧B仍在运行。

## 5. 接下来的具体含义

1. 已有数据足以做新P的离线方向/系数区分，结果见[PA可行性](PA_Local_Oracle_Feasibility.md)。
2. 不足以验证H1主动D上的Pc/Pu，更不能测新单支deep真实价格；需要新非提交式H1探针。
3. W3已有可用的标量历史框架，但缺同轨迹真实收益标签、连续sigma及所需低维probe历史；采集规范见[W3规范](W3_Trend_Label_And_Baseline_Spec.md)。
4. 当前CPU实现/9项检查不等于新生产入口或GPU卡就绪。PA/W3的建议1.5GPUh仍不是完整forecast。

证据：[432步决策](../../reports/wc_p_w3_e0_h1_decisions_20261014.json)、[原件CPU回执](../../reports/wc_p_w3_e0_remote_cpu_capture_20261014.json.gz)、[12状态名单](../../manifests/wc_p_acr_h1_state_selection_e0_20261014.json)。
