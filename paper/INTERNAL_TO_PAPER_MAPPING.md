# 内部实现到论文表述的映射

**N08部署准备更新（492）：** 独立Git绑定CPU stage、九命令单次派发与ETA后只读查收工具已补齐，21本地顶层控制通过；实际最终配置、服务器生产CPU和真实测速均未执行，映射中的空结果保持。见[492](../research/492_WC_N08_PRODUCTION_CPU_DEPLOYMENT_AND_ONCE_COLLECTION_PREPARATION_20261016.md)。

更新：2026-10-16。用途：供写作对话直接读取、生成方法描述、图例和实验表格。配套机器索引：[internal_to_paper_mapping.json](internal_to_paper_mapping.json)。

实验是否已完成、目前在途还是待补，以及每项支撑的贡献和优先级，统一读取[实验总表](EXPERIMENT_MASTER_TABLE.md)及[总表机器索引](experiment_master_table.json)。本文件负责名称和实现身份，总表负责实验状态与证据任务。

本文件结合 `worldcache讨论` 最新命名讨论与实际源码、配置和已接受报告编写。**方法名采用暂定显示名称；内部代码、实验ID、配置、原件与SHA保持不变。** 本次整理不改变任何算法、参数或在运行任务。

**2026-10-16 04:57当前证据更新：**[同26D完整36已接受](../research/469_WC_SIMPLE26D_COMPLETE_RESULTS_POSITION_READOUT_AND_STRONG_SIMPLE_BASELINE_20261016.md)，24正式视频/2232帧、全28旧等价和显存回收通过。原阶段plain优于均匀C，前密C/A也是强对照；原H1不宣称优于所有简单规则。N05完整66已于04:56:48准入，[470](../research/470_WC_N05_CORE66_GPU_ADMITTED_AFTER_COMPLETE_N06_AND_1205_COLLECTION_20261016.md)，今天12:05一次查收；N05尚无新质量/速度。下文旧运行/待验语句按各自历史批次读取，实验当前状态以总表为准。

**近邻身份补充：**[471](../research/471_WC_DIRECT_CORRECTION_NEIGHBOR_AUTHOR_SOURCE_CPU_FIDELITY_AND_MAINLINE_BOUNDARY_20261016.md)仅为作者源码/CPU调用核查；AdaCorrection不得标成已接受Cosmos对手，GP-Refiner仍是公开资源缺口。当前N05仅完整11配置。

**共享执行接口更新：**[475](../research/475_WC_SHARED_REGISTRY952_LOCAL_CPU_ACCEPTED_SEED_PARITY_AND_N05_NEXT_20261016.md)完整952本地CPU接受，seed17/43与旧seed0逐步等价桥接成立；这是执行准备，不是最终共同测试、真实Native或新的方法效果。N05仍12:05验收，最终输入/方法未冻。

## 1. 写作入口：先统一这几件事

论文当前主干是 **CFG一致的缓存读出修正＋校准式计算分配**。两个已完成工作点分别展示效率和保真，不拼接成一个配置的“又快又准”数字。

|层级|统一显示名称|当前含义|
|---|---|---|
|总方法，暂定|**CARA-Cache**|CFG-Aligned Readout and Cost-Aware Allocation for Video Diffusion|
|模块一，暂定|**GCR — Guided Cache Readout**|利用当前浅层增量与过去真实D锚点，构造CFG协调的修正读出|
|模块二，暂定|**CPA — Cost-Calibrated Precision Allocation**|按实际读出的误差、传播标定和费用安排计算；当前高保真证据支持校准导出的阶段部署|
|低费用工作点|**CARA-Cache (Efficient)**|内部 `A_NO_P`，RA式联合控制＋阶段β=1修正，无P0|
|高保真工作点|**CARA-Cache (High-Fidelity)**|内部 `TABLE_PHASE_H1`／`H1_MID`；已验证阶段序列的固定部署为 `FIXED_A`|
|来源扩展|Source-Consistent Readout Fusion|针对D/P0参考的相关误差融合；作为来源机制或扩展描述|
|新P探索|Single-Branch Compensated Readout|内部P-ACR；当前为读出，不写成已经实现的缓存刷新|
|新W3探索|Current-Observation / Causal Short-History Risk Estimation|T1/T2真实标签与分组评价路线；尚无新闭环结果|

`CARA-Cache`、`GCR`、`CPA`来自对话中的命名建议，本次没有开展名称查重，不能写“已确认不存在同名工作”。备选 `SARA-Cache` 不与主显示名混用。定稿只改显示映射，不重命名实验原件。

最短阅读路径：本文件 → [当前正文框架](WORLD_CACHE_MAIN_TEXT_OUTLINE_20261014.md) → [420同批结果](../research/420_WC_FULL60_COST_CURVE_COMPLETE_RESULTS_AND_CONVERGENCE_20261014.md) → [417冻结确认](../research/417_WC_FROZEN_CONFIRMATION_FULL50_RESULTS_AND_COST_CURVE_NEXT_20261013.md)。新探索456已完成简单阶段CPU对照，当前状态见[455](../research/455_WC_W3_RAW_COHORT_ACCEPTANCE_GROUPED_T1_T2_RESULTS_AND_PHASE_ATTRIBUTION_20261016.md)，旧448启动身份保留。

## 2. 计算动作：保留数学符号，明确执行语义

|内部符号|论文英文|中文|实际执行和状态语义|
|---|---|---|---|
|`C`|Direct Cache Reuse|直接缓存复用|执行原WC的缓存读出，包括当前probe、窗口插值、warp/head/RF等；不是直接拷贝上一速度张量|
|`A`|Corrected Cache Reuse|修正缓存复用|在普通C读出上加入修正候选，不执行完整深层；两CFG分支使用共享α|
|`D`|Dense Refresh|完整刷新|两分支执行完整深层，更新真实D锚点；不清除已经积累的latent／求解器轨迹偏差|
|`P`|Partial Refresh|部分刷新的动作类别|作为一般符号保留，必须标明具体执行器；不能把所有P实现视为同一方法|
|旧`P`、`P0`|Partial-MLP Refresh|部分MLP刷新|仅若干层的部分token执行MLP；attention、当前调制与gate仍执行。可更新近似工作来源，与真实D不同|
|新`P_c`／`P_u`|Single-Branch Compensated Readout|单CFG分支补偿读出|真实计算一侧深层，另一侧由A＋创新量补偿；当前不更新工作来源或真实D历史|

旧P0选层见 `partial_mlp_deployment_sampling.py` 的 `LAYERS=(4,10,16,22)`，对应实际 `net.blocks[...]` 零起始索引；正式生产范围还须读取所用配置。不能改称“全Block稀疏刷新”或“稀疏注意力”。

CPA中的precision指计算动作的近似保真等级，不表示已经实施低比特量化或改变浮点位宽。

还要区分 **语义动作** 和 **物理双分支执行**：`CC`表示两支走缓存物理路径，语义C和A都可能通过CC实现；`DD`通常对应语义D；`PP`在旧记录中对应P0。原WC基线还可能有DC/CD，不得为排表强行改成共同D。Native整次无缓存参考称 **Full Inference**，不要与单步Dense Refresh混称。

实现入口：

- A/C/D：[`cfg_guided_w1_deployment.py`](../src/wcomr/cfg_guided_w1_deployment.py)、[`cfg_guided_w1_outputs.py`](../src/wcomr/cfg_guided_w1_outputs.py)。
- P0：[`partial_mlp.py`](../src/wcomr/partial_mlp.py)、[`partial_mlp_guided_readout.py`](../src/wcomr/partial_mlp_guided_readout.py)。
- 新P：[`p_acr_readout_r1.py`](../src/wcomr/p_acr_readout_r1.py)，明确记录 `ACR_READOUT_NOT_REFRESH`、`working_source_updated=False`、`true_D_updated=False`。

## 3. 当前主结果与消融：准确映射每一个配置

下表的论文名是显示标签。稳定身份由“实验命名空间＋内部ID＋配置SHA／参数fingerprint”确定，不能只搜索一个同名字符串。

|内部ID与命名空间|论文显示名|实际区别|论文位置／证据|
|---|---|---|---|
|`NATIVE`／`Native`|Full Inference|当前相同模型、输入、噪声和采样器的无缓存参考|主结果参考；420、417|
|`WC`|WorldCache|官方思路在当前本地协议的实现|主基线；420。不要写“已完成论文原设置完整复现”|
|`RA`；部分旧批次`SOURCE_RA`|RA-CFGCache (local port on WorldCache)|本地移植、校准的CFG联合控制器|主基线；核对各批次配置，不与作者论文数字拼接|
|`A_NO_P`|CARA-Cache (Efficient)|RA式联合C/D选择；复用时执行D参考、阶段β=1修正；禁用P0|效率主工作点；420、417、374|
|`TABLE_PHASE_H1`；后续`H1_MID`|CARA-Cache (High-Fidelity)|来源×阶段absolute guided MSE标定，λ=525.1463509809399；通用合法集含C/A/P0/D|高保真工作点；403、417、420|
|`FIXED_A`|Fixed-Schedule Corrected Reuse|完整36步固定D/A/C计划，跳过表评分／argmin，仍付probe、合法性及缓存维护|同预算读出消融；420。作为High-Fidelity的已验证部署控制，不与H1合并统计|
|`FIXED_PLAIN`|Fixed-Schedule Direct Reuse (matched dense refreshes)|与FIXED_A相同D位置，将五次A全部换C|同26D归因；420|
|`TABLE_POOLED_H1`|Source-Only Calibration|同一absolute-MSE框架，合并EARLY/LATE，只按来源分格|阶段分格相关对照；403。不是未执行的`H1_SOURCE_ONLY`占位名|
|`H1_LOW`|CPA (λ/4)|λ=131.28658774523498|参数敏感性；420|
|`H1_MID`|CPA (λ)|λ=525.1463509809399；同一个主配置，不新增独立样本|参数敏感性／主配置复用；420|
|`H1_HIGH`|CPA (4λ)|λ=2100.5854039237597|参数敏感性；420。不要按名字直接宣称更高质量|
|`P_OFF`|Source-Gated Correction (P0 enabled)|P0仍可执行；仅在P来源上关闭A，D来源上仍可A|可选质量工作点／来源对照；380、403、417、420|
|`SOURCE_FIXED`|Fixed Source-Consistent Readout Fusion|固定来源一致融合，使用原来源控制，不是新的H1优化器|来源机制／开发对照；380|

**P_OFF绝不显示成“w/o P”或“无部分刷新”。** 若需要以总方法标注，可写 `CARA-Cache + P0 (D-source correction)`；短表格仍优先使用上表的明确名称。

**H1_MID与FIXED_A是输出等价控制关系，不是所有输入下的数学同义词。** 已验收开发四CAL与冻结确认的H1轨迹均为26D/0P/5A/5C；420直接比较的四CAL中MID／FIXED_A逐步、终态与RGB一致。不能由此预设新EXPL_DEV父轨迹必然不含P0，也不能把两行视为两个独立有效方法。

## 4. 历史名称：按版本解释，避免“同名换算法”

|历史代码／实验名|建议论文或附录名|准确身份|
|---|---|---|
|旧W1标量拟合／shrink|Scalar Incremental Calibration / Residual Shrinkage|早期开发近似器；不等于当前β=1阶段读出|
|`BETA1_ONE_PHASE`|Unit-Gain Correction with Phase Scaling|β固定1；名字含ONE_PHASE，但α实际按第25步边界取1／0.5|
|`KEEP`、`WORKING_P_AGE_KEEP_INTERVAL`|Retained-Accumulation Source Rule|来源／累计风险规则；不是独立整套方法|
|`NONZERO`、`WORKING_P_AGE_NONZERO_REBASE`|Nonzero Source-Risk Rebaselining|带非零出生误差的来源重基准规则；和KEEP分开，不混合最优结果|
|`KEEP_A_P`／`A_CPD_BETA1_ONE_PHASE`（KEEP批次）|Guided Correction with Partial Refresh (retained accumulation)|374双场景正反测速中的组合配置；不等于后来的P_OFF|
|E3阶段W1／阶段β=1＋P|Partial Refresh with Incremental / Unit-Gain Correction|369两规则×四CAL×八方法的组合开发结果；KEEP收益不证明P独立增益|
|`SOURCE_H1`（N2）|One-Step Normalized-Error Controller (legacy)|380旧normalized-error horizon1；不等于TABLE_PHASE_H1|
|`SOURCE_H2`（N2）|Two-Step Proxy Lookahead Controller (legacy)|380旧horizon2经验预测；不是实际未来rollout或学习的终点动作价值|
|`H2_P_TO_D`|P-to-D Replacement Control|旧H2动作历史中的P替换D对照；不冒称新策略|
|F：RAW／Haar／FFT|Spectral Risk-Feature Probe (archived)|预测／特征探索，已结束；预测误差改善不等于调度改善|
|B：Block reuse／velocity injection|Block-Reuse Diagnostic (archived)|完整端点混合，已结束且未合入；保存实际C缓存与离线速度注入的实验语义|

内部 `H1` 单独出现时必须先确认：是早期缓存寿命实验、N2 normalized horizon1，还是冻结absolute source×phase版本。后者的主入口为 [`source_phase_absolute_h1_control_r1.py`](../src/wcomr/source_phase_absolute_h1_control_r1.py)，VERSION=`SOURCE_PHASE_ABSOLUTE_GUIDED_MSE_FOUR_ACTION_H1_R1`。

### E3完整64的八个原始方法ID

以下只在 `E3_COMPLETE64` 命名空间解析；每项还必须保留KEEP／NONZERO来源规则。不能只看名字就换成后来的420配置。

|E3原始ID|论文显示名|职责|
|---|---|---|
|`SOURCE_RA`|RA-CFGCache (E3 local reference)|本批原RA参考|
|`DYNAMIC_NO_P`|No-Partial-Refresh Controller Control|移除P0的控制路径；本批与SOURCE_RA输出一致|
|`CPD`|Reuse–Partial–Dense Baseline|不使用A的C/P0/D基线，绑定具体来源规则|
|`REF_CPD`|Reference Partial-Refresh Execution Control|P0执行器的参考计算路径；本批与CPD保真一致，不当成新的算法收益|
|`A_CPD_OFF`|Correction-Disabled Wrapper Control|关闭A修正的包装等价控制；本批与CPD一致|
|`A_CPD_W1_ONE_PHASE`|Partial Refresh + Scalar Incremental Correction|阶段缩放的拟合β修正＋P0|
|`A_CPD_BETA1_ONE_PHASE`|Partial Refresh + Unit-Gain Correction|阶段缩放的β=1修正＋P0|
|`DENSE_CONTROL`|All-D Execution Control|强制真实完整计算并与Native核对；不是RA或P0候选|

后来的N2 `NONZERO_CPD` 显示为 **Reuse–Partial–Dense Baseline (nonzero rebasing)**，绑定 `N2_LEGACY`，不无条件替换成E3的CPD。实现入口为 `source_aware_partial_sampling.py`、`real_working_epoch_parameters_r1.py` 和 `e3_complete64_block_scope_r1.py`。

## 5. 新P／W3探索：命名不提前升级证据

|内部名|准确显示名|截至本文件的状态|进入正文的条件|
|---|---|---|---|
|P/W3 `E0`，426|Offline Single-Branch Compensation Analysis|旧16状态；来源×阶段Pu系数按prompt留出，guided MSE均值下降37.2996%，14/16点、4/4提示词改善|可作局部机制，不当作单分支真实费用、闭环LPIPS或新来源寿命证据|
|`P-ACR`／`Pc/Pu`|Single-Branch Compensated Readout (exploratory)|执行器和CPU已准备；PA528尚未选定启动；不更新来源|真实误差—费用和闭环验证后再决定纳入|
|建议的`SBR`|Single-Branch Refresh (reserved)|为以后具有合法来源写回的版本保留名称；当前不是已完成模块|真正实现并验证缓存来源更新后再用|
|`W3_LABEL64`／`FULL864`|Same-State C/A/D Supervision Collection|455验收80原件/1104张量/64真实标签，主6prompt/48点、raw敏感性7/56；1坏视频/2文本拒绝保留|已接受有缺口监督子集；不等于新策略端点或整卡全成功|
|`T0`|Source-and-Phase Table Baseline|冻结旧H1标定表|新预测器的参考，不重新命名成新方法|
|`T1`（当前执行规范）|Current-Observation Risk Estimator|13维Ridge1/window4，prompt LOPO局部regret下降64.83%，6/6改善；参数离线冻结|456仅时间/第23步规则已解释几乎全部局部收益；内容自适应增量未确认，闭环待讨论，未并入主方法|
|`T2`（当前执行规范）|Causal Short-History Risk Estimator|27维Ridge1/window4，主组regret上升24.56%；保留负风险截断的大代价反例|原clip配置保留；456固定负值回退修复大反例，但两组未一致胜过简单规则，不扩频谱/网络|
|`T_TIME / T_STEP_TABLE / STEP23_A_ONLY_POSTHOC`|Phase-Only Allocation Controls|仅时间、训练折内逐步表、事后固定第23步规则；456完成6/48主组和7/56敏感性CPU评价|解释T1几乎全部局部收益；第23步仅开发候选，尚无闭环、速度或统计等价主张|
|`W3-MixTrend`|Trend-Aware Allocation (exploratory umbrella)|研究方向名，不表示已移植或验证MixLinear网络|冻结实际实现后给出具体结构与消融|
|`T3`长期低秩；`T4`频谱|Proposed Long-History Extension / Inactive Spectral Extension|T3为后备，T4本轮不执行；不重启F/B|不列为已有贡献或已有表格行|

对话最初曾把T1写成“含局部趋势”，T2写成“MixLinear双路径”；**以当前仓库规范为准：T1当前观察，T2因果短历史，长期分支为后备T3。** 见[W3标签与基线规范](../research/p_w3_e0_20261014/W3_Trend_Label_And_Baseline_Spec.md)。

原W3已在455接受有缺口监督子集并完成CPU分组评价；456完成简单阶段对照。当前无新W3策略视频。原同26D显存修复R2仍按04:55一次验收，本轮未查其partial或改变任务。

## 6. 数学符号到代码：可直接用于Method的定义

以下是当前β=1主读出的表达，不覆盖全部历史拟合版本。

令 `o` 为Transformer输入、`h^k` 为probe输出、`h^L` 为完整栈输出，分支b的

\[
p_t^b=h_t^{k,b}-o_t^b,\quad r_t^b=h_t^{L,b}-o_t^b,\quad d_t^b=r_t^b-p_t^b.
\]

过去真实D锚点为s，β=1候选为

\[
\widehat r_t^{b,D}=r_s^b+(p_t^b-p_s^b)=p_t^b+d_s^b.
\]

定义完整实际输出路径 `Φ_t^b(rhat;W)` 为 `warp(o+rhat,r_W)` → head/unpatchify → 原RF转换。对WC读出 `v_C^b`，

\[
v_{A,D}^b=(1-\alpha_t)v_C^b+\alpha_t\Phi_t^b(\widehat r_t^{b,D};W),\quad
\alpha_t=\begin{cases}1&t<25\\0.5&t\ge25.\end{cases}
\]

α共享于两分支，混合发生在 **post-RF branch velocity**；不能把warp前hidden混合直接写成同一个实现。当前参数guidance=7的实际合成为

\[
v_g=(1+7)v_c-7v_u=8v_c-7v_u.
\]

`u`在本地输入中精确为negative-prompt CFG branch；若用“unconditional”简称，首次定义应说明，不能声称负分支输入必然为空文本。

|论文符号|含义／代码|不可混称|
|---|---|---|
|β|`calibration.py`中的残差增量系数；一般按分支拟合，当前主配置固定1|不是CFG共享α；β≈1也包含Δr自身含Δp的结构|
|α_t|`cfg_guided_w1_deployment.py`中的共享阶段修正强度|不是学习出的调度概率|
|γ_src|`math_source_fusion_r1.py`中的D/P参考融合系数，冻结0.7235237005554214|不是传播g、CFG guidance或原WC插值系数|
|Γ_WC|原WC窗口／残差插值算子|不是新γ_src|
|g_t|`cfg_ra_calibration_table.py`中的同状态CC/DD差经完整后缀传播的幅度比|MSE评分用g_t²；不是严格Jacobian上界|
|q_a|冻结H1的absolute guided velocity MSE估计；新标签从真实同状态D重算|不是LPIPS、终点风险真值或旧normalized proxy|
|λ|秒／传播加权MSE的权衡系数|LOW/MID/HIGH不代表已知单调性能排序|
|c_a|已支付两支probe之后的双分支动作增量费用|不是整个视频耗时；完整测速仍支付probe与正常维护|

CPA开发期评分为

\[
a_t=\arg\min_{a\in\mathcal A_t}\{c_{a,source}+\lambda g_t^2\widehat q_a\}.
\]

它是校准的局部决策规则。当前高保真已验部署可冻结为 `D1–24, A25–29, C30, D31, C32–35, D36`。描述为 **calibration-derived phase schedule**，不写成已证明内容自适应优越性。新T1/T2的监督若已经采用 `r_A=g²q_A, Δr=g²(q_C−q_A)`，决策时不能再次乘g²。

P-ACR当前实际读出是

\[
P_c=(v_c^D,\ v_u^A+\eta(v_c^D-v_c^A)),\qquad
P_u=(v_c^A+\zeta(v_u^D-v_u^A),\ v_u^D).
\]

在线支付所选一侧的真实D计算；额外省略侧的完整D教师只用于离线评分，不是部署输入。补偿系数来自严格过去或冻结开发标定，不能把逐点oracle系数当在线可用输入。

## 7. 可引用数字：保持批次、分母和计时口径

### 7.1 同批开发主比较：420，四CAL、seed0

40正式＋20完整预热；每方法每场景一次正式主计时。以下是同一批的四场景均值；速度为总Native主时间÷总候选主时间，LPIPS按场景等权。

|内部ID|论文名／短标签|主秒数|全帧LPIPS↓|相对Native加速|
|---|---|---:|---:|---:|
|NATIVE|Full Inference|282.5169|0|1.0000×|
|WC|WorldCache|172.5761|0.4256468|1.6371×|
|RA|RA-CFGCache (local port)|146.8057|0.4186104|1.9244×|
|A_NO_P|CARA-Cache (Efficient)|148.8959|0.3781446|1.8974×|
|P_OFF|Source-Gated Correction (P0 enabled)|156.7193|0.3570513|1.8027×|
|H1_LOW|CPA (λ/4)|221.9447|0.0607302|1.2729×|
|H1_MID|CARA-Cache (High-Fidelity) / CPA (λ)|222.9058|0.0585928|1.2674×|
|H1_HIGH|CPA (4λ)|222.9911|0.0682856|1.2669×|
|FIXED_A|Fixed-Schedule Corrected Reuse|222.8900|0.0585928|1.2675×|
|FIXED_PLAIN|Fixed-Schedule Direct Reuse|222.0137|0.0607302|1.2725×|

这批可写：Efficient相对WC主时间少13.72%、LPIPS失真低11.1600%；相对RA主时间多2.0903秒、失真低9.6667%。同26D下FIXED_A比FIXED_PLAIN失真低3.5196%、多0.8762秒，3/4场景改善。百分比由候选与基线各自的四场景等权LPIPS均值计算，不是逐场景百分比的平均。不要把速度1.8974×与下面确认批的LPIPS 0.0530368组合为一个方法点。

### 7.2 冻结新输入确认：417，四提示词×两个seed

该批50完整路径中40正式；39正式视频兼容评分，RA的一个视频被拒绝且保留。先提示词内平均seed，再按提示词等权。

|内部ID|兼容视频／8|平均主秒数|完整四提示词LPIPS|
|---|---:|---:|---:|
|NATIVE|8|283.5403|0|
|RA|7|149.5848（含全部8次运行）|缺失；不填完整均值|
|A_NO_P|8|149.6402|0.3490875|
|P_OFF|8|157.4421|0.3444344|
|TABLE_PHASE_H1（报告简称H1）|8|223.5968|0.0530368|

高保真点相对Native为1.2681×；相对A_NO_P失真低84.8070%，8/8视频改善。RA相关质量比较必须限定7个实际配对，不能把RA七视频均值与其它八视频均值直接比。93帧是视频内覆盖，不是93个独立样本。

### 7.3 其它证据的论文职责

|报告／实验|论文中的职责|保持的身份|
|---|---|---|
|374 CLEAN_SPEED20|双场景正反顺序重复计时／顺序波动|20正式＋20预热；与420每格一次计时区别，不叫大规模稳定测速|
|369 E3完整64|来源规则与修正读出的交互|KEEP阶段W1／β1改善13.6735%／12.7233%；NONZERO相同组合有反例；不是P净加速证据|
|380旧N2|读出、风险目标与动作下包络的设计分析|旧SOURCE_H1/H2中A未被选择；不是新TABLE_PHASE_H1结果|
|403 absolute H1|absolute guided MSE标定与来源／阶段对照|开发24正式视频；来源与阶段变化伴随计算配额变化|
|426 P/W3 E0|单支创新补偿的离线机制|真实旧张量上的CPU再分析；不是新单支GPU执行或视频收益|
|441/447 CPU|采集恢复、因果隔离与生产准备|Toy数值/接口控制；不列为质量或加速主结果|
|448 W3启动|执行状态／下一证据入口|尚无本卡新策略结果|

所有主计时均要逐批核对。当前clean口径是模型驻留后的文本编码＋去噪＋VAE，正常算法缓存／修正／路由／head开销保留；加载、预热、写盘等另列。研究取证复制／哈希／保存去除。GPUh是实验全wall费用，不能当生成延迟。LPIPS是接近匹配Native的保真失真，不是物理质量或“质量保留率”。

## 8. 正文、图表和消融的显示规则

|位置|建议标题／显示内容|使用依据|
|---|---|---|
|Method Overview|CARA-Cache: Guided Cache Readout and Calibrated Allocation|两个核心模块，不按W1→W3实验历史画图|
|Method 3.2|Guided Cache Readout|当前probe＋D锚点＋共享α，必要时来源融合|
|Method 3.3|Cost-Calibrated Precision Allocation|实际误差／费用标定与阶段部署；趋势增强待结果后加入|
|主表／主图|Quality–Efficiency Trade-off|同协议Full Inference／WC／RA与两个独立工作点|
|消融|Effect of Readout Correction under Matched Dense Refreshes|FIXED_A／FIXED_PLAIN，同D位置|
|消融|Source and Phase Calibration|TABLE_PHASE_H1／TABLE_POOLED_H1，注明配额变化|
|敏感性|Effect of the Cost–Distortion Weight λ|LOW／MID／HIGH的原值，保留非单调结果|
|机制|Source-Consistent Readout and CFG Error Structure|D/P参考、相关融合及局部真实标签|
|部署|Runtime and Calibration Cost|计时边界、正常维护、离线标定和显存；最小profile尚待|

对话提出的 `w/o Phase Scaling`、`w/o Source-Aware Readout`、`w/o CFG-Coordinated Scaling` 是**候选消融名称**，本次没有补做这些实验，不能据名称生成已完成结果行。`TABLE_POOLED_H1`是风险表不分阶段，不等于取消A的α阶段缩放。无P且全D来源时，删除P来源融合可能是no-op，也不能伪装成有效消融。

通用的第二骨干／跨任务泛化、同费用调优WC/RA、少步Native、共同最终测试、重复clean计时和部署自动质量，仍有待补；同26D简单调度现已在469完整接受，N05调优基线正在运行。已完成的417新提示词双seed确认可单独报告，不等于已完成以上全部泛化。

## 9. 写作句子与术语边界

可作为当前摘要／引言的起点：

> We introduce CARA-Cache, a frozen-backbone framework that combines CFG-aligned cache readout correction with calibrated compute allocation for video diffusion.

> Its efficient and high-fidelity configurations provide distinct fidelity–runtime operating points, while matched-refresh controls isolate the contribution of corrected reuse.

高保真实现可以写：

> The calibrated policy admits a phase-scheduled deployment that reproduces the evaluated high-fidelity outputs.

以上是推荐句式，最终量化结论绑定第7节批次。`frozen-backbone`对当前和小预测器增强都较稳妥；若拟合Ridge/小网络，明确为offline-fitted risk estimator。`training-free`只有在清楚定义为无需生成器训练并披露离线标定时才使用；不要写“无需任何标定或学习”。

当前不使用以下扩大表述：内容自适应路由已独立胜出、完整四动作连续Pareto前沿已成立、P0已显著节省总时间、新P已刷新并延长来源寿命、新W3趋势已提高最终视频、全局最优／Kalman保证／物理定律保证。它们各自需要对应实验或数学前提，不能通过改名获得。

## 10. 机器索引和复现绑定

机器索引为 [internal_to_paper_mapping.json](internal_to_paper_mapping.json)。优先以 `id` 查询；`internal_aliases` 带命名空间。每个条目包含显示名、论文角色、实现入口、配置绑定、证据和状态。文件级 `file_bindings` 保存本次实际SHA；证据批次另记录当时运行source，不用当前Git HEAD替换历史source。

关键批次：

|命名空间|配置／参数|当时source|
|---|---|---|
|`CLEAN_SPEED20`|`configs/wc_clean_speed20_r1_20261012.json`|以374及原launch为准|
|`E3_COMPLETE64`|`configs/wc_e3_complete64_production_r1_20261011.json`，另保留来源规则|以369及原launch为准|
|`N2_LEGACY`|`configs/wc_math_n2_full36_production_r2_20261012.json`|以380及原launch为准|
|`ABS_H1_CAL24`|`configs/wc_source_phase_h1_full24_production_r1_20261013.json`|`595382e6dcfda3dfca98b4a80cf800359e6ff3db`|
|`FROZEN_CONFIRM50`|`configs/wc_source_conditional_confirmation_full50_production_r1_20261013.json`|`e48ba58047b09507ea6f438f5077ebffb4fb2114`|
|`COST_CURVE60`|`configs/wc_h1_cost_curve_full60_production_r1_20261013.json`|`361ea5c9372332299f7ca29dbffe0ab942274d0f`|
|`W3_LABEL864`|`manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json`|`047dcf181a3ab706002b2965e74b626e4648deea`|

冻结absolute source×phase参数fingerprint：`34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8`。旧N2参数fingerprint：`39e7f0feb3648dbabe8a98d842bd1d60fa03bd1800259513c5da7c9d976fc9c0`。配置SHA和fingerprint是不同对象，不能互换。

## 11. 给另一个写作对话的接续提示词

**2026-10-15 23:00补充：同26D简单规则卡已因OOM终态；12warm及16正式通过部分原件审计，整卡未接受。** 名称映射如下，命名空间 `SIMPLE26D_FULL36`、source36f5583，原24正式＋12完整预热分母不变；1失败＋7未到达。三个输入完成fixed/uniform配对、两个完成front配对，不填四场景均值。详见[451](../research/451_WC_SIMPLE26D_PARTIAL_RESULTS_OOM_TERMINAL_AND_PAPER_IMPLICATIONS_20261015.md)和总表N06。

| 内部方法 | 论文表述 | 执行身份 |
|---|---|---|
| `FIXED_A` | Calibrated Phase Schedule + Corrected Reuse | 原420固定26D/5A/5C |
| `FIXED_PLAIN` | Calibrated Phase Schedule + Direct Reuse | 同原D位置，26D/10C |
| `UNIFORM_A` | Uniform 26D + Corrected Reuse | 预先均匀D位置，26D/10A |
| `UNIFORM_C` | Uniform 26D + Direct Reuse | 同uniform D位置，26D/10C |
| `FRONT_DENSE_A` | Front-Dense 26D + Corrected Reuse | 粗前密后疏D位置，26D/10A |
| `FRONT_DENSE_C` | Front-Dense 26D + Direct Reuse | 同front D位置，26D/10C |

这是**相同完整刷新配额的简单调度对照**，A次数和总成本没有强行写成相同。所有A使用同一冻结的阶段读出。与W3并发期间的时间统一为 `CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY`，只用于诊断，不作为正式净加速主张。名称映射不代表均匀或前密规则已优于/劣于当前工作点。

```text
请先读取：
/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr/paper/INTERNAL_TO_PAPER_MAPPING.md
及同目录 internal_to_paper_mapping.json，再读取 WORLD_CACHE_MAIN_TEXT_OUTLINE_20261014.md。

以映射中的暂定CARA-Cache、GCR、CPA组织正文，保留C/A/P/D数学符号；
内部方法身份、文件名、配置和SHA不重命名。按命名空间区分旧N2 H1与新absolute H1，
P_OFF仍含P0，新P-ACR当前为单分支补偿读出，不能写成已经实现来源刷新的SBR。
效率A_NO_P和高保真H1/固定A作为不同工作点；420开发比较与417冻结确认分别引用。
新W3标签和P增强尚未合入主线，不把运行、CPU通过或局部oracle写成视频／速度收益。
若有更新的完整结果报告，先核对后更新映射状态，不从在跑任务的partial推断结论。
```

**456更新：**[T1与简单阶段对照](../research/456_WC_T1_VS_SIMPLE_PHASE_CPU_RESULTS_AND_VIDEO_DECISION_20261016.md)：主组T1/时间-only/仅23步regret为0.339971/0.340532/0.337549，敏感性为0.329269/0.332689/0.330417。新增表述用“Phase-Only Allocation Controls / Post-hoc Step-23 Override”；不把本批结果写成新策略端点或已证明内容自适应。后续优先讨论简单阶段完整视频确认，原主方法及04:55同26D验收保持。

**457执行准备：**第23步规则与冻结T1已通过独立owner/controller接口接入既有执行器，六标量控制通过；四配置完整72路径本地Toy CPU已派发，02:28一次查收。仅标为执行准备，不记生产CPU或新视频结果；原同26D04:55验收不变。入口：[457](../research/457_WC_PHASE_RUNTIME_SCALAR_ACCEPTED_FULL72_LOCAL_CPU_LAUNCH_20261016.md)。

**458技术更新：**本地完整CPU R1因缺模块源码元信息/辅助函数绑定在首采样前退出；两处装载修复和严格编译检查通过，完整R2已于02:32派发，02:44收。原方法和冻结参数不变，不据此写新方法失败或CPU72已通过。见[458](../research/458_WC_LOCAL_FULL72_R1_NAMESPACE_FAILURE_R2_REPAIR_AND_RELAUNCH_20261016.md)。

N09记录接口完整102 Toy CPU已在[478](../research/478_WC_N09_FULL102_CPU_PARITY_ACCEPTED_COMPONENT_PEAK_PROFILE_READY_20261016.md)接受；对应实现准备，不是论文新质量/速度或真实CUDA峰值证据。

N10的视频/原提示词身份、采样规则和双seed提示词统计已做CPU准备，见[479](../research/479_WC_N10_IDENTITY_INPUT_SAMPLING_AND_GROUPED_METRICS_CPU_READY_20261016.md)；真实指标模型、资源与最终评分尚待，不把合成分数作为论文结果。

N07原始1044文本请求字节与参数绑定已做CPU准备，见[480](../research/480_WC_N07_ORIGINAL1044_BYTES_AND_PRODUCTION_ARGUMENT_BINDING_CPU_READY_20261016.md)；最终选择、实际生产CPU和GPU卡未完成，不是泛化结果。

N07完整范围/来源/费用绑定与具体批准大卡的独立准入接口CPU准备见[481](../research/481_WC_N07_COMPLETE_SCOPE_CONTRACT_NUMERIC_REUSE_AND_APPROVED_LARGE_CARD_POOL_CPU_READY_20261016.md)；99份数值依赖未变，真实生产CPU、最终scope和GPU未接受。

N07驻留运行器与完整180调度CPU准备见[482](../research/482_WC_N07_RESIDENT_RUNNER_AND_FULL180_FAILURE_PRESERVING_BATCH_CPU_READY_20261016.md)；10项检查使用synthetic callback，实际模型/生产CPU与结果仍待。

N07完整180终态审计/配对93帧评分与N10身份接线CPU准备见[483](../research/483_WC_N07_FULL180_POST_AND_93FRAME_SCORE_CPU_PREPARATION_20261016.md)；八控制为合成输入/度量及小型CPU张量，不是实际视频或LPIPS结果。最终方法/输入/实际生产CPU仍待N05接受后冻结。

N07单次运行/查收/独立汇总代码及Native原字段对齐见[484](../research/484_WC_N07_LIFECYCLE_NATIVE_RECEIPT_ALIGNMENT_AND_INDEPENDENT_ACCEPTANCE_CPU_READY_20261016.md)；31CPU控制含72份旧Native计数字段。该字段修正只涉及未部署的N07元数据检查，不改变算法或原N05；真实新输入/生产CPU/质量速度仍未验。

N08完整40执行适配/计时分列CPU准备见[485](../research/485_WC_N08_FULL40_EXECUTION_BINDING_AND_OBSERVED_TIMER_CPU_READY_20261016.md)；新增6项执行控制，连同受影响共17通过，实际绑定仍null。主计时与原协议不改，真实驻留生产CPU、干净资源与速度尚待。

N07 Git绑定打包、生产CPU六命令查收和远端路径别名接线见[486](../research/486_WC_N07_GIT_BOUND_CPU_PACKAGING_AND_CANONICAL_PATH_PREPARATION_20261016.md)；25本地控制通过，133源码仅静态核对。真实配置、实际CPU与新视频结果仍未完成，原N05不改。

N07 fresh身份审计工具与13本地CPU控制见[487](../research/487_WC_N07_FRESH_IDENTITY_AUDIT_CPU_READY_AND_MAINLINE_ORDER_20261016.md)；实际远端曝光审计、最终八输入/十方法冻结仍待N05完整接受，未产生新泛化或速度结果。

N08完整40驻留入口/生产合同与预热接口修复见[488](../research/488_WC_N08_RESIDENT_FULL40_PRODUCTION_ENTRY_AND_WARM_INTERFACE_REPAIR_CPU_READY_20261016.md)：22本地CPU通过，原R1失败保存；五角色随N07方法在开发阶段一并冻结。真实模型/生产CPU/干净资源/视频与速度尚未接受，不升级任何论文结果。

N08完整40原件/预热等价性、同轮Native的93帧评分和失败隔离见[489](../research/489_WC_N08_FULL40_CPU_POST_REPEAT_PARITY_SAME_ROUND_FIDELITY_AND_FAILURE_ISOLATION_READY_20261016.md)；15本地CPU控制通过。合成视频/指标不填论文速度质量结果，实际生产CPU/监督/独立验收与最终clean计时仍未完成。

N08七命令生产CPU准入、单次派发与原v2结算接线见[490](../research/490_WC_N08_SEVEN_COMMAND_CPU_GATE_SINGLE_DISPATCH_AND_UUID_SETTLEMENT_READY_20261016.md)；26本地CPU控制使用临时账本/mock进程，不是真实服务器CPU或GPU结果。原窗口、真实最终配置和GPU收集/完整独立接受缺口保留。

N08完整40独立接受与N07注册SHA查收字段修复见[491](../research/491_WC_N08_FULL40_INDEPENDENT_ACCEPTANCE_AND_N07_CAPTURE_REGISTRATION_REPAIR_CPU_READY_20261016.md)；23本地控制通过（合成回执，含标准库独立解释器）。真实CPU部署/最终方法/视频/速度未接受，N08未来实际CPU入口现9命令。
